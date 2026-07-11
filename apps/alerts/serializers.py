"""
Alert serializers.
"""
from rest_framework import serializers
from .models import Alert


class AlertSerializer(serializers.ModelSerializer):
    agency_name = serializers.CharField(source='agency.name', read_only=True)
    agency_acronym = serializers.CharField(source='agency.acronym', read_only=True)
    agency_logo = serializers.URLField(source='agency.logo_url', read_only=True)
    trust_category = serializers.CharField(read_only=True)

    class Meta:
        model = Alert
        fields = [
            'id', 'agency_name', 'agency_acronym', 'agency_logo',
            'event_type', 'title', 'positions', 'deadline', 'requirements',
            'source_url', 'trust_score', 'trust_category',
            'ai_classification', 'ai_confidence',
            'status', 'is_verified',
            'recipients_count', 'created_at',
        ]
