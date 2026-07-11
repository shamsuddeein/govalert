"""
GovAlert Backup Writer
Nightly: exports SQLite (users.db) to JSON and posts to govalert-backup channel.
Restore: download JSON from channel → run restore.py → bot is back.
"""
import json
import logging
import sqlite3
from datetime import datetime, date, timezone
from pathlib import Path

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def export_and_backup() -> bool:
    """
    Export all SQLite tables to JSON and post to govalert-backup Telegram channel.
    Called nightly at 1 AM by APScheduler.
    Returns True on success.
    """
    channel_id = settings.TELEGRAM_BACKUP_CHANNEL_ID
    if not channel_id:
        logger.warning("TELEGRAM_BACKUP_CHANNEL_ID not set — skipping backup.")
        return False

    db_path = settings.DATABASES['default']['NAME']

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        backup = {
            'exported_at': datetime.now(timezone.utc).isoformat(),
            'version':     '1.0',
            'users':         [dict(r) for r in conn.execute('SELECT * FROM users')],
            'alerts':        [dict(r) for r in conn.execute('SELECT * FROM alerts_alert')],
            'notifications': [dict(r) for r in conn.execute('SELECT * FROM notifications_notification')],
            'fake_reports':  [dict(r) for r in conn.execute('SELECT * FROM detector_alertreport')],
        }
        conn.close()

        json_bytes = json.dumps(backup, indent=2, ensure_ascii=False, default=str).encode('utf-8')
        filename = f"backup_{date.today().isoformat()}.json"
        caption = (
            f"🗄️ Nightly Backup — {date.today()}\n"
            f"👥 Users: {len(backup['users'])}\n"
            f"🔔 Alerts: {len(backup['alerts'])}\n"
            f"📨 Notifications: {len(backup['notifications'])}"
        )

        base_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"
        response = requests.post(
            f"{base_url}/sendDocument",
            data={'chat_id': channel_id, 'caption': caption},
            files={'document': (filename, json_bytes, 'application/json')},
            timeout=30,
        )
        data = response.json()

        if data.get('ok'):
            logger.info(f"✅ Backup posted to govalert-backup channel: {filename}")
            # Update index.json with backup info
            _update_index_backup(data['result']['message_id'])
            return True
        else:
            logger.error(f"Backup upload failed: {data.get('description')}")
            return False

    except Exception as exc:
        logger.exception(f"Backup failed: {exc}")
        return False


def _update_index_backup(message_id: int):
    """Update index.json with the latest backup message ID."""
    index_path = settings.INDEX_JSON_PATH
    try:
        if index_path.exists():
            with open(index_path) as f:
                index = json.load(f)
        else:
            index = {}

        index.setdefault('backup_channel', {})
        index['backup_channel']['last_backup_id'] = message_id
        index['backup_channel']['last_backup'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2)
    except Exception as exc:
        logger.warning(f"Could not update index.json backup entry: {exc}")
