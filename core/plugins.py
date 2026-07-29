import logging
from django.conf import settings
from django.utils.module_loading import import_string
from core.security import validate_outbound_url, MAX_RESPONSE_BYTES

logger = logging.getLogger(__name__)


# ─── Scraping Backend Plugin System ────────────────────────────────────────────

class BaseScraperBackend:
    """Base class for scraping backends."""
    def scrape(self, url: str) -> tuple[str, int, int]:
        raise NotImplementedError


_USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
    "Gecko/20100101 Firefox/125.0",
]


class RequestsScraper(BaseScraperBackend):
    """
    HTTP scraper using the requests library.

    Improvements over the original:
    - Rotates through 3 real browser User-Agent strings.
    - Sends Accept / Accept-Language headers to look like a real browser.
    - Performs one automatic retry with a 2-second backoff on connection-level
      errors (not on DNS failures or timeouts, which are already counted as
      hard failures by the task layer).
    """

    _HEADERS_BASE = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    def scrape(self, url: str, is_blocked: bool = False) -> tuple[str, int, int]:
        import random
        import requests
        import time
        from core.exceptions import ScraperException

        # SSRF guard: validate before any network I/O.
        validate_outbound_url(url)

        headers = {**self._HEADERS_BASE, 'User-Agent': random.choice(_USER_AGENTS)}

        # When the portal is known to be firewall-blocked, apply anti-blocking measures:
        # randomized delay and additional header spoofing to reduce bot fingerprinting.
        if is_blocked:
            delay = random.uniform(3.0, 8.0)
            logger.info(f"RequestsScraper: applying {delay:.2f}s anti-block delay for {url}")
            time.sleep(delay)
            headers.update({
                'Referer': 'https://www.google.com/',
                'Cache-Control': 'max-age=0',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-User': '?1',
            })

        timeout = 15
        start_time = time.time()
        last_exc = None

        for attempt in range(2):   # 1 try + 1 retry
            try:
                response = requests.get(
                    url, headers=headers, timeout=timeout,
                    verify=True,          # TLS verification always on
                    allow_redirects=True,
                    stream=True,          # stream to enforce size cap
                )
                self.last_content_type = response.headers.get('Content-Type', '')
                # Enforce response size cap before loading body into memory.
                content_bytes = b''
                for chunk in response.iter_content(chunk_size=65536):
                    content_bytes += chunk
                    if len(content_bytes) > MAX_RESPONSE_BYTES:
                        raise ScraperException(
                            f"Response from {url!r} exceeded "
                            f"{MAX_RESPONSE_BYTES // (1024*1024)}MB limit. Aborted."
                        )
                response._content = content_bytes
                response_time = int((time.time() - start_time) * 1000)
                content = response.text.replace('\x00', '') if response.text else ''
                return content, response.status_code, response_time
            except ScraperException:
                raise  # Size cap and SSRF : not retryable
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                last_exc = e
                if attempt == 0:
                    logger.debug(f"RequestsScraper: transient error on attempt 1 for {url}: {e}. Retrying in 2s...")
                    time.sleep(2)
            except Exception as e:
                # Non-retryable error (e.g. invalid URL, SSL decode error)
                response_time = int((time.time() - start_time) * 1000)
                raise ScraperException(f"RequestsScraper failed: {e}") from e

        response_time = int((time.time() - start_time) * 1000)
        raise ScraperException(f"RequestsScraper failed after 2 attempts: {last_exc}") from last_exc


class PlaywrightScraper(BaseScraperBackend):
    def scrape(self, url: str) -> tuple[str, int, int]:
        from apps.monitor.scraper import scrape_portal, _scrape_local
        # Fall back to existing scraping implementation
        content, code, duration = scrape_portal(url, "PLAYWRIGHT")
        self.last_content_type = getattr(_scrape_local, 'last_content_type', 'text/html')
        return content.replace('\x00', '') if content else '', code, duration


class PDFScraper(BaseScraperBackend):
    def scrape(self, url: str) -> tuple[str, int, int]:
        from apps.monitor.scraper import scrape_portal, _scrape_local
        # Fall back to existing scraping implementation
        content, code, duration = scrape_portal(url, "PDF")
        self.last_content_type = getattr(_scrape_local, 'last_content_type', 'application/pdf')
        return content.replace('\x00', '') if content else '', code, duration


# ─── Notification Backend Plugin System ────────────────────────────────────────

class BaseNotificationBackend:
    """Base class for dispatching alerts through notification channels."""
    def send_notification(self, chat_id: str, text: str, **kwargs) -> bool:
        raise NotImplementedError


class TelegramNotificationBackend(BaseNotificationBackend):
    def send_notification(self, chat_id: str, text: str, **kwargs) -> bool:
        from apps.notifications.sender import send_message
        try:
            send_message(chat_id=chat_id, text=text, **kwargs)
            return True
        except Exception as e:
            logger.error(f"TelegramNotificationBackend failed to send to {chat_id}: {e}")
            return False


# ─── AI Classifier Backend Plugin System ───────────────────────────────────────

class BaseAIBackend:
    """Base class for classifying recruitment portals."""
    def classify(self, agency_name: str, url: str, content: str) -> dict:
        raise NotImplementedError


class GeminiAIBackend(BaseAIBackend):
    def classify(self, agency_name: str, url: str, content: str) -> dict:
        from apps.detector.ai import classify_recruitment_with_ai
        return classify_recruitment_with_ai(agency_name, url, content)


class OfflineRulesAIBackend(BaseAIBackend):
    def classify(self, agency_name: str, url: str, content: str) -> dict:
        # Static rules offline classification fallback
        content_lower = content.lower()
        has_fraud = any(kw in content_lower for kw in ["fee", "pay", "charge", "naira", "deposit", "payment", "bank"])
        has_rec = any(kw in content_lower for kw in ["recruitment", "careers", "apply", "job", "vacancy"])
        
        classification = 'REAL'
        confidence = 75
        
        if has_fraud:
            classification = 'SUSPICIOUS'
            confidence = 80
        elif not has_rec:
            classification = 'UNCERTAIN'
            confidence = 50
            
        return {
            'classification': classification,
            'confidence': confidence,
            'event_type': 'RECRUITMENT_OPEN' if has_rec else 'OTHER',
            'red_flags': ['FRAUD_KEYWORDS_DETECTED'] if has_fraud else [],
            'extracted': {
                'positions': 'Multiple Positions',
                'deadline': '',
                'requirements': 'Check website'
            }
        }


# ─── Plugin Manager Helpers ───────────────────────────────────────────────────

def get_scraper_backend(method: str) -> BaseScraperBackend:
    if method == "PLAYWRIGHT":
        return PlaywrightScraper()
    elif method == "PDF":
        return PDFScraper()
    # 'HTTP' and 'REQUESTS' (DB default) both use the requests-based scraper.
    # Any unrecognised method also falls back to RequestsScraper so the portal
    # gets one attempt rather than a hard crash.
    return RequestsScraper()


def get_notification_backend() -> BaseNotificationBackend:
    return TelegramNotificationBackend()


def get_ai_backend() -> BaseAIBackend:
    return GeminiAIBackend()
