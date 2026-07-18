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
