import pytest
from unittest.mock import patch
from apps.bot.dispatcher import dispatch_update


def test_dispatch_update_message_command():
    payload = {
        'update_id': 999,
        'message': {
            'text': '/help',
            'chat': {'id': 12345},
            'from': {'id': 12345, 'first_name': 'Test'}
        }
    }
    with patch('apps.bot.handlers.commands.handle_help') as mock_help:
        dispatch_update(payload)
        mock_help.assert_called_once_with(payload['message'])


def test_dispatch_update_callback_query():
    payload = {
        'update_id': 1000,
        'callback_query': {
            'id': 'abc',
            'data': 'consent_agree',
            'from': {'id': 12345}
        }
    }
    with patch('apps.bot.handlers.callbacks.handle_callback') as mock_callback:
        dispatch_update(payload)
        mock_callback.assert_called_once_with(payload['callback_query'])
