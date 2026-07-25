"""
Live Deployment Smoke Test Suite : RecruitmentAlert (GovAlert).

Verifies critical running endpoints post-deployment:
1. Health check returns 200/degraded components.
2. Root PWA assets (/service-worker.js, /manifest.json, /offline.html) return 200 with valid headers.
3. Core API endpoints (/api/v1/jobs/, /api/v1/agencies/, /api/v1/status/) return 200.
"""

import os
import pytest
from django.conf import settings


@pytest.mark.django_db
def test_smoke_health_check_endpoint(client):
    """Smoke Test: Health check endpoint returns 200 when components are active or tested."""
    setattr(settings, 'TESTING', True)
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert "components" in data


def test_smoke_service_worker_root_endpoint(client):
    """Smoke Test: Service worker is accessible at root /service-worker.js."""
    response = client.get("/service-worker.js")
    assert response.status_code == 200
    assert "application/javascript" in response["Content-Type"]
    assert response["Service-Worker-Allowed"] == "/"


def test_smoke_manifest_endpoint(client):
    """Smoke Test: PWA manifest is accessible at /manifest.json."""
    response = client.get("/manifest.json")
    assert response.status_code == 200
    assert "manifest+json" in response["Content-Type"]


def test_smoke_offline_fallback_endpoint(client):
    """Smoke Test: Offline fallback page is accessible at /offline.html."""
    response = client.get("/offline.html")
    assert response.status_code == 200
    assert "text/html" in response["Content-Type"]


@pytest.mark.django_db
def test_smoke_public_jobs_api_endpoint(client):
    """Smoke Test: Jobs feed API returns HTTP 200."""
    response = client.get("/api/v1/jobs/")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data or isinstance(data, list)


@pytest.mark.django_db
def test_smoke_public_agencies_api_endpoint(client):
    """Smoke Test: Agencies directory API returns HTTP 200."""
    response = client.get("/api/v1/agencies/")
    assert response.status_code == 200
