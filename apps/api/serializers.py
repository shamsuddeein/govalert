"""
GovAlert API v1 — Serializers for agencies, jobs (alerts), and system status.
"""
from rest_framework import serializers
from apps.agencies.models import Agency, Portal
from apps.alerts.models import Alert, AlertStatus, RecruitmentEvent, DecisionLog
from apps.monitor.models import Snapshot


# ─── Agency Serializers ────────────────────────────────────────────────────────

class AgencyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for GET /api/v1/agencies/ list."""
    portal_url = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    last_checked = serializers.SerializerMethodField()
    response_time_ms = serializers.SerializerMethodField()
    jobs_available = serializers.SerializerMethodField()

    class Meta:
        model = Agency
        fields = [
            'id', 'name', 'acronym', 'slug', 'description',
            'category', 'portal_url', 'status',
            'last_checked', 'response_time_ms',
            'jobs_available', 'vetted_score',
        ]

    def _primary_portal(self, obj):
        """Return the primary active portal for this agency (cached on instance)."""
        if not hasattr(obj, '_primary_portal_cache'):
            obj._primary_portal_cache = obj.portals.filter(is_active=True).order_by('priority').first()
        return obj._primary_portal_cache

    def get_portal_url(self, obj):
        portal = self._primary_portal(obj)
        return portal.url if portal else ''

    def get_status(self, obj):
        portal = self._primary_portal(obj)
        if not portal:
            return 'offline'
        status_map = {
            'ONLINE': 'online', 'UP': 'online',
            'OFFLINE': 'offline', 'DOWN': 'offline',
            'MAINTENANCE': 'maintenance', 'BLOCKED': 'maintenance',
            'CAPTCHA': 'maintenance', 'RATE_LIMITED': 'maintenance',
        }
        return status_map.get(portal.status, 'offline')

    def get_last_checked(self, obj):
        portal = self._primary_portal(obj)
        if portal and portal.last_checked_at:
            return portal.last_checked_at.isoformat()
        return None

    def get_response_time_ms(self, obj):
        portal = self._primary_portal(obj)
        return portal.response_time_ms if portal else None

    def get_jobs_available(self, obj):
        return Alert.objects.filter(
            agency=obj,
            status=AlertStatus.APPROVED,
        ).count()


class AgencyDetailSerializer(AgencyListSerializer):
    """Full serializer for GET /api/v1/agencies/{slug}/"""
    monitoring_interval_minutes = serializers.SerializerMethodField()
    uptime_percent = serializers.SerializerMethodField()
    total_recruitments_detected = serializers.IntegerField(source='total_alerts_sent', read_only=True)
    last_update = serializers.SerializerMethodField()
    recruitment_history = serializers.SerializerMethodField()
    last_10_checks = serializers.SerializerMethodField()
    last_offline_at = serializers.SerializerMethodField()
    last_offline_duration_minutes = serializers.SerializerMethodField()

    class Meta(AgencyListSerializer.Meta):
        fields = AgencyListSerializer.Meta.fields + [
            'monitoring_interval_minutes', 'uptime_percent',
            'total_recruitments_detected', 'last_update',
            'recruitment_history', 'last_10_checks',
            'last_offline_at', 'last_offline_duration_minutes',
            'avg_confidence_score', 'false_positives', 'scam_domains_blocked',
            'official_domains',
        ]

    def get_monitoring_interval_minutes(self, obj):
        portal = self._primary_portal(obj)
        if not portal:
            return 15
        interval_map = {'HIGH': 5, 'MEDIUM': 15, 'LOW': 60}
        return interval_map.get(portal.priority, 15)

    def get_uptime_percent(self, obj):
        portal = self._primary_portal(obj)
        if not portal:
            return 0.0
        return float(portal.uptime_percentage)

    def get_last_update(self, obj):
        alert = Alert.objects.filter(agency=obj).order_by('-created_at').first()
        return alert.created_at.isoformat() if alert else None

    def get_recruitment_history(self, obj):
        alerts = Alert.objects.filter(
            agency=obj, status=AlertStatus.APPROVED
        ).order_by('-created_at')[:20]
        return [
            {
                'date': a.created_at.date().isoformat(),
                'event_description': a.title,
            }
            for a in alerts
        ]

    def get_last_10_checks(self, obj):
        portal = self._primary_portal(obj)
        if not portal:
            return []
        snapshots = Snapshot.objects.filter(portal=portal).order_by('-created_at')[:10]
        return [s.status_code is not None and s.status_code < 400 for s in snapshots]

    def get_last_offline_at(self, obj):
        portal = self._primary_portal(obj)
        # Use last snapshot with a 4xx/5xx status as a proxy for "offline"
        if portal:
            snap = Snapshot.objects.filter(
                portal=portal, status_code__gte=400
            ).order_by('-created_at').first()
            if snap:
                return snap.created_at.isoformat()
        return None

    def get_last_offline_duration_minutes(self, obj):
        # Not tracked at snapshot level; return null for now
        return None


# ─── Job (Alert) Serializers ───────────────────────────────────────────────────

def _alert_ref(alert):
    """Generate a stable REF from alert pk, e.g. '8829-GA'."""
    return f"{alert.pk:04d}-GA"


def _alert_frontend_status(alert):
    """Map internal alert state to frontend status vocabulary."""
    if alert.status == AlertStatus.APPROVED and alert.trust_score >= 70:
        return 'verified'
    if alert.status == AlertStatus.APPROVED and alert.trust_score >= 50:
        return 'new_opening'
    if alert.status == AlertStatus.PENDING:
        return 'updating'
    if alert.status == AlertStatus.REJECTED:
        return 'closed'
    return 'updating'


class JobListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for GET /api/v1/jobs/ list."""
    ref = serializers.SerializerMethodField()
    agency_name = serializers.CharField(source='agency.name', read_only=True)
    agency_acronym = serializers.CharField(source='agency.acronym', read_only=True)
    agency_slug = serializers.CharField(source='agency.slug', read_only=True)
    status = serializers.SerializerMethodField()
    category = serializers.CharField(source='agency.category', read_only=True)
    location_state = serializers.SerializerMethodField()
    official_url = serializers.CharField(source='source_url', read_only=True)
    published_at = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Alert
        fields = [
            'ref', 'title', 'agency_name', 'agency_acronym', 'agency_slug',
            'deadline', 'status', 'positions',
            'published_at', 'category', 'location_state', 'official_url',
        ]

    def get_ref(self, obj):
        return _alert_ref(obj)

    def get_status(self, obj):
        return _alert_frontend_status(obj)

    def get_location_state(self, obj):
        if obj.portal:
            return obj.portal.location_state or 'Federal'
        return 'Federal'


class ConfidenceFactorSerializer(serializers.Serializer):
    label = serializers.CharField()
    passed = serializers.BooleanField()


class DetectionTimelineSerializer(serializers.Serializer):
    time = serializers.CharField()
    event = serializers.CharField()


class RelatedJobSerializer(serializers.ModelSerializer):
    ref = serializers.SerializerMethodField()
    agency_name = serializers.CharField(source='agency.name', read_only=True)
    agency_acronym = serializers.CharField(source='agency.acronym', read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = ['ref', 'title', 'agency_name', 'agency_acronym', 'deadline', 'status']

    def get_ref(self, obj):
        return _alert_ref(obj)

    def get_status(self, obj):
        return _alert_frontend_status(obj)


class JobDetailSerializer(JobListSerializer):
    """Full serializer for GET /api/v1/jobs/{ref}/"""
    confidence_score = serializers.IntegerField(source='trust_score', read_only=True)
    confidence_factors = serializers.SerializerMethodField()
    source_url = serializers.URLField(read_only=True)
    last_monitored = serializers.SerializerMethodField()
    detection_timeline = serializers.SerializerMethodField()
    description = serializers.CharField(source='content_excerpt', read_only=True)
    requirements = serializers.SerializerMethodField()
    portal_status = serializers.SerializerMethodField()
    portal_last_checked = serializers.SerializerMethodField()
    portal_response_dots = serializers.SerializerMethodField()
    portal_uptime_percent = serializers.SerializerMethodField()
    related_jobs = serializers.SerializerMethodField()

    class Meta(JobListSerializer.Meta):
        fields = JobListSerializer.Meta.fields + [
            'confidence_score', 'confidence_factors',
            'source_url', 'last_monitored',
            'detection_timeline', 'description', 'requirements',
            'portal_status', 'portal_last_checked',
            'portal_response_dots', 'portal_uptime_percent',
            'related_jobs',
        ]

    def get_confidence_factors(self, obj):
        factors = [
            {'label': 'Official government domain', 'passed': obj.trust_score >= 60},
            {'label': 'AI classification passed', 'passed': obj.ai_classification == 'REAL'},
            {'label': 'No fraud keywords detected', 'passed': not obj.ai_red_flags},
            {'label': 'Portal currently accessible', 'passed': obj.portal and obj.portal.status == 'ONLINE'},
            {'label': 'Recruitment keywords matched', 'passed': obj.trust_score >= 50},
        ]
        return factors

    def get_last_monitored(self, obj):
        if obj.portal and obj.portal.last_checked_at:
            return obj.portal.last_checked_at.isoformat()
        return None

    def get_detection_timeline(self, obj):
        timeline = [
            {'time': obj.created_at.strftime('%H:%M'), 'event': 'Recruitment detected by monitoring engine'},
        ]
        if obj.portal and obj.portal.last_checked_at:
            timeline.append({
                'time': obj.portal.last_checked_at.strftime('%H:%M'),
                'event': 'Portal last checked',
            })
        if obj.is_verified and obj.verified_at:
            timeline.append({
                'time': obj.verified_at.strftime('%H:%M'),
                'event': 'Manually verified by admin',
            })
        return timeline

    def get_requirements(self, obj):
        if obj.requirements:
            # Split by newline or semicolon into list
            import re
            parts = re.split(r'[;\n]', obj.requirements)
            return [p.strip() for p in parts if p.strip()]
        return []

    def get_portal_status(self, obj):
        if not obj.portal:
            return 'offline'
        status_map = {
            'ONLINE': 'online', 'UP': 'online',
            'OFFLINE': 'offline', 'MAINTENANCE': 'maintenance',
        }
        return status_map.get(obj.portal.status, 'offline')

    def get_portal_last_checked(self, obj):
        if obj.portal and obj.portal.last_checked_at:
            return obj.portal.last_checked_at.isoformat()
        return None

    def get_portal_response_dots(self, obj):
        if not obj.portal or not obj.portal.response_time_ms:
            return 2
        ms = obj.portal.response_time_ms
        if ms < 1000:
            return 3
        elif ms < 3000:
            return 2
        return 1

    def get_portal_uptime_percent(self, obj):
        if obj.portal:
            return float(obj.portal.uptime_percentage)
        return 0.0

    def get_related_jobs(self, obj):
        related = Alert.objects.filter(
            agency__category=obj.agency.category,
            status=AlertStatus.APPROVED,
        ).exclude(pk=obj.pk).order_by('-created_at')[:3]
        return RelatedJobSerializer(related, many=True).data


# ─── System Status Serializers ─────────────────────────────────────────────────

class LiveFeedItemSerializer(serializers.Serializer):
    agency_name = serializers.CharField()
    agency_acronym = serializers.CharField()
    event_type = serializers.CharField()
    event_time = serializers.DateTimeField()
    time_ago = serializers.CharField()
