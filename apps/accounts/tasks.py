import logging
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import TelegramUser, UserState

logger = logging.getLogger(__name__)


def cleanup_inactive_users():
    """Mark users as INACTIVE if they have not interacted with the bot for 90 days."""
    logger.info("Starting cleanup of inactive users...")
    cutoff = timezone.now() - timedelta(days=90)
    
    inactive_users = TelegramUser.objects.filter(
        state=UserState.ACTIVE,
        last_active__lt=cutoff
    )
    count = inactive_users.count()
    if count > 0:
        inactive_users.update(state=UserState.INACTIVE)
        logger.info(f"Marked {count} users as INACTIVE due to inactivity.")
    else:
        logger.info("No inactive users to clean up.")
