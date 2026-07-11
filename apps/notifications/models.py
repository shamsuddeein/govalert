"""
Notification Model — tracks Telegram message delivery.
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
