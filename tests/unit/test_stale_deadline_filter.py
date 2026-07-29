import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta
from apps.agencies.models import Agency, Portal
from apps.alerts.models import Alert, RejectedDetection, AlertStatus
from apps.alerts.services import create_alert_from_scrape
from apps.monitor.parser import get_deadline_validation_status, parse_deadline_to_date


@pytest.mark.django_db
def test_parse_deadline_to_date_and_validation_status():
    today = timezone.now().date()
    future_date = today + timedelta(days=30)
    recent_date = today - timedelta(days=3)
    stale_date = today - timedelta(days=90)

    # 1. Future date -> GREEN
    future_str = future_date.strftime("%d %B %Y")
    val_future = get_deadline_validation_status(future_str)
    assert val_future['status'] == 'green'
    assert val_future['is_stale'] is False

    # 2. Recent date (within 7 days) -> AMBER
    recent_str = recent_date.strftime("%d %B %Y")
    val_recent = get_deadline_validation_status(recent_str)
    assert val_recent['status'] == 'amber'
    assert val_recent['is_stale'] is False

    # 3. Stale date (>7 days in past, e.g., 6th April 2026) -> RED & STALE
    stale_str = stale_date.strftime("%d %B %Y")
    val_stale = get_deadline_validation_status(stale_str)
    assert val_stale['status'] == 'red'
    assert val_stale['is_stale'] is True

    # 4. Unspecified -> UNKNOWN / GRAY
    val_unspecified = get_deadline_validation_status("Not Specified")
    assert val_unspecified['status'] == 'unknown'
    assert val_unspecified['is_stale'] is False


@pytest.mark.django_db
@patch('apps.alerts.services.classify_recruitment_with_ai')
def test_stale_deadline_auto_rejected_during_ingestion(mock_ai):
    mock_ai.return_value = {
        'classification': 'REAL',
        'confidence': 90,
        'event_type': 'RECRUITMENT_OPEN',
        'red_flags': [],
        'extracted': {
            'positions': 'Immigration Officers',
            'deadline': '6th April 2026',  # >3 months in the past!
            'requirements': 'Degree'
        }
    }

    agency = Agency.objects.create(name="Federal Ministry of Interior", acronym="FMI", official_domains=["interior.gov.ng"])
    portal = Portal.objects.create(agency=agency, name="FMI Portal", url="https://interior.gov.ng/careers")

    content = "Applications close on 6th April 2026 for Immigration Officers recruitment."
    matched_data = {
        'deadline': '6th April 2026',
        'positions': 'Immigration Officers',
        'rule_matches': ['recruitment', 'apply']
    }

    result = create_alert_from_scrape(portal, content, matched_data)

    # Must NOT create a pending alert
    assert result is None
    assert Alert.objects.filter(portal=portal).count() == 0

    # Must log to RejectedDetection database table with AUTO REJECTED STALE DEADLINE
    rejected = RejectedDetection.objects.filter(portal=portal).first()
    assert rejected is not None
    assert rejected.status == 'AUTO REJECTED STALE DEADLINE'
    assert "6th April 2026" in rejected.deadline
    assert "more than 7 days in the past" in rejected.reason


@pytest.mark.django_db
@patch('apps.alerts.services.classify_recruitment_with_ai')
def test_future_and_unspecified_deadlines_proceed_to_pending_queue(mock_ai):
    mock_ai.return_value = {
        'classification': 'UNCERTAIN',
        'confidence': 30,
        'event_type': 'RECRUITMENT_OPEN',
        'red_flags': [],
        'extracted': {
            'positions': 'Inspectors',
            'deadline': 'Not Specified',
            'requirements': 'Degree'
        }
    }

    agency = Agency.objects.create(name="Civil Defence", acronym="NSCDC", official_domains=["nscdc.gov.ng"])
    portal = Portal.objects.create(agency=agency, name="NSCDC Portal", url="https://nscdc.gov.ng/careers")

    content = "Recruitment into NSCDC is open for eligible candidates."
    matched_data = {
        'deadline': 'Not Specified',
        'positions': 'Inspectors',
        'rule_matches': ['recruitment', 'apply']
    }

    alert = create_alert_from_scrape(portal, content, matched_data)

    # Must proceed to pending queue for human review
    assert alert is not None
    assert alert.status == AlertStatus.PENDING
    assert alert.deadline == "Not Specified"
