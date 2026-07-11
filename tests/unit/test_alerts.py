import pytest
from unittest.mock import patch
from apps.agencies.models import Agency, Portal
from apps.alerts.services import create_alert_from_scrape
from apps.alerts.models import Alert, AlertStatus

@pytest.mark.django_db
@patch('apps.alerts.services.classify_recruitment_with_ai')
@patch('apps.notifications.tasks.send_message')
def test_create_alert_from_scrape_fallback(mock_send, mock_ai):
    # Mock AI raising an exception to force the rule-based fallback engine
    mock_ai.side_effect = Exception("API connection timed out.")

    agency = Agency.objects.create(
        name="Nigeria Customs Service",
        acronym="NCS",
        official_domains=["customs.gov.ng"],
        is_active=True
    )
    portal = Portal.objects.create(
        agency=agency,
        name="Customs Portal",
        url="https://customs.gov.ng/careers",
        is_active=True
    )

    matched_data = {
        'positions': 'Customs Inspector',
        'deadline': '2025-12-31'
    }

    # 1. Scrape content with recruitment keywords, no fraud keywords
    content_real = "Welcome to Nigeria Customs Service. The NCS recruitment 2025 is now open. Apply today."
    alert_real = create_alert_from_scrape(portal, content_real, matched_data)

    assert alert_real is not None
    assert alert_real.ai_classification == 'REAL'
    assert alert_real.ai_confidence == 75
    assert alert_real.positions == 'Customs Inspector'
    assert alert_real.deadline == '2025-12-31'
    assert alert_real.status == AlertStatus.APPROVED

    # Clear database state to prevent the second call from being flagged as a duplicate
    from apps.alerts.models import RecruitmentEvent
    RecruitmentEvent.objects.all().delete()

    # 2. Scrape content with fraud keywords
    content_fraud = "NCS Recruitment. Pay a application fee of 5000 Naira to NCS bank account."
    alert_fraud = create_alert_from_scrape(portal, content_fraud, matched_data)

    assert alert_fraud is not None
    assert alert_fraud.ai_classification == 'SUSPICIOUS'
    assert alert_fraud.ai_confidence == 80
    assert 'FRAUD_KEYWORDS_DETECTED' in alert_fraud.ai_red_flags
