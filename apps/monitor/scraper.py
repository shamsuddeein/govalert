import logging
import random
import time
import requests
from django.conf import settings
from core.exceptions import ScraperException

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
]


def scrape_portal(url: str, method: str = 'HTTP') -> tuple[str, int, int]:
    """
    Fetch content from a portal URL using either HTTP or Playwright.
    Returns: (raw_content_str, http_status_code, response_time_ms)
    """
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    start_time = time.time()

    if method == 'HTTP':
        try:
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            response_time_ms = int((time.time() - start_time) * 1000)
            return response.text, response.status_code, response_time_ms
        except requests.RequestException as e:
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
                response_time_ms = int((time.time() - start_time) * 1000)
                browser.close()
                return content, 200, response_time_ms
        except Exception as e:
            logger.warning(f"Playwright scrape failed/unavailable for {url}: {e}. Falling back to HTTP.")
            try:
                response = requests.get(url, headers=headers, timeout=30, verify=False)
                response_time_ms = int((time.time() - start_time) * 1000)
                return response.text, response.status_code, response_time_ms
            except requests.RequestException as req_err:
                raise ScraperException(f"Playwright failed and fallback HTTP failed: {str(req_err)}")

    elif method == 'PDF':
        try:
            import pdfplumber
            import io
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            if response.status_code != 200:
                raise ScraperException(f"Failed to download PDF: HTTP {response.status_code}")

            with pdfplumber.open(io.BytesIO(response.content)) as pdf:
                pages_text = [page.extract_text() or '' for page in pdf.pages]
                content = '\n'.join(pages_text)

            response_time_ms = int((time.time() - start_time) * 1000)
            return content, 200, response_time_ms
        except Exception as e:
            logger.warning(f"PDF scrape failed/unavailable for {url}: {e}. Falling back to HTTP.")
            try:
                response = requests.get(url, headers=headers, timeout=30, verify=False)
                response_time_ms = int((time.time() - start_time) * 1000)
                return response.text, response.status_code, response_time_ms
            except requests.RequestException as req_err:
                raise ScraperException(f"PDF failed and fallback HTTP failed: {str(req_err)}")

    else:
        raise ScraperException(f"Unsupported scrape method: {method}")
