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
        'operator_instruction', 'is_active', 'last_checked_at'
    )
    list_filter = ('health_status', 'scrape_method', 'is_active', 'agency')
    search_fields = ('name', 'url')
    ordering = ('agency', 'name')
    actions = ['mark_manually_verified']

    @admin.display(description='Check Interval')
    def current_check_interval(self, obj):
        from apps.agencies.models import HealthStatus, PortalStatus
        if obj.health_status == HealthStatus.MANUAL_MONITORING_REQUIRED or obj.status == PortalStatus.MANUAL_MONITORING_REQUIRED:
            return "Manual (Weekly)"
        if obj.health_status == HealthStatus.CAPTCHA_PROTECTED or obj.status == PortalStatus.CAPTCHA_PROTECTED:
            return "6 hours (CAPTCHA)"
        mins = obj.check_interval_minutes
        if mins >= 60:
            hrs = mins // 60
            unit = "hour" if hrs == 1 else "hours"
            if obj.consecutive_failures >= 10:
                return f"{hrs} {unit} (DEGRADED)"
            return f"{hrs} {unit}"
        return f"{mins} mins"

    @admin.display(description='Operator Instructions / Actions')
    def operator_instruction(self, obj):
        from django.utils.html import format_html
        from apps.agencies.models import HealthStatus, PortalStatus
        if obj.health_status in [HealthStatus.CAPTCHA_PROTECTED, HealthStatus.CAPTCHA] or obj.status in [PortalStatus.CAPTCHA_PROTECTED, PortalStatus.CAPTCHA]:
            return format_html(
                "<strong>CAPTCHA PROTECTED:</strong> Verify manually by visiting <a href='{}' target='_blank'>{}</a>",
                obj.url, obj.url
            )
        if obj.health_status == HealthStatus.MANUAL_MONITORING_REQUIRED or obj.status == PortalStatus.MANUAL_MONITORING_REQUIRED:
            return format_html(
                "<strong>MANUAL MONITORING REQUIRED:</strong> Check weekly at <a href='{}' target='_blank'>{}</a>",
                obj.url, obj.url
            )
        return "-"

    @admin.action(description="Mark selected portals as manually verified (Reset failures & set Online)")
    def mark_manually_verified(self, request, queryset):
        from django.utils import timezone
        from apps.agencies.models import HealthStatus, PortalStatus
        now = timezone.now()
        updated_count = 0
        for portal in queryset:
            portal.consecutive_failures = 0
            portal.check_interval_minutes = 15
            portal.poll_interval = 900
            portal.health_status = HealthStatus.ONLINE
            portal.status = PortalStatus.ONLINE
            portal.last_successful_check_at = now
            portal.last_checked_at = now

            timestamp_str = now.strftime('%Y-%m-%d %H:%M:%S UTC')
            username = request.user.username if request.user else 'operator'
            verification_note = f"Manually verified by {username} on {timestamp_str}."
            if verification_note not in (portal.notes or ""):
                portal.notes = f"{portal.notes}\n{verification_note}".strip() if portal.notes else verification_note

            portal.save(update_fields=[
                'consecutive_failures', 'check_interval_minutes', 'poll_interval',
                'health_status', 'status', 'last_successful_check_at', 'last_checked_at', 'notes'
            ])
            updated_count += 1

        self.message_user(request, f"Successfully marked {updated_count} portal(s) as manually verified.")
