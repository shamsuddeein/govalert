"""
GovAlert PWA Root Views — Serves service-worker.js, manifest.json, and offline.html at domain root scope.
"""
import os
from django.http import HttpResponse, Http404
from django.conf import settings
from django.views.decorators.http import require_GET

STATICFILES_DIR = os.path.join(settings.BASE_DIR, 'staticfiles')
FRONTEND_PUBLIC_DIR = '/home/deen/govalert-frontend-design/public'


def _read_file_content(filename):
    paths = [
        os.path.join(FRONTEND_PUBLIC_DIR, filename),
        os.path.join(STATICFILES_DIR, filename),
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                return f.read()
    return None


@require_GET
def service_worker_view(request):
    """
    Serves /service-worker.js from root domain scope.
    Must be served with no-cache and Service-Worker-Allowed header set to '/'.
    """
    content = _read_file_content('service-worker.js')
    if not content:
        raise Http404("Service worker file not found.")

    response = HttpResponse(content, content_type='application/javascript; charset=utf-8')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@require_GET
def manifest_view(request):
    """
    Serves /manifest.json from root domain scope.
    """
    content = _read_file_content('manifest.json')
    if not content:
        raise Http404("Manifest file not found.")

    response = HttpResponse(content, content_type='application/manifest+json; charset=utf-8')
    response['Cache-Control'] = 'public, max-age=86400'
    return response


@require_GET
def offline_view(request):
    """
    Serves /offline.html from root domain scope.
    """
    content = _read_file_content('offline.html')
    if not content:
        raise Http404("Offline fallback template not found.")

    response = HttpResponse(content, content_type='text/html; charset=utf-8')
    response['Cache-Control'] = 'public, max-age=3600'
    return response
