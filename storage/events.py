"""
GovAlert Event Channel Writer
Writes recruitment events as JSON messages to the private govalert-events Telegram channel.
This is the Phase 1 "database" — append-only, permanent, free.

One message per event. Never edited. Only appended.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_base_url() -> str:
    return f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"


def write_event(
    event_id: str,
    event: str,
    agency: str,
    acronym: str,
    category: str,
    title: str,
    url: str,
    trust_score: int,
    deadline: str = '',
    positions: str = '',
    status: str = 'verified',
    content_hash: str = '',
) -> bool:
    """
    Write a recruitment event to the govalert-events Telegram channel.
    Returns True on success.

    Schema matches Volume 5 spec exactly:
    {
      "event_id":    "evt_20260711_0001",
      "event":       "RECRUITMENT_OPEN",
      "agency":      "Nigeria Police Force",
      "acronym":     "NPF",
      "category":    "Security",
      "title":       "Police Constable Recruitment 2026",
      "url":         "https://npf.gov.ng/recruitment",
      "deadline":    "2026-08-10",
      "positions":   "Constable, Inspector",
      "trust_score": 98,
      "status":      "verified",
      "detected_at": "2026-07-11T11:40:00Z",
      "hash":        "4e8f3a1b..."
    }
    """
    channel_id = settings.TELEGRAM_EVENTS_CHANNEL_ID
    if not channel_id:
        logger.warning("TELEGRAM_EVENTS_CHANNEL_ID not set — skipping event write.")
        return False

    payload = {
        'event_id':    event_id,
        'event':       event,
        'agency':      agency,
        'acronym':     acronym,
        'category':    category,
        'title':       title,
        'url':         url,
        'deadline':    deadline,
        'positions':   positions,
        'trust_score': trust_score,
        'status':      status,
        'detected_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'hash':        content_hash,
    }

    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    # Wrap in code block for readability in Telegram
    message_text = f"<pre>{json_text}</pre>"

    try:
        response = requests.post(
            f"{_get_base_url()}/sendMessage",
            json={
                'chat_id': channel_id,
                'text': message_text,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True,
            },
            timeout=10,
        )
        data = response.json()
        if data.get('ok'):
            logger.info(f"Event {event_id} written to govalert-events channel.")
            return True
        else:
            logger.error(f"Failed to write event {event_id}: {data.get('description')}")
            return False
    except requests.RequestException as exc:
        logger.error(f"Network error writing event {event_id}: {exc}")
        return False


def post_public_alert(text: str) -> Optional[int]:
    """
    Post a human-readable alert to the govalert-public channel.
    Returns the Telegram message_id on success.
    """
    channel_id = settings.TELEGRAM_PUBLIC_CHANNEL_ID
    if not channel_id:
        logger.warning("TELEGRAM_PUBLIC_CHANNEL_ID not set — skipping public post.")
        return None

    try:
        response = requests.post(
            f"{_get_base_url()}/sendMessage",
            json={
                'chat_id': channel_id,
                'text': text,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True,
            },
            timeout=10,
        )
        data = response.json()
        if data.get('ok'):
            msg_id = data['result']['message_id']
            logger.info(f"Public alert posted to channel, message_id={msg_id}")
            return msg_id
        else:
            logger.error(f"Failed to post public alert: {data.get('description')}")
            return None
    except requests.RequestException as exc:
        logger.error(f"Network error posting public alert: {exc}")
        return None
