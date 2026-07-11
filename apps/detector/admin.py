from django.contrib import admin
from apps.detector.models import FakeDomain, AlertReport


@admin.register(FakeDomain)
class FakeDomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'agency', 'detected_at', 'confirmed_by_admin', 'report_count')
    list_filter = ('confirmed_by_admin', 'agency')
    search_fields = ('domain',)
    ordering = ('-detected_at',)


@admin.register(AlertReport)
class AlertReportAdmin(admin.ModelAdmin):
    list_display = ('alert', 'user', 'reason', 'reviewed', 'created_at')
    list_filter = ('reason', 'reviewed')
    search_fields = ('user__first_name', 'user__username', 'alert__title')
    ordering = ('-created_at',)
