import logging
from django.conf import settings
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


# ─── Scraping Backend Plugin System ────────────────────────────────────────────

class BaseScraperBackend:
    """Base class for scraping backends."""
    def scrape(self, url: str) -> tuple[str, int, int]:
        raise NotImplementedError


class RequestsScraper(BaseScraperBackend):
    def scrape(self, url: str) -> tuple[str, int, int]:
        import requests
        import time
        import urllib3
        from core.exceptions import ScraperException
        
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        start_time = time.time()
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            response_time = int((time.time() - start_time) * 1000)
            return response.text, response.status_code, response_time
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            raise ScraperException(f"RequestsScraper failed: {e}") from e


class PlaywrightScraper(BaseScraperBackend):
    def scrape(self, url: str) -> tuple[str, int, int]:
        from apps.monitor.scraper import scrape_portal
        # Fall back to existing scraping implementation
        return scrape_portal(url, "PLAYWRIGHT")


class PDFScraper(BaseScraperBackend):
    def scrape(self, url: str) -> tuple[str, int, int]:
        from apps.monitor.scraper import scrape_portal
        # Fall back to existing scraping implementation
        return scrape_portal(url, "PDF")


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
    return RequestsScraper()


def get_notification_backend() -> BaseNotificationBackend:
    return TelegramNotificationBackend()


def get_ai_backend() -> BaseAIBackend:
    return GeminiAIBackend()
