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
    list_display = ('name', 'agency', 'url', 'scrape_method', 'check_interval_minutes', 'is_active', 'last_checked_at')
    list_filter = ('scrape_method', 'is_active', 'agency')
    search_fields = ('name', 'url')
    ordering = ('agency', 'name')
