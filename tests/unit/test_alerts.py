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
    # When AI is unavailable, the rule engine fallback must produce UNCERTAIN/PENDING.
    # The rule engine is triage only — it must never auto-approve.
    assert alert_real.ai_classification == 'UNCERTAIN', (
        "Fallback must produce UNCERTAIN, not REAL. "
        "REAL classification is only valid from a genuine AI call."
    )
    assert alert_real.ai_confidence == 40, (
        "Fallback confidence must be 40, not 75. "
        "A high confidence score from the rule engine would bypass human review."
    )
    assert alert_real.positions == 'Customs Inspector'
    assert alert_real.deadline == '2025-12-31'
    assert alert_real.status == AlertStatus.PENDING, (
        "Fallback must produce PENDING status. "
        "Auto-approval is only valid when a genuine AI call returns REAL."
    )

    # Clear database state to prevent the second call from being flagged as a duplicate
    from apps.alerts.models import RecruitmentEvent
    RecruitmentEvent.objects.all().delete()

    # 2. Scrape content with fraud keywords
    content_fraud = "NCS Recruitment. Pay a application fee of 5000 Naira to NCS bank account."
    alert_fraud = create_alert_from_scrape(portal, content_fraud, matched_data)

    assert alert_fraud is not None
    # Fraud keywords detected via rule engine — still UNCERTAIN (not SUSPICIOUS)
    # because the rule engine cannot assign SUSPICIOUS confidently without AI.
    assert alert_fraud.ai_classification == 'UNCERTAIN'
    assert alert_fraud.ai_confidence == 30
    assert 'FRAUD_KEYWORDS_DETECTED' in alert_fraud.ai_red_flags


@pytest.mark.django_db
@patch('apps.alerts.services.classify_recruitment_with_ai')
def test_position_change_creates_linked_update_event(mock_ai):
    """A changed position must stay in the recruitment chain, not become a new job."""
    mock_ai.return_value = {
        'classification': 'REAL', 'confidence': 90,
        'event_type': 'RECRUITMENT_OPEN', 'red_flags': [],
        'extracted': {'positions': 'Officer', 'deadline': '2026-08-01', 'requirements': 'Check portal'},
    }
    agency = Agency.objects.create(name='Nigeria Customs Service', acronym='NCS', official_domains=['customs.gov.ng'])
    portal = Portal.objects.create(agency=agency, name='Careers', url='https://customs.gov.ng/careers')

    first = create_alert_from_scrape(
        portal, 'Recruitment is open. Apply now.',
        {'positions': 'Officer', 'deadline': '2026-08-01'},
    )
    update = create_alert_from_scrape(
        portal, 'Recruitment is open. Apply now.',
        {'positions': 'Officer, Inspector', 'deadline': '2026-08-01'},
    )

    assert update.pk != first.pk
    assert update.recruitment_event.previous_event_id == first.recruitment_event_id
    assert update.recruitment_event.fingerprint == first.recruitment_event.fingerprint
