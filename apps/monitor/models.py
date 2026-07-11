"""
Monitor App Models — Snapshot and PortalHealthLog.
"""
from django.db import models
from django.utils import timezone


class Snapshot(models.Model):
    """
    Stores a point-in-time snapshot of a portal's content.
    The content_hash is used for change detection (compare with previous).
    Raw content is retained for 30 days then pruned to save DB space.
    """
    portal = models.ForeignKey(
        'agencies.Portal',
        on_delete=models.CASCADE,
        related_name='snapshots',
    )
    content_hash = models.CharField(
        max_length=32,
        help_text="MD5 hash of normalised page content."
    )
    raw_content = models.TextField(
        blank=True, default='',
        help_text="Normalised page text at time of snapshot."
    )
    status_code = models.IntegerField(
        null=True, blank=True,
        help_text="HTTP status code of the response."
    )
    response_time_ms = models.IntegerField(
        null=True, blank=True,
        help_text="How long the request took in milliseconds."
    )
    scrape_method_used = models.CharField(max_length=20, blank=True, default='')
    has_change = models.BooleanField(
        default=False,
        help_text="True if this snapshot differs from the previous one."
    )
    triggered_alert = models.BooleanField(
        default=False,
        help_text="True if this snapshot triggered an alert."
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = 'snapshots'
        ordering = ['-created_at']
        verbose_name = 'Snapshot'
        verbose_name_plural = 'Snapshots'
        indexes = [
            models.Index(fields=['portal', 'created_at'], name='idx_snapshots_portal_date'),
            models.Index(fields=['content_hash'], name='idx_snapshots_hash'),
        ]

    def __str__(self):
        flag = ' ⚡ CHANGE' if self.has_change else ''
        return f"Snapshot #{self.pk} — {self.portal} — {self.created_at.strftime('%Y-%m-%d %H:%M')}{flag}"


class PortalHealthLog(models.Model):
    """
    Daily health summary for a portal.
    Aggregated from individual Snapshots. Used for uptime charts.
    """
    portal = models.ForeignKey(
        'agencies.Portal',
        on_delete=models.CASCADE,
        related_name='health_logs',
    )
    date = models.DateField(db_index=True)
    checks_total = models.PositiveIntegerField(default=0)
    checks_successful = models.PositiveIntegerField(default=0)
    checks_failed = models.PositiveIntegerField(default=0)
    avg_response_time_ms = models.IntegerField(null=True, blank=True)
    uptime_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    changes_detected = models.PositiveIntegerField(default=0)
    alerts_triggered = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'portal_health_logs'
        unique_together = ('portal', 'date')
        ordering = ['-date']
        verbose_name = 'Portal Health Log'
        verbose_name_plural = 'Portal Health Logs'

    def __str__(self):
        return f"{self.portal.agency.acronym} — {self.date} — {self.uptime_percentage}% uptime"
