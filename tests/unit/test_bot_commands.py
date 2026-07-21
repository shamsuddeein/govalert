import pytest
from unittest.mock import patch
from apps.accounts.models import TelegramUser, UserState
from apps.agencies.models import Agency
from apps.bot.handlers.commands import handle_start
from apps.subscriptions.models import Subscription


@pytest.mark.django_db
def test_handle_start_new_user():
    # Arrange: create an active agency
    agency = Agency.objects.create(
        name="Nigeria Customs Service",
        acronym="NCS",
        official_domains=["customs.gov.ng"],
        is_active=True
    )

    # Message mock payload
    message = {
        'chat': {'id': 12345},
        'from': {
            'id': 12345,
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'testuser'
        }
    }

    # Act
    with patch('apps.notifications.sender.send_message') as mock_send:
        handle_start(message)

    # Assert
    # 1. User created
    user = TelegramUser.objects.get(telegram_id=12345)
    assert user.first_name == 'Test'
    assert user.last_name == 'User'
    assert user.state == UserState.ACTIVE

    # 2. Automatically subscribed to active agencies
    assert Subscription.objects.filter(user=user, agency=agency, is_active=True).exists()

    # 3. Welcome message sent
    mock_send.assert_called_once()
    args, kwargs = mock_send.call_args
    assert kwargs['chat_id'] == 12345
    assert "Welcome to RecruitmentAlert" in kwargs['text']
    assert 'reply_markup' in kwargs
    assert kwargs['reply_markup']['inline_keyboard'][0][0]['callback_data'] == 'show_settings'


@pytest.mark.django_db
def test_handle_start_returning_user():
    # Arrange
    user = TelegramUser.objects.create(
        telegram_id=12345,
        first_name="Test",
        state=UserState.ACTIVE
    )
    message = {
        'chat': {'id': 12345},
        'from': {
            'id': 12345,
            'first_name': 'Test',
            'last_name': 'User',
        }
    }

    # Act
    with patch('apps.notifications.sender.send_message') as mock_send:
        handle_start(message)

    # Assert
    mock_send.assert_called_once()
    args, kwargs = mock_send.call_args
    assert kwargs['chat_id'] == 12345
    assert "Welcome back to RecruitmentAlert" in kwargs['text']


@pytest.mark.django_db
def test_handle_start_watch_deeplink():
    from apps.alerts.models import Alert, AlertStatus, EventType
    from apps.subscriptions.models import TelegramJobWatch

    agency = Agency.objects.create(name="Nigeria Police Force", acronym="NPF", official_domains=["npf.gov.ng"], is_active=True)
    alert = Alert.objects.create(pk=999, agency=agency, title="NPF Constable Recruitment 2026", status=AlertStatus.APPROVED, event_type=EventType.RECRUITMENT_OPEN)

    message = {
        'chat': {'id': 99999},
        'from': {'id': 99999, 'first_name': 'Watcher', 'username': 'watcheruser'},
        'text': '/start watch_999-GA'
    }

    with patch('apps.notifications.sender.send_message') as mock_send:
        handle_start(message)

    user = TelegramUser.objects.get(telegram_id=99999)
    assert TelegramJobWatch.objects.filter(user=user, alert=alert, is_active=True).exists()

    mock_send.assert_called_once()
    assert "Job Watch Activated" in mock_send.call_args[1]['text']


@pytest.mark.django_db
def test_notify_job_watchers():
    from apps.alerts.models import Alert, AlertStatus, EventType
    from apps.subscriptions.models import TelegramJobWatch
    from apps.subscriptions.services import notify_job_watchers

    user = TelegramUser.objects.create(telegram_id=88888, first_name="Watcher", state=UserState.ACTIVE)
    agency = Agency.objects.create(name="Nigeria Immigration Service", acronym="NIS", official_domains=["immigration.gov.ng"], is_active=True)
    alert = Alert.objects.create(pk=888, agency=agency, title="NIS Officer Recruitment", status=AlertStatus.APPROVED, event_type=EventType.DEADLINE_EXTENDED)

    TelegramJobWatch.objects.create(user=user, alert=alert, is_active=True)

    with patch('apps.notifications.sender.send_message', return_value=True) as mock_send:
        count = notify_job_watchers(alert)
        assert count == 1
        mock_send.assert_called_once()
        assert "Watched Recruitment Update" in mock_send.call_args[1]['text']


@pytest.mark.django_db
def test_allalerts_mybookmarks_unwatch():
    from apps.alerts.models import Alert, AlertStatus, EventType
    from apps.subscriptions.models import TelegramJobWatch
    from apps.bot.handlers.commands import handle_allalerts, handle_mybookmarks, handle_unwatch

    agency = Agency.objects.create(name="Federal Inland Revenue Service", acronym="FIRS", is_active=True)
    alert = Alert.objects.create(pk=777, agency=agency, title="FIRS Tax Officer 2026", status=AlertStatus.APPROVED, event_type=EventType.RECRUITMENT_OPEN)

    user = TelegramUser.objects.create(telegram_id=77777, first_name="Bookmarker", state=UserState.ACTIVE)
    watch = TelegramJobWatch.objects.create(user=user, alert=alert, is_active=True)

    msg = {'chat': {'id': 77777}, 'from': {'id': 77777, 'first_name': 'Bookmarker'}}

    # Test /mybookmarks
    with patch('apps.notifications.sender.send_message') as mock_send:
        handle_mybookmarks(msg)
        assert "Your Active Job Watches" in mock_send.call_args[1]['text']
        assert "FIRS Tax Officer 2026" in mock_send.call_args[1]['text']

    # Test /unwatch 777
    msg_unwatch = {'chat': {'id': 77777}, 'from': {'id': 77777, 'first_name': 'Bookmarker'}, 'text': '/unwatch 777'}
    with patch('apps.notifications.sender.send_message') as mock_send:
        handle_unwatch(msg_unwatch)
        assert "Watch Removed" in mock_send.call_args[1]['text']
        assert not TelegramJobWatch.objects.filter(pk=watch.pk, is_active=True).exists()

    # Test /allalerts
    watch.is_active = True
    watch.save()
    with patch('apps.notifications.sender.send_message') as mock_send:
        handle_allalerts(msg)
        assert "General Feed Restored" in mock_send.call_args[1]['text']
        assert not TelegramJobWatch.objects.filter(user=user, is_active=True).exists()


