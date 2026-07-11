from django.contrib import admin
from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'alert', 'status', 'queued_at', 'sent_at')
    list_filter = ('status',)
    search_fields = ('user__first_name', 'user__username', 'alert__title')
    ordering = ('-queued_at',)
    readonly_fields = ('queued_at', 'sent_at')
