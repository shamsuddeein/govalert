"""
Notification Model : tracks Telegram message delivery.
"""
from django.db import models
from django.utils import timezone


class NotificationStatus(models.TextChoices):
    QUEUED = 'QUEUED', 'Queued'
    SENT = 'SENT', 'Sent Successfully'
    FAILED = 'FAILED', 'Failed to Deliver'
    BLOCKED = 'BLOCKED', 'User Blocked Bot'


class Notification(models.Model):
    """
    Records each individual Telegram message delivery to a user.
    One per (user, alert) pair. Used for deduplication and delivery tracking.
    """
    user = models.ForeignKey(
        'accounts.TelegramUser',
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    alert = models.ForeignKey(
        'alerts.Alert',
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True, blank=True,
        help_text="Null for broadcast messages not tied to a specific alert."
    )
    status = models.CharField(
        max_length=10,
        choices=NotificationStatus.choices,
        default=NotificationStatus.QUEUED,
        db_index=True,
    )
    telegram_message_id = models.BigIntegerField(
        null=True, blank=True,
        help_text="Telegram message ID returned by sendMessage API."
    )
    error_message = models.TextField(
        blank=True, default='',
        help_text="Error details if status = FAILED."
    )
    queued_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        unique_together = ('user', 'alert')  # Prevent duplicate sends
        ordering = ['-queued_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['status', 'queued_at'], name='idx_notif_status_queued'),
            models.Index(fields=['user', 'alert'], name='idx_notif_user_alert'),
        ]

    def __str__(self):
        return f"Notification → {self.user.display_name} | Alert #{self.alert_id} | {self.status}"

    def mark_sent(self, telegram_message_id: int):
        self.status = NotificationStatus.SENT
        self.telegram_message_id = telegram_message_id
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'telegram_message_id', 'sent_at'])

    def mark_failed(self, error: str, blocked: bool = False):
        self.status = NotificationStatus.BLOCKED if blocked else NotificationStatus.FAILED
        self.error_message = error[:1000]
        self.failed_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'failed_at'])


class PushSubscription(models.Model):
    """
    Web Push Subscription endpoint and cryptographic keys (p256dh, auth).
    Used to send instant browser push notifications for verified recruitments.
    """
    endpoint = models.URLField(max_length=1024, unique=True, db_index=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    user = models.ForeignKey(
        'accounts.WebUser',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='push_subscriptions',
    )
    is_active = models.BooleanField(default=True, db_index=True)
    user_agent = models.CharField(max_length=512, blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'push_subscriptions'
        ordering = ['-created_at']
        verbose_name = 'Push Subscription'
        verbose_name_plural = 'Push Subscriptions'

    def __str__(self):
        return f"PushSubscription → {self.endpoint[:40]}... (Active={self.is_active})"


class WebNotification(models.Model):
    """
    In-dashboard notification model for registered WebUsers.
    Stores recruitment alerts, status changes, and announcements.
    """
    user = models.ForeignKey(
        'accounts.WebUser',
        on_delete=models.CASCADE,
        related_name='dashboard_notifications',
    )
    event = models.ForeignKey(
        'alerts.RecruitmentEvent',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='dashboard_notifications',
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    notification_type = models.CharField(
        max_length=30,
        choices=[
            ('NEW_JOB', 'New Recruitment'),
            ('STATUS_CHANGE', 'Status Update'),
            ('DEADLINE_WARNING', 'Deadline Approaching'),
            ('BROADCAST', 'Official Broadcast'),
        ],
        default='NEW_JOB',
    )
    target_url = models.CharField(max_length=500, blank=True, default='')
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = 'web_notifications'
        ordering = ['-created_at']
        verbose_name = 'Web Notification'
        verbose_name_plural = 'Web Notifications'

    def __str__(self):
        return f"WebNotification → {self.user.email} | {self.title} | Read={self.is_read}"


