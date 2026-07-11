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
    Extract the root domain from a URL.
    
    Examples:
        https://recruitment.customs.gov.ng/apply → customs.gov.ng
        https://customs.gov.ng.application.com/  → application.com  (fake!)
        https://nnpcgroup.com/careers/            → nnpcgroup.com
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ''
        if not hostname:
            return None
        # Split and take last 2 or 3 parts (handles .gov.ng, .com.ng etc.)
        parts = hostname.split('.')
        if len(parts) >= 3 and parts[-2] in ('gov', 'com', 'org', 'edu', 'net'):
            # e.g. customs.gov.ng → ['customs', 'gov', 'ng'] → gov.ng
            return '.'.join(parts[-3:]) if parts[-3] not in ('www',) else '.'.join(parts[-3:])
        return '.'.join(parts[-2:]) if len(parts) >= 2 else hostname
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
