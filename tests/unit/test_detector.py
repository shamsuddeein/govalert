import pytest
from apps.agencies.models import Agency
from apps.detector.domain import is_domain_blacklisted
from apps.detector.trust import calculate_trust_score
from apps.detector.models import FakeDomain


@pytest.mark.django_db
def test_is_domain_blacklisted():
    agency = Agency.objects.create(
        name="Nigeria Customs Service",
        acronym="NCS",
        official_domains=["customs.gov.ng"],
        is_active=True
    )

    assert is_domain_blacklisted("http://customs-recruitment.com") is True
    assert is_domain_blacklisted("https://customs.gov.ng.fakeportal.com/apply") is True
    assert is_domain_blacklisted("https://customs.gov.ng/apply") is False

    FakeDomain.objects.create(domain="customs-scam.com", agency=agency)
    assert is_domain_blacklisted("http://customs-scam.com/recruitment") is True


@pytest.mark.django_db
def test_calculate_trust_score():
    agency = Agency.objects.create(
        name="Nigeria Customs Service",
        acronym="NCS",
        official_domains=["customs.gov.ng"],
        is_active=True
    )

    score1 = calculate_trust_score(agency, "https://customs.gov.ng/jobs", ai_confidence=100)
    assert score1 == 95

    score2 = calculate_trust_score(agency, "http://customs-recruitment.com/jobs", ai_confidence=50)
    assert score2 == 7
