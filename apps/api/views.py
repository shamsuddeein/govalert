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
        # Placeholder — full implementation in Volume 6/7
        return Response({'status': 'broadcast_queued'})


class AdminStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from apps.accounts.models import TelegramUser
        from apps.alerts.models import Alert
        from apps.agencies.models import Agency
        return Response({
            'total_users': TelegramUser.objects.count(),
            'active_users': TelegramUser.objects.filter(state='ACTIVE').count(),
            'total_agencies': Agency.objects.filter(is_active=True).count(),
            'total_alerts': Alert.objects.count(),
        })
