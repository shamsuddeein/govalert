"""
Subscription business logic.
Handles auto-subscribe on /start, unsubscribe all, and re-subscribe.
"""
import logging
from django.db import transaction

from apps.accounts.models import TelegramUser
from apps.agencies.models import Agency
from .models import Subscription

logger = logging.getLogger(__name__)


def auto_subscribe_all(user: TelegramUser) -> int:
    """
    Subscribe a user to ALL active agencies.
    Called immediately after /start or user re-activation.
    Uses bulk_create with ignore_conflicts=True to be idempotent.
    
    Returns: number of new subscriptions created.
    """
    active_agencies = Agency.objects.filter(is_active=True)

    subscriptions_to_create = [
        Subscription(user=user, agency=agency)
        for agency in active_agencies
    ]

    created = Subscription.objects.bulk_create(
        subscriptions_to_create,
        ignore_conflicts=True,     # Skip if (user, agency) pair already exists
    )

    # Re-activate any existing inactive subscriptions
    Subscription.objects.filter(
        user=user,
        agency__in=active_agencies,
        is_active=False,
    ).update(is_active=True, unsubscribed_at=None)

    # Update subscriber counts
    for agency in Agency.objects.filter(is_active=True):
        agency.subscriber_count = Subscription.objects.filter(agency=agency, is_active=True).count()
        agency.save(update_fields=['subscriber_count'])

    logger.info(f"Auto-subscribed user {user.telegram_id} to {len(active_agencies)} agencies.")
    return len(created)


def unsubscribe_all(user: TelegramUser) -> int:
    """
    Deactivate all of a user's subscriptions.
    Called when user sends /unsubscribe.
    Also sets user.receive_alerts = False.
    
    Returns: number of subscriptions deactivated.
    """
    with transaction.atomic():
        count = Subscription.objects.filter(
            user=user, is_active=True
        ).update(is_active=False)

        user.receive_alerts = False
        user.save(update_fields=['receive_alerts'])

    logger.info(f"Unsubscribed user {user.telegram_id} from all agencies ({count} subs).")
    return count


def unsubscribe_from_agency(user: TelegramUser, agency: Agency) -> bool:
    """
    Deactivate a user's subscription to a specific agency.
    Returns True if a subscription was found and deactivated.
    """
    try:
        sub = Subscription.objects.get(user=user, agency=agency)
        sub.unsubscribe()
        logger.info(f"User {user.telegram_id} unsubscribed from {agency.acronym}.")
        return True
    except Subscription.DoesNotExist:
        return False


def get_active_subscriptions(user: TelegramUser):
    """Return queryset of a user's active subscriptions with agency details."""
    return (
        Subscription.objects
        .filter(user=user, is_active=True)
        .select_related('agency')
        .order_by('agency__acronym')
    )


def get_agency_subscriber_ids(agency: Agency) -> list[int]:
    """
    Return list of telegram_ids for all active subscribers of an agency.
    Used by the notification dispatcher to know who to alert.
    """
    return list(
        Subscription.objects
        .filter(agency=agency, is_active=True, user__receive_alerts=True)
        .exclude(user__state='BANNED')
        .values_list('user_id', flat=True)
    )


def match_keyword_subscriptions_for_alert(alert) -> int:
    """
    Check an approved Alert against active KeywordSubscription records.
    Sends email for any case-insensitive substring match in alert title,
    agency name / acronym, or positions text.
    Updates last_matched_at on matched KeywordSubscription.
    """
    from django.core.mail import send_mail
    from django.conf import settings
    from django.utils import timezone
    from .models import KeywordSubscription

    active_subs = KeywordSubscription.objects.filter(is_active=True)
    if not active_subs.exists():
        return 0

    agency_name = alert.agency.name if alert.agency else ""
    agency_acronym = alert.agency.acronym if alert.agency else ""
    alert_title = alert.title or ""
    positions_text = alert.positions or getattr(alert, 'raw_text', '') or ""

    # Combined searchable string
    searchable_text = f"{alert_title} {agency_name} {agency_acronym} {positions_text}".lower()

    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://www.recruitmentalert.com.ng').rstrip('/')
    job_ref = getattr(alert, 'ref', alert.id)
    job_url = f"{frontend_url}/jobs/{job_ref}"
    deadline_str = alert.deadline.strftime("%d %b %Y") if getattr(alert, 'deadline', None) else "See portal for deadline"
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'alerts@recruitmentalert.com.ng')

    match_count = 0
    now = timezone.now()

    for sub in active_subs:
        kw = sub.query_text.strip().lower()
        if kw and kw in searchable_text:
            subject = f"New Matching Recruitment Alert: {alert_title}"
            body = (
                f"Hello,\n\n"
                f"A new recruitment matching your keyword subscription '{sub.query_text}' was just verified:\n\n"
                f"Position: {alert_title}\n"
                f"Agency: {agency_name} ({agency_acronym})\n"
                f"Deadline: {deadline_str}\n"
                f"View details: {job_url}\n\n"
                f"— RecruitmentAlert Intelligence Team\n"
            )
            try:
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=from_email,
                    recipient_list=[sub.email],
                    fail_silently=True,
                )
                sub.last_matched_at = now
                sub.save(update_fields=['last_matched_at'])
                match_count += 1
            except Exception as exc:
                logger.warning(f"Failed to send keyword alert email to {sub.email}: {exc}")

    if match_count > 0:
        logger.info(f"Alert {alert.id} matched {match_count} keyword subscriptions.")
    return match_count


def notify_job_watchers(alert) -> int:
    """
    When a new Alert / RecruitmentEvent update is approved, send direct Telegram
    notifications to all TelegramUser accounts watching this recruitment chain.
    """
    from apps.notifications.sender import send_message
    from apps.bot.templates import format_alert_full
    from django.conf import settings
    from django.utils import timezone
    from .models import TelegramJobWatch

    watches = TelegramJobWatch.objects.filter(is_active=True).select_related('user', 'alert')
    if not watches.exists():
        return 0

    target_alert_ids = {alert.id}
    if alert.recruitment_event:
        prev = alert.recruitment_event.previous_event
        while prev:
            for linked_alert in prev.alerts.all():
                target_alert_ids.add(linked_alert.id)
            prev = prev.previous_event

    matching_watches = watches.filter(alert_id__in=target_alert_ids)
    if not matching_watches.exists():
        return 0

    update_msg = (
        f"<b>🔔 Watched Recruitment Update!</b>\n\n"
        f"{format_alert_full(alert)}\n\n"
        f"<i>You are receiving this update because you subscribed to watch alerts for this job posting on RecruitmentAlert.</i>"
    )

    sent_count = 0
    now = timezone.now()

    for watch in matching_watches:
        if watch.user and watch.user.receive_alerts and watch.user.state != 'BANNED':
            res = send_message(
                chat_id=watch.user.telegram_id,
                text=update_msg,
                parse_mode='HTML'
            )
            if res:
                watch.last_notified_at = now
                watch.save(update_fields=['last_notified_at'])
                sent_count += 1

    if sent_count > 0:
        logger.info(f"Dispatched watched job update for Alert {alert.id} to {sent_count} Telegram watchers.")
    return sent_count


