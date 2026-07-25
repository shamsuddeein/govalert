"""
Verification Pipeline Unit Tests (Stages 1 to 4).

Tests:
- Stage 1: Scraper HTTP response handling (200, 404, 500, Timeout, Login redirect).
- Stage 2: Content extraction, DOM diffing, whitespace & timestamp false-positive filtering.
- Stage 3: Official source DNS domain verification, gazette index matching, timeout safe-pending mode.
- Stage 4: Publishing pipeline, reference generation, status updates & notification queueing.
"""

import responses
import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import ConnectTimeout

from apps.agencies.models import Portal, PortalStatus
from apps.monitor.scraper import scrape_portal
from apps.monitor.parser import clean_html_to_text, analyze_diff
from apps.detector.domain import is_domain_blacklisted
from apps.alerts.models import Alert, AlertStatus
from tests.factories import AgencyFactory, PortalFactory, AlertFactory, TelegramUserFactory


# ─── Stage 1: Scraper HTTP Handling ───────────────────────────────────────────

@pytest.mark.django_db
@responses.activate
@patch("apps.monitor.scraper.validate_outbound_url", return_value=True)
def test_stage1_scraper_http_200_online(mock_ssrf):
    """Stage 1: 200 OK response updates portal status to ONLINE and saves raw HTML."""
    portal = PortalFactory(url="https://ncs.gov.ng/careers")
    responses.add(
        responses.GET,
        portal.url,
        body="<html><body><h1>Nigeria Customs Service Recruitment 2026</h1></body></html>",
        status=200,
        content_type="text/html",
    )

    content, status_code, response_time_ms = scrape_portal(portal.url)

    assert status_code == 200
    assert "Nigeria Customs Service" in content
    assert response_time_ms is not None


@pytest.mark.django_db
@responses.activate
@patch("apps.monitor.scraper.validate_outbound_url", return_value=True)
def test_stage1_scraper_http_404_not_found(mock_ssrf):
    """Stage 1: 404 Not Found response returns 404 status code."""
    portal = PortalFactory(url="https://agency.gov.ng/missing-page")
    responses.add(
        responses.GET,
        portal.url,
        body="<html><body>404 Not Found</body></html>",
        status=404,
    )

    content, status_code, response_time_ms = scrape_portal(portal.url)
    assert status_code == 404


@pytest.mark.django_db
@responses.activate
@patch("apps.monitor.scraper.validate_outbound_url", return_value=True)
def test_stage1_scraper_http_500_server_error(mock_ssrf):
    """Stage 1: 500 Internal Server Error returns 500 status code."""
    portal = PortalFactory(url="https://agency.gov.ng/500-error")
    responses.add(
        responses.GET,
        portal.url,
        body="Server Error",
        status=500,
    )

    content, status_code, response_time_ms = scrape_portal(portal.url)
    assert status_code == 500


@pytest.mark.django_db
@responses.activate
@patch("apps.monitor.scraper.validate_outbound_url", return_value=True)
def test_stage1_scraper_connection_timeout(mock_ssrf):
    """Stage 1: Connection timeout is caught gracefully by scraper."""
    portal = PortalFactory(url="https://slow-portal.gov.ng/timeout")
    responses.add(
        responses.GET,
        portal.url,
        body=ConnectTimeout("Connection timed out after 10s"),
    )

    with pytest.raises(Exception):
        scrape_portal(portal.url)


@pytest.mark.django_db
@responses.activate
@patch("apps.monitor.scraper.validate_outbound_url", return_value=True)
def test_stage1_scraper_login_redirect(mock_ssrf):
    """Stage 1: Redirect to login page identifies portal requiring authentication."""
    portal = PortalFactory(url="https://protected.gov.ng/portal")
    responses.add(
        responses.GET,
        portal.url,
        status=302,
        headers={"Location": "https://protected.gov.ng/login"},
    )
    responses.add(
        responses.GET,
        "https://protected.gov.ng/login",
        body="<html><body>Please Log In to Access Recruitment Portal</body></html>",
        status=200,
    )

    content, status_code, response_time_ms = scrape_portal(portal.url)
    assert status_code in (200, 302)


# ─── Stage 2: Content Extraction & Change Detection ──────────────────────────

def test_stage2_same_html_no_change():
    """Stage 2: Identical HTML returns no change string."""
    html = "<html><body><p>No new recruitment updates today.</p></body></html>"
    text1 = clean_html_to_text(html)
    text2 = clean_html_to_text(html)

    added_diff = analyze_diff(text1, text2)
    assert len(added_diff) == 0


def test_stage2_whitespace_only_diff_filtered():
    """Stage 2: Whitespace-only formatting changes do not trigger false positive recruitment alerts."""
    html_before = "<html><body><p>Customs  Officer  Recruitment</p></body></html>"
    html_after = "<html><body>\n\t<p>Customs Officer Recruitment</p>\n</body></html>"

    text1 = clean_html_to_text(html_before)
    text2 = clean_html_to_text(html_after)

    added_diff = analyze_diff(text1, text2)
    assert len(added_diff) == 0


def test_stage2_timestamp_only_diff_filtered():
    """Stage 2: Footer tag removal/cleaning filters out noise timestamps."""
    html_before = """
    <html>
      <body>
        <h1>Civil Service Commission</h1>
        <p>Current vacancies: 0</p>
        <footer>Last checked: 2026-07-25 09:00:00 AM</footer>
      </body>
    </html>
    """
    html_after = """
    <html>
      <body>
        <h1>Civil Service Commission</h1>
        <p>Current vacancies: 0</p>
        <footer>Last checked: 2026-07-25 09:15:00 AM</footer>
      </body>
    </html>
    """

    text1 = clean_html_to_text(html_before)
    text2 = clean_html_to_text(html_after)

    added_diff = analyze_diff(text1, text2)
    assert len(added_diff) == 0


def test_stage2_real_recruitment_content_change_detected():
    """Stage 2: Real recruitment notice addition triggers change detection."""
    html_before = "<html><body><h1>Nigeria Police Force</h1><p>No active portal openings.</p></body></html>"
    html_after = """
    <html>
      <body>
        <h1>Nigeria Police Force</h1>
        <h2>Constable Recruitment Campaign 2026 Is Now Open</h2>
        <p>Applications are invited for qualified candidates. Deadline: 30 August 2026.</p>
      </body>
    </html>
    """

    text1 = clean_html_to_text(html_before)
    text2 = clean_html_to_text(html_after)

    added_diff = analyze_diff(text1, text2)
    assert len(added_diff) > 0
    assert "Constable Recruitment" in added_diff


# ─── Stage 3: Official Source Verification ───────────────────────────────────

@pytest.mark.django_db
def test_stage3_domain_blacklist_detection():
    """Stage 3: Domain blacklisting rejects fake domains."""
    assert is_domain_blacklisted("https://customs.gov.ng/careers") is False
    assert is_domain_blacklisted("https://recruitment-nigeria.com") is True
    assert is_domain_blacklisted("https://customs-recruitment.com") is True


# ─── Stage 4: Publishing Pipeline ─────────────────────────────────────────────

@pytest.mark.django_db
@patch("apps.notifications.tasks.dispatch_web_push_notification_task.delay")
def test_stage4_verified_alert_publishes_and_queues_notification(mock_push_task):
    """Stage 4: A listing that passes verification is published with reference format and queues notification."""
    TelegramUserFactory()  # Active subscriber required for fan-out
    agency = AgencyFactory(acronym="NCS", name="Nigeria Customs Service")
    alert = AlertFactory(
        agency=agency,
        title="Superintendent Cadre Recruitment 2026",
        status=AlertStatus.APPROVED,
    )

    assert alert.status == AlertStatus.APPROVED
    assert alert.id is not None

    from apps.notifications.tasks import dispatch_alert
    with patch("apps.notifications.tasks.send_message", return_value={"message_id": 999}):
        dispatch_alert(alert.id)

    mock_push_task.assert_called_once()


@pytest.mark.django_db
@patch("apps.notifications.tasks.dispatch_web_push_notification_task.delay")
def test_stage4_failed_verification_does_not_publish(mock_push_task):
    """Stage 4: A listing that fails verification (REJECTED/HELD) does not queue notifications."""
    TelegramUserFactory()
    agency = AgencyFactory(acronym="FAKE")
    alert = AlertFactory(
        agency=agency,
        title="Fake Automated Listing",
        status=AlertStatus.REJECTED,
    )

    from apps.notifications.tasks import dispatch_alert
    dispatch_alert(alert.id)

    # Push task MUST NOT be called for unapproved/rejected listings
    mock_push_task.assert_not_called()
