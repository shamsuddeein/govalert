from django.contrib import admin
from apps.subscriptions.models import Subscription, KeywordSubscription, TelegramJobWatch


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'agency', 'is_active', 'subscribed_at', 'unsubscribed_at')
    list_filter = ('is_active', 'agency')
    search_fields = ('user__first_name', 'user__username', 'agency__name')
    ordering = ('-subscribed_at',)
    readonly_fields = ('subscribed_at', 'unsubscribed_at')


@admin.register(KeywordSubscription)
class KeywordSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('email', 'query_text', 'is_active', 'created_at', 'last_matched_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('email', 'query_text')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'last_matched_at')


@admin.register(TelegramJobWatch)
class TelegramJobWatchAdmin(admin.ModelAdmin):
    list_display = ('user', 'alert', 'is_active', 'created_at', 'last_notified_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__first_name', 'user__username', 'alert__title', 'alert__agency__acronym')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'last_notified_at')


