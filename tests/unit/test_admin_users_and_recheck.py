import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.accounts.models import WebUser, TelegramUser, UserState
from apps.subscriptions.models import KeywordSubscription
from apps.agencies.models import Agency, Portal

User = get_user_model()


@pytest.fixture
def admin_client():
    admin = User.objects.create_superuser(
        username="adminuser",
        email="admin@govalert.com.ng",
        password="adminpassword123"
    )
    client = APIClient()
    client.force_authenticate(user=admin)
    return client


@pytest.mark.django_db
def test_admin_user_list_api(admin_client):
    # 1. Create WebUser
    u1 = User.objects.create_user(username="webuser1", email="web1@example.com", password="pass")
    WebUser.objects.create(user=u1)

    # 2. Create TelegramUser
    TelegramUser.objects.create(
        telegram_id=987654321,
        username="tguser1",
        first_name="Telegram",
        last_name="User",
        state=UserState.ACTIVE
    )

    # 3. Create KeywordSubscription
    KeywordSubscription.objects.create(email="kw1@example.com", query_text="Customs")

    url = reverse('api:admin_user_list')
    response = admin_client.get(url)
    assert response.status_code == 200

    data = response.data.get('results', response.data)
    assert len(data) == 3

    # Check search filter
    response_search = admin_client.get(f"{url}?search=web1")
    assert response_search.status_code == 200
    search_results = response_search.data.get('results', response_search.data)
    assert len(search_results) == 1
    assert search_results[0]['email'] == 'web1@example.com'


@pytest.mark.django_db
def test_admin_user_stats_api(admin_client):
    u1 = User.objects.create_user(username="webuser1", email="web1@example.com", password="pass")
    WebUser.objects.create(user=u1)

    TelegramUser.objects.create(telegram_id=111222, username="tg1", state=UserState.ACTIVE)
    KeywordSubscription.objects.create(email="kw@example.com", query_text="Police")

    url = reverse('api:admin_user_stats')
    response = admin_client.get(url)
    assert response.status_code == 200

    data = response.data
    assert data['total_web_users'] >= 1
    assert data['total_telegram_subscribers'] == 1
    assert data['active_telegram_subscribers'] == 1
    assert data['total_keyword_subscribers'] == 1


@pytest.mark.django_db
def test_admin_user_toggle_active_api(admin_client):
    u1 = User.objects.create_user(username="webuser2", email="web2@example.com", password="pass", is_active=True)
    web_u = WebUser.objects.create(user=u1)

    url = reverse('api:admin_user_toggle_active', kwargs={'user_type': 'web', 'pk': web_u.pk})
    response = admin_client.patch(url)
    assert response.status_code == 200
    assert response.data['is_active'] is False

    u1.refresh_from_db()
    assert u1.is_active is False


@pytest.mark.django_db
def test_admin_portal_trigger_check_all_api(admin_client, monkeypatch):
    agency = Agency.objects.create(name="Test Agency", acronym="TA", is_active=True)
    p1 = Portal.objects.create(agency=agency, name="P1", url="https://p1.gov.ng", is_active=True)
    p2 = Portal.objects.create(agency=agency, name="P2", url="https://p2.gov.ng", is_active=True)

    triggered_ids = []

    def mock_portal_check(portal_id):
        triggered_ids.append(portal_id)

    import apps.api.views
    monkeypatch.setattr("apps.monitor.tasks.portal_check", mock_portal_check)

    url = reverse('api:admin_portal_trigger_check_all')
    response = admin_client.post(url)
    assert response.status_code == 200
    assert response.data['triggered_count'] == 2
    assert p1.id in triggered_ids
    assert p2.id in triggered_ids
