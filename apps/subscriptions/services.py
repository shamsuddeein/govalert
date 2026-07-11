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
