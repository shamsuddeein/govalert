"""
Web Push Notification Service : Handles VAPID signing, payload encryption,
dispatching web push notifications, and automatic cleanup of 404/410 expired subscriptions.
"""
import json
import logging
from django.conf import settings
from pywebpush import webpush, WebPushException
from apps.notifications.models import PushSubscription

logger = logging.getLogger('apps.notifications')


def get_vapid_public_key():
    """Returns the configured VAPID public key."""
    return getattr(settings, 'VAPID_PUBLIC_KEY', 'BEl62iUYgUivxIkv69yViEuiBIa1-A1J9s3kK3yP1N2_vH3v_rK2A0Z0J_7R9a1x_B2u4E5F6G7H8I9J0K1L2M3')


def get_vapid_private_key():
    """Returns the configured VAPID private key."""
    return getattr(settings, 'VAPID_PRIVATE_KEY', 'x1y2z3A4B5C6D7E8F9G0H1I2J3K4L5M6N7O8P9Q0R1S')


def get_vapid_claims():
    """Returns the VAPID claims dictionary."""
    admin_email = getattr(settings, 'VAPID_ADMIN_EMAIL', 'mailto:admin@recruitmentalert.com.ng')
    if not admin_email.startswith('mailto:'):
        admin_email = f"mailto:{admin_email}"
    return {
        'sub': admin_email
    }


def send_single_push(subscription: PushSubscription, title: str, body: str, url: str = '/jobs', icon: str = '/icon-192x192.png') -> bool:
    """
    Sends a Web Push notification to a single PushSubscription record.
    If the subscription is no longer valid (HTTP 404 or 410 Gone), automatically deletes it from the database.
    """
    subscription_info = {
        'endpoint': subscription.endpoint,
        'keys': {
            'p256dh': subscription.p256dh,
            'auth': subscription.auth,
        }
    }

    payload = json.dumps({
        'title': title,
        'body': body,
        'url': url,
        'icon': icon,
        'tag': f"job-alert-{hash(url)}",
    })

    try:
        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=get_vapid_private_key(),
            vapid_claims=get_vapid_claims(),
            ttl=86400,  # 24 hours delivery window
        )
        logger.info("Web push delivered successfully", extra={'endpoint': subscription.endpoint[:30]})
        return True
    except WebPushException as ex:
        status_code = getattr(ex.response, 'status_code', None)
        logger.warning(f"Web push failed: {ex} (status={status_code})", extra={'endpoint': subscription.endpoint[:30]})

        # If HTTP 404 (Not Found) or 410 (Gone / Unsubscribed), purge invalid subscription
        if status_code in (404, 410):
            logger.info("Deleting expired / invalid web push subscription", extra={'endpoint': subscription.endpoint[:30]})
            subscription.delete()
        else:
            # Mark inactive for retries if temporary server failure
            subscription.is_active = False
            subscription.save(update_fields=['is_active'])

        return False
    except Exception as ex:
        logger.error(f"Unexpected error sending web push: {ex}", exc_info=True)
        return False


def broadcast_push_notification(title: str, body: str, url: str = '/jobs', icon: str = '/icon-192x192.png') -> dict:
    """
    Broadcasts a push notification to all active web push subscribers.
    Returns stats dict: { 'total': N, 'sent': S, 'failed': F }.
    """
    active_subs = PushSubscription.objects.filter(is_active=True)
    total = active_subs.count()
    sent = 0
    failed = 0

    for sub in active_subs.iterator(chunk_size=100):
        success = send_single_push(sub, title=title, body=body, url=url, icon=icon)
        if success:
            sent += 1
        else:
            failed += 1

    logger.info(f"Broadcast push finished: {sent}/{total} sent successfully, {failed} failed/purged.")
    return {'total': total, 'sent': sent, 'failed': failed}
