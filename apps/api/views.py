"""
RecruitmentAlert API v1 — Public endpoints for agencies, jobs, and system status.

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
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.db import connection
from django.db.models import Q, Sum, Avg, Count, Max, Min, F, Prefetch
from django.shortcuts import get_object_or_404
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework.throttling import AnonRateThrottle
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
from apps.subscriptions.models import KeywordSubscription

logger = logging.getLogger(__name__)


class KeywordSubscriptionThrottle(AnonRateThrottle):
    rate = '5/hour'


class KeywordSubscriptionView(APIView):
    """
    POST /api/v1/keyword-subscriptions/
    Body: {"email": str, "query_text": str}
    Rate limited to max 5 requests per IP per hour.
    """
    permission_classes = [AllowAny]
    throttle_classes = [KeywordSubscriptionThrottle]

    def post(self, request):
        email = (request.data.get('email') or '').strip()
        query_text = (request.data.get('query_text') or '').strip()

        if not email:
            return Response({'detail': 'Email address is required.'}, status=http_status.HTTP_400_BAD_REQUEST)

        try:
            validate_email(email)
        except ValidationError:
            return Response({'detail': 'Please enter a valid email address.'}, status=http_status.HTTP_400_BAD_REQUEST)

        if not query_text:
            return Response({'detail': 'Search keyword is required.'}, status=http_status.HTTP_400_BAD_REQUEST)

        if len(query_text) > 200:
            return Response({'detail': 'Search keyword must be 200 characters or less.'}, status=http_status.HTTP_400_BAD_REQUEST)

        sub, created = KeywordSubscription.objects.get_or_create(
            email=email.lower(),
            query_text=query_text,
            defaults={'is_active': True}
        )
        if not sub.is_active:
            sub.is_active = True
            sub.save(update_fields=['is_active'])

        return Response({
            'detail': f"You'll be notified at {sub.email} when a match appears.",
            'email': sub.email,
            'query_text': sub.query_text,
        }, status=http_status.HTTP_201_CREATED)


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

        qs = Alert.objects.filter(
            status=AlertStatus.APPROVED
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
        from apps.alerts.models import Alert, AlertStatus

        pk = _pk_from_ref(ref)
        if pk is None:
            return Response({'detail': 'Invalid job reference.'}, status=http_status.HTTP_400_BAD_REQUEST)

        try:
            alert = Alert.objects.select_related('agency', 'portal', 'recruitment_event').get(
                pk=pk, status=AlertStatus.APPROVED
            )
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
        from apps.alerts.models import Alert, AlertStatus

        pk = _pk_from_ref(ref)
        if pk is None:
            return Response({'detail': 'Invalid job reference.'}, status=http_status.HTTP_400_BAD_REQUEST)

        try:
            alert = Alert.objects.select_related('agency', 'portal').get(
                pk=pk, status=AlertStatus.APPROVED
            )
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


class JobAiSummaryView(APIView):
    """
    GET /api/v1/jobs/{ref}/ai-summary/
    Triggers/retrieves OpenAI-powered recruitment intelligence:
    - Structured Summarization
    - Scam Detection & Red Flags
    - Government Verification Check
    - Dynamic Trust Score
    """
    permission_classes = [AllowAny]

    def get(self, request, ref):
        from apps.alerts.models import Alert, AlertStatus
        from apps.detector.ai import (
            summarize_recruitment_with_openai,
            detect_scam_with_openai,
            verify_recruitment_with_openai
        )
        from apps.detector.trust import calculate_trust_score

        pk = _pk_from_ref(ref)
        if pk is None:
            return Response({'detail': 'Invalid job reference.'}, status=http_status.HTTP_400_BAD_REQUEST)

        try:
            alert = Alert.objects.select_related('agency', 'portal').get(
                pk=pk, status=AlertStatus.APPROVED
            )
        except Alert.DoesNotExist:
            return Response({'detail': 'Job not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        content = alert.raw_text or alert.description or alert.title or ""
        agency_name = alert.agency.name if alert.agency else ""
        source_url = alert.source_url or ""

        summary = summarize_recruitment_with_openai(alert.title, agency_name, content)
        scam_analysis = detect_scam_with_openai(agency_name, source_url, content)
        verification = verify_recruitment_with_openai(agency_name, source_url, content)
        computed_trust_score = calculate_trust_score(alert.agency, source_url, alert.ai_confidence or 85, content)

        return Response({
            'ref': ref,
            'title': alert.title,
            'agency': agency_name,
            'summary': summary,
            'scam_analysis': scam_analysis,
            'verification': verification,
            'trust_score': computed_trust_score,
            'ai_engine': 'OpenAI (gpt-4o-mini)'
        })


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
    Public live feed endpoint.
    Returns real recruitment activity, verified openings, and portal incidents.
    Filters out routine 'no_changes' scan logs to keep the public feed clean and relevant.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        from apps.monitor.models import Snapshot
        from apps.alerts.models import Alert
        from django.db.models import Q

        feed = []

        # 1. Fetch recent snapshots with actual events or incidents
        event_snapshots = Snapshot.objects.select_related('portal__agency').filter(
            Q(has_change=True) | Q(triggered_alert=True) | Q(status_code__gte=400)
        ).order_by('-created_at')[:10]

        for snap in event_snapshots:
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
        from apps.monitor.models import Snapshot
        from apps.alerts.models import Alert, DecisionLog
        from apps.notifications.models import Notification, NotificationStatus

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
        portal = get_object_or_404(Portal, pk=pk)
        return Response(PortalSerializer(portal).data)


class AdminVerifyAlertView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        from apps.alerts.models import Alert, AlertStatus
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


# ─── Custom DRF Admin API ──────────────────────────────────────────────────────

from core.permissions import IsStaffUser
from apps.api.serializers import (
    AdminAlertDetailSerializer, AdminAgencySerializer,
    SnapshotSerializer, AdminPortalSerializer, AdminPortalDetailSerializer,
)
from apps.alerts.models import Alert, AlertStatus
from apps.agencies.models import Agency, Portal
from apps.monitor.models import Snapshot, PortalHealthLog
from django.contrib.auth import authenticate


class CustomAdminLoginView(APIView):
    """
    POST /api/v1/admin/auth/login/
    Validates auth.User with is_staff=True.
    Returns access & refresh tokens + user info.
    If user exists but is_staff=False, returns 403 Forbidden.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = (request.data.get('username') or request.data.get('email') or '').strip()
        password = request.data.get('password', '')

        if not identifier or not password:
            return Response(
                {'detail': 'Username/email and password are required.'},
                status=http_status.HTTP_400_BAD_REQUEST
            )

        from django.contrib.auth.models import User
        user_obj = User.objects.filter(Q(username__iexact=identifier) | Q(email__iexact=identifier)).first()

        if not user_obj:
            return Response(
                {'detail': 'Invalid email/username or password.'},
                status=http_status.HTTP_401_UNAUTHORIZED
            )

        if not user_obj.is_staff:
            return Response(
                {'detail': 'Staff credentials required to access the admin portal.'},
                status=http_status.HTTP_403_FORBIDDEN
            )

        user = authenticate(request, username=user_obj.username, password=password)
        if not user:
            return Response(
                {'detail': 'Invalid email/username or password.'},
                status=http_status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_staff:
            return Response(
                {'detail': 'Staff credentials required to access the admin portal.'},
                status=http_status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_superuser': user.is_superuser,
            }
        })


class CustomAdminMeView(APIView):
    """
    GET /api/v1/admin/auth/me/
    Returns current authenticated admin user's info.
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        })


class CustomAdminAlertListView(APIView):
    """
    GET /api/v1/admin/alerts/
    List alerts with full detail for admins.
    Supports ?status=PENDING|APPROVED|REJECTED|HELD (default: PENDING)
    Supports ?agency={acronym}
    Supports ?ai_classification=REAL|FAKE|UNCERTAIN
    Supports ?ordering=-created_at, -ai_confidence, -trust_score, etc.
    Default ordering for PENDING: lowest ai_confidence first (ai_confidence asc).
    Paginated 20 per page.
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        status_param = request.query_params.get('status', 'PENDING').strip()
        agency_param = request.query_params.get('agency', '').strip()
        ai_class_param = request.query_params.get('ai_classification', '').strip()
        ordering_param = request.query_params.get('ordering', '').strip()

        qs = Alert.objects.select_related('agency', 'portal', 'recruitment_event', 'verified_by', 'trust_score_overridden_by').all()

        # Status filter
        if status_param.upper() != 'ALL':
            qs = qs.filter(status__iexact=status_param)

        # Agency filter
        if agency_param:
            qs = qs.filter(agency__acronym__iexact=agency_param)

        # AI Classification filter
        if ai_class_param:
            qs = qs.filter(ai_classification__iexact=ai_class_param)

        # Ordering
        if ordering_param:
            qs = qs.order_by(ordering_param)
        elif status_param.upper() == 'PENDING':
            # Default sorting for PENDING queue: lowest ai_confidence first (needs most judgment)
            qs = qs.order_by('ai_confidence', '-created_at')
        else:
            qs = qs.order_by('-created_at')

        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = AdminAlertDetailSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class CustomAdminAlertApproveView(APIView):
    """
    POST /api/v1/admin/alerts/{id}/approve/
    Body: {"admin_notes": str (optional)}
    Sets status='APPROVED', is_verified=True, verified_by=user, verified_at=now.
    Appends admin_notes if provided.
    Triggers downstream dispatch.
    """
    permission_classes = [IsStaffUser]

    def post(self, request, pk):
        try:
            alert = Alert.objects.select_related('agency', 'portal', 'recruitment_event').get(pk=pk)
        except Alert.DoesNotExist:
            return Response({'detail': 'Alert not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        new_notes = request.data.get('admin_notes', '').strip()
        now = timezone.now()

        alert.status = AlertStatus.APPROVED
        alert.is_verified = True
        alert.verified_by = request.user
        alert.verified_at = now

        if new_notes:
            timestamp_str = now.strftime('%Y-%m-%d %H:%M')
            formatted_note = f"[{timestamp_str} - {request.user.username}]: {new_notes}"
            if alert.admin_notes:
                alert.admin_notes = f"{alert.admin_notes}\n{formatted_note}"
            else:
                alert.admin_notes = formatted_note

        alert.save(update_fields=['status', 'is_verified', 'verified_by', 'verified_at', 'admin_notes', 'updated_at'])

        # Trigger downstream publishing
        from apps.notifications.tasks import dispatch_alert
        try:
            dispatch_alert.delay(alert.id)
        except Exception:
            try:
                dispatch_alert(alert.id)
            except Exception as exc:
                logger.warning(f"Failed to trigger alert dispatch: {exc}")

        serializer = AdminAlertDetailSerializer(alert)
        return Response({
            'detail': 'Alert approved and queued for dispatch.',
            'alert': serializer.data
        })


class CustomAdminAlertRejectView(APIView):
    """
    POST /api/v1/admin/alerts/{id}/reject/
    Body: {"admin_notes": str (required)}
    Sets status='REJECTED', verified_by=user, verified_at=now.
    Increments agency.false_positives if ai_classification was 'REAL'.
    """
    permission_classes = [IsStaffUser]

    def post(self, request, pk):
        try:
            alert = Alert.objects.select_related('agency', 'portal', 'recruitment_event').get(pk=pk)
        except Alert.DoesNotExist:
            return Response({'detail': 'Alert not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        new_notes = request.data.get('admin_notes', '').strip()
        if not new_notes:
            return Response(
                {'detail': 'admin_notes is required when rejecting an alert.'},
                status=http_status.HTTP_400_BAD_REQUEST
            )

        now = timezone.now()
        alert.status = AlertStatus.REJECTED
        alert.verified_by = request.user
        alert.verified_at = now

        timestamp_str = now.strftime('%Y-%m-%d %H:%M')
        formatted_note = f"[{timestamp_str} - {request.user.username}]: {new_notes}"
        if alert.admin_notes:
            alert.admin_notes = f"{alert.admin_notes}\n{formatted_note}"
        else:
            alert.admin_notes = formatted_note

        # Increment false positives if AI was REAL
        if alert.ai_classification == 'REAL':
            from apps.agencies.models import Agency
            Agency.objects.filter(pk=alert.agency_id).update(false_positives=F('false_positives') + 1)

        alert.save(update_fields=['status', 'verified_by', 'verified_at', 'admin_notes', 'updated_at'])

        serializer = AdminAlertDetailSerializer(alert)
        return Response({
            'detail': 'Alert rejected successfully.',
            'alert': serializer.data
        })


class CustomAdminAlertAiAnalyzeView(APIView):
    """
    POST /api/v1/admin/alerts/{pk}/ai-analyze/
    Admin endpoint to execute full OpenAI scan on a pending/flagged alert.
    Updates alert.trust_score, alert.ai_classification, alert.ai_red_flags.
    """
    permission_classes = [IsStaffUser]

    def post(self, request, pk):
        from apps.alerts.models import Alert
        from apps.detector.ai import detect_scam_with_openai, verify_recruitment_with_openai
        from apps.detector.trust import calculate_trust_score

        try:
            alert = Alert.objects.select_related('agency').get(pk=pk)
        except Alert.DoesNotExist:
            return Response({'detail': 'Alert not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        content = alert.raw_text or alert.description or alert.title or ""
        agency_name = alert.agency.name if alert.agency else ""
        source_url = alert.source_url or ""

        scam_res = detect_scam_with_openai(agency_name, source_url, content)
        verification_res = verify_recruitment_with_openai(agency_name, source_url, content)
        trust_score = calculate_trust_score(alert.agency, source_url, alert.ai_confidence or 85, content)

        alert.trust_score = trust_score
        alert.ai_red_flags = scam_res.get('red_flags', [])
        if scam_res.get('is_scam'):
            alert.ai_classification = 'FAKE'
        elif verification_res.get('verification_status') == 'VERIFIED':
            alert.ai_classification = 'REAL'
        alert.save(update_fields=['trust_score', 'ai_red_flags', 'ai_classification'])

        return Response({
            'detail': 'Alert analyzed with OpenAI engine.',
            'pk': alert.pk,
            'trust_score': alert.trust_score,
            'classification': alert.ai_classification,
            'red_flags': alert.ai_red_flags,
            'scam_analysis': scam_res,
            'verification': verification_res
        })



class CustomAdminAlertHoldView(APIView):
    """
    POST /api/v1/admin/alerts/{id}/hold/
    Body: {"admin_notes": str (optional)}
    Sets status='HELD', verified_by=user, verified_at=now.
    """
    permission_classes = [IsStaffUser]

    def post(self, request, pk):
        try:
            alert = Alert.objects.select_related('agency', 'portal', 'recruitment_event').get(pk=pk)
        except Alert.DoesNotExist:
            return Response({'detail': 'Alert not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        new_notes = request.data.get('admin_notes', '').strip()
        now = timezone.now()

        alert.status = AlertStatus.HELD
        alert.verified_by = request.user
        alert.verified_at = now

        if new_notes:
            timestamp_str = now.strftime('%Y-%m-%d %H:%M')
            formatted_note = f"[{timestamp_str} - {request.user.username}]: {new_notes}"
            if alert.admin_notes:
                alert.admin_notes = f"{alert.admin_notes}\n{formatted_note}"
            else:
                alert.admin_notes = formatted_note

        alert.save(update_fields=['status', 'verified_by', 'verified_at', 'admin_notes', 'updated_at'])

        serializer = AdminAlertDetailSerializer(alert)
        return Response({
            'detail': 'Alert marked as HELD for review.',
            'alert': serializer.data
        })


class CustomAdminAlertUpdateView(APIView):
    """
    PATCH /api/v1/admin/alerts/{id}/
    Body: {"admin_notes": str (optional), "trust_score": int (optional, 0-100)}
    Allows editing notes and manually overriding trust_score with audit trail.
    """
    permission_classes = [IsStaffUser]

    def patch(self, request, pk):
        try:
            alert = Alert.objects.select_related('agency', 'portal', 'recruitment_event').get(pk=pk)
        except Alert.DoesNotExist:
            return Response({'detail': 'Alert not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        update_fields = ['updated_at']

        if 'admin_notes' in request.data:
            new_notes = str(request.data['admin_notes']).strip()
            alert.admin_notes = new_notes
            update_fields.append('admin_notes')

        if 'trust_score' in request.data:
            try:
                score = int(request.data['trust_score'])
            except (ValueError, TypeError):
                return Response(
                    {'detail': 'trust_score must be an integer between 0 and 100.'},
                    status=http_status.HTTP_400_BAD_REQUEST
                )
            if not (0 <= score <= 100):
                return Response(
                    {'detail': 'trust_score must be between 0 and 100.'},
                    status=http_status.HTTP_400_BAD_REQUEST
                )

            if score != alert.trust_score:
                alert.trust_score = score
                alert.trust_score_overridden_by = request.user
                alert.trust_score_overridden_at = timezone.now()
                update_fields.extend(['trust_score', 'trust_score_overridden_by', 'trust_score_overridden_at'])

        alert.save(update_fields=list(set(update_fields)))
        serializer = AdminAlertDetailSerializer(alert)
        return Response(serializer.data)


class CustomAdminAlertStatsView(APIView):
    """
    GET /api/v1/admin/alerts/stats/
    Returns queue status metrics: pending_count, approved_today, rejected_today,
    avg_review_time_minutes, oldest_pending_age_hours.
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        now = timezone.now()
        today = now.date()

        pending_count = Alert.objects.filter(status=AlertStatus.PENDING).count()
        approved_today = Alert.objects.filter(status=AlertStatus.APPROVED, verified_at__date=today).count()
        rejected_today = Alert.objects.filter(status=AlertStatus.REJECTED, verified_at__date=today).count()

        reviewed_alerts = Alert.objects.filter(verified_at__isnull=False).only('created_at', 'verified_at')[:200]
        if reviewed_alerts.exists():
            durations = [(a.verified_at - a.created_at).total_seconds() for a in reviewed_alerts if a.verified_at]
            avg_seconds = sum(durations) / len(durations) if durations else 0.0
            avg_review_time_minutes = round(avg_seconds / 60.0, 1)
        else:
            avg_review_time_minutes = 0.0

        oldest_pending = Alert.objects.filter(status=AlertStatus.PENDING).order_by('created_at').first()
        if oldest_pending:
            oldest_pending_age_hours = round((now - oldest_pending.created_at).total_seconds() / 3600.0, 1)
        else:
            oldest_pending_age_hours = 0.0

        return Response({
            'pending_count': pending_count,
            'approved_today': approved_today,
            'rejected_today': rejected_today,
            'avg_review_time_minutes': avg_review_time_minutes,
            'oldest_pending_age_hours': oldest_pending_age_hours,
        })


# ─── Custom Admin Agency Endpoints ─────────────────────────────────────────────

class CustomAdminAgencyListCreateView(APIView):
    """
    GET  /api/v1/admin/agencies/ — list all agencies (including inactive)
    POST /api/v1/admin/agencies/ — create new agency
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        agencies = Agency.objects.all().order_by('acronym')
        
        category_param = request.query_params.get('category', '').strip()
        if category_param:
            agencies = agencies.filter(category__iexact=category_param)
            
        search_param = request.query_params.get('search', '').strip()
        if search_param:
            agencies = agencies.filter(
                Q(name__icontains=search_param) |
                Q(acronym__icontains=search_param)
            )

        serializer = AdminAgencySerializer(agencies, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AdminAgencySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=http_status.HTTP_201_CREATED)


class CustomAdminAgencyDetailView(APIView):
    """
    GET    /api/v1/admin/agencies/{id}/ — full agency detail
    PATCH  /api/v1/admin/agencies/{id}/ — edit any field
    DELETE /api/v1/admin/agencies/{id}/ — soft delete (set is_active=False)
    """
    permission_classes = [IsStaffUser]

    def get_object(self, pk):
        try:
            return Agency.objects.get(pk=pk)
        except Agency.DoesNotExist:
            return None

    def get(self, request, pk):
        agency = self.get_object(pk)
        if not agency:
            return Response({'detail': 'Agency not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        serializer = AdminAgencySerializer(agency)
        return Response(serializer.data)

    def patch(self, request, pk):
        agency = self.get_object(pk)
        if not agency:
            return Response({'detail': 'Agency not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        serializer = AdminAgencySerializer(agency, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        agency = self.get_object(pk)
        if not agency:
            return Response({'detail': 'Agency not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        
        # Soft delete — never hard delete an agency with attached alerts/portals
        agency.is_active = False
        agency.save(update_fields=['is_active', 'updated_at'])
        return Response({
            'detail': 'Agency deactivated (soft-deleted).',
            'id': agency.id,
            'is_active': False,
        })


# ─── Custom Admin Portal Endpoints ─────────────────────────────────────────────

class CustomAdminPortalListCreateView(APIView):
    """
    GET  /api/v1/admin/portals/ — list all, filterable by agency & health_status
    POST /api/v1/admin/portals/ — create new portal for an agency
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        portals = Portal.objects.select_related('agency').all().order_by('agency__acronym', 'name')

        agency_param = request.query_params.get('agency', '').strip()
        if agency_param:
            if agency_param.isdigit():
                portals = portals.filter(agency_id=int(agency_param))
            else:
                portals = portals.filter(
                    Q(agency__acronym__iexact=agency_param) |
                    Q(agency__slug__iexact=agency_param)
                )

        health_param = request.query_params.get('health_status', '').strip() or request.query_params.get('status', '').strip()
        if health_param:
            portals = portals.filter(
                Q(health_status__iexact=health_param) |
                Q(status__iexact=health_param)
            )

        serializer = AdminPortalSerializer(portals, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AdminPortalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=http_status.HTTP_201_CREATED)


class CustomAdminPortalDetailView(APIView):
    """
    GET    /api/v1/admin/portals/{id}/ — full detail including last 10 snapshots
    PATCH  /api/v1/admin/portals/{id}/ — edit url, poll_interval, priority, is_active, etc.
    DELETE /api/v1/admin/portals/{id}/ — soft delete (is_active=False)
    """
    permission_classes = [IsStaffUser]

    def get_object(self, pk):
        try:
            return Portal.objects.select_related('agency').get(pk=pk)
        except Portal.DoesNotExist:
            return None

    def get(self, request, pk):
        portal = self.get_object(pk)
        if not portal:
            return Response({'detail': 'Portal not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        serializer = AdminPortalDetailSerializer(portal)
        return Response(serializer.data)

    def patch(self, request, pk):
        portal = self.get_object(pk)
        if not portal:
            return Response({'detail': 'Portal not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        serializer = AdminPortalSerializer(portal, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        portal = self.get_object(pk)
        if not portal:
            return Response({'detail': 'Portal not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        
        portal.is_active = False
        portal.save(update_fields=['is_active', 'updated_at'])
        return Response({
            'detail': 'Portal deactivated (soft-deleted).',
            'id': portal.id,
            'is_active': False,
        })


class CustomAdminPortalTriggerCheckView(APIView):
    """
    POST /api/v1/admin/portals/{id}/trigger-check/
    Manually trigger an immediate scrape of this portal outside the normal polling cycle.
    Returns resulting Snapshot data and whether a change was detected.
    """
    permission_classes = [IsStaffUser]

    def post(self, request, pk):
        try:
            portal = Portal.objects.get(pk=pk)
        except Portal.DoesNotExist:
            return Response({'detail': 'Portal not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        from apps.monitor.tasks import portal_check
        try:
            portal_check(portal.id)
        except Exception as exc:
            logger.error(f"Manual portal_check failed for portal #{pk}: {exc}")
            exc_str = str(exc)
            if "NUL" in exc_str or "0x00" in exc_str or "parse" in exc_str.lower() or "encoding" in exc_str.lower():
                return Response(
                    {'detail': 'This portal returned content that could not be parsed — may not be a standard HTML page.'},
                    status=http_status.HTTP_422_UNPROCESSABLE_ENTITY
                )
            return Response(
                {'detail': f'Error executing portal scrape: {str(exc)}'},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        latest_snapshot = Snapshot.objects.filter(portal=portal).order_by('-created_at').first()
        snapshot_data = SnapshotSerializer(latest_snapshot).data if latest_snapshot else None

        return Response({
            'detail': f"Manual check triggered successfully for portal '{portal.name}'.",
            'has_change': latest_snapshot.has_change if latest_snapshot else False,
            'triggered_alert': latest_snapshot.triggered_alert if latest_snapshot else False,
            'snapshot': snapshot_data,
        })


class CustomAdminPortalHistoryView(APIView):
    """
    GET /api/v1/admin/portals/{id}/history/
    Returns last 30 days of Snapshot records for this portal
    (timestamp, status_code, response_time_ms, has_change, triggered_alert).
    """
    permission_classes = [IsStaffUser]

    def get(self, request, pk):
        try:
            portal = Portal.objects.get(pk=pk)
        except Portal.DoesNotExist:
            return Response({'detail': 'Portal not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        cutoff = timezone.now() - timedelta(days=30)
        snapshots = Snapshot.objects.filter(
            portal=portal,
            created_at__gte=cutoff
        ).order_by('-created_at')

        serializer = SnapshotSerializer(snapshots, many=True)
        return Response(serializer.data)


# ─── Custom Admin System Health Endpoint ──────────────────────────────────────

class CustomAdminSystemHealthView(APIView):
    """
    GET /api/v1/admin/system-health/
    Detailed system health dashboard endpoint for staff users.
    Returns:
      - system_status (top-level system metrics)
      - portals_breakdown (every portal, consecutive_failures, last_checked_at, health_status, needs_attention flag)
      - recent_failed_snapshots (20 most recent failed Snapshot records)
      - daily_trend_7_days (total_checks and success_rate for the last 7 days)
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        now = timezone.now()
        today = now.date()

        # 1. System Status Top Level Metrics
        total_agencies = Agency.objects.filter(is_active=True).count()
        active_portals = Portal.objects.filter(is_active=True).select_related('agency')

        agencies_offline = active_portals.filter(
            Q(health_status__in=['OFFLINE', 'DOWN']) | Q(status__in=['OFFLINE', 'DOWN']) | Q(consecutive_failures__gt=0)
        ).values('agency').distinct().count()

        agencies_maintenance = active_portals.filter(
            Q(health_status__in=['MAINTENANCE', 'BLOCKED', 'RATE_LIMITED', 'CAPTCHA']) | Q(status__in=['MAINTENANCE', 'BLOCKED', 'RATE_LIMITED', 'CAPTCHA'])
        ).values('agency').distinct().count()

        agencies_online = max(0, total_agencies - (agencies_offline + agencies_maintenance))

        # Check today's snapshots
        today_snaps = Snapshot.objects.filter(created_at__date=today)
        total_checks_today = today_snaps.count()

        if total_checks_today > 0:
            successful_checks_today = today_snaps.filter(status_code__lt=400).count()
            failed_checks_today = total_checks_today - successful_checks_today
            success_rate_today = round((successful_checks_today / total_checks_today) * 100, 2)
        else:
            # Fallback to 24h window if no checks yet today
            snaps_24h = Snapshot.objects.filter(created_at__gte=now - timedelta(hours=24))
            if snaps_24h.exists():
                total_checks_today = snaps_24h.count()
                successful_checks_today = snaps_24h.filter(status_code__lt=400).count()
                failed_checks_today = total_checks_today - successful_checks_today
                success_rate_today = round((successful_checks_today / total_checks_today) * 100, 2)
            else:
                # If no snapshots in last 24h, derive from live portal roster state
                total_portals_count = active_portals.count()
                offline_portals_count = active_portals.filter(
                    Q(health_status__in=['OFFLINE', 'DOWN']) | Q(status__in=['OFFLINE', 'DOWN']) | Q(consecutive_failures__gt=0)
                ).count()
                online_portals_count = max(0, total_portals_count - offline_portals_count)

                total_checks_today = total_portals_count
                successful_checks_today = online_portals_count
                failed_checks_today = offline_portals_count
                success_rate_today = round((online_portals_count / max(total_portals_count, 1)) * 100, 2)

        changes_detected_today = Snapshot.objects.filter(
            created_at__date=today, has_change=True
        ).count()

        system_operational = (agencies_offline == 0)

        system_status = {
            'agencies_online': agencies_online,
            'agencies_offline': agencies_offline,
            'agencies_maintenance': agencies_maintenance,
            'total_agencies': total_agencies,
            'total_checks_today': total_checks_today,
            'successful_checks_today': successful_checks_today,
            'failed_checks_today': failed_checks_today,
            'success_rate_today': success_rate_today,
            'changes_detected_today': changes_detected_today,
            'system_operational': system_operational,
        }

        # 2. Per-Portal Breakdown
        portals = Portal.objects.select_related('agency').all().order_by('agency__acronym', 'name')
        portals_breakdown = []
        for portal in portals:
            effective_status = portal.health_status if (portal.health_status and portal.health_status != 'UNKNOWN') else portal.status
            is_failing = (portal.consecutive_failures > 0 or effective_status in ['OFFLINE', 'DOWN', 'BLOCKED', 'CAPTCHA', 'RATE_LIMITED'])

            down_duration_seconds = 0
            if is_failing:
                if portal.last_successful_check_at:
                    down_duration_seconds = max(int((now - portal.last_successful_check_at).total_seconds()), 0)
                elif portal.last_checked_at:
                    down_duration_seconds = max(int((now - portal.last_checked_at).total_seconds()), 0)
                else:
                    down_duration_seconds = 3600

            failing_over_24h = (is_failing and down_duration_seconds >= 86400)

            needs_attention = (
                is_failing and (
                    portal.consecutive_failures >= 1 or
                    effective_status in ['OFFLINE', 'DOWN', 'BLOCKED', 'CAPTCHA', 'RATE_LIMITED']
                )
            )

            portals_breakdown.append({
                'id': portal.id,
                'name': portal.name,
                'agency_acronym': portal.agency.acronym if portal.agency else '',
                'url': portal.url,
                'consecutive_failures': portal.consecutive_failures,
                'last_checked_at': portal.last_checked_at.isoformat() if portal.last_checked_at else None,
                'last_successful_check_at': portal.last_successful_check_at.isoformat() if portal.last_successful_check_at else None,
                'health_status': effective_status,
                'status': portal.status,
                'needs_attention': needs_attention,
                'down_duration_seconds': down_duration_seconds,
                'failing_over_24h': failing_over_24h,
            })

        # 3. 20 Most Recent Failed Snapshots across all portals
        failed_snapshots_qs = Snapshot.objects.filter(
            Q(status_code__gte=400) | Q(status_code__isnull=True)
        ).select_related('portal__agency').order_by('-created_at')[:20]

        recent_failed_snapshots = []
        seen_portal_ids = set()

        for snap in failed_snapshots_qs:
            portal_obj = snap.portal
            if portal_obj:
                seen_portal_ids.add(portal_obj.id)
            agency_acronym = portal_obj.agency.acronym if (portal_obj and portal_obj.agency) else ''
            portal_name = portal_obj.name if portal_obj else 'Unknown Portal'

            code = snap.status_code
            if code == 403:
                error_detail = 'HTTP 403 Forbidden (Blocked/Cloudflare)'
            elif code == 404:
                error_detail = 'HTTP 404 Not Found'
            elif code == 429:
                error_detail = 'HTTP 429 Rate Limited'
            elif code == 500:
                error_detail = 'HTTP 500 Internal Server Error'
            elif code == 502:
                error_detail = 'HTTP 502 Bad Gateway'
            elif code == 503:
                error_detail = 'HTTP 503 Service Unavailable'
            elif code is None:
                error_detail = 'Network Connection Failed / Timeout'
            else:
                error_detail = f'HTTP Error {code}'

            recent_failed_snapshots.append({
                'id': snap.id,
                'portal_id': portal_obj.id if portal_obj else None,
                'portal_name': portal_name,
                'agency_acronym': agency_acronym,
                'status_code': snap.status_code or 500,
                'response_time_ms': snap.response_time_ms,
                'error_detail': error_detail,
                'timestamp': snap.created_at.isoformat(),
            })

        # Ensure all currently failing/offline portals appear in the log if they lack recent failed snapshot rows
        failing_portals = Portal.objects.filter(
            Q(consecutive_failures__gt=0) | Q(health_status__in=['OFFLINE', 'DOWN', 'BLOCKED', 'CAPTCHA']) | Q(status__in=['OFFLINE', 'DOWN', 'BLOCKED', 'CAPTCHA'])
        ).select_related('agency')

        for p_obj in failing_portals:
            if p_obj.id not in seen_portal_ids:
                status_label = p_obj.health_status if (p_obj.health_status and p_obj.health_status != 'UNKNOWN') else p_obj.status
                code = 404 if status_label in ['OFFLINE', 'DOWN'] else (403 if status_label == 'BLOCKED' else (429 if status_label == 'RATE_LIMITED' else 500))
                error_detail = f'Portal {status_label} ({p_obj.consecutive_failures} consecutive failures)'

                recent_failed_snapshots.append({
                    'id': f'portal-fail-{p_obj.id}',
                    'portal_id': p_obj.id,
                    'portal_name': p_obj.name,
                    'agency_acronym': p_obj.agency.acronym if p_obj.agency else '',
                    'status_code': code,
                    'response_time_ms': p_obj.response_time_ms or 0,
                    'error_detail': error_detail,
                    'timestamp': (p_obj.last_checked_at or now).isoformat(),
                })

        # Sort combined recent failed snapshots by timestamp descending
        recent_failed_snapshots.sort(key=lambda s: s['timestamp'], reverse=True)
        recent_failed_snapshots = recent_failed_snapshots[:20]

        # 4. 7-Day Daily Trend (from PortalHealthLog with Snapshot fallback)
        daily_trend_7_days = []
        for i in range(6, -1, -1):
            day_date = today - timedelta(days=i)

            health_logs = PortalHealthLog.objects.filter(date=day_date)
            if health_logs.exists():
                agg = health_logs.aggregate(
                    total=Sum('checks_total'),
                    success=Sum('checks_successful'),
                    failed=Sum('checks_failed')
                )
                total_checks = agg['total'] or 0
                successful_checks = agg['success'] or 0
                failed_checks = agg['failed'] or 0
                success_rate = round((successful_checks / total_checks * 100), 2) if total_checks > 0 else None
            else:
                day_snaps = Snapshot.objects.filter(created_at__date=day_date)
                total_checks = day_snaps.count()
                successful_checks = day_snaps.filter(status_code__lt=400).count()
                failed_checks = total_checks - successful_checks
                success_rate = round((successful_checks / total_checks * 100), 2) if total_checks > 0 else None

            daily_trend_7_days.append({
                'date': day_date.strftime('%Y-%m-%d'),
                'total_checks': total_checks,
                'successful_checks': successful_checks,
                'failed_checks': failed_checks,
                'success_rate': success_rate,
            })

        return Response({
            'system_status': system_status,
            'portals_breakdown': portals_breakdown,
            'recent_failed_snapshots': recent_failed_snapshots,
            'daily_trend_7_days': daily_trend_7_days,
        })


# ─── Custom Admin User Management & Mass Recheck Endpoints ────────────────────

class CustomAdminUserListView(APIView):
    """
    GET /api/v1/admin/users/
    Returns paginated/searchable roster of registered Web users, Telegram bot subscribers, and Keyword subscribers.
    Query params:
      ?search={email|username|telegram_id|name}
      ?user_type={web|telegram|keyword}
      ?status={active|inactive|blocked}
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        from apps.accounts.models import WebUser, TelegramUser, UserState
        from apps.subscriptions.models import KeywordSubscription
        from django.contrib.auth import get_user_model

        User = get_user_model()
        search = (request.query_params.get('search') or '').strip().lower()
        user_type = (request.query_params.get('user_type') or '').strip().lower()
        status_filter = (request.query_params.get('status') or '').strip().lower()

        results = []

        # 1. Web Users
        if not user_type or user_type == 'web':
            web_qs = WebUser.objects.select_related('user').all().order_by('-user__date_joined')
            for w in web_qs:
                u = w.user
                if not u:
                    continue
                is_act = u.is_active
                if status_filter == 'active' and not is_act:
                    continue
                if status_filter in ['inactive', 'blocked'] and is_act:
                    continue

                full_name = f"{u.first_name} {u.last_name}".strip() or u.username
                search_haystack = f"{u.email} {u.username} {full_name}".lower()

                if search and search not in search_haystack:
                    continue

                results.append({
                    'id': f"web-{w.id}",
                    'raw_id': w.id,
                    'user_type': 'WEB',
                    'email': u.email or u.username,
                    'display_name': full_name,
                    'telegram_id': None,
                    'is_active': u.is_active,
                    'email_alerts_enabled': getattr(w, 'email_alerts_enabled', True),
                    'date_joined': u.date_joined.isoformat() if u.date_joined else None,
                    'last_login': u.last_login.isoformat() if u.last_login else None,
                })

        # 2. Telegram Users
        if not user_type or user_type == 'telegram':
            tg_qs = TelegramUser.objects.all().order_by('-joined_at')
            for tg in tg_qs:
                is_act = (tg.state == UserState.ACTIVE)
                if status_filter == 'active' and not is_act:
                    continue
                if status_filter in ['inactive', 'blocked'] and is_act:
                    continue

                full_name = f"{tg.first_name or ''} {tg.last_name or ''}".strip() or f"User {tg.telegram_id}"
                search_haystack = f"{tg.telegram_id} {tg.username or ''} {full_name}".lower()

                if search and search not in search_haystack:
                    continue

                results.append({
                    'id': f"tg-{tg.telegram_id}",
                    'raw_id': tg.telegram_id,
                    'user_type': 'TELEGRAM',
                    'email': None,
                    'display_name': full_name,
                    'username': tg.username,
                    'telegram_id': tg.telegram_id,
                    'is_active': is_act,
                    'state': tg.state,
                    'date_joined': tg.joined_at.isoformat() if hasattr(tg, 'joined_at') and tg.joined_at else None,
                    'last_login': tg.last_active_at.isoformat() if hasattr(tg, 'last_active_at') and tg.last_active_at else None,
                })

        # 3. Keyword Subscriptions
        if not user_type or user_type == 'keyword':
            kw_qs = KeywordSubscription.objects.all().order_by('-created_at')
            for kw in kw_qs:
                is_act = kw.is_active
                if status_filter == 'active' and not is_act:
                    continue
                if status_filter in ['inactive', 'blocked'] and is_act:
                    continue

                search_haystack = f"{kw.email} {kw.query_text}".lower()
                if search and search not in search_haystack:
                    continue

                results.append({
                    'id': f"kw-{kw.id}",
                    'raw_id': kw.id,
                    'user_type': 'KEYWORD_SUBSCRIBER',
                    'email': kw.email,
                    'query_text': kw.query_text,
                    'display_name': kw.email,
                    'telegram_id': None,
                    'is_active': kw.is_active,
                    'date_joined': kw.created_at.isoformat() if hasattr(kw, 'created_at') and kw.created_at else None,
                    'last_login': None,
                })

        # Sort by date_joined descending
        results.sort(key=lambda item: item['date_joined'] or '', reverse=True)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(results, request)
        return paginator.get_paginated_response(page)


class CustomAdminUserStatsView(APIView):
    """
    GET /api/v1/admin/users/stats/
    Returns user aggregate metrics: total_web_users, total_telegram_subscribers,
    total_keyword_subscribers, active_web_users, new_web_users_today.
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        from apps.accounts.models import WebUser, TelegramUser, UserState
        from apps.subscriptions.models import KeywordSubscription
        from django.contrib.auth import get_user_model

        User = get_user_model()
        today = timezone.now().date()

        total_web_users = User.objects.count()
        active_web_users = User.objects.filter(is_active=True).count()
        new_web_users_today = User.objects.filter(date_joined__date=today).count()

        total_telegram_subscribers = TelegramUser.objects.count()
        active_telegram_subscribers = TelegramUser.objects.filter(state=UserState.ACTIVE).count()

        total_keyword_subscribers = KeywordSubscription.objects.values('email').distinct().count()
        active_keyword_subscriptions = KeywordSubscription.objects.filter(is_active=True).count()

        return Response({
            'total_web_users': total_web_users,
            'active_web_users': active_web_users,
            'new_web_users_today': new_web_users_today,
            'total_telegram_subscribers': total_telegram_subscribers,
            'active_telegram_subscribers': active_telegram_subscribers,
            'total_keyword_subscribers': total_keyword_subscribers,
            'active_keyword_subscriptions': active_keyword_subscriptions,
        })


class CustomAdminUserToggleActiveView(APIView):
    """
    PATCH /api/v1/admin/users/{user_type}/{pk}/toggle-active/
    Toggles is_active / state for a WebUser, TelegramUser, or KeywordSubscription.
    """
    permission_classes = [IsStaffUser]

    def patch(self, request, user_type, pk):
        from apps.accounts.models import WebUser, TelegramUser, UserState
        from apps.subscriptions.models import KeywordSubscription

        utype = user_type.lower()
        if utype == 'web':
            try:
                web_user = WebUser.objects.select_related('user').get(pk=pk)
                u = web_user.user
                u.is_active = not u.is_active
                u.save(update_fields=['is_active'])
                return Response({'status': 'updated', 'user_type': 'web', 'id': pk, 'is_active': u.is_active})
            except WebUser.DoesNotExist:
                return Response({'detail': 'WebUser not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        elif utype == 'telegram':
            try:
                tg_user = TelegramUser.objects.get(pk=pk)
                if tg_user.state == UserState.ACTIVE:
                    tg_user.state = UserState.BLOCKED
                else:
                    tg_user.state = UserState.ACTIVE
                tg_user.save(update_fields=['state'])
                return Response({
                    'status': 'updated',
                    'user_type': 'telegram',
                    'id': pk,
                    'is_active': tg_user.state == UserState.ACTIVE,
                    'state': tg_user.state
                })
            except TelegramUser.DoesNotExist:
                return Response({'detail': 'TelegramUser not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        elif utype == 'keyword':
            try:
                kw = KeywordSubscription.objects.get(pk=pk)
                kw.is_active = not kw.is_active
                kw.save(update_fields=['is_active'])
                return Response({'status': 'updated', 'user_type': 'keyword', 'id': pk, 'is_active': kw.is_active})
            except KeywordSubscription.DoesNotExist:
                return Response({'detail': 'KeywordSubscription not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        return Response({'detail': 'Invalid user_type.'}, status=http_status.HTTP_400_BAD_REQUEST)


class CustomAdminPortalTriggerCheckAllView(APIView):
    """
    POST /api/v1/admin/portals/trigger-check-all/
    Manually trigger an immediate scrape check across all active portals in parallel.
    Executes checks and updates portal health statuses in real time.
    """
    permission_classes = [IsStaffUser]

    def post(self, request):
        import concurrent.futures
        from apps.agencies.models import Portal
        from apps.monitor.tasks import portal_check

        active_portals = list(Portal.objects.filter(is_active=True))
        count = len(active_portals)
        portal_ids = [p.id for p in active_portals]
        completed_ids = []

        from django.db import close_old_connections

        def _do_check(p_id):
            try:
                close_old_connections()
                portal_check(p_id)
                return p_id
            except Exception as exc:
                logger.error(f"Error executing portal check for portal #{p_id}: {exc}")
                return None
            finally:
                close_old_connections()

        # Execute portal checks in parallel using worker threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(_do_check, portal_ids))
            completed_ids = [pid for pid in results if pid is not None]

        return Response({
            'detail': f"Completed immediate recheck for {len(completed_ids)} out of {count} active portals.",
            'total_active_portals': count,
            'triggered_count': len(completed_ids),
            'triggered_portal_ids': completed_ids,
            'timestamp': timezone.now().isoformat(),
        })





