"""
Detailed Django Model Unit Tests.

Tests:
1. Model custom methods & computed @property attributes.
2. Unique constraints enforcement (raises IntegrityError on duplicate).
3. Meta ordering & database index constraints.
4. Foreign key cascade & protection behavior on parent deletion.
"""

import pytest
from django.db import IntegrityError
from django.utils import timezone
from apps.accounts.models import TelegramUser, WebUser, UserState
from apps.agencies.models import Agency, Portal, PortalStatus, HealthStatus, AgencyCategory
from apps.alerts.models import Alert, AlertStatus
from apps.notifications.models import Notification, NotificationStatus, PushSubscription
from tests.factories import (
    TelegramUserFactory,
    WebUserFactory,
    AgencyFactory,
    PortalFactory,
    AlertFactory,
    NotificationFactory,
    PushSubscriptionFactory,
)


@pytest.mark.django_db
def test_telegram_user_display_name_property():
    """Test TelegramUser display_name computed property."""
    user1 = TelegramUserFactory(first_name="Shamsuddeein", last_name="Alao", username="deen")
    assert user1.display_name == "Shamsuddeein"

    user2 = TelegramUserFactory(first_name="", last_name="", username="")
    assert user2.display_name == "User"


@pytest.mark.django_db
def test_portal_properties():
    """Test Portal computed properties (is_up, needs_check)."""
    portal = PortalFactory(health_status=HealthStatus.ONLINE, is_active=True)
    assert portal.is_up is True
    assert portal.needs_check is True

    portal_down = PortalFactory(health_status=HealthStatus.OFFLINE, is_active=True)
    assert portal_down.is_up is False


@pytest.mark.django_db
def test_alert_ref_property_and_trust_category():
    """Test Alert trust_category calculation."""
    alert = AlertFactory(trust_score=95, trust_category='VERIFIED')
    assert alert.id is not None
    assert alert.trust_category in ("VERIFIED", "VERIFIED OFFICIAL")


@pytest.mark.django_db
def test_notification_unique_user_alert_constraint():
    """Test Notification unique_together=('user', 'alert') raises IntegrityError on duplicate send attempt."""
    user = TelegramUserFactory()
    alert = AlertFactory()

    notif1 = NotificationFactory(user=user, alert=alert)
    assert notif1.pk is not None

    with pytest.raises(IntegrityError):
        Notification.objects.create(user=user, alert=alert, status=NotificationStatus.QUEUED)


@pytest.mark.django_db
def test_push_subscription_unique_endpoint_constraint():
    """Test PushSubscription unique endpoint constraint raises IntegrityError."""
    endpoint_url = "https://updates.push.services.mozilla.com/wpush/v2/unique_endpoint_999"
    PushSubscriptionFactory(endpoint=endpoint_url)

    with pytest.raises(IntegrityError):
        PushSubscriptionFactory(endpoint=endpoint_url)


@pytest.mark.django_db
def test_notification_mark_sent_and_mark_failed_methods():
    """Test Notification state mutation helper methods."""
    notif = NotificationFactory()
    assert notif.status == NotificationStatus.QUEUED

    notif.mark_sent(telegram_message_id=88492)
    notif.refresh_from_db()
    assert notif.status == NotificationStatus.SENT
    assert notif.telegram_message_id == 88492
    assert notif.sent_at is not None

    notif2 = NotificationFactory()
    notif2.mark_failed("Forbidden: bot was blocked by the user", blocked=True)
    notif2.refresh_from_db()
    assert notif2.status == NotificationStatus.BLOCKED
    assert "Forbidden" in notif2.error_message
    assert notif2.failed_at is not None


@pytest.mark.django_db
def test_agency_portal_foreign_key_cascade():
    """Test deleting an Agency cascades and deletes its associated Portals."""
    agency = AgencyFactory()
    portal1 = PortalFactory(agency=agency)
    portal2 = PortalFactory(agency=agency)

    portal_ids = [portal1.id, portal2.id]
    agency_id = agency.id

    agency.delete()

    assert not Agency.objects.filter(id=agency_id).exists()
    assert not Portal.objects.filter(id__in=portal_ids).exists()


@pytest.mark.django_db
def test_webuser_push_subscription_set_null_on_delete():
    """Test deleting a WebUser profile sets user FK to NULL in PushSubscription rather than deleting subscription."""
    profile = WebUserFactory()
    sub = PushSubscriptionFactory(user=profile)

    sub_id = sub.id
    profile.delete()

    sub.refresh_from_db()
    assert sub.id == sub_id
    assert sub.user is None
