"""
GovAlert API v1 — Serializers for agencies, jobs (alerts), and system status.
"""
from django.utils import timezone
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
    description = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

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
        ).exclude(status=AlertStatus.SUPERSEDED).count()


    def get_description(self, obj):
        desc = obj.description or ''
        import re
        sentences = re.split(r'(?<=[.!?])\s+', desc)
        truncated = ' '.join(sentences[:2]).strip()
        return truncated

    def get_category(self, obj):
        mapping = {
            'SECURITY': 'Security',
            'FINANCE': 'Finance',
            'UTILITIES': 'Utilities',
            'HEALTH': 'Health',
            'EDUCATION': 'Education',
            'TRANSPORT': 'Transport',
            'STATISTICS': 'Statistics',
            'JUDICIARY': 'Judiciary',
            'OTHER': 'Other',
        }
        return mapping.get(obj.category, obj.category)


class AgencyDetailSerializer(AgencyListSerializer):
    """Full serializer for GET /api/v1/agencies/{slug}/"""
    description = serializers.CharField(read_only=True)
    monitoring_interval_minutes = serializers.SerializerMethodField()
    uptime_percent = serializers.SerializerMethodField()
    total_recruitments_detected = serializers.IntegerField(source='total_alerts_sent', read_only=True)
    last_update = serializers.SerializerMethodField()
    recruitment_history = serializers.SerializerMethodField()
    last_10_checks = serializers.SerializerMethodField()
    total_checks = serializers.SerializerMethodField()
    last_offline_at = serializers.SerializerMethodField()
    last_offline_duration_minutes = serializers.SerializerMethodField()

    class Meta(AgencyListSerializer.Meta):
        fields = AgencyListSerializer.Meta.fields + [
            'monitoring_interval_minutes', 'uptime_percent',
            'total_recruitments_detected', 'last_update',
            'recruitment_history', 'last_10_checks', 'total_checks',
            'last_offline_at', 'last_offline_duration_minutes',
            'avg_confidence_score', 'false_positives', 'scam_domains_blocked',
            'official_domains',
        ]

    def get_total_checks(self, obj):
        portal = self._primary_portal(obj)
        if not portal:
            return 0
        return Snapshot.objects.filter(portal=portal).count()

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
        alert = Alert.objects.filter(
            agency=obj, status=AlertStatus.APPROVED
        ).order_by('-created_at').first()
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
        portal = self._primary_portal(obj)
        if not portal:
            return None
        
        snaps = list(Snapshot.objects.filter(portal=portal).order_by('-created_at')[:20])
        if not snaps:
            return None
        
        # Current status is offline
        if snaps[0].status_code is not None and snaps[0].status_code >= 400:
            first_offline = snaps[0]
            for s in snaps:
                if s.status_code is not None and s.status_code >= 400:
                    first_offline = s
                else:
                    break
            duration = timezone.now() - first_offline.created_at
            return int(duration.total_seconds() // 60)
        
        # Find last offline check
        offline_idx = -1
        for i, s in enumerate(snaps):
            if s.status_code is not None and s.status_code >= 400:
                offline_idx = i
                break
        
        if offline_idx != -1:
            online_before = snaps[offline_idx - 1] if offline_idx > 0 else None
            first_offline = snaps[offline_idx]
            for s in snaps[offline_idx:]:
                if s.status_code is not None and s.status_code >= 400:
                    first_offline = s
                else:
                    break
            if online_before:
                duration = online_before.created_at - first_offline.created_at
                return int(duration.total_seconds() // 60)
            else:
                duration = timezone.now() - first_offline.created_at
                return int(duration.total_seconds() // 60)
                
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


# ─── User & Auth Serializers ───────────────────────────────────────────────────

from django.contrib.auth.models import User
from apps.accounts.models import WebUser


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def create(self, validated_data):
        name = validated_data['name'].strip()
        email = validated_data['email'].lower().strip()
        password = validated_data['password']

        parts = name.split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''

        # Use email prefix or unique string for username
        username = email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        WebUser.objects.create(user=user)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    phone = serializers.CharField(required=False, allow_blank=True)
    categories_of_interest = serializers.JSONField(required=False)

    class Meta:
        model = WebUser
        fields = ['email', 'first_name', 'last_name', 'phone', 'categories_of_interest']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if 'first_name' in user_data:
            instance.user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            instance.user.last_name = user_data['last_name']
        if user_data:
            instance.user.save()

        instance.phone = validated_data.get('phone', instance.phone)
        if 'categories_of_interest' in validated_data:
            instance.categories_of_interest = validated_data['categories_of_interest']
        instance.save()
        return instance


class AdminAlertDetailSerializer(serializers.ModelSerializer):
    agency = serializers.SerializerMethodField()
    portal = serializers.SerializerMethodField()
    agency_name = serializers.CharField(source='agency.name', read_only=True, default='')
    agency_acronym = serializers.CharField(source='agency.acronym', read_only=True, default='')
    portal_name = serializers.CharField(source='portal.name', read_only=True, default='')
    portal_url = serializers.CharField(source='portal.url', read_only=True, default='')
    verified_by = serializers.SerializerMethodField()
    trust_score_overridden_by = serializers.SerializerMethodField()
    recruitment_event = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = [
            'id', 'title', 'agency', 'portal', 'agency_name', 'agency_acronym',
            'portal_name', 'portal_url', 'deadline', 'positions',
            'requirements', 'source_url', 'content_excerpt', 'trust_score',
            'trust_score_overridden_by', 'trust_score_overridden_at',
            'ai_classification', 'ai_confidence', 'ai_red_flags', 'status',
            'is_verified', 'verified_by', 'verified_at', 'admin_notes',
            'report_count', 'created_at', 'recruitment_event',
        ]

    def get_agency(self, obj):
        if obj.agency:
            return {'name': obj.agency.name, 'acronym': obj.agency.acronym}
        return None

    def get_portal(self, obj):
        if obj.portal:
            return {'name': obj.portal.name, 'url': obj.portal.url}
        return None

    def get_verified_by(self, obj):
        return obj.verified_by.username if obj.verified_by else None

    def get_trust_score_overridden_by(self, obj):
        return obj.trust_score_overridden_by.username if obj.trust_score_overridden_by else None

    def get_recruitment_event(self, obj):
        if obj.recruitment_event:
            return {
                'event_id': obj.recruitment_event.event_id,
                'fingerprint': obj.recruitment_event.fingerprint,
                'event_type': obj.recruitment_event.event_type,
            }
        return None


# ─── Custom DRF Admin Serializers for Agency and Portal ───────────────────────

class AdminAgencySerializer(serializers.ModelSerializer):
    portal_count = serializers.SerializerMethodField()
    alert_count = serializers.SerializerMethodField()

    class Meta:
        model = Agency
        fields = [
            'id', 'name', 'acronym', 'slug', 'official_domains', 'logo_url',
            'category', 'is_active', 'description', 'vetted_score',
            'avg_confidence_score', 'false_positives', 'scam_domains_blocked',
            'subscriber_count', 'total_alerts_sent', 'portal_count',
            'alert_count', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'slug', 'avg_confidence_score', 'subscriber_count',
            'total_alerts_sent', 'created_at', 'updated_at',
        ]

    def get_portal_count(self, obj):
        return obj.portals.count()

    def get_alert_count(self, obj):
        return obj.alerts.count()


class SnapshotSerializer(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Snapshot
        fields = [
            'id', 'portal', 'content_hash', 'status_code', 'response_time_ms',
            'scrape_method_used', 'has_change', 'triggered_alert',
            'created_at', 'timestamp',
        ]


class AdminPortalSerializer(serializers.ModelSerializer):
    agency_name = serializers.CharField(source='agency.name', read_only=True, default='')
    agency_acronym = serializers.CharField(source='agency.acronym', read_only=True, default='')

    class Meta:
        model = Portal
        fields = [
            'id', 'agency', 'agency_name', 'agency_acronym', 'name', 'url',
            'scrape_method', 'check_interval_minutes', 'poll_interval',
            'priority', 'is_active', 'health_status', 'status', 'location_state',
            'last_checked_at', 'last_successful_check_at', 'last_change_detected_at',
            'consecutive_failures', 'uptime_percentage', 'confidence',
            'response_time_ms', 'tags', 'country', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'health_status', 'status', 'last_checked_at', 'last_successful_check_at',
            'last_change_detected_at', 'consecutive_failures', 'uptime_percentage',
            'confidence', 'response_time_ms', 'created_at', 'updated_at',
        ]


class AdminPortalDetailSerializer(AdminPortalSerializer):
    recent_snapshots = serializers.SerializerMethodField()

    class Meta(AdminPortalSerializer.Meta):
        fields = AdminPortalSerializer.Meta.fields + ['recent_snapshots']

    def get_recent_snapshots(self, obj):
        snapshots = obj.snapshots.order_by('-created_at')[:10]
        return SnapshotSerializer(snapshots, many=True).data




