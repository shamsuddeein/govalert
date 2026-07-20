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
