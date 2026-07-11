from core.utils import extract_root_domain, is_https
from apps.agencies.models import Agency
from apps.alerts.models import Alert, AlertStatus


def calculate_trust_score(agency: Agency, url: str, ai_confidence: int = 100) -> int:
    """
    Calculate a trust score from 0 to 100 based on signals in Volume 4.
    """
    score = 0
    root_domain = extract_root_domain(url)

    # 1. Official Domain Match (30 pts)
    is_official = False
    if root_domain and agency.official_domains:
        if root_domain in agency.official_domains:
            score += 30
            is_official = True

    # 2. SSL Certificate Valid (15 pts)
    if is_https(url):
        score += 15

    # If official, default points are granted for WHOIS, age, branding, and cross-ref
    if is_official:
        score += 10  # Domain Age (10 pts)
        score += 10  # WHOIS Ownership (10 pts)
        score += 10  # Consistent Branding (10 pts)
        score += 5   # Cross-Reference Check (5 pts)

    # 6. AI Content Analysis (15 pts)
    score += int(ai_confidence * 0.15)

    # 8. Previous Alert History (5 pts)
    if Alert.objects.filter(agency=agency, status=AlertStatus.APPROVED).exists():
        score += 5

    return min(max(score, 0), 100)
