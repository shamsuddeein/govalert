import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from apps.agencies.models import Agency, Portal, HealthStatus, PortalStatus
from apps.monitor.tasks import portal_check, daily_health_report
from apps.monitor.models import Snapshot
from rest_framework import status as http_status


@pytest.mark.django_db
@patch('core.plugins.get_scraper_backend')
def test_captcha_detection_sets_captcha_protected_status_and_6hr_interval(mock_backend):
    mock_scraper = MagicMock()
    mock_scraper.scrape.return_value = ("<html><body>Please solve CAPTCHA challenge</body></html>", 200, 150)
    mock_backend.return_value = mock_scraper

    agency = Agency.objects.create(name="Ministry of Finance", acronym="FMF", official_domains=["finance.gov.ng"])
    portal = Portal.objects.create(
        agency=agency, name="FMF Careers", url="https://finance.gov.ng/careers",
        consecutive_failures=0, check_interval_minutes=15, poll_interval=900
    )

    portal_check(portal.id)
    portal.refresh_from_db()

    # Must be flagged as CAPTCHA_PROTECTED with 6-hour check interval (360 min)
    assert portal.health_status == HealthStatus.CAPTCHA_PROTECTED
    assert portal.status == PortalStatus.CAPTCHA_PROTECTED
    assert portal.check_interval_minutes == 360
    assert portal.poll_interval == 21600
    # Failure counter must NOT be incremented for CAPTCHA responses
    assert portal.consecutive_failures == 0


@pytest.mark.django_db
def test_admin_action_mark_manually_verified():
    from apps.agencies.admin import PortalAdmin
    from django.contrib.admin.sites import AdminSite

    agency = Agency.objects.create(name="ICPC Agency", acronym="ICPC", official_domains=["icpc.gov.ng"])
    portal = Portal.objects.create(
        agency=agency, name="ICPC Careers", url="https://icpc.gov.ng/careers",
        consecutive_failures=5, check_interval_minutes=360, poll_interval=21600,
        health_status=HealthStatus.CAPTCHA_PROTECTED, status=PortalStatus.CAPTCHA_PROTECTED
    )

    admin_site = AdminSite()
    portal_admin = PortalAdmin(Portal, admin_site)

    mock_request = MagicMock()
    mock_request.user.username = "admin_operator"

    queryset = Portal.objects.filter(id=portal.id)
    portal_admin.mark_manually_verified(mock_request, queryset)

    portal.refresh_from_db()

    # Reset failure counter, restore 15-min interval, set status ONLINE
    assert portal.consecutive_failures == 0
    assert portal.check_interval_minutes == 15
    assert portal.poll_interval == 900
    assert portal.health_status == HealthStatus.ONLINE
    assert portal.status == PortalStatus.ONLINE
    assert portal.last_successful_check_at is not None
    assert "Manually verified by admin_operator" in portal.notes


@pytest.mark.django_db
def test_rest_api_manual_verify_endpoint():
    from django.contrib.auth import get_user_model
    from rest_framework.test import APIClient

    User = get_user_model()
    admin = User.objects.create_superuser(username="adminuser", email="admin@govalert.com.ng", password="pass")
    client = APIClient()
    client.force_authenticate(user=admin)

    agency = Agency.objects.create(name="NAFDAC Agency", acronym="NAFDAC", official_domains=["nafdac.gov.ng"])
    portal = Portal.objects.create(
        agency=agency, name="NAFDAC Careers", url="https://nafdac.gov.ng/careers",
        consecutive_failures=3, check_interval_minutes=360,
        health_status=HealthStatus.CAPTCHA_PROTECTED, status=PortalStatus.CAPTCHA_PROTECTED
    )

    url = f"/api/v1/admin/portals/{portal.id}/manual-verify/"
    response = client.post(url)

    assert response.status_code == http_status.HTTP_200_OK
    portal.refresh_from_db()

    assert portal.consecutive_failures == 0
    assert portal.check_interval_minutes == 15
    assert portal.health_status == HealthStatus.ONLINE
    assert portal.status == PortalStatus.ONLINE
    assert portal.last_successful_check_at is not None
    assert "Manually verified by" in portal.notes


@pytest.mark.django_db
@patch('apps.notifications.sender.send_message')
def test_daily_health_report_separates_captcha_protected(mock_send_message):
    agency = Agency.objects.create(name="NIMASA Agency", acronym="NIMASA", official_domains=["nimasa.gov.ng"])
    portal_captcha = Portal.objects.create(
        agency=agency, name="NIMASA Careers", url="https://nimasa.gov.ng/careers",
        health_status=HealthStatus.CAPTCHA_PROTECTED, status=PortalStatus.CAPTCHA_PROTECTED
    )
    portal_ok = Portal.objects.create(
        agency=agency, name="NIMASA Main", url="https://nimasa.gov.ng/main",
        health_status=HealthStatus.ONLINE, status=PortalStatus.ONLINE
    )

    yesterday = timezone.now().date() - timezone.timedelta(days=1)
    yesterday_dt = timezone.now() - timezone.timedelta(days=1)

    # Snapshot 1: CAPTCHA protected check
    Snapshot.objects.create(
        portal=portal_captcha, status_code=200, created_at=yesterday_dt
    )
    # Snapshot 2: Successful check
    Snapshot.objects.create(
        portal=portal_ok, status_code=200, created_at=yesterday_dt
    )

    daily_health_report()

    mock_send_message.assert_called_once()
    report_text = mock_send_message.call_args[1]['text']

    # Must contain separate CAPTCHA Protected metric line and 100% success rate
    assert "🛡️ CAPTCHA Protected: 1" in report_text
    assert "📈 Success Rate: 100.00%" in report_text
