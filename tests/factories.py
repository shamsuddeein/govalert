"""
Factory Boy Model Factories for RecruitmentAlert (GovAlert).
Provides sensible default fixtures for all core domain models.
"""
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from django.utils import timezone

from apps.accounts.models import TelegramUser, WebUser, UserState
from apps.agencies.models import Agency, Portal, PortalStatus, AgencyCategory
from apps.alerts.models import Alert, AlertStatus, RecruitmentEvent
from apps.notifications.models import Notification, NotificationStatus, PushSubscription
from apps.subscriptions.models import KeywordSubscription, TelegramJobWatch


class TelegramUserFactory(DjangoModelFactory):
    class Meta:
        model = TelegramUser
        django_get_or_create = ('telegram_id',)

    telegram_id = factory.Sequence(lambda n: 1000000 + n)
    username = factory.Sequence(lambda n: f"user_{n}")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    state = UserState.ACTIVE
    receive_alerts = True
    consented_to_data_policy = True


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False


class StaffUserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Sequence(lambda n: f"staff_{n}")
    email = factory.Sequence(lambda n: f"staff{n}@example.com")
    first_name = "Staff"
    last_name = "Admin"
    is_active = True
    is_staff = True
    is_superuser = False


class WebUserFactory(DjangoModelFactory):
    class Meta:
        model = WebUser

    user = factory.SubFactory(UserFactory)
    phone = "+2348012345678"
    categories_of_interest = ["SECURITY", "FINANCE"]


class AgencyFactory(DjangoModelFactory):
    class Meta:
        model = Agency
        django_get_or_create = ('acronym',)

    name = factory.Sequence(lambda n: f"Nigerian Federal Agency {n}")
    acronym = factory.Sequence(lambda n: f"NFA{n}")
    slug = factory.Sequence(lambda n: f"nfa-{n}")
    category = AgencyCategory.SECURITY
    description = "Federal government recruitment monitoring agency."
    official_domains = ["agency.gov.ng"]
    is_active = True
    vetted_score = 95


class PortalFactory(DjangoModelFactory):
    class Meta:
        model = Portal

    agency = factory.SubFactory(AgencyFactory)
    url = factory.Sequence(lambda n: f"https://portal{n}.agency.gov.ng/careers")
    status = PortalStatus.ONLINE
    health_status = 'ONLINE'
    is_active = True
    check_interval_minutes = 15
    last_checked_at = factory.LazyFunction(timezone.now)


class RecruitmentEventFactory(DjangoModelFactory):
    class Meta:
        model = RecruitmentEvent

    agency = factory.SubFactory(AgencyFactory)
    event_type = 'new_opening'
    title = factory.Sequence(lambda n: f"Federal Recruitment Campaign {n}")


class AlertFactory(DjangoModelFactory):
    class Meta:
        model = Alert

    agency = factory.SubFactory(AgencyFactory)
    title = factory.Sequence(lambda n: f"Officer Recruitment Position {n}")
    content_excerpt = "Official civil service recruitment position requirements and qualifications."
    source_url = factory.Sequence(lambda n: f"https://portal{n}.agency.gov.ng/apply")
    status = AlertStatus.APPROVED
    trust_score = 92
    ai_classification = 'REAL'


class NotificationFactory(DjangoModelFactory):
    class Meta:
        model = Notification

    user = factory.SubFactory(TelegramUserFactory)
    alert = factory.SubFactory(AlertFactory)
    status = NotificationStatus.QUEUED


class PushSubscriptionFactory(DjangoModelFactory):
    class Meta:
        model = PushSubscription

    endpoint = factory.Sequence(lambda n: f"https://updates.push.services.mozilla.com/wpush/v2/sub_{n}")
    p256dh = "test_p256dh_key_base64"
    auth = "test_auth_key_base64"
    is_active = True


class KeywordSubscriptionFactory(DjangoModelFactory):
    class Meta:
        model = KeywordSubscription

    email = factory.Sequence(lambda n: f"subscriber{n}@example.com")
    query_text = "Customs"
    is_active = True
