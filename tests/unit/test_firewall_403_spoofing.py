import pytest
from unittest.mock import patch, MagicMock
from apps.agencies.models import Agency, Portal, HealthStatus, PortalStatus
from apps.monitor.tasks import portal_check
from apps.monitor.scraper import scrape_portal
from core.exceptions import ScraperException


@pytest.mark.django_db
@patch('apps.monitor.scraper.time.sleep')
@patch('apps.monitor.scraper._http_get_with_impersonation')
def test_scrape_portal_with_is_blocked_headers_and_delay(mock_http_get, mock_sleep):
    mock_resp = MagicMock()
    mock_resp.text = "<html><body>OK</body></html>"
    mock_resp.status_code = 200
    mock_resp.headers = {'Content-Type': 'text/html'}
    mock_http_get.return_value = mock_resp

    content, code, duration = scrape_portal("https://joinnigeriannavy.com/careers", is_blocked=True)

    assert code == 200
    # Verify randomized delay (3-8 seconds) was applied
    mock_sleep.assert_called_once()
    sleep_arg = mock_sleep.call_args[0][0]
    assert 3.0 <= sleep_arg <= 8.0

    # Verify real browser spoofing headers were passed
    mock_http_get.assert_called_once()
    headers_used = mock_http_get.call_args[1]['headers']
    assert "Chrome" in headers_used['User-Agent']
    assert headers_used['Referer'] == "https://joinnigeriannavy.com/"
    assert headers_used['Connection'] == "keep-alive"
    assert "text/html" in headers_used['Accept']


@pytest.mark.django_db
@patch('core.plugins.get_scraper_backend')
def test_portal_check_403_does_not_increment_consecutive_failures(mock_backend):
    mock_scraper = MagicMock()
    mock_scraper.scrape.return_value = ("Forbidden", 403, 100)
    mock_backend.return_value = mock_scraper

    agency = Agency.objects.create(name="Navy Agency", acronym="NN", official_domains=["joinnigeriannavy.com"])
    portal = Portal.objects.create(
        agency=agency, name="Navy Portal", url="https://joinnigeriannavy.com/careers",
        consecutive_failures=0, is_active=True
    )

    portal_check(portal.id)
    portal.refresh_from_db()

    # consecutive_failures must NOT be incremented on 403 (access restriction, not network failure)
    assert portal.consecutive_failures == 0
    # Portals identified with firewall block set status to BLOCKED or MANUAL_MONITORING_REQUIRED
    assert portal.health_status in [HealthStatus.BLOCKED, HealthStatus.MANUAL_MONITORING_REQUIRED]


@pytest.mark.django_db
@patch('core.plugins.get_scraper_backend')
def test_portal_check_persistent_403_transitions_to_manual_monitoring(mock_backend):
    mock_scraper = MagicMock()
    mock_scraper.scrape.return_value = ("Cloudflare Blocked 403", 403, 100)
    mock_backend.return_value = mock_scraper

    agency = Agency.objects.create(name="FCSC Agency", acronym="FCSC", official_domains=["fedcivilservice.gov.ng"])
    portal = Portal.objects.create(
        agency=agency, name="FCSC Recruitment", url="https://fedcivilservice.gov.ng/careers",
        consecutive_failures=0, health_status=HealthStatus.BLOCKED, status=PortalStatus.BLOCKED,
        is_active=True
    )

    portal_check(portal.id)
    portal.refresh_from_db()

    # Must transition to MANUAL_MONITORING_REQUIRED, stop automated checks (is_active=False), and add operator note
    assert portal.health_status == HealthStatus.MANUAL_MONITORING_REQUIRED
    assert portal.status == PortalStatus.MANUAL_MONITORING_REQUIRED
    assert portal.is_active is False
    assert "MANUAL MONITORING REQUIRED" in portal.notes
    assert "Operator must check this portal manually once per week" in portal.notes
    assert portal.consecutive_failures == 0  # Consecutive failures untouched


@pytest.mark.django_db
@patch('core.plugins.get_scraper_backend')
def test_portal_check_200_after_blocked_recovers_to_online(mock_backend):
    mock_scraper = MagicMock()
    mock_scraper.scrape.return_value = ("<html><body>Recruitment Open</body></html>", 200, 150)
    mock_backend.return_value = mock_scraper

    agency = Agency.objects.create(name="Navy Agency 2", acronym="NN2", official_domains=["joinnigeriannavy.com"])
    portal = Portal.objects.create(
        agency=agency, name="Navy Careers", url="https://joinnigeriannavy.com/careers",
        consecutive_failures=0, health_status=HealthStatus.BLOCKED, status=PortalStatus.BLOCKED,
        is_active=True
    )

    portal_check(portal.id)
    portal.refresh_from_db()

    assert portal.health_status == HealthStatus.ONLINE
    assert portal.status == PortalStatus.ONLINE
    assert portal.check_interval_minutes == 15
    assert portal.poll_interval == 900
