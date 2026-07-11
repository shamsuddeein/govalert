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
    text: str = message.get('text', '')
    if not text:
        return

    command = text.split()[0].lower().split('@')[0]  # Strip bot username suffix

    from apps.bot.handlers.commands import (
        handle_start, handle_help, handle_unsubscribe,
        handle_agencies, handle_jobs, handle_history,
        handle_status, handle_settings, handle_search,
        handle_latest, handle_report,
    )
    from apps.bot.handlers.admin import handle_admin, handle_broadcast, handle_stats

    handlers = {
        '/start': handle_start,
        '/help': handle_help,
        '/unsubscribe': handle_unsubscribe,
        '/agencies': handle_agencies,
        '/jobs': handle_jobs,
        '/history': handle_history,
        '/status': handle_status,
        '/settings': handle_settings,
        '/search': handle_search,
        '/latest': handle_latest,
        '/report': handle_report,
        '/admin': handle_admin,
        '/broadcast': handle_broadcast,
        '/stats': handle_stats,
    }

    handler = handlers.get(command)
    if handler:
        try:
            handler(message)
        except Exception as exc:
            logger.exception(f"Handler error for command {command}: {exc}")
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
