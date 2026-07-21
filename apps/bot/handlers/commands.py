"""
Command handlers — stub implementations.
Full logic implemented in Volume 2 (Bot Specification).
"""
import logging
from django.db.models import Avg

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


def _pk_from_ref(ref: str) -> int | None:
    if '-GA' in ref:
        try:
            return int(ref.split('-GA')[0])
        except ValueError:
            return None
    if ref.isdigit():
        return int(ref)
    return None


def handle_start(message: dict):
    """
    /start — Register user + auto-subscribe to ALL agencies immediately.
    Supports Telegram Deep Linking payload `/start general` or `/start watch_{job_ref}`.
    """
    from apps.subscriptions.services import auto_subscribe_all
    from apps.subscriptions.models import TelegramJobWatch
    from apps.alerts.models import Alert
    from apps.notifications.sender import send_message
    from apps.bot.messages import WELCOME_MESSAGE, RETURNING_MESSAGE
    from apps.bot.keyboards import get_start_keyboard
    from django.conf import settings

    user, created = _get_or_create_user(message)
    if not user:
        return

    chat_id = message['chat']['id']

    if created:
        auto_subscribe_all(user)
        user.state = 'ACTIVE'
        user.save(update_fields=['state'])

    text_content = (message.get('text') or '').strip()
    parts = text_content.split()
    payload = parts[1] if len(parts) > 1 else ''

    if payload == 'general':
        # Reset user to general feed mode
        TelegramJobWatch.objects.filter(user=user, is_active=True).update(is_active=False)
        send_message(
            chat_id=chat_id,
            text=(
                f"<b>🔔 General Recruitment Feed Active!</b>\n\n"
                f"Hello {user.display_name}! You are set to receive <b>all verified Nigerian government recruitment alerts</b> across all 41 monitored MDA portals in real-time."
            ),
            parse_mode='HTML',
            reply_markup=get_start_keyboard()
        )
        return

    if payload.startswith('watch_'):
        job_ref = payload.replace('watch_', '').strip()
        alert = None
        
        pk = _pk_from_ref(job_ref)
        if pk:
            alert = Alert.objects.filter(pk=pk).first()

        if not alert and job_ref:
            alert = Alert.objects.filter(title__icontains=job_ref).first()

        if alert:
            watch, watch_created = TelegramJobWatch.objects.get_or_create(
                user=user,
                alert=alert,
                defaults={'is_active': True}
            )
            if not watch.is_active:
                watch.is_active = True
                watch.save(update_fields=['is_active'])

            frontend_url = getattr(settings, 'FRONTEND_URL', 'https://www.recruitmentalert.com.ng').rstrip('/')
            web_url = f"{frontend_url}/jobs/{getattr(alert, 'ref', alert.id)}"

            agency_name = alert.agency.name if alert.agency else "Official Agency"

            watch_msg = (
                f"<b>🔔 Job Watch Activated!</b>\n\n"
                f"You're now watching <b>'{alert.title}'</b> at {agency_name}.\n"
                f"You'll be notified if this recruitment's deadline changes, a shortlist is published, or it closes.\n\n"
                f"<b>Note:</b> Since you have an active watch, you will only receive alerts for jobs you've watched, not the general feed. Use /allalerts anytime to switch back to receiving every verified alert instead."
            )
            send_message(chat_id=chat_id, text=watch_msg, parse_mode='HTML')
            logger.info(f"User {user.telegram_id} is watching job #{alert.id}")
            return

    if created:
        send_message(
            chat_id=chat_id,
            text=WELCOME_MESSAGE.format(name=user.display_name),
            parse_mode='HTML',
            reply_markup=get_start_keyboard()
        )
        logger.info(f"New user {user.telegram_id} registered and subscribed.")
    else:
        user.mark_active()
        send_message(chat_id=chat_id, text=RETURNING_MESSAGE.format(name=user.display_name), parse_mode='HTML')
        logger.info(f"Returning user {user.telegram_id} re-started bot.")


def handle_allalerts(message: dict):
    """
    /allalerts — Deactivates all active TelegramJobWatch records for this user,
    confirming: "You're now receiving all verified alerts again."
    """
    from apps.subscriptions.models import TelegramJobWatch
    from apps.notifications.sender import send_message

    user, _ = _get_or_create_user(message)
    if not user:
        return

    updated_count = TelegramJobWatch.objects.filter(user=user, is_active=True).update(is_active=False)
    chat_id = message['chat']['id']

    send_message(
        chat_id=chat_id,
        text="<b>🔔 General Feed Restored</b>\n\nYou're now receiving all verified alerts again.",
        parse_mode='HTML'
    )
    logger.info(f"User {user.telegram_id} reset watches to general feed (deactivated {updated_count} watches).")


def handle_mybookmarks(message: dict):
    """
    /mybookmarks — List this user's active watches with instructions to reply or use /unwatch.
    """
    from apps.subscriptions.models import TelegramJobWatch
    from apps.notifications.sender import send_message

    user, _ = _get_or_create_user(message)
    if not user:
        return

    chat_id = message['chat']['id']
    active_watches = TelegramJobWatch.objects.filter(user=user, is_active=True).select_related('alert', 'alert__agency')

    if not active_watches.exists():
        send_message(
            chat_id=chat_id,
            text="<b>🔖 You have no active job watches.</b>\n\nYou are currently receiving the <b>general feed</b> of all verified alerts. Tap '🔔 Get alerts for this job' on any recruitment page on RecruitmentAlert to watch specific postings!",
            parse_mode='HTML'
        )
        return

    items = []
    for w in active_watches:
        acronym = w.alert.agency.acronym if w.alert.agency else "MDA"
        items.append(f"• <b>#{w.alert.pk}</b>: {w.alert.title} ({acronym}) — <i>Active Watch</i>")

    watches_text = "\n".join(items)
    reply_msg = (
        f"<b>🔖 Your Active Job Watches ({len(active_watches)})</b>\n\n"
        f"{watches_text}\n\n"
        f"<i>To stop watching a specific job, use:</i>\n"
        f"<code>/unwatch [job_id]</code>\n\n"
        f"<i>To switch back to receiving all verified alerts:</i>\n"
        f"<code>/allalerts</code>"
    )
    send_message(chat_id=chat_id, text=reply_msg, parse_mode='HTML')


def handle_unwatch(message: dict):
    """
    /unwatch {id} — Deactivate a specific watch, confirm removal.
    """
    from apps.subscriptions.models import TelegramJobWatch
    from apps.alerts.models import Alert
    from apps.notifications.sender import send_message

    user, _ = _get_or_create_user(message)
    if not user:
        return

    chat_id = message['chat']['id']
    text = (message.get('text') or '').strip()
    parts = text.split(maxsplit=1)

    if len(parts) < 2:
        send_message(
            chat_id=chat_id,
            text="<b>Usage:</b> <code>/unwatch [job_id]</code>\n\nExample: <code>/unwatch 102</code>\nType /mybookmarks to see your active watches.",
            parse_mode='HTML'
        )
        return

    target_ref = parts[1].strip()
    pk = _pk_from_ref(target_ref)

    watch = None
    if pk:
        watch = TelegramJobWatch.objects.filter(user=user, alert_id=pk, is_active=True).first()

    if not watch and target_ref:
        watch = TelegramJobWatch.objects.filter(user=user, alert__title__icontains=target_ref, is_active=True).first()

    if not watch:
        send_message(
            chat_id=chat_id,
            text=f"⚠️ No active watch found for '{target_ref}'. Type /mybookmarks to see your active watches.",
            parse_mode='HTML'
        )
        return

    watch.is_active = False
    watch.save(update_fields=['is_active'])

    remaining_watches = TelegramJobWatch.objects.filter(user=user, is_active=True).count()
    if remaining_watches == 0:
        mode_note = "\n\nYou now have 0 active watches. You have been switched back to the general feed for all verified alerts!"
    else:
        mode_note = f"\n\nYou have {remaining_watches} remaining active watch(es)."

    send_message(
        chat_id=chat_id,
        text=f"<b>❌ Watch Removed</b>\n\nYou are no longer watching <b>{watch.alert.title}</b>.{mode_note}",
        parse_mode='HTML'
    )
    logger.info(f"User {user.telegram_id} unwatched job {watch.alert.id}")


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


def format_agencies_message(agencies):
    online  = [a for a in agencies if a.status == "online"]
    offline = [a for a in agencies if a.status != "online"]

    lines = []
    lines.append(f"📡 <b>Monitored Agencies</b> — {len(agencies)}")
    lines.append(f"🟢 Online: {len(online)}   🔴 Offline: {len(offline)}")
    lines.append("")

    categories = {
        "Security & Law Enforcement": ["NPF","NIS","Army","Navy","NAF","NDA","DSS","NSCDC","NCoS","CDCFIB","FFS"],
        "Anti-Corruption & Justice":  ["EFCC","ICPC"],
        "Finance & Revenue":          ["CBN", "FIRS", "FMF", "NCS"],
        "Energy & Natural Resources": ["NNPC"],
        "Immigration & Identity":     ["NIS","NIMC","FRSC"],
        "Education":                  ["JAMB","NUC","UBEC","TRCN","FME"],
        "Health":                     ["NAFDAC","NHIA","FMH"],
        "Infrastructure":             ["NRC","NPA","NIMASA","FMW"],
        "Technology & Communications":["NCC","NITDA"],
        "Other Federal Agencies":     ["INEC","ICPC","FCSC","PSC","FMA","FMD","FMI","FMEnv","FMI","NDA","NDLEA"],
    }

    placed = set()
    for category, acronyms in categories.items():
        acronyms_upper = [ac.upper() for ac in acronyms]
        members = [a for a in agencies if a.acronym.upper() in acronyms_upper and a.acronym.upper() not in placed]
        if not members:
            continue
        lines.append(f"<b>{category}</b>")
        for a in members:
            dot = "🟢" if a.status == "online" else "🔴"
            lines.append(f"{dot} {a.acronym} — {a.name}")
            placed.add(a.acronym.upper())
        lines.append("")

    # Any not placed
    rest = [a for a in agencies if a.acronym.upper() not in placed]
    if rest:
        lines.append("<b>Other</b>")
        for a in rest:
            dot = "🟢" if a.status == "online" else "🔴"
            lines.append(f"{dot} {a.acronym} — {a.name}")

    return "\n".join(lines)


def handle_agencies(message: dict):
    """Show list of all monitored agencies with portal status."""
    from apps.agencies.models import Agency
    from apps.notifications.sender import send_message
    chat_id = message['chat']['id']
    agencies_qs = Agency.objects.filter(is_active=True).prefetch_related('portals').order_by('acronym')
    
    agencies_list = list(agencies_qs)
    for agency in agencies_list:
        is_online = any(p.status in ['ONLINE', 'UP'] for p in agency.portals.all())
        agency.status = "online" if is_online else "offline"
        
    text = format_agencies_message(agencies_list)
    send_message(chat_id=chat_id, text=text, parse_mode='HTML')


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
        f"Blocked: <b>{blocked}</b>\n"
        f"Captcha: <b>{captcha}</b>\n"
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
        send_message(chat_id=chat_id, text="Usage: /search [keyword]\nExample: /search customs")
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
