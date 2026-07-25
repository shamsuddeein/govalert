import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from apps.agencies.models import Agency, Portal, HealthStatus, PortalStatus
from apps.monitor.tasks import portal_check


@pytest.mark.django_db
@patch('core.plugins.get_scraper_backend')
def test_http_200_always_results_in_online_status_regardless_of_content(mock_backend):
    mock_scraper = MagicMock()
    # Short content or non-standard HTML body returning HTTP 200
    mock_scraper.scrape.return_value = ("<html><body>OK</body></html>", 200, 120)
    mock_backend.return_value = mock_scraper

    agency = Agency.objects.create(name="Nigerian Consumer Credit Corporation", acronym="CREDICORP", official_domains=["credicorp.ng"])
    portal = Portal.objects.create(agency=agency, name="CREDICORP Portal", url="https://credicorp.ng", consecutive_failures=2)

    portal_check(portal.id)
    portal.refresh_from_db()

    # HTTP 200 MUST result in ONLINE status and reset failure counter to 0
    assert portal.health_status == HealthStatus.ONLINE
    assert portal.status == PortalStatus.ONLINE
    assert portal.consecutive_failures == 0
    assert portal.check_interval_minutes == 15


@pytest.mark.django_db
@patch('core.plugins.get_scraper_backend')
def test_http_500_or_404_triggers_offline_status(mock_backend):
    mock_scraper = MagicMock()
    mock_scraper.scrape.return_value = ("<html><body>Internal Server Error</body></html>", 500, 150)
    mock_backend.return_value = mock_scraper

    agency = Agency.objects.create(name="Test Agency", acronym="TA", official_domains=["ta.gov.ng"])
    portal = Portal.objects.create(agency=agency, name="TA Portal", url="https://ta.gov.ng", consecutive_failures=0)

    portal_check(portal.id)
    portal.refresh_from_db()

    # HTTP 500 MUST trigger OFFLINE status and increment consecutive_failures
    assert portal.health_status == HealthStatus.OFFLINE
    assert portal.status == PortalStatus.OFFLINE
    assert portal.consecutive_failures == 1
