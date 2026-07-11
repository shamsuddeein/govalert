from django.contrib import admin
from apps.alerts.models import Alert, AlertAction


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'agency', 'event_type', 'trust_score', 'status', 'created_at')
    list_filter = ('event_type', 'status', 'agency')
    search_fields = ('title', 'positions', 'deadline')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AlertAction)
class AlertActionAdmin(admin.ModelAdmin):
    list_display = ('user', 'alert', 'action_type', 'created_at')
    list_filter = ('action_type',)
    search_fields = ('user__first_name', 'user__username', 'alert__title')
    ordering = ('-created_at',)
