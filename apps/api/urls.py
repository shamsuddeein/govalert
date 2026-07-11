"""
API app URLs — public and authenticated REST endpoints.
"""
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

app_name = 'api'

# ── Auth ──────────────────────────────────────────────────────────────────────
auth_patterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# ── Public ────────────────────────────────────────────────────────────────────
public_patterns = [
    path('agencies/', views.AgencyListView.as_view(), name='agency_list'),
    path('agencies/<int:pk>/', views.AgencyDetailView.as_view(), name='agency_detail'),
    path('alerts/latest/', views.LatestAlertsView.as_view(), name='latest_alerts'),
    path('portals/status/', views.PortalStatusView.as_view(), name='portal_status'),
]

# ── Admin ─────────────────────────────────────────────────────────────────────
admin_patterns = [
    path('portals/', views.AdminPortalListView.as_view(), name='admin_portal_list'),
    path('portals/<int:pk>/', views.AdminPortalDetailView.as_view(), name='admin_portal_detail'),
    path('alerts/<int:pk>/verify/', views.AdminVerifyAlertView.as_view(), name='admin_verify_alert'),
    path('alerts/<int:pk>/reject/', views.AdminRejectAlertView.as_view(), name='admin_reject_alert'),
    path('broadcast/', views.AdminBroadcastView.as_view(), name='admin_broadcast'),
    path('stats/', views.AdminStatsView.as_view(), name='admin_stats'),
]

urlpatterns = [
    path('auth/', include(auth_patterns)),
    path('v1/', include(public_patterns)),
    path('v1/admin/', include(admin_patterns)),
]
