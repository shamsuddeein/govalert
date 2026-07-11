import pytest
from apps.accounts.models import TelegramUser, UserState
from apps.agencies.models import Agency
from apps.subscriptions.models import Subscription
from apps.subscriptions.services import (
    auto_subscribe_all,
    unsubscribe_all,
    unsubscribe_from_agency,
    get_active_subscriptions,
    get_agency_subscriber_ids,
)


@pytest.mark.django_db
def test_subscription_services():
    user = TelegramUser.objects.create(
        telegram_id=12345,
        first_name="Test",
        state=UserState.ACTIVE
    )
    agency1 = Agency.objects.create(
        name="Nigeria Customs Service",
        acronym="NCS",
        official_domains=["customs.gov.ng"],
        is_active=True
    )
    agency2 = Agency.objects.create(
        name="Nigeria Police Force",
        acronym="NPF",
        official_domains=["npf.gov.ng"],
        is_active=True
    )
    agency_inactive = Agency.objects.create(
        name="Inactive Agency",
        acronym="IA",
        official_domains=["ia.gov.ng"],
        is_active=False
    )

    # 1. auto_subscribe_all
    auto_subscribe_all(user)
    assert Subscription.objects.filter(user=user, agency=agency1, is_active=True).exists()
    assert Subscription.objects.filter(user=user, agency=agency2, is_active=True).exists()
    assert not Subscription.objects.filter(user=user, agency=agency_inactive).exists()

    # 2. get_active_subscriptions
    active_subs = list(get_active_subscriptions(user))
    assert len(active_subs) == 2

    # 3. get_agency_subscriber_ids
    sub_ids = get_agency_subscriber_ids(agency1)
    assert 12345 in sub_ids

    # 4. unsubscribe_from_agency
    assert unsubscribe_from_agency(user, agency1) is True
    assert Subscription.objects.filter(user=user, agency=agency1, is_active=False).exists()

    # 5. unsubscribe_all
    unsubscribe_all(user)
    assert not Subscription.objects.filter(user=user, is_active=True).exists()
    user.refresh_from_db()
    assert user.receive_alerts is False
