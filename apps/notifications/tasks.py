import logging
from django.utils import timezone
from datetime import timedelta
from apps.notifications.models import Notification, NotificationStatus
from apps.notifications.sender import send_message
from core.exceptions import TelegramDeliveryException
from apps.bot.templates import format_alert_full
from apps.bot.keyboards import get_alert_keyboard
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def retry_failed_notifications():
    """
    Retry notifications that failed in the last 24 hours.
    Runs hourly via APScheduler.
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


@shared_task
def dispatch_alert(alert_id: int):
    """
    Fan out alert to all active subscribers.
    Creates Notification entries for all matching users and sends messages bulk.
    """
    from apps.alerts.models import Alert
    from apps.subscriptions.models import Subscription
    from apps.accounts.models import TelegramUser, UserState

    logger.info(f"Starting dispatch for alert {alert_id}...")
    try:
        alert = Alert.objects.select_related('agency', 'recruitment_event').get(pk=alert_id)
    except Alert.DoesNotExist:
        logger.error(f"Alert {alert_id} not found for dispatch.")
        return

    from apps.subscriptions.models import TelegramJobWatch
    from apps.accounts.models import TelegramUser

    # Identify all users with at least 1 active job watch (curated mode users)
    curated_user_ids = set(
        TelegramJobWatch.objects.filter(is_active=True)
        .values_list('user_id', flat=True)
    )

    # General Feed Users: Active TelegramUsers with ZERO active watches
    general_users = TelegramUser.objects.filter(
        receive_alerts=True
    ).exclude(state='BANNED').exclude(id__in=curated_user_ids)

    is_update = bool(alert.recruitment_event and alert.recruitment_event.previous_event)

    if not is_update:
        # BRAND NEW RECRUITMENT: Send ONLY to general feed users (no active watches)
        users = list(general_users)
    else:
        # UPDATE TO AN EXISTING RECRUITMENT:
        # Find watchers of any Alert in the previous_event chain
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
        watched_users = TelegramUser.objects.filter(id__in=watchers_user_ids, receive_alerts=True).exclude(state='BANNED')

        # Target users = General Feed users + Watchers of this specific recruitment chain
        users = list(set(general_users).union(set(watched_users)))

    if not users:
        logger.info(f"No target subscribers for alert #{alert.id} ({alert.agency.acronym}). Dispatch skipped.")
        return

    text = format_alert_full(alert)
    keyboard = get_alert_keyboard(alert.id)

    # Match and send emails to keyword subscribers
    try:
        from apps.subscriptions.services import match_keyword_subscriptions_for_alert, notify_job_watchers
        match_keyword_subscriptions_for_alert(alert)
        notify_job_watchers(alert)
    except Exception as exc:
        logger.warning(f"Failed to match subscriptions/watchers for alert {alert_id}: {exc}")

    # Post to public alert channel
    try:
        from storage.events import post_public_alert
        post_public_alert(text)
    except Exception as exc:
        logger.warning(f"Failed to post to public alert channel: {exc}")

    success_count = 0
    failure_count = 0

    for user in users:
        # Check if already sent
        if Notification.objects.filter(user=user, alert=alert).exists():
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

        # Global Telegram rate limit is 30 msg/sec, sleep 0.034s per send
        import time
        time.sleep(0.034)

    logger.info(f"Dispatch complete for alert {alert_id}: {success_count} sent, {failure_count} failed.")
