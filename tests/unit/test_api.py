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
