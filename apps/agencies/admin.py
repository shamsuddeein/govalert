"""
Agency Admin Registration.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Agency, Portal, PortalStatus


class PortalInline(admin.TabularInline):
    """Show portals inline on the Agency change page."""
    model = Portal
    extra = 0
    fields = ('name', 'url', 'scrape_method', 'check_interval_minutes', 'is_active', 'status')
    readonly_fields = ('status', 'last_checked_at', 'consecutive_failures')
    show_change_link = True


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = (
        'acronym', 'name', 'category', 'portal_count',
        'subscriber_count', 'total_alerts_sent', 'is_active',
    )
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'acronym')
    readonly_fields = ('subscriber_count', 'total_alerts_sent', 'created_at', 'updated_at')
    inlines = [PortalInline]

    @admin.display(description='Portals')
    def portal_count(self, obj):
        return obj.portals.filter(is_active=True).count()


@admin.register(Portal)
class PortalAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'agency', 'url_display', 'scrape_method',
        'check_interval_minutes', 'status_badge', 'is_active',
        'last_checked_at', 'consecutive_failures',
    )
    list_filter = ('status', 'scrape_method', 'is_active', 'agency__category')
    search_fields = ('name', 'url', 'agency__acronym', 'agency__name')
    readonly_fields = (
        'status', 'last_checked_at', 'last_successful_check_at',
        'last_change_detected_at', 'consecutive_failures', 'uptime_percentage',
        'created_at', 'updated_at',
    )
    actions = ['force_check', 'pause_portals', 'resume_portals']

    @admin.display(description='URL')
    def url_display(self, obj):
        return format_html('<a href="{0}" target="_blank">{0}</a>', obj.url)

    @admin.display(description='Status')
    def status_badge(self, obj):
        colours = {
            PortalStatus.UP: '#27ae60',
            PortalStatus.DOWN: '#e74c3c',
            PortalStatus.UNKNOWN: '#95a5a6',
            PortalStatus.PAUSED: '#f39c12',
        }
        colour = colours.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="color:white;background:{};padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            colour, obj.status
        )

    @admin.action(description='Pause selected portals')
    def pause_portals(self, request, queryset):
        queryset.update(status=PortalStatus.PAUSED, is_active=False)
        self.message_user(request, f"{queryset.count()} portals paused.")

    @admin.action(description='Resume selected portals')
    def resume_portals(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} portals resumed.")

    @admin.action(description='Force immediate check on selected portals')
    def force_check(self, request, queryset):
        from apps.monitor.tasks import portal_check
        count = 0
        for portal in queryset:
            portal_check.delay(portal.id)
            count += 1
        self.message_user(request, f"Queued immediate check for {count} portals.")
