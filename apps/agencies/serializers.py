"""
Agency and Portal serializers.
"""
from rest_framework import serializers
from .models import Agency, Portal


class AgencySerializer(serializers.ModelSerializer):
    portal_count = serializers.SerializerMethodField()
    primary_domain = serializers.SerializerMethodField()

    class Meta:
        model = Agency
        fields = [
            'id', 'name', 'acronym', 'category', 'official_domains',
            'logo_url', 'description', 'subscriber_count',
            'total_alerts_sent', 'portal_count', 'primary_domain', 'is_active',
        ]

    def get_portal_count(self, obj):
        return obj.portals.filter(is_active=True).count()

    def get_primary_domain(self, obj):
        return obj.get_primary_domain()


class PortalSerializer(serializers.ModelSerializer):
    agency_acronym = serializers.CharField(source='agency.acronym', read_only=True)

    class Meta:
        model = Portal
        fields = [
            'id', 'agency', 'agency_acronym', 'name', 'url',
            'scrape_method', 'check_interval_minutes', 'is_active',
            'status', 'last_checked_at', 'consecutive_failures', 'uptime_percentage',
        ]
        read_only_fields = [
            'status', 'last_checked_at', 'consecutive_failures', 'uptime_percentage',
        ]


class PortalStatusSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the public portal status endpoint."""
    agency_name = serializers.CharField(source='agency.name', read_only=True)
    agency_acronym = serializers.CharField(source='agency.acronym', read_only=True)

    class Meta:
        model = Portal
        fields = [
            'id', 'name', 'agency_name', 'agency_acronym',
            'status', 'last_checked_at', 'uptime_percentage',
        ]
