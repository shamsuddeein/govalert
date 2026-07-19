"""
GovAlert Agencies Models
Agency — a Nigerian government body being monitored.
Portal — a specific URL within an agency that is scraped for recruitment news.
"""
from django.db import models
from django.utils.text import slugify


class AgencyCategory(models.TextChoices):
    SECURITY = 'SECURITY', 'Security & Law Enforcement'
    FINANCE = 'FINANCE', 'Finance & Revenue'
    UTILITIES = 'UTILITIES', 'Utilities & Energy'
    HEALTH = 'HEALTH', 'Health & Pharmaceuticals'
    EDUCATION = 'EDUCATION', 'Education & Research'
    TRANSPORT = 'TRANSPORT', 'Transport & Aviation'
    STATISTICS = 'STATISTICS', 'Statistics & Data'
    JUDICIARY = 'JUDICIARY', 'Judiciary & Legal'
    OTHER = 'OTHER', 'Other'


class ScrapeMethod(models.TextChoices):
    REQUESTS = 'REQUESTS', 'HTTP Requests (BeautifulSoup)'
    PLAYWRIGHT = 'PLAYWRIGHT', 'Headless Browser (Playwright)'
    PDF = 'PDF', 'PDF Parser'
    RSS = 'RSS', 'RSS Feed'
    API = 'API', 'REST API'


class PortalPriority(models.TextChoices):
    HIGH = 'HIGH', 'High Priority (5 min)'
    MEDIUM = 'MEDIUM', 'Medium Priority (20 min)'
    LOW = 'LOW', 'Low Priority (60 min)'


class HealthStatus(models.TextChoices):
    ONLINE = 'ONLINE', 'Online / Healthy'
    OFFLINE = 'OFFLINE', 'Offline'
    BLOCKED = 'BLOCKED', 'Blocked by Firewall/Cloudflare'
    CAPTCHA = 'CAPTCHA', 'Captcha Challenge Detected'
    RATE_LIMITED = 'RATE_LIMITED', 'Rate Limited'
    MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
    UNKNOWN = 'UNKNOWN', 'Unknown'


class PortalStatus(models.TextChoices):
    ONLINE = 'ONLINE', 'Online / Up'
    OFFLINE = 'OFFLINE', 'Offline'
    BLOCKED = 'BLOCKED', 'Blocked by Firewall/Cloudflare'
    CAPTCHA = 'CAPTCHA', 'Captcha Challenge Detected'
    MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
    CHANGED_LAYOUT = 'CHANGED_LAYOUT', 'Changed Layout'
    RATE_LIMITED = 'RATE_LIMITED', 'Rate Limited'
    UNKNOWN = 'UNKNOWN', 'Unknown'
    UP = 'UP', 'Up (Deprecated)'
    DOWN = 'DOWN', 'Down (Deprecated)'
    PAUSED = 'PAUSED', 'Paused (Deprecated)'


class Agency(models.Model):
    """
    Represents a Nigerian government agency being monitored.
    Each agency may have one or more portals (URLs to scrape).
    """
    name = models.CharField(max_length=200, unique=True)
    acronym = models.CharField(
        max_length=20, unique=True,
        help_text="Short code e.g. NNPC, NCS, EFCC."
    )
    slug = models.SlugField(
        max_length=30, unique=True, blank=True,
        help_text="URL-safe identifier, auto-generated from acronym. e.g. 'nnpc', 'ncs'."
    )
    official_domains = models.JSONField(
        default=list,
        help_text="List of whitelisted official domains e.g. [\"customs.gov.ng\"]"
    )
    logo_url = models.URLField(
        blank=True, default='',
        help_text="URL to agency logo image for use in alert messages."
    )
    category = models.CharField(
        max_length=50,
        choices=AgencyCategory.choices,
        default=AgencyCategory.OTHER,
        db_index=True,
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this agency is currently being monitored."
    )
    description = models.TextField(
        blank=True, default='',
        help_text="Brief description of the agency for /agencies command."
    )

    # ── Trust & Verification ──────────────────────────────────────────────────
    vetted_score = models.PositiveIntegerField(
        default=85,
        help_text="Agency vetting score 0-100. Manual admin field."
    )
    avg_confidence_score = models.FloatField(
        default=0.0,
        help_text="Average AI confidence score across all alerts from this agency."
    )
    false_positives = models.PositiveIntegerField(
        default=0,
        help_text="Count of confirmed false-positive alerts from this agency."
    )
    scam_domains_blocked = models.PositiveIntegerField(
        default=0,
        help_text="Count of scam domains blocked for this agency."
    )

    # ── Denormalised Counters ─────────────────────────────────────────────────
    subscriber_count = models.PositiveIntegerField(
        default=0,
        help_text="Cached count of active subscribers (updated by signal)."
    )
    total_alerts_sent = models.PositiveIntegerField(
        default=0,
        help_text="Total alerts ever dispatched from this agency."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'agencies'
        ordering = ['acronym']
        verbose_name = 'Agency'
        verbose_name_plural = 'Agencies'

    def __str__(self):
        return f"{self.acronym} — {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.acronym)
        super().save(*args, **kwargs)

    def get_primary_domain(self) -> str:
        """Return the first official domain for display purposes."""
        return self.official_domains[0] if self.official_domains else ''

    def is_domain_official(self, domain: str) -> bool:
        """Check if a given domain matches any of this agency's official domains."""
        return domain in self.official_domains


class Portal(models.Model):
    """
    A specific URL within an agency that GovAlert monitors for changes.
    One agency can have multiple portals (e.g. careers page + announcements page).
    """
    agency = models.ForeignKey(
        Agency,
        on_delete=models.CASCADE,
        related_name='portals',
    )
    name = models.CharField(
        max_length=200,
        help_text="Human-readable name e.g. 'NCS Recruitment Portal'"
    )
    url = models.URLField(
        max_length=500,
        help_text="The URL to scrape."
    )
    scrape_method = models.CharField(
        max_length=20,
        choices=ScrapeMethod.choices,
        default=ScrapeMethod.REQUESTS,
    )
    check_interval_minutes = models.PositiveIntegerField(
        default=15,
        help_text="Legacy field. Use poll_interval instead (in seconds)."
    )
    poll_interval = models.PositiveIntegerField(
        default=900,
        help_text="How often to check this portal (seconds). 300=5min, 900=15min, 1800=30min, 3600=60min."
    )
    priority = models.CharField(
        max_length=10,
        choices=PortalPriority.choices,
        default=PortalPriority.MEDIUM,
        db_index=True,
        help_text="Portal priority: HIGH (5 min), MEDIUM (20 min), LOW (60 min)."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Set to False to pause monitoring without deleting.",
        db_index=True,
    )
    health_status = models.CharField(
        max_length=30,
        choices=HealthStatus.choices,
        default=HealthStatus.UNKNOWN,
        db_index=True,
        help_text="Current health status of the portal."
    )
    # Keep 'status' for backward compatibility with existing code
    status = models.CharField(
        max_length=30,
        choices=PortalStatus.choices,
        default=PortalStatus.UNKNOWN,
        db_index=True,
        help_text="Deprecated. Use health_status instead."
    )

    # ── Job/Recruitment Metadata ─────────────────────────────────────────────
    location_state = models.CharField(
        max_length=50, blank=True, default='Federal',
        help_text="Primary location/state for this portal's listings."
    )

    # ── Health Stats ──────────────────────────────────────────────────────────
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_successful_check_at = models.DateTimeField(null=True, blank=True)
    last_change_detected_at = models.DateTimeField(null=True, blank=True)
    consecutive_failures = models.PositiveIntegerField(
        default=0,
        help_text="Number of consecutive failed checks. Resets on success."
    )
    uptime_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=100.00
    )
    confidence = models.PositiveIntegerField(
        default=100,
        help_text="Scraping reliability score (0-100). Decreases on failures."
    )
    response_time_ms = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Last recorded response time in milliseconds."
    )

    # ── Metadata ──────────────────────────────────────────────────────────────
    tags = models.JSONField(
        default=list,
        help_text="List of tags/categories: ['Security', 'Finance', 'Education', etc.]"
    )
    country = models.CharField(
        max_length=2,
        default='NG',
        help_text="Country code (NG=Nigeria, GH=Ghana, etc.)"
    )
    notes = models.TextField(
        blank=True, default='',
        help_text="Internal admin notes about this portal."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'portals'
        ordering = ['agency__acronym', 'name']
        verbose_name = 'Portal'
        verbose_name_plural = 'Portals'
        indexes = [
            models.Index(fields=['is_active', 'status'], name='idx_portals_active_status'),
            models.Index(fields=['agency', 'is_active'], name='idx_portals_agency_active'),
            # Monitoring loop query: filter(is_active=True, priority='HIGH') runs every 5 min.
            models.Index(fields=['is_active', 'priority'], name='idx_portals_active_priority'),
        ]

    def __str__(self):
        return f"{self.agency.acronym} — {self.name} ({self.url})"

    @property
    def is_up(self) -> bool:
        # Use health_status (current field). status is deprecated but still written in sync.
        return self.health_status in [HealthStatus.ONLINE]

    @property
    def needs_check(self) -> bool:
        """True if this portal is active and eligible for a new check."""
        return self.is_active and self.health_status not in [
            HealthStatus.MAINTENANCE,
            # PAUSED and DOWN are deprecated PortalStatus values that don't exist
            # in HealthStatus, so checking health_status is sufficient here.
        ]
