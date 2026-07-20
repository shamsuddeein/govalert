"""
Admin bot command handlers — /admin, /broadcast, /stats.
Restricted to is_admin / is_super_admin users only.
"""
import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


def _require_admin(message: dict):
    """Return user if they are admin, else send denial and return None."""
    from apps.accounts.models import TelegramUser
    from apps.notifications.sender import send_message
    telegram_id = message.get('from', {}).get('id')
    chat_id = message.get('chat', {}).get('id')
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
        if not user.is_admin:
            send_message(chat_id=chat_id, text="🚫 Admin access required.")
            return None
        return user
    except TelegramUser.DoesNotExist:
        send_message(chat_id=chat_id, text="🚫 You are not registered. Send /start first.")
        return None


def handle_admin(message: dict):
    """Show admin panel summary."""
    user = _require_admin(message)
    if not user:
        return
    from apps.accounts.models import TelegramUser
    from apps.alerts.models import Alert, AlertStatus
    from apps.agencies.models import Portal, PortalStatus
    from apps.notifications.sender import send_message

    chat_id = message['chat']['id']
    total_users = TelegramUser.objects.filter(state='ACTIVE').count()
    pending_alerts = Alert.objects.filter(status=AlertStatus.PENDING).count()
    portals_down = Portal.objects.filter(status=PortalStatus.OFFLINE, is_active=True).count()

    text = (
        f"🔧 <b>RecruitmentAlert Admin Panel</b>\n\n"
        f"👥 Active Users: <b>{total_users:,}</b>\n"
        f"⏳ Alerts Pending Review: <b>{pending_alerts}</b>\n"
        f"❌ Portals Down: <b>{portals_down}</b>\n\n"
        f"Commands:\n"
        f"/stats — Full statistics\n"
        f"/broadcast — Send message to all users"
    )
    send_message(chat_id=chat_id, text=text, parse_mode='HTML')


def handle_broadcast(message: dict):
    """Super admin only — initiate a broadcast message."""
    from apps.accounts.models import TelegramUser
    from apps.notifications.sender import send_message
    telegram_id = message.get('from', {}).get('id')
    chat_id = message.get('chat', {}).get('id')

    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)
    except TelegramUser.DoesNotExist:
        return

    if not user.is_super_admin:
        send_message(chat_id=chat_id, text="🚫 Super Admin access required for /broadcast.")
        return

    # Extract message text after /broadcast
    parts = message.get('text', '').split(maxsplit=1)
    if len(parts) < 2:
        send_message(chat_id=chat_id, text="Usage: /broadcast [message text]\n\nThis will be sent to all active users.")
        return

    broadcast_text = parts[1].strip()
    recipient_count = TelegramUser.objects.filter(state='ACTIVE', receive_alerts=True).count()

    send_message(
        chat_id=chat_id,
        text=(
            f"📢 <b>Broadcast Preview</b>\n\n"
            f"{broadcast_text}\n\n"
            f"───────────────\n"
            f"This will be sent to <b>{recipient_count:,} users</b>.\n"
            f"Reply /confirm_broadcast to send."
        ),
        parse_mode='HTML',
    )


def handle_stats(message: dict):
    """Show detailed bot statistics to admin."""
    user = _require_admin(message)
    if not user:
        return

    from apps.accounts.models import TelegramUser
    from apps.alerts.models import Alert, AlertStatus
    from apps.agencies.models import Agency, Portal
    from apps.notifications.models import Notification, NotificationStatus
    from apps.notifications.sender import send_message

    chat_id = message['chat']['id']
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_users = TelegramUser.objects.count()
    active_users = TelegramUser.objects.filter(state='ACTIVE').count()
    alerts_today = Alert.objects.filter(created_at__gte=today_start).count()
    notifs_today = Notification.objects.filter(queued_at__gte=today_start, status=NotificationStatus.SENT).count()
    failed_today = Notification.objects.filter(queued_at__gte=today_start, status=NotificationStatus.FAILED).count()

    text = (
        f"📊 <b>RecruitmentAlert Statistics</b>\n\n"
        f"👥 Total Users: <b>{total_users:,}</b>\n"
        f"✅ Active Users: <b>{active_users:,}</b>\n"
        f"🏛️ Agencies Monitored: <b>{Agency.objects.filter(is_active=True).count()}</b>\n"
        f"🌐 Active Portals: <b>{Portal.objects.filter(is_active=True).count()}</b>\n\n"
        f"<b>Today</b>\n"
        f"🔔 Alerts Detected: <b>{alerts_today}</b>\n"
        f"📨 Notifications Sent: <b>{notifs_today:,}</b>\n"
        f"❌ Failed Deliveries: <b>{failed_today}</b>"
    )
    send_message(chat_id=chat_id, text=text, parse_mode='HTML')
