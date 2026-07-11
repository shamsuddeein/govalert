import pytest
from unittest.mock import patch, MagicMock
from apps.accounts.models import TelegramUser, UserState
from apps.agencies.models import Agency
from apps.alerts.models import Alert, EventType
from apps.notifications.models import Notification, NotificationStatus
from apps.notifications.tasks import retry_failed_notifications
from apps.notifications.sender import send_message
from core.exceptions import TelegramDeliveryException


@pytest.mark.django_db
@patch('requests.post')
def test_send_message_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        'ok': True,
        'result': {'message_id': 9999}
    }
    mock_post.return_value = mock_resp

    with patch('django.conf.settings.TELEGRAM_BOT_TOKEN', 'mock-token'):
        res = send_message(12345, "Hello")
        assert res['message_id'] == 9999


@pytest.mark.django_db
@patch('requests.post')
def test_send_message_blocked(mock_post):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        'ok': False,
        'error_code': 403,
        'description': 'Forbidden: bot was blocked by the user'
    }
    mock_post.return_value = mock_resp

    with patch('django.conf.settings.TELEGRAM_BOT_TOKEN', 'mock-token'):
        with pytest.raises(TelegramDeliveryException):
            send_message(12345, "Hello")


@pytest.mark.django_db
@patch('apps.notifications.tasks.send_message')
def test_retry_failed_notifications(mock_send):
    user = TelegramUser.objects.create(
        telegram_id=12345, first_name="Test", state=UserState.ACTIVE
    )
    agency = Agency.objects.create(
        name="Customs", acronym="NCS", official_domains=["customs.gov.ng"], is_active=True
    )
    alert = Alert.objects.create(
        agency=agency, event_type=EventType.RECRUITMENT_OPEN, title="Recruitment"
    )

    notif = Notification.objects.create(
        user=user, alert=alert, status=NotificationStatus.FAILED
    )

    mock_send.return_value = {'message_id': 7777}

    retry_failed_notifications()

    notif.refresh_from_db()
    assert notif.status == NotificationStatus.SENT
    assert notif.telegram_message_id == 7777
