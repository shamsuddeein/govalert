import logging
import random
import time
import requests
from django.conf import settings
from core.exceptions import ScraperException

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


def _http_get_with_impersonation(url: str, headers: dict, timeout: int = 30):
    """
    Attempt HTTP GET using curl_cffi with Chrome 124 browser impersonation (JA3/JA4 TLS signature spoofing).
    Falls back to standard requests if curl_cffi is unavailable or fails with an environment issue.
    """
    try:
        from curl_cffi import requests as curl_requests
        response = curl_requests.get(
            url,
            headers=headers,
            timeout=timeout,
            verify=False,
            impersonate="chrome124",
            allow_redirects=True,
        )
        return response
    except Exception as curl_err:
        logger.debug(f"curl_cffi impersonate failed for {url} ({curl_err}), falling back to standard requests.")
        return requests.get(url, headers=headers, timeout=timeout, verify=False, allow_redirects=True)


def scrape_portal(url: str, method: str = 'HTTP') -> tuple[str, int, int]:
    """
    Fetch content from a portal URL using HTTP (with TLS browser impersonation), Playwright, or PDF parsing.
    Returns: (raw_content_str, http_status_code, response_time_ms)
    """
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
    }

    start_time = time.time()

    if method == 'HTTP':
        try:
            response = _http_get_with_impersonation(url, headers=headers, timeout=30)
            scrape_portal.last_content_type = response.headers.get('Content-Type', '')
            response_time_ms = int((time.time() - start_time) * 1000)
            content = response.text.replace('\x00', '') if response.text else ''
            return content, response.status_code, response_time_ms
        except Exception as e:
            logger.warning(f"HTTP scrape failed for {url}: {e}")
            raise ScraperException(f"Failed to scrape {url}: {str(e)}")

    elif method == 'PLAYWRIGHT':
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=30000)
                page.wait_for_timeout(2000)
                content = page.content()
                scrape_portal.last_content_type = 'text/html'
                response_time_ms = int((time.time() - start_time) * 1000)
                browser.close()
                return content.replace('\x00', '') if content else '', 200, response_time_ms
        except Exception as e:
            logger.warning(f"Playwright scrape failed/unavailable for {url}: {e}. Falling back to HTTP.")
            try:
                response = _http_get_with_impersonation(url, headers=headers, timeout=30)
                scrape_portal.last_content_type = response.headers.get('Content-Type', '')
                response_time_ms = int((time.time() - start_time) * 1000)
                content = response.text.replace('\x00', '') if response.text else ''
                return content, response.status_code, response_time_ms
            except Exception as req_err:
                raise ScraperException(f"Playwright failed and fallback HTTP failed: {str(req_err)}")

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
        except Exception as e:
            logger.warning(f"PDF scrape failed/unavailable for {url}: {e}. Falling back to HTTP.")
            try:
                response = _http_get_with_impersonation(url, headers=headers, timeout=30)
                scrape_portal.last_content_type = response.headers.get('Content-Type', '')
                response_time_ms = int((time.time() - start_time) * 1000)
                content = response.text.replace('\x00', '') if response.text else ''
                return content, response.status_code, response_time_ms
            except Exception as req_err:
                raise ScraperException(f"PDF failed and fallback HTTP failed: {str(req_err)}")

    else:
        raise ScraperException(f"Unsupported scrape method: {method}")
