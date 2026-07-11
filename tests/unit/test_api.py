import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.agencies.models import Agency
from apps.alerts.models import Alert, AlertStatus, EventType


@pytest.mark.django_db
def test_agency_list_api():
    client = APIClient()
    Agency.objects.create(
        name="Nigeria Customs Service",
        acronym="NCS",
        official_domains=["customs.gov.ng"],
        is_active=True
    )
    url = reverse('api:agency_list')
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['acronym'] == 'NCS'


@pytest.mark.django_db
def test_latest_alerts_api():
    client = APIClient()
    agency = Agency.objects.create(
        name="Nigeria Customs Service",
        acronym="NCS",
        official_domains=["customs.gov.ng"],
        is_active=True
    )
    Alert.objects.create(
        agency=agency,
        title="Customs Recruitment 2025",
        status=AlertStatus.APPROVED,
        event_type=EventType.RECRUITMENT_OPEN
    )
    url = reverse('api:latest_alerts')
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['title'] == 'Customs Recruitment 2025'


from unittest.mock import patch
from django.contrib.auth.models import User

@pytest.mark.django_db
@patch('apps.notifications.sender.send_message')
def test_admin_broadcast_api(mock_send):
    client = APIClient()
    user = User.objects.create_superuser(username='superadmin', password='password', email='admin@example.com')
    client.force_authenticate(user=user)

    from apps.accounts.models import TelegramUser
    TelegramUser.objects.create(telegram_id=123, first_name="Test", state="ACTIVE")

    url = reverse('api:admin_broadcast')
    response = client.post(url, {'text': 'Hello All!'}, format='json')
    assert response.status_code == 200
    assert response.data['status'] == 'broadcast_sent'
    assert response.data['recipients_count'] == 1
    mock_send.assert_called_once_with(chat_id=123, text='Hello All!')


@pytest.mark.django_db
def test_health_api():
    client = APIClient()
    url = reverse('api:health')
    response = client.get(url)
    assert response.status_code == 200
    assert response.data['status'] in ['ok', 'degraded']
    assert 'database' in response.data
    assert 'telegram' in response.data
    assert 'scheduler' in response.data
    assert 'scrapers' in response.data
