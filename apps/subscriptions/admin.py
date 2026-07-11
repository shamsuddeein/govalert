from django.contrib import admin
from apps.subscriptions.models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'agency', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'agency')
    search_fields = ('user__first_name', 'user__username', 'agency__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
