import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.utils import timezone
from apps.agencies.models import Agency, Portal, HealthStatus, PortalStatus, PortalPriority
from apps.monitor.tasks import portal_check, check_standard_portals, check_high_priority_portals, check_low_activity_portals


@pytest.mark.django_db
def test_portal_calculate_backoff_interval_minutes():
    agency = Agency.objects.create(name="Test Agency 1", acronym="TA1", official_domains=["ta1.gov.ng"])
    portal = Portal.objects.create(agency=agency, name="P1", url="https://ta1.gov.ng")

    # 0 to 3 consecutive failures: 15 min
    for fail_count in [0, 1, 2, 3]:
        portal.consecutive_failures = fail_count
        assert portal.calculate_backoff_interval_minutes() == 15

    # 4 to 6 consecutive failures: 60 min (1 hr)
    for fail_count in [4, 5, 6]:
        portal.consecutive_failures = fail_count
        assert portal.calculate_backoff_interval_minutes() == 60

    # 7 to 9 consecutive failures: 180 min (3 hrs)
    for fail_count in [7, 8, 9]:
        portal.consecutive_failures = fail_count
        assert portal.calculate_backoff_interval_minutes() == 180

    # 10 or more consecutive failures: 360 min (6 hrs)
    for fail_count in [10, 11, 20]:
        portal.consecutive_failures = fail_count
        assert portal.calculate_backoff_interval_minutes() == 360


@pytest.mark.django_db
def test_portal_is_due_for_check_property():
    now = timezone.now()
    agency = Agency.objects.create(name="Test Agency 2", acronym="TA2", official_domains=["ta2.gov.ng"])
    portal = Portal.objects.create(
        agency=agency, name="P2", url="https://ta2.gov.ng",
        check_interval_minutes=60, poll_interval=3600
    )

    # Never checked -> due
    portal.last_checked_at = None
    assert portal.is_due_for_check is True

    # Checked 15 minutes ago (interval 60 min) -> NOT due
    portal.last_checked_at = now - timedelta(minutes=15)
    assert portal.is_due_for_check is False

    # Checked 65 minutes ago (interval 60 min) -> due
    portal.last_checked_at = now - timedelta(minutes=65)
    assert portal.is_due_for_check is True

    # Inactive portal -> NOT due
    portal.is_active = False
    assert portal.is_due_for_check is False


from core.exceptions import ScraperException


@pytest.mark.django_db
@patch('core.plugins.get_scraper_backend')
def test_portal_check_failure_backoff_progression(mock_backend):
    # Mock scraper to fail
    mock_scraper = MagicMock()
    mock_scraper.scrape.side_effect = ScraperException("Connection Failed")
    mock_backend.return_value = mock_scraper

    agency = Agency.objects.create(name="EFCC Agency", acronym="EFCC", official_domains=["efcc.gov.ng"])
    portal = Portal.objects.create(
        agency=agency, name="EFCC Careers", url="https://efcc.gov.ng/careers",
        check_interval_minutes=15, poll_interval=900, consecutive_failures=3
    )

    # 4th failure: should change check interval to 60 mins (1 hr)
    portal_check(portal.id)
    portal.refresh_from_db()
    assert portal.consecutive_failures == 4
    assert portal.check_interval_minutes == 60
    assert portal.poll_interval == 3600
    assert portal.health_status == HealthStatus.OFFLINE
    assert portal.is_active is True

    # Fast forward to 7 failures
    portal.consecutive_failures = 6
    portal.save()
    portal_check(portal.id)
    portal.refresh_from_db()
    assert portal.consecutive_failures == 7
    assert portal.check_interval_minutes == 180
    assert portal.poll_interval == 10800
    assert portal.health_status == HealthStatus.OFFLINE

    # Fast forward to 10 failures: should enter DEGRADED status with 360 min (6 hrs) interval
    portal.consecutive_failures = 9
    portal.save()
    portal_check(portal.id)
    portal.refresh_from_db()
    assert portal.consecutive_failures == 10
    assert portal.check_interval_minutes == 360
    assert portal.poll_interval == 21600
    assert portal.health_status == HealthStatus.DEGRADED
    assert portal.status == PortalStatus.DEGRADED
    assert portal.is_active is True  # Stays active in 6-hour backoff


@pytest.mark.django_db
@patch('core.plugins.get_scraper_backend')
def test_portal_check_success_resets_backoff(mock_backend):
    # Portal currently in 6-hour backoff (10 failures, DEGRADED)
    agency = Agency.objects.create(name="FFS Agency", acronym="FFS", official_domains=["ffs.gov.ng"])
    portal = Portal.objects.create(
        agency=agency, name="FFS Careers", url="https://ffs.gov.ng/careers",
        consecutive_failures=10, check_interval_minutes=360, poll_interval=21600,
        health_status=HealthStatus.DEGRADED, status=PortalStatus.DEGRADED
    )

    # Mock scraper returning successful 200 response
    mock_scraper = MagicMock()
    mock_scraper.scrape.return_value = ("<html><body>Careers Page</body></html>", 200, 150)
    mock_backend.return_value = mock_scraper

    portal_check(portal.id)
    portal.refresh_from_db()

    # Must reset failure count and restore 15-min check interval & ONLINE status
    assert portal.consecutive_failures == 0
    assert portal.check_interval_minutes == 15
    assert portal.poll_interval == 900
    assert portal.health_status == HealthStatus.ONLINE
    assert portal.status == PortalStatus.ONLINE


@pytest.mark.django_db
@patch('apps.monitor.tasks.portal_check.apply_async')
def test_check_standard_portals_skips_portals_in_backoff(mock_apply_async):
    now = timezone.now()
    agency = Agency.objects.create(name="FIRS Agency", acronym="FIRS", official_domains=["firs.gov.ng"])

    # Portal 1: Healthy (checked 20 min ago, interval 15 min) -> DUE
    p1 = Portal.objects.create(
        agency=agency, name="P1", url="https://firs.gov.ng/p1",
        priority=PortalPriority.MEDIUM, check_interval_minutes=15, poll_interval=900,
        last_checked_at=now - timedelta(minutes=20)
    )

    # Portal 2: In backoff (checked 20 min ago, 5 failures, interval 60 min) -> NOT DUE
    p2 = Portal.objects.create(
        agency=agency, name="P2", url="https://firs.gov.ng/p2",
        priority=PortalPriority.MEDIUM, consecutive_failures=5,
        check_interval_minutes=60, poll_interval=3600,
        last_checked_at=now - timedelta(minutes=20)
    )

    check_standard_portals()

    # Only p1 should be queued!
    mock_apply_async.assert_called_once_with(args=[p1.id], queue='crawl')


@pytest.mark.django_db
def test_portal_admin_current_check_interval_display():
    from apps.agencies.admin import PortalAdmin
    from django.contrib.admin.sites import AdminSite

    agency = Agency.objects.create(name="NHIA Agency", acronym="NHIA", official_domains=["nhia.gov.ng"])
    portal_admin = PortalAdmin(Portal, AdminSite())

    p_normal = Portal.objects.create(agency=agency, name="N1", url="u1", check_interval_minutes=15)
    p_1hr = Portal.objects.create(agency=agency, name="N2", url="u2", check_interval_minutes=60, consecutive_failures=4)
    p_3hr = Portal.objects.create(agency=agency, name="N3", url="u3", check_interval_minutes=180, consecutive_failures=7)
    p_degraded = Portal.objects.create(agency=agency, name="N4", url="u4", check_interval_minutes=360, consecutive_failures=10)

    assert portal_admin.current_check_interval(p_normal) == "15 mins"
    assert portal_admin.current_check_interval(p_1hr) == "1 hour"
    assert portal_admin.current_check_interval(p_3hr) == "3 hours"
    assert portal_admin.current_check_interval(p_degraded) == "6 hours (DEGRADED)"
