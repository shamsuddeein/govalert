from django.contrib import admin
from apps.agencies.models import Agency, Portal


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'acronym', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'acronym')
    ordering = ('name',)


@admin.register(Portal)
class PortalAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'agency', 'url', 'scrape_method', 'check_interval_minutes',
        'current_check_interval', 'consecutive_failures', 'health_status',
        'is_active', 'last_checked_at'
    )
    list_filter = ('health_status', 'scrape_method', 'is_active', 'agency')
    search_fields = ('name', 'url')
    ordering = ('agency', 'name')

    @admin.display(description='Check Interval')
    def current_check_interval(self, obj):
        mins = obj.check_interval_minutes
        if mins >= 60:
            hrs = mins // 60
            unit = "hour" if hrs == 1 else "hours"
            if obj.consecutive_failures >= 10:
                return f"{hrs} {unit} (DEGRADED)"
            return f"{hrs} {unit}"
        return f"{mins} mins"
