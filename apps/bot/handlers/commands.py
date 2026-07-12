"""
Command handlers — stub implementations.
Full logic implemented in Volume 2 (Bot Specification).
"""
import logging

logger = logging.getLogger(__name__)


def _get_or_create_user(message: dict):
    """Get or create a TelegramUser from an incoming message."""
    from apps.accounts.models import TelegramUser, UserState
    from django.conf import settings
    from_user = message.get('from', {})
    telegram_id = from_user.get('id')
    if not telegram_id:
        return None, False

    is_super = telegram_id in getattr(settings, 'SUPER_ADMIN_TELEGRAM_IDS', [])

    user, created = TelegramUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            'first_name': from_user.get('first_name', ''),
            'last_name': from_user.get('last_name', ''),
            'username': from_user.get('username'),
            'state': UserState.NEW_USER,
            'is_admin': is_super,
            'is_super_admin': is_super,
        }
    )

    if not created:
        user.mark_active()
        # Update name in case it changed
        updated = False
        if user.first_name != from_user.get('first_name', ''):
            user.first_name = from_user.get('first_name', '')
            updated = True
        # Ensure super admin permissions are updated if environment settings changed
        if is_super and (not user.is_admin or not user.is_super_admin):
            user.is_admin = True
            user.is_super_admin = True
            updated = True
        if updated:
            user.save(update_fields=['first_name', 'is_admin', 'is_super_admin'])

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
    from apps.bot.keyboards import get_start_keyboard

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
            reply_markup=get_start_keyboard()
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
    agencies = Agency.objects.filter(is_active=True).prefetch_related('portals').order_by('acronym')
    lines = [f"<b>Monitored Agencies ({agencies.count()})</b>\n"]
    for i, agency in enumerate(agencies, 1):
        is_online = any(p.status in ['ONLINE', 'UP'] for p in agency.portals.all())
        status = "[Online]" if is_online else "[Offline]"
        lines.append(f"{i}. {status} <b>{agency.acronym}</b> - {agency.name}")
    send_message(chat_id=chat_id, text='\n'.join(lines), parse_mode='HTML')


def handle_jobs(message: dict):
    from apps.alerts.models import Alert, AlertStatus
    from apps.notifications.sender import send_message
    from apps.bot.templates import format_alert_brief
    chat_id = message['chat']['id']
    alerts = Alert.objects.filter(status=AlertStatus.APPROVED, agency__is_active=True).order_by('-updated_at')[:10]
    if not alerts:
        send_message(chat_id=chat_id, text="No job alerts found yet. Check back soon!")
        return
    
    formatted_alerts = [f"{i}. {format_alert_brief(alert)}" for i, alert in enumerate(alerts, 1)]
    divider = "\n\n"
    text = "<b>Latest Jobs</b>\n\n" + divider.join(formatted_alerts)
    send_message(chat_id=chat_id, text=text, parse_mode='HTML')


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
        send_message(chat_id=chat_id, text="No alerts in your history yet.")
        return
    lines = [f"<b>Your Last {notifs.count()} Alerts</b>\n"]
    for i, n in enumerate(notifs, 1):
        lines.append(f"{i}. [{n.alert.agency.acronym}] {n.alert.title} - {n.sent_at.strftime('%d %b %Y')}")
    send_message(chat_id=chat_id, text='\n'.join(lines), parse_mode='HTML')


def handle_status(message: dict):
    from apps.agencies.models import Portal, PortalStatus
    from apps.notifications.sender import send_message
    from django.db.models import Avg
    chat_id = message['chat']['id']
    
    portals = Portal.objects.filter(is_active=True)
    total = portals.count()
    
    online = portals.filter(status__in=[PortalStatus.ONLINE, PortalStatus.UP]).count()
    offline = portals.filter(status__in=[PortalStatus.OFFLINE, PortalStatus.DOWN]).count()
    blocked = portals.filter(status=PortalStatus.BLOCKED).count()
    captcha = portals.filter(status=PortalStatus.CAPTCHA).count()
    rate_limited = portals.filter(status=PortalStatus.RATE_LIMITED).count()
    maintenance = portals.filter(status=PortalStatus.MAINTENANCE).count()
    unknown = portals.filter(status=PortalStatus.UNKNOWN).count()
    
    avg_res = portals.filter(response_time_ms__isnull=False).aggregate(Avg('response_time_ms'))['response_time_ms__avg']
    avg_res_text = f"{int(avg_res)} ms" if avg_res is not None else "0 ms"
    
    text = (
        f"<b>Portal Health Status</b>\n\n"
        f"Online: <b>{online}</b>\n"
        f"Offline: <b>{offline}</b>\n"
        f"Rate Limited: <b>{rate_limited}</b>\n"
        f"Maintenance: <b>{maintenance}</b>\n"
        f"Unknown: <b>{unknown}</b>\n\n"
        f"Average response: <b>{avg_res_text}</b>\n"
        f"Total Monitored: <b>{total}</b>"
    )
    send_message(chat_id=chat_id, text=text, parse_mode='HTML')


def handle_settings(message: dict):
    from apps.notifications.sender import send_message
    from apps.bot.keyboards import get_settings_keyboard
    user, _ = _get_or_create_user(message)
    chat_id = message['chat']['id']
    text = (
        f"<b>Settings</b>\n\n"
        f"Timezone: <code>{user.timezone}</code>\n"
        f"Alerts: {'Enabled' if user.receive_alerts else 'Disabled'}\n"
        f"Language: {user.language.upper()}"
    )
    send_message(chat_id=chat_id, text=text, parse_mode='HTML', reply_markup=get_settings_keyboard())


def handle_search(message: dict):
    from apps.notifications.sender import send_message
    chat_id = message['chat']['id']
    # Extract keyword after /search command
    parts = message.get('text', '').split(maxsplit=1)
    if len(parts) < 2:
        send_message(chat_id=chat_id, text="Usage: /search <keyword>\nExample: /search customs")
        return
    keyword = parts[1].strip()[:200]
    from apps.alerts.models import Alert, AlertStatus
    from apps.bot.templates import format_alert_brief
    results = Alert.objects.filter(
        status=AlertStatus.APPROVED,
        agency__is_active=True,
        title__icontains=keyword
    ).order_by('-updated_at')[:10]
    if not results:
        send_message(chat_id=chat_id, text=f"No results for <b>{keyword}</b>", parse_mode='HTML')
        return
    
    formatted_alerts = [f"{i}. {format_alert_brief(alert)}" for i, alert in enumerate(results, 1)]
    divider = "\n\n"
    text = f"<b>Results for '{keyword}'</b>\n\n" + divider.join(formatted_alerts)
    send_message(chat_id=chat_id, text=text, parse_mode='HTML')


def handle_latest(message: dict):
    from apps.alerts.models import Alert, AlertStatus
    from apps.notifications.sender import send_message
    from apps.bot.templates import format_alert_full
    from apps.bot.keyboards import get_alert_keyboard
    chat_id = message['chat']['id']
    alert = Alert.objects.filter(status=AlertStatus.APPROVED).order_by('-created_at').first()
    if not alert:
        send_message(chat_id=chat_id, text="No alerts yet.")
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
        text="To report a fake alert, tap the <b>[Report Fake]</b> button directly on the alert message.",
        parse_mode='HTML',
    )
