import pytest
from unittest.mock import patch, MagicMock
from apps.monitor.scraper import scrape_portal
from apps.monitor.parser import clean_html_to_text, analyze_diff, match_recruitment_keywords
from core.exceptions import ScraperException


def test_clean_html_to_text():
    html = "<html><head><title>Test</title></head><body><nav>Menu</nav><main><h1>Job Openings</h1><p>Apply for positions.</p></main><footer>Foot</footer></body></html>"
    text = clean_html_to_text(html)
    assert "Menu" not in text
    assert "Foot" not in text
    assert "Job Openings Apply for positions." in text


def test_analyze_diff():
    old = "Line 1\nLine 2"
    new = "Line 1\nLine 2\nLine 3"
    assert analyze_diff(old, new) == "Line 3"


def test_match_recruitment_keywords():
    text = "NCS Recruitment 2025. Apply now for multiple positions. Deadline is December 31, 2025."
    res = match_recruitment_keywords(text)
    assert res['is_recruitment'] is True
    assert res['confidence'] == 'HIGH'
    assert "December 31, 2025" in res['deadline']


@patch('apps.monitor.scraper.requests.get')
def test_scrape_portal_http_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.text = "Hello World"
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp

    content, code, duration = scrape_portal("http://example.com", method="HTTP")
    assert content == "Hello World"
    assert code == 200
    assert duration >= 0


import requests


@patch('apps.monitor.scraper.requests.get')
def test_scrape_portal_http_fail(mock_get):
    mock_get.side_effect = requests.RequestException("Connection Refused")
    with pytest.raises(ScraperException):
        scrape_portal("http://example.com", method="HTTP")


@patch('apps.monitor.scraper.requests.get')
def test_scrape_portal_pdf_fallback(mock_get):
    mock_resp = MagicMock()
    mock_resp.text = "Hello PDF Content fallback"
    mock_resp.status_code = 200
    mock_get.return_value = mock_resp

    content, code, duration = scrape_portal("http://example.com/file.pdf", method="PDF")
    assert content == "Hello PDF Content fallback"
    assert code == 200


@pytest.mark.django_db
@patch('apps.monitor.scraper.scrape_portal')
@patch('apps.detector.ai.classify_recruitment_with_ai')
@patch('apps.notifications.tasks.send_message')
def test_portal_check_pipeline(mock_send, mock_ai, mock_scrape):
    from apps.agencies.models import Agency, Portal
    from apps.monitor.tasks import portal_check
    from apps.monitor.models import Snapshot
    from apps.alerts.models import Alert

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
        is_active=True,
        check_interval_minutes=10,
        scrape_method="PLAYWRIGHT"
    )

    # 1. First scrape: Initial snapshot (no change, no alert)
    mock_scrape.return_value = ("<html><body>Careers Page</body></html>", 200, 150)
    portal_check(portal.id)

    assert Snapshot.objects.filter(portal=portal).count() == 1
    snap1 = Snapshot.objects.first()
    assert snap1.has_change is False
    assert Alert.objects.count() == 0

    # 2. Second scrape: Content has changed and matches recruitment!
    mock_scrape.return_value = ("<html><body>Careers Page - NCS Recruitment 2025 is open. Apply now! deadline 2025-12-31</body></html>", 200, 160)
    mock_ai.return_value = {
        'classification': 'REAL',
        'confidence': 95,
        'event_type': 'RECRUITMENT_OPEN',
        'red_flags': [],
        'extracted': {
            'positions': 'Customs Officer',
            'deadline': '2025-12-31',
            'requirements': 'WAEC'
        }
    }
    mock_send.return_value = {'message_id': 12345}

    portal_check(portal.id)

    assert Snapshot.objects.filter(portal=portal).count() == 2
    snap2 = Snapshot.objects.order_by('-created_at').first()
    assert snap2.has_change is True
    assert snap2.triggered_alert is True

    assert Alert.objects.count() == 1
    alert = Alert.objects.first()
    assert alert.trust_score >= 70
    assert alert.status == 'APPROVED'
