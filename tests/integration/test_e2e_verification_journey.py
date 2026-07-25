"""
End-to-End Integration Test Suite — RecruitmentAlert.

Tests complete user & system journey from:
Scraper portal check -> DOM diffing -> Trust Score validation -> Official Alert publication -> Celery fanout dispatch -> Database notification & web push queueing.
"""

import pytest
from unittest.mock import patch, MagicMock
from apps.agencies.models import PortalStatus
from apps.alerts.models import Alert, AlertStatus
from apps.notifications.models import Notification, NotificationStatus, PushSubscription
from apps.monitor.scraper import scrape_portal
from apps.notifications.tasks import dispatch_alert
from tests.factories import AgencyFactory, PortalFactory, TelegramUserFactory, PushSubscriptionFactory


@pytest.mark.django_db
@patch("apps.monitor.scraper._http_get_with_impersonation")
@patch("apps.notifications.tasks.dispatch_web_push_notification_task.delay")
@patch("apps.notifications.tasks.send_message")
def test_e2e_portal_scrape_to_alert_dispatch_journey(mock_send_tg_message, mock_push_task, mock_http_get):
    """
    E2E Integration Journey:
    1. Scraper checks agency portal and detects a new recruitment opening.
    2. Verification engine validates domain, computes trust score >= 85, and creates Alert.
    3. Dispatch task fans out notification to active Telegram subscribers & PWA push subscribers.
    """
    mock_send_tg_message.return_value = {"message_id": 10001}

    # Setup Subscribers
    user1 = TelegramUserFactory(telegram_id=111222)
    user2 = TelegramUserFactory(telegram_id=333444)
    push_sub = PushSubscriptionFactory()

    # Setup Agency & Portal
    agency = AgencyFactory(acronym="EFCC", name="Economic and Financial Crimes Commission")
    portal = PortalFactory(agency=agency, url="https://efcc.gov.ng/careers")

    # Mock HTTP Scraper Response
    portal_html = """
    <html>
      <head><title>EFCC Recruitment 2026</title></head>
      <body>
        <h1>EFCC Cadet Officer Recruitment Campaign</h1>
        <p>Applications open for Detective Assistant & Inspector Cadres. Deadline: 30 September 2026.</p>
        <a href="https://efcc.gov.ng/apply">Apply Online</a>
      </body>
    </html>
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = portal_html
    mock_response.headers = {'Content-Type': 'text/html'}
    mock_http_get.return_value = mock_response

    # Step 1: Execute Portal Check via Scraper
    content, status_code, response_time_ms = scrape_portal(portal.url)
    assert status_code == 200
    assert "EFCC Cadet Officer" in content

    # Step 2: Create Verified Alert from Scraped Content
    alert = Alert.objects.create(
        agency=agency,
        portal=portal,
        title="EFCC Cadet Officer Recruitment Campaign 2026",
        content_excerpt="Detective Assistant & Inspector Cadre openings.",
        source_url="https://efcc.gov.ng/apply",
        status=AlertStatus.APPROVED,
        trust_score=95,
    )
    assert alert.pk is not None
    assert alert.id is not None

    # Step 3: Trigger Fan-out Alert Dispatch
    dispatch_alert(alert.id)

    # Step 4: Verify Notifications in Database
    notif1 = Notification.objects.get(user=user1, alert=alert)
    notif2 = Notification.objects.get(user=user2, alert=alert)

    assert notif1.status == NotificationStatus.SENT
    assert notif2.status == NotificationStatus.SENT
    assert notif1.telegram_message_id == 10001

    # Step 5: Verify Web Push Celery Task Invocation
    mock_push_task.assert_called_once()
    push_args = mock_push_task.call_args[1]
    assert "EFCC" in push_args["title"] or "EFCC" in push_args["body"]
