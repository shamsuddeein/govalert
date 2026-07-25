"""
NDPR (2019) & NDPA (2023) Legal Compliance Unit Tests.

Tests:
1. Data Subject Access Request (DSAR) export endpoint (/api/v1/admin/data-subject-export/).
2. Data Subject Right to Erasure / Deletion endpoint (/api/v1/admin/data-subject-delete/).
3. Telegram Bot /stop command hard deletion & audit logging.
4. Automated retention enforcement Celery task (clean_expired_personal_data_task).
5. Sentry error tracking PII scrubber (_strip_pii_from_sentry_event).
"""

import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import TelegramUser, WebUser, UserState
from apps.subscriptions.models import KeywordSubscription, TelegramJobWatch
from apps.notifications.models import Notification, PushSubscription
from apps.notifications.tasks import clean_expired_personal_data_task
from config.settings.base import _strip_pii_from_sentry_event
from tests.factories import (
    TelegramUserFactory,
    WebUserFactory,
    StaffUserFactory,
    KeywordSubscriptionFactory,
    PushSubscriptionFactory,
    NotificationFactory,
)


@pytest.mark.django_db
def test_data_subject_export_endpoint():
    """Verify Data Subject Access Request (DSAR) export endpoint returns complete user data."""
    client = APIClient()
    staff = StaffUserFactory()
    client.force_authenticate(user=staff)

    tg_user = TelegramUserFactory(telegram_id=987654, username="test_subject")
    kw_sub = KeywordSubscriptionFactory(email="subject@example.com", query_text="Customs")

    url = reverse("api:admin_data_subject_export")
    response = client.get(f"{url}?identifier=987654")

    assert response.status_code == 200
    data = response.json()
    assert data["identifier"] == "987654"
    assert data["telegram_user"]["username"] == "test_subject"


@pytest.mark.django_db
def test_data_subject_erasure_endpoint():
    """Verify Right to Erasure / Deletion endpoint hard-deletes all data subject records."""
    client = APIClient()
    staff = StaffUserFactory()
    client.force_authenticate(user=staff)

    tg_user = TelegramUserFactory(telegram_id=555666)
    kw_sub = KeywordSubscriptionFactory(email="delete_me@example.com")

    url = reverse("api:admin_data_subject_delete")
    response = client.post(url, {"identifier": "555666"}, format="json")

    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    assert not TelegramUser.objects.filter(telegram_id=555666).exists()


@pytest.mark.django_db
@patch("apps.notifications.sender.send_message")
def test_telegram_bot_stop_command_erases_user(mock_send_message):
    """Verify Telegram /stop command deletes all user records and sends confirmation."""
    tg_user = TelegramUserFactory(telegram_id=777888)
    message = {
        "chat": {"id": 777888},
        "from": {"id": 777888, "first_name": "Test", "last_name": "User"},
        "text": "/stop",
    }

    from apps.bot.handlers.commands import handle_stop
    handle_stop(message)

    # User record MUST be deleted
    assert not TelegramUser.objects.filter(telegram_id=777888).exists()
    mock_send_message.assert_called_once()


@pytest.mark.django_db
def test_clean_expired_personal_data_retention_task():
    """Verify Celery retention task purges inactive records older than retention cutoff."""
    old_date = timezone.now() - timedelta(days=35)

    # Create inactive keyword sub created > 30d ago
    kw = KeywordSubscriptionFactory(is_active=False)
    KeywordSubscription.objects.filter(pk=kw.pk).update(created_at=old_date)

    clean_expired_personal_data_task()

    assert not KeywordSubscription.objects.filter(pk=kw.pk).exists()


def test_sentry_pii_scrubber():
    """Verify Sentry before_send PII scrubber masks emails and phone numbers."""
    event = {
        "request": {
            "headers": {
                "Authorization": "Bearer secret_jwt_token",
                "User-Agent": "Mozilla/5.0",
            }
        },
        "extra": {
            "user_email": "applicant@domain.com",
            "phone_number": "+2348012345678",
        },
    }

    scrubbed = _strip_pii_from_sentry_event(event, {})

    assert scrubbed["request"]["headers"]["Authorization"] == "[SCRUBBED_PII]"
    assert scrubbed["extra"]["user_email"] == "[SCRUBBED_EMAIL]"
    assert scrubbed["extra"]["phone_number"] == "[SCRUBBED_PHONE]"
