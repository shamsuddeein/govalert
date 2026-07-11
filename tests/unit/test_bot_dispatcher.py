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


def test_dispatch_update_channel_forward():
    payload = {
        'update_id': 1001,
        'message': {
            'chat': {'id': 12345},
            'from': {'id': 12345, 'first_name': 'Test'},
            'forward_from_chat': {
                'id': -1004469069163,
                'title': 'Test Channel',
                'username': 'test_channel_username',
                'type': 'channel'
            }
        }
    }
    with patch('apps.notifications.sender.send_message') as mock_send:
        dispatch_update(payload)
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        assert kwargs['chat_id'] == 12345
        assert '-1004469069163' in kwargs['text']
        assert 'Test Channel' in kwargs['text']
