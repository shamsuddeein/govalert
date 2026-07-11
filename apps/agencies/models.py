"""
GovAlert Agencies Models
Agency — a Nigerian government body being monitored.
Portal — a specific URL within an agency that is scraped for recruitment news.
"""
from django.db import models
from django.contrib.postgres.fields import ArrayField


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
    HTTP = 'HTTP', 'Simple HTTP (BeautifulSoup)'
    PLAYWRIGHT = 'PLAYWRIGHT', 'Headless Browser (Playwright)'
    PDF = 'PDF', 'PDF Parser'


class PortalStatus(models.TextChoices):
    UP = 'UP', 'Up'
    DOWN = 'DOWN', 'Down'
    UNKNOWN = 'UNKNOWN', 'Unknown'
    PAUSED = 'PAUSED', 'Paused (maintenance)'


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
    official_domains = ArrayField(
        models.CharField(max_length=100),
        help_text="Array of whitelisted official domains e.g. ['customs.gov.ng']"
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
        default=ScrapeMethod.HTTP,
    )
    check_interval_minutes = models.PositiveIntegerField(
        default=15,
        help_text="How often to check this portal (minutes). Default: 15."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Set to False to pause monitoring without deleting."
    )
    status = models.CharField(
        max_length=10,
        choices=PortalStatus.choices,
        default=PortalStatus.UNKNOWN,
        db_index=True,
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

    # ── Notes ─────────────────────────────────────────────────────────────────
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
        ]

    def __str__(self):
        return f"{self.agency.acronym} — {self.name} ({self.url})"

    @property
    def is_up(self) -> bool:
        return self.status == PortalStatus.UP

    @property
    def needs_check(self) -> bool:
        """True if this portal is active and eligible for a new check."""
        return self.is_active and self.status != PortalStatus.PAUSED
