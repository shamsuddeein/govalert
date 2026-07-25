import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status as http_status
from apps.agencies.models import Agency, Portal, HealthStatus, PortalStatus
from apps.monitor.models import Snapshot
from apps.monitor.tasks import daily_health_report


@pytest.mark.django_db
def test_system_health_view_recalculates_genuine_success_rate_and_excluded_metrics():
    from django.contrib.auth import get_user_model
    User = get_user_model()
    admin = User.objects.create_superuser(username="adminmetrics", email="adminmetrics@govalert.com.ng", password="pass")

    client = APIClient()
    client.force_authenticate(user=admin)

    agency = Agency.objects.create(name="Federal Agency", acronym="FA", official_domains=["fa.gov.ng"])

    # 1. Healthy online portal
    portal_online = Portal.objects.create(
        agency=agency, name="Online Portal", url="https://fa.gov.ng/online",
        health_status=HealthStatus.ONLINE, status=PortalStatus.ONLINE
    )
    # 2. Portal in exponential backoff (10+ failures) -> DEGRADED
    portal_backoff = Portal.objects.create(
        agency=agency, name="Degraded Portal", url="https://fa.gov.ng/degraded",
        consecutive_failures=10, check_interval_minutes=360,
        health_status=HealthStatus.DEGRADED, status=PortalStatus.DEGRADED
    )
    # 3. CAPTCHA protected portal
    portal_captcha = Portal.objects.create(
        agency=agency, name="Captcha Portal", url="https://fa.gov.ng/captcha",
        health_status=HealthStatus.CAPTCHA_PROTECTED, status=PortalStatus.CAPTCHA_PROTECTED
    )
    # 4. Firewall blocked portal
    portal_firewall = Portal.objects.create(
        agency=agency, name="Firewall Portal", url="https://fa.gov.ng/blocked",
        health_status=HealthStatus.MANUAL_MONITORING_REQUIRED, status=PortalStatus.MANUAL_MONITORING_REQUIRED
    )

    now = timezone.now()
    # Create snapshots today
    Snapshot.objects.create(portal=portal_online, status_code=200, created_at=now)
    Snapshot.objects.create(portal=portal_backoff, status_code=500, created_at=now)
    Snapshot.objects.create(portal=portal_captcha, status_code=200, created_at=now)
    Snapshot.objects.create(portal=portal_firewall, status_code=403, created_at=now)

    response = client.get("/api/v1/admin/system-health/")
    assert response.status_code == http_status.HTTP_200_OK

    sys_status = response.data['system_status']

    # Must display 3 distinct excluded metrics
    assert sys_status['backoff_skipped'] == 1
    assert sys_status['captcha_blocked'] == 1
    assert sys_status['firewall_blocked'] == 1

    # Total checks = 4. Excluded = 3. Effective denominator = 1. Successful = 1.
    assert sys_status['effective_total_checks_today'] == 1
    assert sys_status['successful_checks_today'] == 1
    assert sys_status['failed_checks_today'] == 0
    # Genuine success rate must be 100.0% instead of 50.0% or 25.0%!
    assert sys_status['success_rate_today'] == 100.0


@pytest.mark.django_db
@patch('apps.notifications.sender.send_message')
def test_daily_health_report_outputs_distinct_excluded_metrics(mock_send_message):
    agency = Agency.objects.create(name="Test Agency", acronym="TA", official_domains=["ta.gov.ng"])
    p_online = Portal.objects.create(agency=agency, name="Online", url="https://ta.gov.ng/1", health_status=HealthStatus.ONLINE)
    p_degraded = Portal.objects.create(agency=agency, name="Degraded", url="https://ta.gov.ng/2", consecutive_failures=12, health_status=HealthStatus.DEGRADED)
    p_captcha = Portal.objects.create(agency=agency, name="Captcha", url="https://ta.gov.ng/3", health_status=HealthStatus.CAPTCHA_PROTECTED)
    p_blocked = Portal.objects.create(agency=agency, name="Blocked", url="https://ta.gov.ng/4", health_status=HealthStatus.MANUAL_MONITORING_REQUIRED)

    yesterday_dt = timezone.now() - timedelta(days=1)
    Snapshot.objects.create(portal=p_online, status_code=200, created_at=yesterday_dt)
    Snapshot.objects.create(portal=p_degraded, status_code=500, created_at=yesterday_dt)
    Snapshot.objects.create(portal=p_captcha, status_code=200, created_at=yesterday_dt)
    Snapshot.objects.create(portal=p_blocked, status_code=403, created_at=yesterday_dt)

    daily_health_report()

    mock_send_message.assert_called_once()
    report_text = mock_send_message.call_args[1]['text']

    assert "⏸️ Backoff Skipped: 1" in report_text
    assert "🛡️ CAPTCHA Blocked: 1" in report_text
    assert "🚫 Firewall Blocked: 1" in report_text
    assert "❌ Genuine Failures: 0" in report_text
    assert "📈 Genuine Success Rate: 100.00%" in report_text
