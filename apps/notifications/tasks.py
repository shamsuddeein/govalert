import logging
from django.utils import timezone
from datetime import timedelta
from apps.notifications.models import Notification, NotificationStatus
from apps.notifications.sender import send_message
from core.exceptions import TelegramDeliveryException
from apps.bot.templates import format_alert_full
from apps.bot.keyboards import get_alert_keyboard

logger = logging.getLogger(__name__)


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
