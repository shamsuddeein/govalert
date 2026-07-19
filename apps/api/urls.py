"""
GovAlert API — URL configuration.

Public v1 routes (no auth required):
  GET  /api/v1/agencies/
  GET  /api/v1/agencies/{slug}/
  GET  /api/v1/jobs/
  GET  /api/v1/jobs/{ref}/
  GET  /api/v1/jobs/{ref}/verification/
  GET  /api/v1/status/
  GET  /api/v1/status/live-feed/
  GET  /api/v1/health/

Auth routes:
  POST /api/auth/token/
  POST /api/auth/token/refresh/

Admin routes (IsAdminUser required):
  GET  /api/v1/admin/portals/
  GET  /api/v1/admin/portals/{pk}/
  POST /api/v1/admin/alerts/{pk}/verify/
  POST /api/v1/admin/alerts/{pk}/reject/
  POST /api/v1/admin/broadcast/
  GET  /api/v1/admin/stats/
"""
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'api'

# ── Auth ───────────────────────────────────────────────────────────────────────
auth_patterns = [
    path('token/', views.EmailTokenObtainPairView.as_view(), name='token_obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('me/', views.MeView.as_view(), name='me'),
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
]

# ── Public v1 ─────────────────────────────────────────────────────────────────
public_patterns = [
    # Agencies
    path('agencies/', views.AgencyListView.as_view(), name='agency_list'),
    path('agencies/<slug:slug>/', views.AgencyDetailView.as_view(), name='agency_detail'),

    # Jobs (Alerts)
    path('jobs/', views.JobListView.as_view(), name='job_list'),
    path('jobs/<str:ref>/', views.JobDetailView.as_view(), name='job_detail'),
    path('jobs/<str:ref>/verification/', views.JobVerificationView.as_view(), name='job_verification'),

    # Saved Jobs (Me)
    path('me/saved-jobs/', views.SavedJobsView.as_view(), name='saved_jobs'),
    path('me/saved-jobs/<str:ref>/', views.SavedJobDetailView.as_view(), name='saved_job_detail'),

    # System Status
    path('status/', views.SystemStatusView.as_view(), name='system_status'),
    path('status/live-feed/', views.LiveFeedView.as_view(), name='live_feed'),

    # Health
    path('health/', views.HealthView.as_view(), name='health'),
]

# ── Admin v1 ──────────────────────────────────────────────────────────────────
admin_patterns = [
    # Auth
    path('auth/login/', views.CustomAdminLoginView.as_view(), name='admin_auth_login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='admin_auth_refresh'),
    path('auth/me/', views.CustomAdminMeView.as_view(), name='admin_auth_me'),

    # Alert Review Queue
    path('alerts/', views.CustomAdminAlertListView.as_view(), name='admin_alert_list'),
    path('alerts/stats/', views.CustomAdminAlertStatsView.as_view(), name='admin_alert_stats'),
    path('alerts/<int:pk>/approve/', views.CustomAdminAlertApproveView.as_view(), name='admin_alert_approve'),
    path('alerts/<int:pk>/reject/', views.CustomAdminAlertRejectView.as_view(), name='admin_alert_reject'),
    path('alerts/<int:pk>/hold/', views.CustomAdminAlertHoldView.as_view(), name='admin_alert_hold'),
    path('alerts/<int:pk>/', views.CustomAdminAlertUpdateView.as_view(), name='admin_alert_update'),

    # Agency Management
    path('agencies/', views.CustomAdminAgencyListCreateView.as_view(), name='admin_agency_list_create'),
    path('agencies/<int:pk>/', views.CustomAdminAgencyDetailView.as_view(), name='admin_agency_detail'),

    # Portal Management
    path('portals/', views.CustomAdminPortalListCreateView.as_view(), name='admin_portal_list_create'),
    path('portals/<int:pk>/', views.CustomAdminPortalDetailView.as_view(), name='admin_portal_detail'),
    path('portals/<int:pk>/trigger-check/', views.CustomAdminPortalTriggerCheckView.as_view(), name='admin_portal_trigger_check'),
    path('portals/<int:pk>/history/', views.CustomAdminPortalHistoryView.as_view(), name='admin_portal_history'),

    # System Health & Broadcast
    path('system-health/', views.CustomAdminSystemHealthView.as_view(), name='admin_system_health'),
    path('broadcast/', views.AdminBroadcastView.as_view(), name='admin_broadcast'),
    path('stats/', views.AdminStatsView.as_view(), name='admin_stats'),
]

urlpatterns = [
    path('auth/', include(auth_patterns)),
    path('v1/', include(public_patterns)),
    path('v1/admin/', include(admin_patterns)),
]
