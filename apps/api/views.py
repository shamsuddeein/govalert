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
        from apps.agencies.models import Agency
        from django.db.models import Prefetch
        from apps.agencies.models import Portal

        agencies = Agency.objects.filter(is_active=True).prefetch_related(
            Prefetch('portals', queryset=Portal.objects.filter(is_active=True).order_by('priority'))
        )

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
        try:
            agency = Agency.objects.get(slug__iexact=slug, is_active=True)
        except Agency.DoesNotExist:
            return Response({'detail': 'Agency not found.'}, status=http_status.HTTP_404_NOT_FOUND)
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

        category_param = request.query_params.get('category')
        if category_param:
            qs = qs.filter(agency__category__iexact=category_param)

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
