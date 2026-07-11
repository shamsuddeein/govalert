import pytest
from django.test import Client
from unittest.mock import patch


@pytest.mark.django_db
def test_webhook_invalid_secret():
    client = Client()
    url = '/telegram/webhook/'
    with patch('django.conf.settings.TELEGRAM_WEBHOOK_SECRET', 'my-expected-secret'):
        response = client.post(
            url,
            data='{"update_id": 12345}',
            content_type='application/json',
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN='wrong-secret'
        )
        assert response.status_code == 403


@pytest.mark.django_db
@patch('apps.bot.dispatcher.dispatch_update')
def test_webhook_valid_secret(mock_dispatch):
    client = Client()
    url = '/telegram/webhook/'
    with patch('django.conf.settings.TELEGRAM_WEBHOOK_SECRET', 'my-expected-secret'):
        response = client.post(
            url,
            data='{"update_id": 12345}',
            content_type='application/json',
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN='my-expected-secret'
        )
        assert response.status_code == 200
        mock_dispatch.assert_called_once_with({"update_id": 12345})
