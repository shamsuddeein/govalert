import re
from urllib.parse import urlparse
from core.utils import extract_root_domain
from apps.detector.models import FakeDomain

FAKE_PATTERNS = [
    r'recruitment-nigeria\.com$',
    r'jobsportal.*\.com$',
    r'\.gov\.ng\..+\.com$',  # Spoofed subdomains
    r'^nnpcjobs.*\.com$',
    r'^customs-recruitment.*\.com$',
]


def is_domain_blacklisted(url: str) -> bool:
    """Check if root domain or hostname is blacklisted or matches fake patterns."""
    parsed = urlparse(url)
    hostname = parsed.hostname or ''

    root = extract_root_domain(url)
    if not root:
        return True

    if FakeDomain.objects.filter(domain=root).exists():
        return True

    for pattern in FAKE_PATTERNS:
        if re.search(pattern, root) or re.search(pattern, hostname):
            return True

    return False
