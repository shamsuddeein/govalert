"""
GovAlert — Root URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts.forms import EmailAdminAuthenticationForm
from core import pwa_views

admin.site.login_form = EmailAdminAuthenticationForm

# The Django admin is served at a secret URL read from ADMIN_URL env var.
# This removes it from the default /admin/ path that every automated scanner
# probes within hours of a deployment going live.
# In production, set ADMIN_URL to something non-guessable, e.g. a UUID.
# If ADMIN_URL is not set, the admin is effectively unreachable (no URL registered).
_admin_url = getattr(settings, 'ADMIN_URL', '').strip('/')
if not _admin_url:
    import warnings
    warnings.warn(
        "ADMIN_URL is not set. The Django admin interface will not be reachable. "
        "Set ADMIN_URL to a secret path in your environment to enable it.",
        stacklevel=1
    )

urlpatterns = [
    # Telegram Bot Webhook
    path('telegram/', include('apps.bot.urls')),

    # REST API
    path('api/', include('apps.api.urls')),

    # Root Progressive Web App (PWA) Endpoints
    path('service-worker.js', pwa_views.service_worker_view, name='pwa_service_worker'),
    path('manifest.json', pwa_views.manifest_view, name='pwa_manifest'),
    path('offline.html', pwa_views.offline_view, name='pwa_offline'),
]

# Only register the admin URL if ADMIN_URL is configured.
if _admin_url:
    urlpatterns.insert(0, path(f'{_admin_url}/', admin.site.urls))

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

