import logging
import random
import time
import requests
from django.conf import settings
from core.exceptions import ScraperException
from core.security import validate_outbound_url, MAX_RESPONSE_BYTES

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


def _http_get_with_impersonation(url: str, headers: dict, timeout: int = 30):
    """
    Attempt HTTP GET using curl_cffi with Chrome 124 browser impersonation (JA3/JA4 TLS
    signature spoofing). Falls back to standard requests if curl_cffi is unavailable.

    TLS verification is ALWAYS enabled. Disabling verify=True would allow a
    man-in-the-middle to serve fake content and bypass our change detection entirely.
    Government portals with self-signed certs should add their CA to the system
    trust store, not disable verification globally.
    """
    # SSRF guard: validate before any network I/O.
    validate_outbound_url(url)

    try:
        from curl_cffi import requests as curl_requests
        response = curl_requests.get(
            url,
            headers=headers,
            timeout=timeout,
            verify=True,       # MUST be True : never disable TLS verification
            impersonate="chrome124",
            allow_redirects=True,
            stream=True,       # stream to enforce size cap before reading
        )
        # Enforce response size cap before loading body into memory.
        # A 500MB HTML response from a malicious server would OOM-kill the worker.
        content_bytes = b''
        for chunk in response.iter_content(chunk_size=65536):
            content_bytes += chunk
            if len(content_bytes) > MAX_RESPONSE_BYTES:
                raise ScraperException(
                    f"Response from {url!r} exceeded {MAX_RESPONSE_BYTES // (1024*1024)}MB limit. Aborted."
                )
        response._content = content_bytes
        return response

    except ScraperException:
        raise
    except Exception as curl_err:
        logger.debug(f"curl_cffi impersonate failed for {url} ({curl_err}), falling back to standard requests.")

        # Fallback: requests with streaming + size cap.
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            verify=True,       # TLS verification always on
            allow_redirects=True,
            stream=True,
        )
        content_bytes = b''
        for chunk in response.iter_content(chunk_size=65536):
            content_bytes += chunk
            if len(content_bytes) > MAX_RESPONSE_BYTES:
                raise ScraperException(
                    f"Response from {url!r} exceeded {MAX_RESPONSE_BYTES // (1024*1024)}MB limit. Aborted."
                )
        response._content = content_bytes
        return response


def scrape_portal(url: str, method: str = 'HTTP', is_blocked: bool = False, custom_headers: dict = None) -> tuple[str, int, int]:
    """
    Fetch content from a portal URL using HTTP (with TLS browser impersonation),
    Playwright, or PDF parsing.
    Returns: (raw_content_str, http_status_code, response_time_ms)

    Every outbound request passes through the SSRF guard in
    _http_get_with_impersonation before any network I/O occurs.
    """
    import urllib.parse

    parsed = urllib.parse.urlparse(url)
    domain_referer = f"{parsed.scheme}://{parsed.netloc}/" if (parsed.scheme and parsed.netloc) else url

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': domain_referer,
        'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
    }
    if custom_headers:
        headers.update(custom_headers)

    if is_blocked:
        delay = random.uniform(3.0, 8.0)
        logger.info(f"Applying randomized delay of {delay:.2f}s before scraping firewalled portal: {url}")
        time.sleep(delay)

    start_time = time.time()

    if method == 'HTTP':
        try:
            response = _http_get_with_impersonation(url, headers=headers, timeout=30)
            scrape_portal.last_content_type = response.headers.get('Content-Type', '')
            response_time_ms = int((time.time() - start_time) * 1000)
            content = response.text.replace('\x00', '') if response.text else ''
            return content, response.status_code, response_time_ms
        except ScraperException:
            raise
        except Exception as e:
            logger.warning(f"HTTP scrape failed for {url}: {e}")
            raise ScraperException(f"Failed to scrape {url}: {str(e)}")

    elif method == 'PLAYWRIGHT':
        # Try fast curl_cffi HTTP impersonation first (bypasses Cloudflare & JS checks
        # in ~500ms without spawning heavy Chromium)
        try:
            response = _http_get_with_impersonation(url, headers=headers, timeout=20)
            if response.status_code == 200 and response.text and len(response.text) > 200:
                scrape_portal.last_content_type = response.headers.get('Content-Type', '')
                response_time_ms = int((time.time() - start_time) * 1000)
                content = response.text.replace('\x00', '')
                return content, 200, response_time_ms
        except ScraperException:
            raise
        except Exception as http_err:
            logger.debug(f"HTTP impersonation before Playwright failed for {url}: {http_err}")

        # Fall back to Playwright headless browser if HTTP impersonation returned non-200.
        # The SSRF guard already ran above; we do not need to re-validate here
        # because the URL is unchanged.
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=20000)
                page.wait_for_timeout(1000)
                content = page.content()
                scrape_portal.last_content_type = 'text/html'
                response_time_ms = int((time.time() - start_time) * 1000)
                browser.close()
                return content.replace('\x00', '') if content else '', 200, response_time_ms
        except Exception as e:
            logger.warning(f"Playwright scrape failed/unavailable for {url}: {e}.")
            raise ScraperException(f"Playwright failed for {url}: {str(e)}")

    elif method == 'PDF':
        try:
            import pdfplumber
            import io
            response = _http_get_with_impersonation(url, headers=headers, timeout=30)
            scrape_portal.last_content_type = response.headers.get('Content-Type', 'application/pdf')
            if response.status_code != 200:
                raise ScraperException(f"Failed to download PDF: HTTP {response.status_code}")

            with pdfplumber.open(io.BytesIO(response.content)) as pdf:
                pages_text = [page.extract_text() or '' for page in pdf.pages]
                content = '\n'.join(pages_text)

            response_time_ms = int((time.time() - start_time) * 1000)
            return content.replace('\x00', '') if content else '', 200, response_time_ms
        except ScraperException:
            raise
        except Exception as e:
            logger.warning(f"PDF scrape failed/unavailable for {url}: {e}. Falling back to HTTP.")
            try:
                response = _http_get_with_impersonation(url, headers=headers, timeout=30)
                scrape_portal.last_content_type = response.headers.get('Content-Type', '')
                response_time_ms = int((time.time() - start_time) * 1000)
                content = response.text.replace('\x00', '') if response.text else ''
                return content, response.status_code, response_time_ms
            except ScraperException:
                raise
            except Exception as req_err:
                raise ScraperException(f"PDF failed and fallback HTTP failed: {str(req_err)}")

    else:
        raise ScraperException(f"Unsupported scrape method: {method}")
