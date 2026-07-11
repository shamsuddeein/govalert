"""
Telegram message sender — wraps the Bot API with rate limiting.
"""
import json
import logging
import time
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_BASE_URL = None


def _get_base_url() -> str:
    global _BASE_URL
    if _BASE_URL is None:
        token = settings.TELEGRAM_BOT_TOKEN
        _BASE_URL = f"https://api.telegram.org/bot{token}"
    return _BASE_URL


def send_message(
    chat_id: int,
    text: str,
    parse_mode: str = 'HTML',
    reply_markup: dict | None = None,
    disable_web_page_preview: bool = True,
) -> dict | None:
    """
    Send a Telegram message to a single chat_id.
    Returns the API response dict on success, None on failure.
    Raises TelegramDeliveryException if user has blocked the bot.
    """
    if getattr(settings, 'TESTING', False):
        import unittest.mock
        if not isinstance(requests.post, (unittest.mock.Mock, unittest.mock.MagicMock)):
            logger.info(f"[TESTING] send_message suppressed for chat_id={chat_id}")
            return {'message_id': 999999}

    payload = {
        'chat_id': chat_id,
        'text': text[:4096],  # Telegram message limit
        'parse_mode': parse_mode,
        'disable_web_page_preview': disable_web_page_preview,
    }
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)

    try:
        response = requests.post(
            f"{_get_base_url()}/sendMessage",
            json=payload,
            timeout=10,
        )
        data = response.json()

        if not data.get('ok'):
            error_code = data.get('error_code')
            description = data.get('description', '')
            if error_code in (403, 400) and 'blocked' in description.lower():
                from core.exceptions import TelegramDeliveryException
                raise TelegramDeliveryException(f"User {chat_id} has blocked the bot.")
            logger.warning(f"Telegram API error for chat {chat_id}: {description}")
            return None

        return data.get('result')

    except requests.RequestException as exc:
        logger.error(f"Network error sending to chat {chat_id}: {exc}")
        return None


def answer_callback_query(callback_query_id: str, text: str = '') -> None:
    """Answer an inline keyboard callback query (required to clear the loading state)."""
    if getattr(settings, 'TESTING', False):
        import unittest.mock
        if not isinstance(requests.post, (unittest.mock.Mock, unittest.mock.MagicMock)):
            logger.info("[TESTING] answer_callback_query suppressed")
            return

    try:
        requests.post(
            f"{_get_base_url()}/answerCallbackQuery",
            json={'callback_query_id': callback_query_id, 'text': text},
            timeout=5,
        )
    except requests.RequestException as exc:
        logger.warning(f"Failed to answer callback query: {exc}")


def send_bulk_messages(
    chat_ids: list[int],
    text: str,
    parse_mode: str = 'HTML',
    reply_markup: dict | None = None,
    rate_limit: float = 1 / 30,  # 30 messages per second
) -> tuple[int, int]:
    """
    Send the same message to multiple chat_ids with rate limiting.
    Returns (success_count, failure_count).
    """
    success = 0
    failure = 0

    for chat_id in chat_ids:
        result = send_message(chat_id=chat_id, text=text, parse_mode=parse_mode, reply_markup=reply_markup)
        if result:
            success += 1
        else:
            failure += 1
        time.sleep(rate_limit)

    logger.info(f"Bulk send complete: {success} sent, {failure} failed out of {len(chat_ids)}")
    return success, failure
