"""
PWA & Web Push API Automated Unit & Integration Tests.

Verifies:
1. Root service-worker.js headers (Content-Type, Service-Worker-Allowed: /, Cache-Control: no-cache).
2. Root manifest.json schema and offline.html fallback template serving.
3. Web Push API endpoints (/api/v1/push/vapid-key/, /api/v1/push/subscribe/, /api/v1/push/unsubscribe/).
4. Automatic deletion of 404/410 expired PushSubscriptions in send_single_push().
"""
import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from apps.notifications.models import PushSubscription
from apps.notifications.push_service import (
    get_vapid_public_key,
    get_vapid_private_key,
    send_single_push,
    broadcast_push_notification,
)
from pywebpush import WebPushException


def test_service_worker_root_endpoint_and_headers(client):
    """Verify /service-worker.js is served at root with mandatory PWA headers."""
    response = client.get('/service-worker.js')
    assert response.status_code == 200
    assert 'application/javascript' in response['Content-Type']
    assert response['Service-Worker-Allowed'] == '/'
    assert 'no-cache' in response['Cache-Control']


def test_manifest_root_endpoint(client):
    """Verify /manifest.json is served with application/manifest+json content type."""
    response = client.get('/manifest.json')
    assert response.status_code == 200
    assert 'manifest+json' in response['Content-Type']
    assert 'RecruitmentAlert' in response.content.decode('utf-8')


def test_offline_fallback_endpoint(client):
    """Verify /offline.html is served as standalone html."""
    response = client.get('/offline.html')
    assert response.status_code == 200
    assert 'text/html' in response['Content-Type']
    assert 'You are currently offline' in response.content.decode('utf-8')


def test_vapid_public_key_endpoint(client):
    """Verify GET /api/v1/push/vapid-key/ returns VAPID public key."""
    url = reverse('api:push_vapid_key')
    response = client.get(url)
    assert response.status_code == 200
    assert 'public_key' in response.json()
    assert response.json()['public_key'] == get_vapid_public_key()


@pytest.mark.django_db
def test_push_subscribe_and_unsubscribe_endpoints(client):
    """Verify POST /api/v1/push/subscribe/ creates sub and /push/unsubscribe/ removes it."""
    subscribe_url = reverse('api:push_subscribe')
    payload = {
        'endpoint': 'https://updates.push.services.mozilla.com/wpush/v2/test_endpoint_123',
        'keys': {
            'p256dh': 'BNcRdreALRFXTkOOUHK1EtKX_W57F',
            'auth': 'tBHItIgWS6p39'
        }
    }
    response = client.post(subscribe_url, payload, content_type='application/json')
    assert response.status_code in (200, 201)
    assert PushSubscription.objects.filter(endpoint=payload['endpoint']).exists()

    # Test unsubscribe
    unsubscribe_url = reverse('api:push_unsubscribe')
    unsub_response = client.post(unsubscribe_url, {'endpoint': payload['endpoint']}, content_type='application/json')
    assert unsub_response.status_code == 200
    assert not PushSubscription.objects.filter(endpoint=payload['endpoint']).exists()


@pytest.mark.django_db
@patch('apps.notifications.push_service.webpush')
def test_send_single_push_success(mock_webpush):
    """Verify successful web push dispatch."""
    mock_webpush.return_value = MagicMock(status_code=201)
    sub = PushSubscription.objects.create(
        endpoint='https://fcm.googleapis.com/fcm/send/test_sub_456',
        p256dh='test_p256dh',
        auth='test_auth'
    )
    result = send_single_push(sub, title="NNPC Opening", body="Verified recruitment alert", url="/jobs/123")
    assert result is True
    assert PushSubscription.objects.filter(pk=sub.pk).exists()


@pytest.mark.django_db
@patch('apps.notifications.push_service.webpush')
def test_send_single_push_deletes_expired_410_subscription(mock_webpush):
    """Verify HTTP 410 Gone automatically deletes invalid subscription from DB."""
    mock_response = MagicMock(status_code=410)
    mock_webpush.side_effect = WebPushException("410 Gone", response=mock_response)

    sub = PushSubscription.objects.create(
        endpoint='https://fcm.googleapis.com/fcm/send/expired_sub_789',
        p256dh='expired_p256dh',
        auth='expired_auth'
    )

    result = send_single_push(sub, title="Customs Update", body="Recruitment update", url="/jobs/456")
    assert result is False
    # Subscription MUST be purged from database
    assert not PushSubscription.objects.filter(pk=sub.pk).exists()
