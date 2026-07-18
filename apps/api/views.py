"""
GovAlert API v1 — Public endpoints for agencies, jobs, and system status.

Endpoint map:
  GET /api/v1/agencies/             → AgencyListView
  GET /api/v1/agencies/{slug}/      → AgencyDetailView
  GET /api/v1/jobs/                 → JobListView
  GET /api/v1/jobs/{ref}/           → JobDetailView
  GET /api/v1/status/               → SystemStatusView   (cached 60s)
  GET /api/v1/status/live-feed/     → LiveFeedView
  GET /api/v1/health/               → HealthView
  POST /api/auth/token/             → EmailTokenObtainPairView
  POST /api/auth/token/refresh/     → TokenRefreshView
  GET /api/v1/admin/stats/          → AdminStatsView     (admin only)
  POST /api/v1/admin/alerts/{pk}/verify/  → AdminVerifyAlertView
  POST /api/v1/admin/alerts/{pk}/reject/  → AdminRejectAlertView
  POST /api/v1/admin/broadcast/           → AdminBroadcastView
"""
import logging
from django.utils import timezone
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework import status as http_status

from core.permissions import IsAdminUser, IsSuperAdmin
from apps.api.serializers import (
    AgencyListSerializer, AgencyDetailSerializer,
    JobListSerializer, JobDetailSerializer,
    LiveFeedItemSerializer,
)

logger = logging.getLogger(__name__)

SYSTEM_STATUS_CACHE_KEY = 'api_system_status_v1'
SYSTEM_STATUS_CACHE_TTL = 60  # seconds


# ─── Pagination ────────────────────────────────────────────────────────────────

class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _time_ago(dt) -> str:
    """Return a human-readable 'N ago' string for a datetime."""
    if not dt:
        return 'unknown'
    delta = timezone.now() - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{delta.days}d ago"


def _pk_from_ref(ref: str) -> int | None:
    """Extract the alert pk from a ref string like '0042-GA'."""
    try:
        return int(ref.split('-')[0])
    except (ValueError, IndexError, AttributeError):
        return None


# ─── Agency Endpoints ──────────────────────────────────────────────────────────

class AgencyListView(APIView):
    """
    GET /api/v1/agencies/
    Returns paginated list of all active agencies with portal health data.
    Sorted: online first, then maintenance, then offline.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        from apps.agencies.models import Agency, Portal
        from django.db.models import Prefetch

        agencies = list(Agency.objects.filter(is_active=True).prefetch_related(
            Prefetch('portals', queryset=Portal.objects.filter(is_active=True).order_by('priority'))
        ))

        def get_status_rank(agency):
            portals = list(agency.portals.all())
            if not portals:
                return 2
            portal = portals[0]
            status_map = {
                'ONLINE': 0, 'UP': 0,
                'MAINTENANCE': 1, 'BLOCKED': 1, 'CAPTCHA': 1, 'RATE_LIMITED': 1,
            }
            val = status_map.get(portal.status, 2)
            if val == 2:
                val = status_map.get(portal.health_status, 2)
            return val

        agencies.sort(key=get_status_rank)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(agencies, request)
        serializer = AgencyListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AgencyDetailView(APIView):
    """
    GET /api/v1/agencies/{slug}/
    Returns full agency detail including monitoring history, uptime, and health.
    """
    permission_classes = [AllowAny]

    def get(self, request, slug):
        from apps.agencies.models import Agency
        from django.db.models import Q
        try:
            agency = Agency.objects.filter(
                Q(slug__iexact=slug) | Q(acronym__iexact=slug),
                is_active=True
            ).first()
            if not agency:
                return Response({'detail': 'Agency not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response({'detail': 'Agency lookup error.'}, status=http_status.HTTP_400_BAD_REQUEST)
        serializer = AgencyDetailSerializer(agency)
        return Response(serializer.data)


# ─── Job (Alert) Endpoints ─────────────────────────────────────────────────────

class JobListView(APIView):
    """
    GET /api/v1/jobs/
    Paginated, filterable job listing from approved Alert records.

    Query params:
      ?agency={acronym}
      ?status={verified|urgent|updating|closed|new_opening}
      ?category={category}
      ?location={state}
      ?search={text}
      ?ordering=detected (default) | deadline | published_at
    """
    permission_classes = [AllowAny]

    def get(self, request):
        from apps.alerts.models import Alert, AlertStatus
        from django.db.models import Q

        qs = Alert.objects.filter(
            status__in=[AlertStatus.APPROVED, AlertStatus.PENDING]
        ).select_related('agency', 'portal').order_by('-created_at')

        # ── Filters ────────────────────────────────────────────────────────────
        agency_param = request.query_params.get('agency')
        if agency_param:
            qs = qs.filter(agency__acronym__iexact=agency_param)

        agency_slug_param = request.query_params.get('agency_slug')
        if agency_slug_param:
            qs = qs.filter(agency__slug__iexact=agency_slug_param)

        category_param = request.query_params.get('category')
        if category_param:
            rev_mapping = {
                'security': 'SECURITY',
                'finance': 'FINANCE',
                'utilities': 'UTILITIES',
                'health': 'HEALTH',
                'education': 'EDUCATION',
                'transport': 'TRANSPORT',
                'statistics': 'STATISTICS',
                'judiciary': 'JUDICIARY',
                'other': 'OTHER',
            }
            db_cat = rev_mapping.get(category_param.lower(), category_param)
            qs = qs.filter(agency__category__iexact=db_cat)

        location_param = request.query_params.get('location')
        if location_param:
            qs = qs.filter(portal__location_state__iexact=location_param)

        status_param = request.query_params.get('status')
        if status_param:
            # Map frontend status vocab back to DB filter
            if status_param == 'verified':
                qs = qs.filter(status=AlertStatus.APPROVED, trust_score__gte=70)
            elif status_param == 'new_opening':
                qs = qs.filter(status=AlertStatus.APPROVED, trust_score__lt=70)
            elif status_param == 'updating':
                qs = qs.filter(status=AlertStatus.PENDING)
            elif status_param == 'closed':
                qs = qs.filter(status=AlertStatus.REJECTED)

        search_param = request.query_params.get('search')
        if search_param:
            qs = qs.filter(
                Q(title__icontains=search_param) |
                Q(agency__name__icontains=search_param) |
                Q(agency__acronym__icontains=search_param)
            )

        # ── Ordering ───────────────────────────────────────────────────────────
        ordering = request.query_params.get('ordering', 'detected')
        if ordering == 'deadline':
            qs = qs.order_by('deadline')
        elif ordering == 'published_at':
            qs = qs.order_by('-created_at')
        else:
            qs = qs.order_by('-created_at')

        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = JobListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class JobDetailView(APIView):
    """
    GET /api/v1/jobs/{ref}/
    Returns full job detail using a ref like '0042-GA'.
    """
    permission_classes = [AllowAny]

    def get(self, request, ref):
        from apps.alerts.models import Alert

        pk = _pk_from_ref(ref)
        if pk is None:
            return Response({'detail': 'Invalid job reference.'}, status=http_status.HTTP_400_BAD_REQUEST)

        try:
            alert = Alert.objects.select_related('agency', 'portal', 'recruitment_event').get(pk=pk)
        except Alert.DoesNotExist:
            return Response({'detail': 'Job not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        serializer = JobDetailSerializer(alert)
        return Response(serializer.data)


class JobVerificationView(APIView):
    """
    GET /api/v1/jobs/{ref}/verification/
    Returns the full verification report for a job: AI classification,
    confidence score, red flags, confidence factors, and detection timeline.
    """
    permission_classes = [AllowAny]

    def get(self, request, ref):
        from apps.alerts.models import Alert

        pk = _pk_from_ref(ref)
        if pk is None:
            return Response({'detail': 'Invalid job reference.'}, status=http_status.HTTP_400_BAD_REQUEST)

        try:
            alert = Alert.objects.select_related('agency', 'portal').get(pk=pk)
        except Alert.DoesNotExist:
            return Response({'detail': 'Job not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        # Confidence factors
        confidence_factors = [
            {'label': 'Official government domain', 'passed': alert.trust_score >= 60},
            {'label': 'AI classification passed', 'passed': alert.ai_classification == 'REAL'},
            {'label': 'No fraud keywords detected', 'passed': not alert.ai_red_flags},
            {'label': 'Portal currently accessible', 'passed': bool(alert.portal and alert.portal.status == 'ONLINE')},
            {'label': 'Recruitment keywords matched', 'passed': alert.trust_score >= 50},
        ]

        # Detection timeline
        timeline = [
            {'time': alert.created_at.strftime('%H:%M'), 'event': 'Recruitment detected by monitoring engine'},
        ]
        if alert.portal and alert.portal.last_checked_at:
            timeline.append({
                'time': alert.portal.last_checked_at.strftime('%H:%M'),
                'event': 'Portal last checked',
            })
        if alert.is_verified and hasattr(alert, 'verified_at') and alert.verified_at:
            timeline.append({
                'time': alert.verified_at.strftime('%H:%M'),
                'event': 'Manually verified by admin',
            })

        data = {
            'ref': f"{alert.pk:04d}-GA",
            'title': alert.title,
            'agency_name': alert.agency.name if alert.agency else '',
            'agency_acronym': alert.agency.acronym if alert.agency else '',
            'confidence_score': alert.trust_score,
            'ai_classification': alert.ai_classification or 'UNCERTAIN',
            'ai_confidence': alert.ai_confidence or 0,
            'ai_red_flags': alert.ai_red_flags or [],
            'confidence_factors': confidence_factors,
            'detection_timeline': timeline,
            'source_url': alert.source_url or '',
            'last_monitored': alert.portal.last_checked_at.isoformat() if alert.portal and alert.portal.last_checked_at else None,
            'is_verified': getattr(alert, 'is_verified', False),
        }

        return Response(data)


# ─── System Status Endpoints ───────────────────────────────────────────────────

class SystemStatusView(APIView):
    """
    GET /api/v1/status/
    Returns aggregated system metrics. Response cached 60 seconds.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        cached = cache.get(SYSTEM_STATUS_CACHE_KEY)
        if cached is not None:
            return Response(cached)

        from apps.agencies.models import Agency, Portal, PortalStatus
        from apps.alerts.models import Alert, AlertStatus
        from apps.monitor.models import Snapshot

        today = timezone.now().date()

        total_agencies = Agency.objects.filter(is_active=True).count()
        agencies_online = Portal.objects.filter(
            is_active=True, status__in=['ONLINE', 'UP']
        ).values('agency').distinct().count()
        agencies_offline = Portal.objects.filter(
            is_active=True, status__in=['OFFLINE', 'DOWN']
        ).values('agency').distinct().count()
        agencies_maintenance = Portal.objects.filter(
            is_active=True, status__in=['MAINTENANCE', 'BLOCKED', 'RATE_LIMITED', 'CAPTCHA']
        ).values('agency').distinct().count()

        total_checks_today = Snapshot.objects.filter(created_at__date=today).count()
        successful_checks_today = Snapshot.objects.filter(
            created_at__date=today, status_code__lt=400
        ).count()
        failed_checks_today = total_checks_today - successful_checks_today
        success_rate_today = round(
            (successful_checks_today / total_checks_today * 100) if total_checks_today > 0 else 100.0, 2
        )
        changes_detected_today = Snapshot.objects.filter(
            created_at__date=today, has_change=True
        ).count()
        active_campaigns = Alert.objects.filter(status=AlertStatus.APPROVED).count()

        last_snapshot = Snapshot.objects.order_by('-created_at').first()
        last_audit_at = last_snapshot.created_at.isoformat() if last_snapshot else None

        system_operational = (
            agencies_offline == 0 or
            (agencies_offline / max(total_agencies, 1)) < 0.5
        )

        data = {
            'agencies_online': agencies_online,
            'agencies_offline': agencies_offline,
            'agencies_maintenance': agencies_maintenance,
            'total_agencies': total_agencies,
            'total_checks_today': total_checks_today,
            'successful_checks_today': successful_checks_today,
            'failed_checks_today': failed_checks_today,
            'success_rate_today': success_rate_today,
            'changes_detected_today': changes_detected_today,
            'active_campaigns': active_campaigns,
            'monitoring_interval_minutes': 15,
            'last_audit_at': last_audit_at,
            'system_operational': system_operational,
        }

        cache.set(SYSTEM_STATUS_CACHE_KEY, data, SYSTEM_STATUS_CACHE_TTL)
        return Response(data)


class LiveFeedView(APIView):
    """
    GET /api/v1/status/live-feed/
    Returns the 10 most recent monitoring events with human-readable time_ago.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        from apps.monitor.models import Snapshot

        snapshots = Snapshot.objects.select_related(
            'portal__agency'
        ).order_by('-created_at')[:10]

        feed = []
        for snap in snapshots:
            agency = snap.portal.agency if snap.portal else None
            if not agency:
                continue

            if snap.triggered_alert:
                event_type = 'new_opening'
            elif snap.has_change:
                event_type = 'verified'
            elif snap.status_code and snap.status_code >= 400:
                event_type = 'urgent'
            else:
                event_type = 'no_changes'

            feed.append({
                'agency_name': agency.name,
                'agency_acronym': agency.acronym,
                'event_type': event_type,
                'event_time': snap.created_at.isoformat(),
                'time_ago': _time_ago(snap.created_at),
            })

        return Response(feed)


# ─── Health Endpoint ───────────────────────────────────────────────────────────

class HealthView(APIView):
    """Simple health endpoint for uptime checks and load balancer pings."""
    permission_classes = [AllowAny]

    def get(self, request):
        from django.db import connection
        from django.conf import settings
        from apps.monitor.models import Snapshot
        from apps.alerts.models import Alert, DecisionLog
        from apps.notifications.models import Notification, NotificationStatus
        from django.db.models import Avg

        data = {'status': 'ok'}

        try:
            with connection.cursor() as cur:
                cur.execute('SELECT 1')
            data['database'] = 'connected'
        except Exception:
            data['database'] = 'unavailable'
            data['status'] = 'degraded'

        bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        data['telegram'] = 'configured' if bot_token else 'not_configured'
        if not bot_token:
            data['status'] = 'degraded'

        try:
            from config.scheduler import get_scheduler
            sched = get_scheduler()
            data['scheduler'] = 'running' if getattr(sched, 'running', False) else 'stopped'
        except Exception:
            data['scheduler'] = 'unknown'

        try:
            from apps.agencies.models import Portal
            data['active_scrapers'] = Portal.objects.filter(is_active=True).count()
        except Exception:
            data['active_scrapers'] = 0

        try:
            today = timezone.now().date()
            data['metrics'] = {
                'total_scrapes': Snapshot.objects.count(),
                'successful_scrapes': Snapshot.objects.filter(status_code__lt=400).count(),
                'alerts_today': Alert.objects.filter(created_at__date=today).count(),
                'notifications_sent_today': Notification.objects.filter(
                    status=NotificationStatus.SENT, sent_at__date=today
                ).count(),
                'avg_response_ms': int(
                    Snapshot.objects.filter(response_time_ms__isnull=False)
                    .aggregate(Avg('response_time_ms'))['response_time_ms__avg'] or 0
                ),
                'queue_length': Notification.objects.filter(status=NotificationStatus.QUEUED).count(),
                'duplicate_events_skipped': cache.get('metrics_duplicate_events_skipped', 0),
            }
        except Exception as e:
            data['metrics'] = {'error': str(e)}

        return Response(data)


# ─── Admin Endpoints ───────────────────────────────────────────────────────────

class AdminPortalListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from apps.agencies.models import Portal
        from apps.agencies.serializers import PortalSerializer
        portals = Portal.objects.all().select_related('agency')
        return Response(PortalSerializer(portals, many=True).data)

    def post(self, request):
        from apps.agencies.serializers import PortalSerializer
        serializer = PortalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)


class AdminPortalDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        from apps.agencies.models import Portal
        from apps.agencies.serializers import PortalSerializer
        from django.shortcuts import get_object_or_404
        portal = get_object_or_404(Portal, pk=pk)
        return Response(PortalSerializer(portal).data)


class AdminVerifyAlertView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        from apps.alerts.models import Alert, AlertStatus
        from django.shortcuts import get_object_or_404
        alert = get_object_or_404(Alert, pk=pk)
        alert.is_verified = True
        alert.status = AlertStatus.APPROVED
        alert.verified_by = request.user
        alert.verified_at = timezone.now()
        alert.save()
        return Response({'status': 'verified', 'alert_id': alert.pk})


class AdminRejectAlertView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        from apps.alerts.models import Alert, AlertStatus
        from django.shortcuts import get_object_or_404
        alert = get_object_or_404(Alert, pk=pk)
        alert.status = AlertStatus.REJECTED
        alert.save()
        return Response({'status': 'rejected', 'alert_id': alert.pk})


class AdminBroadcastView(APIView):
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        text = request.data.get('text')
        if not text:
            return Response({'error': 'text field is required'}, status=400)

        from apps.accounts.models import TelegramUser, UserState
        from apps.notifications.sender import send_message

        users = TelegramUser.objects.filter(state=UserState.ACTIVE)
        success_count = 0
        for user in users:
            try:
                send_message(chat_id=user.telegram_id, text=text)
                success_count += 1
            except Exception:
                pass

        return Response({'status': 'broadcast_sent', 'recipients_count': success_count})


class AdminStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from apps.accounts.models import TelegramUser
        from apps.alerts.models import Alert, DecisionLog
        from apps.agencies.models import Agency
        from apps.monitor.models import Snapshot
        from apps.notifications.models import Notification, NotificationStatus
        from django.db.models import Avg

        today = timezone.now().date()

        avg_ms = Snapshot.objects.filter(
            response_time_ms__isnull=False
        ).aggregate(Avg('response_time_ms'))['response_time_ms__avg']

        return Response({
            'total_users': TelegramUser.objects.count(),
            'active_users': TelegramUser.objects.filter(state='ACTIVE').count(),
            'total_agencies': Agency.objects.filter(is_active=True).count(),
            'total_alerts': Alert.objects.count(),
            'total_scrapes': Snapshot.objects.count(),
            'successful_scrapes': Snapshot.objects.filter(status_code__lt=400).count(),
            'failed_scrapes': Snapshot.objects.filter(status_code__gte=400).count(),
            'alerts_generated_today': Alert.objects.filter(created_at__date=today).count(),
            'notifications_sent_today': Notification.objects.filter(
                status=NotificationStatus.SENT, sent_at__date=today
            ).count(),
            'duplicate_events_skipped': cache.get('metrics_duplicate_events_skipped', 0),
            'ai_decisions_made': DecisionLog.objects.filter(reason__icontains='Gemini AI').count(),
            'rule_engine_decisions_made': DecisionLog.objects.filter(reason__icontains='Rule Engine Fallback').count(),
            'average_scrape_duration_ms': int(avg_ms) if avg_ms else 0,
            'queue_length': Notification.objects.filter(status=NotificationStatus.QUEUED).count(),
        })


# ─── JWT Auth ──────────────────────────────────────────────────────────────────

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.api.serializers import AgencyListSerializer   # noqa (used above)


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'


class EmailTokenObtainPairView(TokenObtainPairView):
    """Accept email + password instead of username + password."""
    serializer_class = EmailTokenObtainPairSerializer


from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from apps.api.serializers import (
    RegisterSerializer, UserProfileSerializer, JobListSerializer
)
from apps.accounts.models import WebUser
from apps.alerts.models import Alert


class RegisterView(APIView):
    """
    POST /api/auth/register/
    Creates a new user account and returns access & refresh tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=http_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklists the refresh token to log out server-side.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'Refresh token required.'}, status=http_status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Successfully logged out.'})
        except Exception:
            return Response({'detail': 'Invalid or expired refresh token.'}, status=http_status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    """
    GET /api/auth/me/ — Get current user profile
    PATCH /api/auth/me/ — Update profile info
    """
    permission_classes = [IsAuthenticated]

    def get_web_profile(self, user):
        profile, _ = WebUser.objects.get_or_create(user=user)
        return profile

    def get(self, request):
        profile = self.get_web_profile(request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        profile = self.get_web_profile(request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    """
    POST /api/auth/password/change/
    Change password for authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response(
                {'detail': 'Both old_password and new_password are required.'},
                status=http_status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        if not user.check_password(old_password):
            return Response({'detail': 'Incorrect old password.'}, status=http_status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 6:
            return Response({'detail': 'New password must be at least 6 characters.'}, status=http_status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password updated successfully.'})


class SavedJobsView(APIView):
    """
    GET /api/v1/me/saved-jobs/ — List saved jobs
    POST /api/v1/me/saved-jobs/ — Save a job {ref: "1234-GA"}
    """
    permission_classes = [IsAuthenticated]

    def get_web_profile(self, user):
        profile, _ = WebUser.objects.get_or_create(user=user)
        return profile

    def get(self, request):
        profile = self.get_web_profile(request.user)
        saved_jobs = profile.saved_jobs.select_related('agency', 'portal').order_by('-created_at')
        serializer = JobListSerializer(saved_jobs, many=True)
        return Response(serializer.data)

    def post(self, request):
        ref = request.data.get('ref')
        if not ref:
            return Response({'detail': 'Job ref required.'}, status=http_status.HTTP_400_BAD_REQUEST)

        pk = _pk_from_ref(ref)
        if pk is None:
            return Response({'detail': 'Invalid job ref.'}, status=http_status.HTTP_400_BAD_REQUEST)

        try:
            alert = Alert.objects.get(pk=pk)
        except Alert.DoesNotExist:
            return Response({'detail': 'Job not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        profile = self.get_web_profile(request.user)
        profile.saved_jobs.add(alert)
        return Response({'detail': f'Job {ref} saved successfully.'}, status=http_status.HTTP_201_CREATED)


class SavedJobDetailView(APIView):
    """
    DELETE /api/v1/me/saved-jobs/{ref}/ — Unsave a job
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, ref):
        pk = _pk_from_ref(ref)
        if pk is None:
            return Response({'detail': 'Invalid job ref.'}, status=http_status.HTTP_400_BAD_REQUEST)

        try:
            alert = Alert.objects.get(pk=pk)
        except Alert.DoesNotExist:
            return Response({'detail': 'Job not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        profile, _ = WebUser.objects.get_or_create(user=request.user)
        profile.saved_jobs.remove(alert)
        return Response({'detail': f'Job {ref} unsaved successfully.'})

