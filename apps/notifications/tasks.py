import time
import logging
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from apps.notifications.models import Notification, NotificationStatus
from apps.notifications.sender import send_message
from core.exceptions import TelegramDeliveryException
from apps.bot.templates import format_alert_full
from apps.bot.keyboards import get_alert_keyboard
from celery import shared_task


logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def retry_failed_notifications():
    """
    Retry notifications that failed in the last 24 hours.
    Runs hourly via Celery Beat.
    """
    logger.info("Starting retry of failed notifications...")
    cutoff = timezone.now() - timedelta(days=1)
    failed = Notification.objects.filter(
        status=NotificationStatus.FAILED,
        queued_at__gte=cutoff
    ).select_related('user', 'alert__agency')

    count = failed.count()
    if count == 0:
        logger.info("No failed notifications to retry.")
        return

    logger.info(f"Found {count} failed notifications to retry.")
    success_count = 0

    for notif in failed:
        if not notif.alert:
            continue
        try:
            text = format_alert_full(notif.alert)
            keyboard = get_alert_keyboard(notif.alert.id)
            result = send_message(
                chat_id=notif.user.telegram_id,
                text=text,
                reply_markup=keyboard
            )
            if result:
                notif.mark_sent(result['message_id'])
                success_count += 1
            else:
                notif.mark_failed("Retry failed again.")
        except TelegramDeliveryException as exc:
            notif.mark_failed(str(exc), blocked=True)
        except Exception as exc:
            notif.mark_failed(f"Unexpected error: {str(exc)}")

    logger.info(f"Retry completed: {success_count} succeeded, {count - success_count} failed.")


@shared_task(
    ignore_result=True,
    soft_time_limit=600,   # 10 min soft limit : fan-out to large subscriber base
    time_limit=700,        # 11.7 min hard limit
)
def dispatch_alert(alert_id: int):
    """
    Fan out alert to all active subscribers.
    Creates Notification entries for all matching users and sends messages.

    Deduplication is done with a single pre-fetch of already-notified user IDs
    before the send loop, avoiding one EXISTS query per user.
    """
    from apps.alerts.models import Alert, AlertStatus
    from apps.accounts.models import TelegramUser, UserState

    logger.info(f"Starting dispatch for alert {alert_id}...")
    try:
        alert = Alert.objects.select_related('agency', 'recruitment_event').get(pk=alert_id)
    except Alert.DoesNotExist:
        logger.error(f"Alert {alert_id} not found for dispatch.")
        return

    if alert.status != AlertStatus.APPROVED:
        logger.warning(f"Alert {alert_id} is not APPROVED (status={alert.status}). Dispatch skipped.")
        return

    from apps.subscriptions.models import TelegramJobWatch
    from apps.subscriptions.models import Subscription

    # Identify all users with at least 1 active job watch (curated mode users)
    curated_user_ids = set(
        TelegramJobWatch.objects.filter(is_active=True)
        .values_list('user_id', flat=True)
    )

    # General-feed users still honour consent, account state, and agency-level
    # unsubscribe preferences. A job watch only changes feed mode; it never
    # overrides the user's privacy or subscription choices.
    eligible_users = TelegramUser.objects.filter(
        receive_alerts=True,
        state=UserState.ACTIVE,
        consented_to_data_policy=True,
    )

    unsubscribed_user_ids = set(
        Subscription.objects.filter(agency=alert.agency, is_active=False)
        .values_list('user_id', flat=True)
    )

    general_users = eligible_users.filter(
        Q(subscriptions__agency=alert.agency, subscriptions__is_active=True) |
        Q(subscriptions__isnull=True)
    ).exclude(pk__in=unsubscribed_user_ids).exclude(pk__in=curated_user_ids).distinct()

    is_update = bool(alert.recruitment_event and alert.recruitment_event.previous_event)

    if not is_update:
        users = list(general_users)
    else:
        chain_alert_ids = {alert.id}
        prev = alert.recruitment_event.previous_event
        while prev:
            for linked_alert in prev.alerts.all():
                chain_alert_ids.add(linked_alert.id)
            prev = prev.previous_event

        watchers_user_ids = set(
            TelegramJobWatch.objects.filter(alert_id__in=chain_alert_ids, is_active=True)
            .values_list('user_id', flat=True)
        )
        watched_users = eligible_users.filter(pk__in=watchers_user_ids)
        users = list(set(general_users).union(set(watched_users)))

    # Dispatch web email notifications to registered Web users
    try:
        from apps.subscriptions.services import (
            dispatch_web_user_emails, match_keyword_subscriptions_for_alert, notify_job_watchers
        )
        dispatch_web_user_emails(alert)
        match_keyword_subscriptions_for_alert(alert)
        if is_update:
            notify_job_watchers(alert)
    except Exception as exc:
        logger.warning(f"Failed multi-channel subscriber dispatch for alert {alert.id}: {exc}")

    if not users:
        logger.info(
            f"No active Telegram subscribers for alert #{alert.id} "
            f"({alert.agency.acronym}). Dispatch skipped."
        )
        return

    text = format_alert_full(alert)
    keyboard = get_alert_keyboard(alert.id)

    # Post to public alert channel
    try:
        from storage.events import post_public_alert
        post_public_alert(text)
    except Exception as exc:
        logger.warning(f"Failed to post to public alert channel: {exc}")

    # Pre-fetch user IDs that have already received this alert.
    # One query up-front eliminates N per-user EXISTS checks inside the loop.
    already_sent_user_ids = set(
        Notification.objects.filter(alert=alert)
        .values_list('user_id', flat=True)
    )

    success_count = 0
    failure_count = 0

    for user in users:
        # O(1) set lookup : no DB hit per user.
        if user.pk in already_sent_user_ids:
            continue

        notif = Notification.objects.create(
            user=user,
            alert=alert,
            status=NotificationStatus.QUEUED
        )

        try:
            result = send_message(
                chat_id=user.telegram_id,
                text=text,
                reply_markup=keyboard
            )
            if result:
                notif.mark_sent(result['message_id'])
                success_count += 1
            else:
                notif.mark_failed("Send failed.")
                failure_count += 1
        except TelegramDeliveryException as exc:
            notif.mark_failed(str(exc), blocked=True)
            failure_count += 1
        except Exception as exc:
            notif.mark_failed(f"Unexpected error: {str(exc)}")
            failure_count += 1

        # Global Telegram rate limit is 30 msg/sec; sleep 34ms per send.
        time.sleep(0.034)

    # Trigger Web Push API notification dispatch to all browser subscribers
    try:
        ref_code = getattr(alert, 'ref', None) or alert.id
        dispatch_web_push_notification_task.delay(
            title=f"New Verified Opening: {alert.title[:45]}",
            body=f"{alert.agency.name} ({alert.agency.acronym}) : Verified recruitment update.",
            url=f"/jobs/{ref_code}",
        )
    except Exception as exc:
        logger.warning(f"Failed to queue Web Push notification task: {exc}")

    logger.info(f"Dispatch complete for alert {alert_id}: {success_count} sent, {failure_count} failed.")


@shared_task(ignore_result=True)
def dispatch_web_push_notification_task(title: str, body: str, url: str = '/jobs', icon: str = '/icon-192x192.png'):
    """
    Celery task to broadcast Web Push notifications to all active PWA subscribers.
    Runs asynchronously following new verified recruitment publication.
    """
    from apps.notifications.push_service import broadcast_push_notification
    logger.info(f"Executing web push broadcast task: '{title}'...")
    try:
        res = broadcast_push_notification(title=title, body=body, url=url, icon=icon)
        logger.info(f"Web push broadcast finished: {res}")
        return res
    except Exception as exc:
        logger.error(f"Error in web push broadcast task: {exc}", exc_info=True)
        return None


@shared_task(ignore_result=True)
def clean_expired_personal_data_task():
    """
    Daily Celery periodic task to enforce NDPR/NDPA data retention rules:
    - Purges inactive KeywordSubscriptions older than 30 days.
    - Purges inactive PushSubscriptions older than 30 days.
    - Purges Notification delivery logs older than 90 days.
    - Purges inactive TelegramUser accounts older than 30 days.
    """
    from datetime import timedelta
    from apps.subscriptions.models import KeywordSubscription
    from apps.notifications.models import Notification, PushSubscription
    from apps.accounts.models import TelegramUser, UserState

    now = timezone.now()
    cutoff_30d = now - timedelta(days=30)
    cutoff_90d = now - timedelta(days=90)

    kw_count, _ = KeywordSubscription.objects.filter(is_active=False, created_at__lt=cutoff_30d).delete()
    push_count, _ = PushSubscription.objects.filter(is_active=False, updated_at__lt=cutoff_30d).delete()
    notif_count, _ = Notification.objects.filter(queued_at__lt=cutoff_90d).delete()
    tg_count, _ = TelegramUser.objects.filter(state=UserState.INACTIVE, last_active_at__lt=cutoff_30d).delete()

    logger.info(
        f"NDPR Periodic Retention Cleanup Completed: "
        f"{kw_count} inactive keyword subs, {push_count} inactive push subs, "
        f"{notif_count} old notifications (>90d), {tg_count} inactive Telegram users purged."
    )


