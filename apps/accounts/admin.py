"""
GovAlert Accounts Admin
Admin registration for TelegramUser.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import TelegramUser, UserState


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = (
        'telegram_id', 'full_name_display', 'username_display',
        'state_badge', 'is_admin', 'alerts_received',
        'joined_at', 'last_active_at',
    )
    list_filter = ('state', 'is_admin', 'is_super_admin', 'is_premium', 'language')
    search_fields = ('telegram_id', 'first_name', 'last_name', 'username')
    readonly_fields = ('telegram_id', 'joined_at', 'alerts_received', 'consent_given_at')
    ordering = ('-joined_at',)

    fieldsets = (
        ('Identity', {
            'fields': ('telegram_id', 'first_name', 'last_name', 'username'),
        }),
        ('Status & Permissions', {
            'fields': ('state', 'is_admin', 'is_super_admin', 'receive_alerts'),
        }),
        ('Preferences', {
            'fields': ('timezone', 'language', 'notification_frequency'),
        }),
        ('Premium', {
            'fields': ('is_premium', 'premium_expires'),
        }),
        ('NDPR Compliance', {
            'fields': ('consented_to_data_policy', 'consent_given_at'),
        }),
        ('Stats', {
            'fields': ('alerts_received', 'joined_at', 'last_active_at'),
        }),
    )

    actions = ['ban_users', 'unban_users', 'promote_to_admin', 'demote_from_admin']

    @admin.display(description='Name')
    def full_name_display(self, obj):
        return obj.full_name

    @admin.display(description='Username')
    def username_display(self, obj):
        if obj.username:
            return format_html('<a href="https://t.me/{0}" target="_blank">@{0}</a>', obj.username)
        return '—'

    @admin.display(description='State')
    def state_badge(self, obj):
        colours = {
            UserState.ACTIVE: '#27ae60',
            UserState.INACTIVE: '#95a5a6',
            UserState.BANNED: '#e74c3c',
            UserState.PREMIUM: '#f39c12',
            UserState.NEW_USER: '#3498db',
        }
        colour = colours.get(obj.state, '#95a5a6')
        return format_html(
            '<span style="color:white;background:{};padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            colour, obj.get_state_display()
        )

    @admin.action(description='Ban selected users')
    def ban_users(self, request, queryset):
        queryset.update(state=UserState.BANNED)
        self.message_user(request, f"{queryset.count()} users banned.")

    @admin.action(description='Unban selected users')
    def unban_users(self, request, queryset):
        queryset.update(state=UserState.ACTIVE)
        self.message_user(request, f"{queryset.count()} users unbanned.")

    @admin.action(description='Promote to admin')
    def promote_to_admin(self, request, queryset):
        queryset.update(is_admin=True)
        self.message_user(request, f"{queryset.count()} users promoted to admin.")

    @admin.action(description='Remove admin privileges')
    def demote_from_admin(self, request, queryset):
        queryset.update(is_admin=False)
        self.message_user(request, f"{queryset.count()} users demoted.")
