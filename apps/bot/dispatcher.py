"""
Bot update dispatcher — routes incoming Telegram updates to the correct handler.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def dispatch_update(data: dict[str, Any]) -> None:
    """
    Parse a raw Telegram Update dict and route to the appropriate handler.
    In production this runs synchronously in the webhook view;
    for heavy tasks (scraping etc.) it delegates to Celery.
    """
    update_id = data.get('update_id')
    logger.debug(f"Dispatching update #{update_id}")

    if 'message' in data:
        _handle_message(data['message'])
    elif 'callback_query' in data:
        _handle_callback_query(data['callback_query'])
    elif 'inline_query' in data:
        logger.info("Inline query received — not yet implemented.")
    else:
        logger.warning(f"Unknown update type in update #{update_id}: {list(data.keys())}")


def _handle_message(message: dict) -> None:
    """Route an incoming message to the correct command handler."""
    # Check for forwarded channel messages first to help retrieve IDs
    if 'forward_from_chat' in message:
        chat = message['forward_from_chat']
        if chat.get('type') == 'channel':
            chat_id = chat.get('id')
            chat_title = chat.get('title', 'Unknown')
            chat_username = chat.get('username')
            logger.info(f"Detected channel forward: {chat_title} (ID: {chat_id})")
            from apps.notifications.sender import send_message
            send_message(
                chat_id=message['chat']['id'],
                text=(
                    f"🏷️ <b>Detected Channel ID</b>\n\n"
                    f"• <b>Title</b>: <code>{chat_title}</code>\n"
                    f"• <b>ID</b>: <code>{chat_id}</code>\n"
                    f"• <b>Username</b>: @{chat_username if chat_username else 'None'}\n\n"
                    f"You can copy this ID directly into your <code>.env</code> file."
                ),
                parse_mode='HTML'
            )
            return

    text: str = message.get('text', '')
    if not text:
        return

    command = text.split()[0].lower().split('@')[0]  # Strip bot username suffix

    from apps.bot.handlers.commands import (
        handle_start, handle_help, handle_unsubscribe, handle_stop,
        handle_agencies, handle_jobs, handle_history,
        handle_status, handle_settings, handle_search,
        handle_latest, handle_report, handle_allalerts,
        handle_mybookmarks, handle_unwatch, handle_verify,
    )
    from apps.bot.handlers.admin import handle_admin, handle_broadcast, handle_stats

    handlers = {
        '/start': handle_start,
        '/help': handle_help,
        '/verify': handle_verify,
        '/stop': handle_stop,
        '/unsubscribe': handle_stop,
        '/agencies': handle_agencies,
        '/jobs': handle_jobs,
        '/history': handle_history,
        '/status': handle_status,
        '/settings': handle_settings,
        '/search': handle_search,
        '/latest': handle_latest,
        '/report': handle_report,
        '/allalerts': handle_allalerts,
        '/mybookmarks': handle_mybookmarks,
        '/mywatches': handle_mybookmarks,
        '/unwatch': handle_unwatch,
        '/admin': handle_admin,
        '/broadcast': handle_broadcast,
        '/stats': handle_stats,
    }

    handler = handlers.get(command)
    if handler:
        import time
        import json
        from django.utils import timezone

        user_id = message.get('from', {}).get('id', 'unknown')
        t0 = time.perf_counter()
        try:
            handler(message)
            duration_ms = (time.perf_counter() - t0) * 1000.0
            log_payload = {
                'timestamp': timezone.now().isoformat(),
                'component': 'bot',
                'command': command,
                'user_id': user_id,
                'duration_ms': round(duration_ms, 2),
                'status': 'success'
            }
            logger.info(
                f"BOT_COMMAND command={command} user_id={user_id} status=success in {duration_ms:.2f}ms",
                extra={'structured_log': json.dumps(log_payload)}
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - t0) * 1000.0
            log_payload = {
                'timestamp': timezone.now().isoformat(),
                'component': 'bot',
                'command': command,
                'user_id': user_id,
                'duration_ms': round(duration_ms, 2),
                'status': 'error',
                'error': str(exc)
            }
            logger.exception(
                f"BOT_COMMAND ERROR command={command} user_id={user_id}: {exc}",
                extra={'structured_log': json.dumps(log_payload)}
            )
            _send_error_reply(message)
    else:
        # Unknown command or plain text — ignore gracefully
        logger.debug(f"No handler for: {command}")


def _handle_callback_query(callback_query: dict) -> None:
    """Route inline keyboard button presses."""
    from apps.bot.handlers.callbacks import handle_callback
    try:
        handle_callback(callback_query)
    except Exception as exc:
        logger.exception(f"Callback handler error: {exc}")


def _send_error_reply(message: dict) -> None:
    """Send a generic error message to the user."""
    chat_id = message.get('chat', {}).get('id')
    if not chat_id:
        return
    from apps.notifications.sender import send_message
    send_message(
        chat_id=chat_id,
        text="⚠️ Something went wrong. Please try again or type /help."
    )
