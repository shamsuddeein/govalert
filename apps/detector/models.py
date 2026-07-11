"""
Detector App Models — FakeDomain and AlertReport.
"""
from django.db import models
from django.utils import timezone


class FakeDomain(models.Model):
    """
    Permanent blacklist of confirmed fake/scam recruitment domains.
    Once added, any alert from this domain is immediately discarded.
    """
    domain = models.CharField(
        max_length=255, unique=True,
        help_text="Root domain e.g. 'customs-recruitment-2025.com'"
    )
    agency = models.ForeignKey(
        'agencies.Agency',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='fake_domains',
        help_text="Agency this domain was pretending to be."
    )
    detected_at = models.DateTimeField(default=timezone.now)
    confirmed_by_admin = models.BooleanField(
        default=False,
        help_text="Admin has manually confirmed this is fake."
    )
    confirmed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='confirmed_fake_domains',
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    report_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of user reports that flagged this domain."
    )
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'fake_domains'
        ordering = ['-detected_at']
        verbose_name = 'Fake Domain'
        verbose_name_plural = 'Fake Domains'

    def __str__(self):
        confirmed = ' ✓ Admin Confirmed' if self.confirmed_by_admin else ' (pending)'
        agency = f' → impersonating {self.agency.acronym}' if self.agency else ''
        return f"{self.domain}{agency}{confirmed}"


class ReportReason(models.TextChoices):
    PAYMENT_REQUESTED = 'PAYMENT', 'It asked me to pay'
    WRONG_WEBSITE = 'WRONG_URL', 'Wrong or unofficial website'
    NOT_OFFICIAL = 'NOT_OFFICIAL', 'Not from the official agency source'
    SUSPICIOUS_CONTENT = 'SUSPICIOUS', 'Content looks suspicious'
    OTHER = 'OTHER', 'Other reason'


class AlertReport(models.Model):
    """
    A user-submitted report flagging an alert as potentially fake.
    3+ reports on the same alert triggers urgent admin review.
    """
    alert = models.ForeignKey(
        'alerts.Alert',
        on_delete=models.CASCADE,
        related_name='reports',
    )
    user = models.ForeignKey(
        'accounts.TelegramUser',
        on_delete=models.CASCADE,
        related_name='reports_submitted',
    )
    reason = models.CharField(
        max_length=20,
        choices=ReportReason.choices,
        default=ReportReason.OTHER,
    )
    notes = models.CharField(max_length=500, blank=True, default='')
    reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_reports',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'alert_reports'
        unique_together = ('alert', 'user')
        ordering = ['-created_at']
        verbose_name = 'Alert Report'
        verbose_name_plural = 'Alert Reports'

    def __str__(self):
        return f"Report by {self.user.display_name} on Alert #{self.alert_id} — {self.reason}"
