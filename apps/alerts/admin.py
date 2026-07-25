from django.contrib import admin
from django.utils.html import format_html
from apps.alerts.models import Alert, AlertAction, BlogPost, RejectedDetection


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'agency', 'deadline', 'deadline_indicator',
        'event_type', 'trust_score', 'status', 'created_at'
    )
    list_filter = ('event_type', 'status', 'agency')
    search_fields = ('title', 'positions', 'deadline')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='Deadline Validation')
    def deadline_indicator(self, obj):
        from apps.monitor.parser import get_deadline_validation_status
        val = get_deadline_validation_status(obj.deadline)
        st = val['status']
        if st == 'green':
            return format_html("<span style='color: #2e7d32; font-weight: bold;'>🟢 Future ({})</span>", val.get('deadline_date') or obj.deadline)
        elif st == 'amber':
            return format_html("<span style='color: #ed6c02; font-weight: bold;'>🟡 Expiring Soon ({})</span>", val.get('deadline_date') or obj.deadline)
        elif st == 'red':
            return format_html("<span style='color: #d32f2f; font-weight: bold;'>🔴 EXPIRED ({})</span>", val.get('deadline_date') or obj.deadline)
        return format_html("<span style='color: #757575;'>⚪ Not Specified</span>")


@admin.register(RejectedDetection)
class RejectedDetectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'agency', 'portal', 'deadline', 'status', 'created_at')
    list_filter = ('status', 'agency')
    search_fields = ('title', 'reason', 'deadline')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(AlertAction)
class AlertActionAdmin(admin.ModelAdmin):
    list_display = ('user', 'alert', 'action_type', 'created_at')
    list_filter = ('action_type',)
    search_fields = ('user__first_name', 'user__username', 'alert__title')
    ordering = ('-created_at',)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'category', 'author', 'is_published', 'created_at')
    list_filter = ('is_published', 'category')
    search_fields = ('title', 'content', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('-created_at',)

