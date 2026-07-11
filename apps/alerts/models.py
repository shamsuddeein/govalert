"""
GovAlert Alert Model
An Alert represents a detected recruitment event on a government portal.
"""
from django.db import models
from django.utils import timezone


class EventType(models.TextChoices):
    RECRUITMENT_OPEN = 'RECRUITMENT_OPEN', 'Recruitment Open'
    RECRUITMENT_CLOSED = 'RECRUITMENT_CLOSED', 'Recruitment Closed'
    DEADLINE_EXTENDED = 'DEADLINE_EXTENDED', 'Deadline Extended'
    SHORTLIST_PUBLISHED = 'SHORTLIST_PUBLISHED', 'Shortlist Published'
    PORTAL_DOWN = 'PORTAL_DOWN', 'Portal Down'
    PORTAL_UP = 'PORTAL_UP', 'Portal Up'
    FAKE_PORTAL_DETECTED = 'FAKE_PORTAL_DETECTED', 'Fake Portal Detected'
    BROADCAST = 'BROADCAST', 'Admin Broadcast'
    OTHER = 'OTHER', 'Other Update'


class AlertStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Admin Review'
    APPROVED = 'APPROVED', 'Approved — Sent to Users'
    REJECTED = 'REJECTED', 'Rejected — Marked Fake'
    HELD = 'HELD', 'Held for Admin Review'


class Alert(models.Model):
    """
    A single detected recruitment event. Created by the detection engine.
    May be held for admin review if trust score is low.
    """
    agency = models.ForeignKey(
        'agencies.Agency',
        on_delete=models.CASCADE,
        related_name='alerts',
    )
    portal = models.ForeignKey(
        'agencies.Portal',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='alerts',
    )

    # ── Event Data ────────────────────────────────────────────────────────────
    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices,
        default=EventType.RECRUITMENT_OPEN,
        db_index=True,
    )
    title = models.CharField(
        max_length=500,
        help_text="Alert headline e.g. 'NCS 2025 Recruitment Portal Now Open'"
    )
    positions = models.TextField(
        blank=True, default='',
        help_text="Extracted positions/roles from the page."
    )
    deadline = models.CharField(
        max_length=100, blank=True, default='',
        help_text="Extracted deadline string e.g. '28 February 2025'"
    )
    requirements = models.TextField(
        blank=True, default='',
        help_text="Extracted requirements (WAEC, SSCE, degree level, etc.)"
    )
    source_url = models.URLField(
        max_length=500,
        help_text="URL where the recruitment was detected."
    )
    content_excerpt = models.TextField(
        blank=True, default='',
        help_text="First 2000 characters of the page content at time of detection."
    )

    # ── Trust / Fake Detection ────────────────────────────────────────────────
    trust_score = models.IntegerField(
        default=0,
        help_text="Trust score 0–100. Computed by the fake detection engine."
    )
    ai_classification = models.CharField(
        max_length=20, blank=True, default='',
        help_text="Gemini AI result: REAL | FAKE | UNCERTAIN"
    )
    ai_confidence = models.IntegerField(
        default=0,
        help_text="Gemini AI confidence 0–100."
    )
    ai_red_flags = models.JSONField(
        default=list, blank=True,
        help_text="List of red flags identified by Gemini AI."
    )

    # ── Admin Workflow ────────────────────────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=AlertStatus.choices,
        default=AlertStatus.PENDING,
        db_index=True,
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Manually verified as real by an admin."
    )
    verified_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='verified_alerts',
        help_text="Django admin user who verified this alert."
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, default='')

    # ── Delivery ──────────────────────────────────────────────────────────────
    recipients_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of users this alert was sent to."
    )
    sent_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When dispatch began."
    )

    # ── Report Tracking ───────────────────────────────────────────────────────
    report_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of user fake reports on this alert."
    )

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'alerts'
        ordering = ['-created_at']
        verbose_name = 'Alert'
        verbose_name_plural = 'Alerts'
        indexes = [
            models.Index(fields=['agency', 'created_at'], name='idx_alerts_agency_date'),
            models.Index(fields=['event_type', 'status'], name='idx_alerts_type_status'),
            models.Index(fields=['trust_score'], name='idx_alerts_trust'),
        ]

    def __str__(self):
        return f"[{self.agency.acronym}] {self.event_type} — Trust {self.trust_score} — {self.created_at.date()}"

    @property
    def trust_category(self) -> str:
        if self.trust_score >= 90:
            return 'VERIFIED OFFICIAL'
        elif self.trust_score >= 70:
            return 'LIKELY OFFICIAL'
        elif self.trust_score >= 50:
            return 'UNCONFIRMED'
        elif self.trust_score >= 30:
            return 'SUSPICIOUS'
        return 'FLAGGED AS FAKE'


class AlertActionType(models.TextChoices):
    SAVED = 'SAVED', 'Saved'
    REPORTED = 'REPORTED', 'Reported as Fake'
    SHARED = 'SHARED', 'Shared'


class AlertAction(models.Model):
    """
    Records user actions on alerts: saves, reports, shares.
    Used for fake detection escalation and user engagement tracking.
    """
    user = models.ForeignKey(
        'accounts.TelegramUser',
        on_delete=models.CASCADE,
        related_name='alert_actions',
    )
    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name='actions',
    )
    action_type = models.CharField(
        max_length=20,
        choices=AlertActionType.choices,
    )
    report_reason = models.CharField(
        max_length=200, blank=True, default='',
        help_text="Reason given when action_type = REPORTED."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'alert_actions'
        unique_together = ('user', 'alert', 'action_type')
        verbose_name = 'Alert Action'
        verbose_name_plural = 'Alert Actions'

    def __str__(self):
        return f"{self.user.display_name} {self.action_type} → Alert #{self.alert_id}"
