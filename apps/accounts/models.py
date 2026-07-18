"""
GovAlert Accounts Models
Defines TelegramUser — the primary user entity, identified by Telegram ID.
"""
from django.db import models
from django.utils import timezone as tz


class UserState(models.TextChoices):
    NEW_USER = 'NEW_USER', 'New User'
    ACTIVE = 'ACTIVE', 'Active'
    INACTIVE = 'INACTIVE', 'Inactive'
    PREMIUM = 'PREMIUM', 'Premium'
    BANNED = 'BANNED', 'Banned'


class TelegramUser(models.Model):
    """
    Represents a GovAlert bot user identified by their Telegram user ID.
    The telegram_id is the PRIMARY KEY — no surrogate key needed.
    """
    # ── Identity ──────────────────────────────────────────────────────────────
    telegram_id = models.BigIntegerField(
        primary_key=True,
        help_text="Telegram user ID — permanent, unique per user."
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, default='')
    username = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Telegram @username, nullable (not all users set one)."
    )

    # ── Status ────────────────────────────────────────────────────────────────
    state = models.CharField(
        max_length=20,
        choices=UserState.choices,
        default=UserState.NEW_USER,
        db_index=True,
    )
    is_admin = models.BooleanField(
        default=False,
        help_text="Has access to /admin bot commands."
    )
    is_super_admin = models.BooleanField(
        default=False,
        help_text="Has access to /broadcast and destructive admin commands."
    )

    # ── Preferences ───────────────────────────────────────────────────────────
    timezone = models.CharField(
        max_length=50, default='Africa/Lagos',
        help_text="User's preferred timezone for alert times."
    )
    language = models.CharField(
        max_length=10, default='en',
        help_text="Bot language preference (en / ha)."
    )
    receive_alerts = models.BooleanField(
        default=True,
        help_text="Master switch — False means user has /unsubscribed."
    )
    notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ('instant', 'Instant'),
            ('daily', 'Daily Digest'),
        ],
        default='instant',
    )

    # ── Premium ───────────────────────────────────────────────────────────────
    is_premium = models.BooleanField(default=False)
    premium_expires = models.DateTimeField(null=True, blank=True)

    # ── NDPR Consent ──────────────────────────────────────────────────────────
    consented_to_data_policy = models.BooleanField(
        default=False,
        help_text="NDPR: User tapped [I Agree] on /start."
    )
    consent_given_at = models.DateTimeField(null=True, blank=True)

    # ── Denormalised Counters ─────────────────────────────────────────────────
    alerts_received = models.PositiveIntegerField(
        default=0,
        help_text="Total alerts delivered to this user (denormalised for performance)."
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    joined_at = models.DateTimeField(
        default=tz.now,
        help_text="When user first sent /start."
    )
    last_active_at = models.DateTimeField(
        default=tz.now,
        help_text="Timestamp of their last bot interaction."
    )

    class Meta:
        db_table = 'users'
        ordering = ['-joined_at']
        verbose_name = 'Telegram User'
        verbose_name_plural = 'Telegram Users'
        indexes = [
            models.Index(fields=['state'], name='idx_users_state'),
            models.Index(fields=['is_admin'], name='idx_users_admin'),
            models.Index(fields=['joined_at'], name='idx_users_joined'),
        ]

    def __str__(self):
        name = f"{self.first_name} {self.last_name}".strip()
        uname = f" (@{self.username})" if self.username else ''
        return f"{name}{uname} [{self.telegram_id}]"

    # ── Properties ────────────────────────────────────────────────────────────
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def display_name(self) -> str:
        """First name for Telegram message personalisation."""
        return self.first_name or 'User'

    @property
    def is_active(self) -> bool:
        return self.state == UserState.ACTIVE

    @property
    def is_banned(self) -> bool:
        return self.state == UserState.BANNED

    # ── Lifecycle Methods ─────────────────────────────────────────────────────
    def mark_active(self):
        """Call when user sends any message to the bot."""
        self.state = UserState.ACTIVE
        self.last_active_at = tz.now()
        self.save(update_fields=['state', 'last_active_at'])

    def mark_inactive(self):
        """Call when Telegram reports user has blocked the bot."""
        self.state = UserState.INACTIVE
        self.save(update_fields=['state'])

    def give_consent(self):
        """Record NDPR consent when user taps [I Agree]."""
        self.consented_to_data_policy = True
        self.consent_given_at = tz.now()
        self.save(update_fields=['consented_to_data_policy', 'consent_given_at'])

    def increment_alerts(self):
        """Atomically increment alerts_received counter."""
        TelegramUser.objects.filter(pk=self.pk).update(
            alerts_received=models.F('alerts_received') + 1
        )


class WebUser(models.Model):
    """
    Web user profile extending Django's built-in User model.
    Stores saved jobs, phone number, and preferences for web application users.
    """
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='web_profile'
    )
    phone = models.CharField(max_length=20, blank=True, default='')
    categories_of_interest = models.JSONField(default=list, blank=True)
    saved_jobs = models.ManyToManyField(
        'alerts.Alert',
        blank=True,
        related_name='saved_by_users'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'web_users'
        verbose_name = 'Web User Profile'
        verbose_name_plural = 'Web User Profiles'

    def __str__(self):
        return f"WebUser: {self.user.email or self.user.username}"

