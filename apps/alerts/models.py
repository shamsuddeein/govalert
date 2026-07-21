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


class EventStatus(models.TextChoices):
    """Status of a RecruitmentEvent: whether it's new, an update, or closed."""
    NEW = 'NEW', 'New Recruitment Detected'
    UPDATED = 'UPDATED', 'Existing Recruitment Updated'
    CLOSED = 'CLOSED', 'Recruitment Closed'


class RecruitmentEvent(models.Model):
    """
    Represents a raw change/recruitment event detected by the monitor.
    Separated from user-facing Alerts to allow auditing and multi-channel notifications.
    """
    event_id = models.CharField(
        max_length=50, unique=True,
        help_text="Unique event code, e.g. evt_20260711_000412"
    )
    fingerprint = models.CharField(
        max_length=64, db_index=True,
        help_text="SHA-256 fingerprint of the recruitment identity. Multiple events may share it as an update chain."
    )
    status = models.CharField(
        max_length=20,
        choices=EventStatus.choices,
        default=EventStatus.NEW,
        db_index=True,
        help_text="Whether this is a new recruitment, an update, or closure."
    )
    previous_event = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='updates',
        help_text="If status=UPDATED, link to the previous event."
    )
    portal = models.ForeignKey(
        'agencies.Portal',
        on_delete=models.CASCADE,
        related_name='events'
    )
    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices,
        default=EventType.RECRUITMENT_OPEN
    )
    content_hash = models.CharField(max_length=64, blank=True, default='')
    title = models.CharField(
        max_length=500, blank=True, default='',
        help_text="Recruitment title for display and comparison."
    )
    deadline = models.CharField(
        max_length=100, blank=True, default='',
        help_text="Application deadline."
    )
    positions = models.TextField(
        blank=True, default='',
        help_text="Positions available."
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'recruitment_events'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_id} — {self.status} — {self.event_type} — {self.portal.agency.acronym}"


class DecisionLog(models.Model):
    """
    Audit log detailing why a recruitment event was classified the way it was.
    """
    event = models.OneToOneField(
        RecruitmentEvent,
        on_delete=models.CASCADE,
        related_name='decision_log'
    )
    rule_matches = models.JSONField(
        default=list, blank=True,
        help_text="List of rules matched during classification."
    )
    gemini_score = models.FloatField(
        default=0.0,
        help_text="Gemini confidence score (0.0 to 1.0)"
    )
    final_trust = models.IntegerField(
        default=0,
        help_text="Calculated trust score (0 to 100)"
    )
    reason = models.TextField(
        blank=True, default='',
        help_text="Human readable summary of the decision."
    )
    title = models.CharField(
        max_length=500, blank=True, default='',
        help_text="Recruitment title at time of decision."
    )
    deadline = models.CharField(
        max_length=100, blank=True, default='',
        help_text="Deadline at time of decision."
    )
    positions = models.TextField(
        blank=True, default='',
        help_text="Positions at time of decision."
    )
    changes = models.JSONField(
        default=dict, blank=True,
        help_text="Fields that changed compared to previous event."
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'decision_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"Decision for {self.event.event_id} — Trust: {self.final_trust}"


class Alert(models.Model):
    """
    A single detected recruitment event. Created by the detection engine.
    May be held for admin review if trust score is low.
    """
    recruitment_event = models.ForeignKey(
        RecruitmentEvent,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='alerts'
    )
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
    trust_score_overridden_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='trust_score_overridden_alerts',
        help_text="Django staff user who manually override the trust score."
    )
    trust_score_overridden_at = models.DateTimeField(null=True, blank=True)


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
            # Primary public API query: filter(status='APPROVED').order_by('-created_at')
            # Without this, every /api/v1/jobs/ request does a full table scan.
            models.Index(fields=['status', 'created_at'], name='idx_alerts_status_date'),
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
