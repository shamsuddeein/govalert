"""
GovAlert Subscriptions Model
A Subscription links a TelegramUser to an Agency.
Users are auto-subscribed to ALL agencies on /start.
"""
from django.db import models
from django.utils import timezone


class Subscription(models.Model):
    """
    Represents a user's subscription to a specific agency's alerts.
    Created automatically for all agencies when user sends /start.
    """
    user = models.ForeignKey(
        'accounts.TelegramUser',
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    agency = models.ForeignKey(
        'agencies.Agency',
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="False = user unsubscribed from this specific agency."
    )
    subscribed_at = models.DateTimeField(default=timezone.now)
    unsubscribed_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Timestamp when user last unsubscribed from this agency."
    )

    class Meta:
        db_table = 'subscriptions'
        unique_together = ('user', 'agency')
        ordering = ['agency__acronym']
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        indexes = [
            models.Index(fields=['user', 'is_active'], name='idx_subs_user_active'),
            models.Index(fields=['agency', 'is_active'], name='idx_subs_agency_active'),
        ]

    def __str__(self):
        status = 'active' if self.is_active else 'inactive'
        return f"{self.user.display_name} → {self.agency.acronym} ({status})"

    def unsubscribe(self):
        """Deactivate this subscription."""
        self.is_active = False
        self.unsubscribed_at = timezone.now()
        self.save(update_fields=['is_active', 'unsubscribed_at'])

    def resubscribe(self):
        """Re-activate this subscription."""
        self.is_active = True
        self.unsubscribed_at = None
        self.save(update_fields=['is_active', 'unsubscribed_at'])


class KeywordSubscription(models.Model):
    """
    Captured search keyword subscription for instant email notifications when
    a matching recruitment alert is approved.
    """
    email = models.EmailField()
    query_text = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_matched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'keyword_subscriptions'
        ordering = ['-created_at']
        verbose_name = 'Keyword Subscription'
        verbose_name_plural = 'Keyword Subscriptions'
        indexes = [
            models.Index(fields=['email', 'is_active'], name='idx_kw_sub_email_active'),
            models.Index(fields=['is_active'], name='idx_kw_sub_active'),
        ]

    def __str__(self):
        return f"{self.email} → '{self.query_text}'"

