import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.test import Client
from django.utils import timezone
from django.urls import reverse

from apps.agencies.models import Agency, Portal
from apps.monitor.models import Snapshot
from core.middleware import APMMiddleware


@pytest.mark.django_db
def test_health_view_all_healthy():
    client = Client()
    # Create a fresh snapshot within 30 minutes
    agency = Agency.objects.create(name="Test Agency", acronym="TA", is_active=True)
    portal = Portal.objects.create(agency=agency, url="https://example.gov.ng/jobs", is_active=True)
    Snapshot.objects.create(portal=portal, status_code=200, raw_content="<html></html>")

    response = client.get('/api/v1/health/')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    assert data['components']['database']['status'] == 'healthy'
    assert data['components']['redis']['status'] == 'healthy'
    assert data['components']['celery']['status'] == 'healthy'
    assert data['components']['crawler']['status'] == 'healthy'


@pytest.mark.django_db
def test_health_view_db_failure_returns_503():
    client = Client()
    # Mock cursor to raise an exception simulating database failure
    with patch('django.db.connection.cursor') as mock_cursor:
        mock_cursor.side_effect = Exception("Database connection refused")
        response = client.get('/api/v1/health/')
        assert response.status_code == 503
        data = response.json()
        assert data['status'] == 'unhealthy'
        assert data['components']['database']['status'] == 'unhealthy'


@pytest.mark.django_db
def test_health_view_stale_crawler_returns_503():
    client = Client()
    agency = Agency.objects.create(name="Stale Agency", acronym="SA", is_active=True)
    portal = Portal.objects.create(agency=agency, url="https://stale.gov.ng", is_active=True)
    
    # Create a snapshot created 45 minutes ago (>30m threshold)
    snap = Snapshot.objects.create(portal=portal, status_code=200, raw_content="<html></html>")
    snap.created_at = timezone.now() - timedelta(minutes=45)
    snap.save()

    response = client.get('/api/v1/health/')
    assert response.status_code == 503
    data = response.json()
    assert data['status'] == 'unhealthy'
    assert data['components']['crawler']['status'] == 'unhealthy'
    assert data['components']['crawler']['last_run_minutes_ago'] >= 45.0


@pytest.mark.django_db
def test_apm_middleware_execution():
    get_response = MagicMock(return_value=MagicMock(status_code=200))
    middleware = APMMiddleware(get_response)
    
    request = MagicMock()
    request.method = 'GET'
    request.path = '/api/v1/jobs/'

    response = middleware(request)
    assert response.status_code == 200
    get_response.assert_called_once_with(request)


@pytest.mark.django_db
@patch('apps.bot.handlers.commands.handle_start')
def test_bot_dispatcher_logging(mock_start):
    from apps.bot.dispatcher import dispatch_update
    update_data = {
        'update_id': 999,
        'message': {
            'message_id': 1,
            'from': {'id': 123456, 'first_name': 'TestUser'},
            'chat': {'id': 123456},
            'text': '/start'
        }
    }
    dispatch_update(update_data)
    mock_start.assert_called_once()
