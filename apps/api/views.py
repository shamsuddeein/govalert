"""
API Views — stub implementations. Full logic in later volumes.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from core.permissions import IsAdminUser, IsSuperAdmin


class AgencyListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from apps.agencies.models import Agency
        from apps.agencies.serializers import AgencySerializer
        agencies = Agency.objects.filter(is_active=True)
        return Response(AgencySerializer(agencies, many=True).data)


class AgencyDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        from apps.agencies.models import Agency
        from apps.agencies.serializers import AgencySerializer
        from django.shortcuts import get_object_or_404
        agency = get_object_or_404(Agency, pk=pk, is_active=True)
        return Response(AgencySerializer(agency).data)


class LatestAlertsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from apps.alerts.models import Alert, AlertStatus
        from apps.alerts.serializers import AlertSerializer
        alerts = Alert.objects.filter(status=AlertStatus.APPROVED).order_by('-created_at')[:10]
        return Response(AlertSerializer(alerts, many=True).data)


class PortalStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from apps.agencies.models import Portal
        from apps.agencies.serializers import PortalStatusSerializer
        portals = Portal.objects.filter(is_active=True).select_related('agency')
        return Response(PortalStatusSerializer(portals, many=True).data)


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
        from django.utils import timezone
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
        from django.utils import timezone
        from django.core.cache import cache

        today = timezone.now().date()

        total_scrapes = Snapshot.objects.count()
        successful_scrapes = Snapshot.objects.filter(status_code__lt=400).count()
        failed_scrapes = Snapshot.objects.filter(status_code__gte=400).count()
        avg_scrape_duration = Snapshot.objects.filter(response_time_ms__isnull=False).aggregate(Avg('response_time_ms'))['response_time_ms__avg']

        alerts_today = Alert.objects.filter(created_at__date=today).count()
        notifications_today = Notification.objects.filter(status=NotificationStatus.SENT, sent_at__date=today).count()
        queue_length = Notification.objects.filter(status=NotificationStatus.QUEUED).count()

        ai_decisions = DecisionLog.objects.filter(reason__icontains="Gemini AI").count()
        rule_decisions = DecisionLog.objects.filter(reason__icontains="Rule Engine Fallback").count()

        duplicate_skipped = cache.get('metrics_duplicate_events_skipped', 0)

        return Response({
            'total_users': TelegramUser.objects.count(),
            'active_users': TelegramUser.objects.filter(state='ACTIVE').count(),
            'total_agencies': Agency.objects.filter(is_active=True).count(),
            'total_alerts': Alert.objects.count(),
            'total_scrapes': total_scrapes,
            'successful_scrapes': successful_scrapes,
            'failed_scrapes': failed_scrapes,
            'alerts_generated_today': alerts_today,
            'notifications_sent_today': notifications_today,
            'duplicate_events_skipped': duplicate_skipped,
            'ai_decisions_made': ai_decisions,
            'rule_engine_decisions_made': rule_decisions,
            'average_scrape_duration_ms': int(avg_scrape_duration) if avg_scrape_duration is not None else 0,
            'queue_length': queue_length,
        })


class HealthView(APIView):
    """Simple health endpoint for monitoring and uptime checks."""
    permission_classes = [AllowAny]

    def get(self, request):
        from django.db import connection
        from django.conf import settings
        from django.utils import timezone
        from django.db.models import Avg
        from django.core.cache import cache
        from apps.monitor.models import Snapshot
        from apps.alerts.models import Alert, DecisionLog
        from apps.notifications.models import Notification, NotificationStatus
        
        data = {'status': 'ok'}

        # Database check
        try:
            with connection.cursor() as cur:
                cur.execute('SELECT 1')
                _ = cur.fetchone()
            data['database'] = 'connected'
        except Exception:
            data['database'] = 'unavailable'
            data['status'] = 'degraded'

        # Telegram check (basic: token presence)
        bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        if bot_token:
            data['telegram'] = 'configured'
        else:
            data['telegram'] = 'not_configured'
            data['status'] = 'degraded'

        # Scheduler check
        try:
            from config.scheduler import get_scheduler
            sched = get_scheduler()
            data['scheduler'] = 'running' if getattr(sched, 'running', False) else 'stopped'
            if not getattr(sched, 'running', False):
                data['status'] = 'degraded'
        except Exception:
            data['scheduler'] = 'unknown'
            data['status'] = 'degraded'

        # Scrapers / portals count
        try:
            from apps.agencies.models import Portal
            data['scrapers'] = Portal.objects.filter(is_active=True).count()
        except Exception:
            data['scrapers'] = 0

        # Production Metrics
        try:
            today = timezone.now().date()
            data['production_metrics'] = {
                'total_scrapes': Snapshot.objects.count(),
                'successful_scrapes': Snapshot.objects.filter(status_code__lt=400).count(),
                'failed_scrapes': Snapshot.objects.filter(status_code__gte=400).count(),
                'alerts_generated_today': Alert.objects.filter(created_at__date=today).count(),
                'notifications_sent_today': Notification.objects.filter(status=NotificationStatus.SENT, sent_at__date=today).count(),
                'duplicate_events_skipped': cache.get('metrics_duplicate_events_skipped', 0),
                'ai_decisions_made': DecisionLog.objects.filter(reason__icontains="Gemini AI").count(),
                'rule_engine_decisions_made': DecisionLog.objects.filter(reason__icontains="Rule Engine Fallback").count(),
                'average_scrape_duration_ms': int(Snapshot.objects.filter(response_time_ms__isnull=False).aggregate(Avg('response_time_ms'))['response_time_ms__avg'] or 0),
                'queue_length': Notification.objects.filter(status=NotificationStatus.QUEUED).count(),
            }
        except Exception as e:
            data['production_metrics'] = {'error': str(e)}

        return Response(data)


from rest_framework_simplejwt.views import TokenObtainPairView
from apps.api.serializers import EmailTokenObtainPairSerializer

class EmailTokenObtainPairView(TokenObtainPairView):
    """
    Custom TokenObtainPairView that accepts email and password.
    """
    serializer_class = EmailTokenObtainPairSerializer
