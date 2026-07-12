"""
GovAlert — Root URL Configuration (Phase 1)
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts.forms import EmailAdminAuthenticationForm

admin.site.login_form = EmailAdminAuthenticationForm

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # Telegram Bot Webhook
    path('telegram/', include('apps.bot.urls')),

    # REST API
    path('api/', include('apps.api.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
