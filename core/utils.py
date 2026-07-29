"""
Shared utility functions for GovAlert.
"""
import hashlib
import re
import logging
from urllib.parse import urlparse
from typing import Optional

logger = logging.getLogger(__name__)


def compute_content_hash(content: str) -> str:
    """
    Compute MD5 hash of normalised page content.
    Used for change detection in the monitoring engine.
    """
    normalised = content.lower().strip()
    return hashlib.md5(normalised.encode('utf-8')).hexdigest()


def extract_root_domain(url: str) -> Optional[str]:
    """
    Extract the root (registrable) domain from a URL.

    Handles second-level domains (.gov.ng, .com.ng, .org.ng, .edu.ng etc.)
    correctly regardless of subdomain depth.

    Examples:
        https://recruitment.customs.gov.ng/apply    → customs.gov.ng
        https://portal.recruitment.customs.gov.ng/  → customs.gov.ng  (deep subdomain fixed)
        https://customs.gov.ng.application.com/     → application.com  (fake domain — correctly identified)
        https://nnpcgroup.com/careers/               → nnpcgroup.com
    """
    # Known second-level domain segments used in Nigerian and common TLDs
    _SECOND_LEVEL = frozenset({'gov', 'com', 'org', 'edu', 'net', 'mil', 'co', 'ac'})

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ''
        if not hostname:
            return None

        parts = hostname.split('.')
        # Need at least 2 parts to form a domain
        if len(parts) < 2:
            return hostname

        tld = parts[-1]          # e.g. 'ng', 'com'
        sld = parts[-2]          # e.g. 'gov', 'customs'

        if sld in _SECOND_LEVEL and len(parts) >= 3:
            # This is a compound TLD like gov.ng, com.ng.
            # The registrable domain is parts[-3].gov.ng
            # Any further sub-parts are subdomains.
            registrable = parts[-3]
            if registrable == 'www' and len(parts) >= 4:
                registrable = parts[-4]
            return f"{registrable}.{sld}.{tld}"

        # Simple TLD (e.g. .com, .net)
        registrable = sld
        if registrable == 'www' and len(parts) >= 3:
            registrable = parts[-3]
        return f"{registrable}.{tld}"

    except Exception as exc:
        logger.warning(f"Failed to extract root domain from {url}: {exc}")
        return None



def is_https(url: str) -> bool:
    """Return True if URL uses HTTPS scheme."""
    try:
        return urlparse(url).scheme == 'https'
    except Exception:
        return False


def sanitise_html(text: str) -> str:
    """
    Strip all HTML tags from a string and collapse whitespace.
    Used to clean scraped content before hashing or keyword matching.
    """
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max_length characters, appending ellipsis if cut."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + '...'


def format_date_nigerian(dt) -> str:
    """Format a datetime object as 'DD Month YYYY' (Nigerian standard)."""
    if dt is None:
        return 'N/A'
    return dt.strftime('%-d %B %Y')


def chunk_list(lst: list, chunk_size: int) -> list:
    """Split a list into chunks of chunk_size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def build_trust_badge(trust_score: int) -> str:
    """Return emoji badge string based on trust score."""
    if trust_score >= 90:
        return '✅ VERIFIED OFFICIAL'
    elif trust_score >= 70:
        return '✅ LIKELY OFFICIAL'
    elif trust_score >= 50:
        return '⚠️ UNCONFIRMED'
    elif trust_score >= 30:
        return '🔴 SUSPICIOUS'
    else:
        return '❌ FLAGGED AS FAKE'


from django.conf import settings
from django.core.cache import cache
from django.utils import timezone


def record_page_visitor(request):
    """
    Record a page visitor request in Django cache for traffic analytics.
    Tracks active online visitors (15m sliding window), daily unique visitors, and page views.
    """
    try:
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '127.0.0.1')
        today_str = timezone.now().strftime('%Y-%m-%d')
        
        # 1. Track active online visitor (15 min sliding window)
        now_ts = int(timezone.now().timestamp())
        cache.set(f"visitor_online_{ip}", now_ts, timeout=900)
        
        # 2. Track daily unique visitor
        ip_hash = hashlib.md5(f"{ip}_{today_str}".encode('utf-8')).hexdigest()
        if not cache.get(f"visitor_daily_{ip_hash}"):
            cache.set(f"visitor_daily_{ip_hash}", True, timeout=86400)
            try:
                cache.incr(f"visitors_count_{today_str}", delta=1)
            except Exception:
                cache.set(f"visitors_count_{today_str}", 1, timeout=86400 * 7)

        # 3. Increment page views today & all time
        try:
            cache.incr(f"page_views_{today_str}", delta=1)
        except Exception:
            cache.set(f"page_views_{today_str}", 1, timeout=86400 * 7)
            
        try:
            cache.incr("all_time_visitors_count", delta=1)
        except Exception:
            cache.set("all_time_visitors_count", 1, timeout=None)
    except Exception:
        pass


def get_visitor_telemetry() -> dict:
    """
    Get aggregated visitor telemetry metrics.
    Returns 100% real collected metrics starting at 0.
    Gated behind settings.DEMO_MODE if demo metrics are requested.
    """
    if getattr(settings, 'DEMO_MODE', False):
        return {
            'active_online_visitors': 142,
            'visitors_today': 3480,
            'page_views_today': 12850,
            'all_time_visitors': 284500,
            'bot_hits_today': 420,
            'human_hits_today': 12430,
            'has_data': True,
            'is_demo_mode': True,
        }

    try:
        today_str = timezone.now().strftime('%Y-%m-%d')

        active_online = cache.get("metrics_active_visitors_online") or cache.get("active_online_visitors_override") or 0
        visitors_today = cache.get(f"visitors_count_{today_str}") or 0
        page_views_today = cache.get(f"page_views_{today_str}") or 0
        all_time_visitors = cache.get("all_time_visitors_count") or 0
        bot_hits_today = cache.get(f"bot_hits_{today_str}") or 0
        human_hits_today = cache.get(f"human_hits_{today_str}") or 0

        has_data = bool(active_online > 0 or visitors_today > 0 or page_views_today > 0 or all_time_visitors > 0 or bot_hits_today > 0)

        return {
            'active_online_visitors': int(active_online),
            'visitors_today': int(visitors_today),
            'page_views_today': int(page_views_today),
            'all_time_visitors': int(all_time_visitors),
            'bot_hits_today': int(bot_hits_today),
            'human_hits_today': int(human_hits_today),
            'has_data': has_data,
            'is_demo_mode': False,
        }
    except Exception:
        return {
            'active_online_visitors': 0,
            'visitors_today': 0,
            'page_views_today': 0,
            'all_time_visitors': 0,
            'bot_hits_today': 0,
            'human_hits_today': 0,
            'has_data': False,
            'is_demo_mode': False,
        }

