"""
Command handlers — stub implementations.
Full logic implemented in Volume 2 (Bot Specification).
"""
import logging

logger = logging.getLogger(__name__)


def _get_or_create_user(message: dict):
    """Get or create a TelegramUser from an incoming message."""
    from apps.accounts.models import TelegramUser, UserState
    from_user = message.get('from', {})
    telegram_id = from_user.get('id')
    if not telegram_id:
        return None, False

    user, created = TelegramUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            'first_name': from_user.get('first_name', ''),
            'last_name': from_user.get('last_name', ''),
            'username': from_user.get('username'),
            'state': UserState.NEW_USER,
        }
    )

    if not created:
        user.mark_active()
        # Update name in case it changed
        updated = False
        if user.first_name != from_user.get('first_name', ''):
            user.first_name = from_user.get('first_name', '')
            updated = True
        if updated:
            user.save(update_fields=['first_name'])

    return user, created


def handle_start(message: dict):
    """
    /start — Register user + auto-subscribe to ALL agencies immediately.
    FR-U001, FR-S001.

    Volume 2 (updated): No consent gate. One tap = fully subscribed.
    New user  → create record, subscribe all, send WELCOME message.
    Returning → send RETURNING message (already subscribed, nothing to do).
    """
    from apps.subscriptions.services import auto_subscribe_all
    from apps.notifications.sender import send_message
    from apps.bot.messages import WELCOME_MESSAGE, RETURNING_MESSAGE
    from apps.bot.keyboards import get_onboarding_keyboard

    user, created = _get_or_create_user(message)
    if not user:
        return

    chat_id = message['chat']['id']

    if created:
        # New user — subscribe to everything immediately
        auto_subscribe_all(user)
        user.state = 'ACTIVE'
        user.save(update_fields=['state'])
        send_message(
            chat_id=chat_id,
            text=WELCOME_MESSAGE.format(name=user.display_name),
            parse_mode='HTML',
            reply_markup=get_onboarding_keyboard()
        )
        logger.info(f"New user {user.telegram_id} registered and subscribed.")
    else:
        # Returning user — just greet them, subscriptions are already active
        user.mark_active()
        send_message(chat_id=chat_id, text=RETURNING_MESSAGE.format(name=user.display_name), parse_mode='HTML')
        logger.info(f"Returning user {user.telegram_id} re-started bot.")


def handle_help(message: dict):
    from apps.notifications.sender import send_message
    from apps.bot.messages import HELP_MESSAGE
    chat_id = message['chat']['id']
    send_message(chat_id=chat_id, text=HELP_MESSAGE)


def handle_unsubscribe(message: dict):
    from apps.subscriptions.services import unsubscribe_all
    from apps.notifications.sender import send_message
    from apps.bot.messages import UNSUBSCRIBED_MESSAGE
    user, _ = _get_or_create_user(message)
    if not user:
        return
    unsubscribe_all(user)
    send_message(chat_id=message['chat']['id'], text=UNSUBSCRIBED_MESSAGE)


def handle_agencies(message: dict):
    """Show list of all monitored agencies with portal status."""
    from apps.agencies.models import Agency
    from apps.notifications.sender import send_message
    chat_id = message['chat']['id']
    agencies = Agency.objects.filter(is_active=True).prefetch_related('portals')
    lines = [f"<b>📋 Monitored Agencies ({agencies.count()})</b>\n"]
    for agency in agencies:
        status = "🟢" if any(p.status == 'UP' for p in agency.portals.all()) else "🔴"
        lines.append(f"{status} <b>{agency.acronym}</b> — {agency.name}")
    send_message(chat_id=chat_id, text='\n'.join(lines), parse_mode='HTML')


def handle_jobs(message: dict):
    from apps.alerts.models import Alert, AlertStatus
    from apps.notifications.sender import send_message
    from apps.bot.templates import format_alert_brief
    chat_id = message['chat']['id']
    alerts = Alert.objects.filter(status=AlertStatus.APPROVED).order_by('-created_at')[:10]
    if not alerts:
        send_message(chat_id=chat_id, text="📭 No job alerts found yet. Check back soon!")
        return
    lines = ["<b>🔔 Latest 10 Job Alerts</b>\n"]
    for alert in alerts:
        lines.append(format_alert_brief(alert))
    send_message(chat_id=chat_id, text='\n'.join(lines), parse_mode='HTML')


def handle_history(message: dict):
    from apps.notifications.models import Notification, NotificationStatus
    from apps.notifications.sender import send_message
    user, _ = _get_or_create_user(message)
    chat_id = message['chat']['id']
    if not user:
        return
    notifs = Notification.objects.filter(
        user=user, status=NotificationStatus.SENT
    ).select_related('alert__agency').order_by('-sent_at')[:20]
    if not notifs:
        send_message(chat_id=chat_id, text="📭 No alerts in your history yet.")
        return
    lines = [f"<b>📜 Your Last {notifs.count()} Alerts</b>\n"]
    for n in notifs:
        lines.append(f"• [{n.alert.agency.acronym}] {n.alert.title} — {n.sent_at.strftime('%d %b %Y')}")
    send_message(chat_id=chat_id, text='\n'.join(lines), parse_mode='HTML')


def handle_status(message: dict):
    from apps.agencies.models import Portal, PortalStatus
    from apps.notifications.sender import send_message
    chat_id = message['chat']['id']
    total = Portal.objects.filter(is_active=True).count()
    up = Portal.objects.filter(is_active=True, status=PortalStatus.UP).count()
    down = Portal.objects.filter(is_active=True, status=PortalStatus.DOWN).count()
    text = (
        f"<b>📡 Portal Health Status</b>\n\n"
        f"✅ Online: <b>{up}</b>\n"
        f"❌ Offline: <b>{down}</b>\n"
        f"📋 Total Monitored: <b>{total}</b>"
    )
    send_message(chat_id=chat_id, text=text, parse_mode='HTML')


def handle_settings(message: dict):
    from apps.notifications.sender import send_message
    from apps.bot.keyboards import get_settings_keyboard
    user, _ = _get_or_create_user(message)
    chat_id = message['chat']['id']
    text = (
        f"⚙️ <b>Settings</b>\n\n"
        f"🌍 Timezone: <code>{user.timezone}</code>\n"
        f"🔔 Alerts: {'Enabled' if user.receive_alerts else 'Disabled'}\n"
        f"💬 Language: {user.language.upper()}"
    )
    send_message(chat_id=chat_id, text=text, parse_mode='HTML', reply_markup=get_settings_keyboard())


def handle_search(message: dict):
    from apps.notifications.sender import send_message
    chat_id = message['chat']['id']
    # Extract keyword after /search command
    parts = message.get('text', '').split(maxsplit=1)
    if len(parts) < 2:
        send_message(chat_id=chat_id, text="🔍 Usage: /search <keyword>\nExample: /search customs")
        return
    keyword = parts[1].strip()[:200]
    from apps.alerts.models import Alert, AlertStatus
    from apps.bot.templates import format_alert_brief
    results = Alert.objects.filter(
        status=AlertStatus.APPROVED,
        title__icontains=keyword
    ).order_by('-created_at')[:10]
    if not results:
        send_message(chat_id=chat_id, text=f"🔍 No results for <b>{keyword}</b>", parse_mode='HTML')
        return
    lines = [f"🔍 <b>Results for '{keyword}'</b>\n"]
    for alert in results:
        lines.append(format_alert_brief(alert))
    send_message(chat_id=chat_id, text='\n'.join(lines), parse_mode='HTML')


def handle_latest(message: dict):
    from apps.alerts.models import Alert, AlertStatus
    from apps.notifications.sender import send_message
    from apps.bot.templates import format_alert_full
    from apps.bot.keyboards import get_alert_keyboard
    chat_id = message['chat']['id']
    alert = Alert.objects.filter(status=AlertStatus.APPROVED).order_by('-created_at').first()
    if not alert:
        send_message(chat_id=chat_id, text="📭 No alerts yet.")
        return
    send_message(
        chat_id=chat_id,
        text=format_alert_full(alert),
        parse_mode='HTML',
        reply_markup=get_alert_keyboard(alert.id),
    )


def handle_report(message: dict):
    from apps.notifications.sender import send_message
    chat_id = message['chat']['id']
    send_message(
        chat_id=chat_id,
        text="⚠️ To report a fake alert, tap the <b>[Report Fake]</b> button directly on the alert message.",
        parse_mode='HTML',
    )
