import time
import logging
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Q, Sum
from storage.backup import export_and_backup
from celery import shared_task

logger = logging.getLogger(__name__)

# Number of consecutive failures before a portal is automatically suspended.
# Covers DNS failures, persistent timeouts, and dead domains. Operators can
# re-enable a portal by setting is_active=True via the Django admin.
MAX_CONSECUTIVE_FAILURES = 10


@shared_task(
    bind=True,
    ignore_result=True,
    soft_time_limit=120,   # 2 min soft: triggers SoftTimeLimitExceeded so we can clean up
    time_limit=150,        # 2.5 min hard: SIGKILL if soft limit handler hangs
    max_retries=3,
    default_retry_delay=30,  # seconds between retries
)
def portal_check(self, portal_id: int):
    """
    Check a single portal for changes.
    If changes are detected and recruitment keywords match, creates an alert.

    Design notes:
    - Uses a single portal.save() per execution path to avoid redundant DB writes.
    - Auto-suspends portals that have failed MAX_CONSECUTIVE_FAILURES times in a
      row so dead domains don't waste the scrape budget indefinitely.
    - Logs a content snippet when a change is detected but no keywords matched,
      allowing operators to audit whether the keyword list needs expanding.
    - Uptime is computed with a single DB aggregate, not a Python loop over rows.
    - soft_time_limit/time_limit guard against hung Playwright sessions.
    """
    from apps.agencies.models import Portal, PortalStatus, HealthStatus
    from apps.monitor.scraper import scrape_portal
    from apps.monitor.parser import clean_html_to_text, analyze_diff, match_recruitment_keywords
    from apps.monitor.models import Snapshot
    from apps.alerts.services import create_alert_from_scrape
    from core.utils import compute_content_hash
    from core.exceptions import ScraperException
    from celery.exceptions import SoftTimeLimitExceeded

    try:
        portal = Portal.objects.get(pk=portal_id)
    except Portal.DoesNotExist:
        logger.error(f"Portal {portal_id} not found.")
        return

    logger.info(f"Checking portal: {portal.name} ({portal.url}) using {portal.scrape_method}...")

    is_firewall_blocked = (
        portal.health_status == HealthStatus.BLOCKED or
        portal.status == PortalStatus.BLOCKED or
        'joinnigeriannavy.com' in portal.url.lower() or
        'fedcivilservice.gov.ng' in portal.url.lower()
    )

    from core.plugins import get_scraper_backend

    try:
        scraper = get_scraper_backend(portal.scrape_method)
        if hasattr(scraper, 'scrape'):
            import inspect
            sig = inspect.signature(scraper.scrape)
            if 'is_blocked' in sig.parameters:
                content, status_code, response_time_ms = scraper.scrape(portal.url, is_blocked=is_firewall_blocked)
            else:
                content, status_code, response_time_ms = scraper.scrape(portal.url)
        else:
            from apps.monitor.scraper import scrape_portal as raw_scrape_portal
            content, status_code, response_time_ms = raw_scrape_portal(portal.url, method=portal.scrape_method, is_blocked=is_firewall_blocked)

        content = content.replace('\x00', '') if content else ''
        content_type = getattr(scraper, 'last_content_type', '')
        success = True
    except SoftTimeLimitExceeded:
        logger.warning(f"Soft time limit exceeded for portal {portal.name} ({portal.url}). Aborting check.")
        raise
    except ScraperException as e:
        logger.warning(f"Scraper failed for {portal.url}: {e}")
        content = ""
        content_type = ""
        status_code = 403 if "403" in str(e) else 500
        response_time_ms = 0
        success = False

    # ── Update portal health ─────────────────────────────────────────────────
    portal.last_checked_at = timezone.now()

    # Handle HTTP 403 Forbidden / Cloudflare firewall block
    if status_code in [403, 401]:
        # Do NOT count FIREWALL BLOCKED status toward consecutive_failures
        if is_firewall_blocked:
            # Persistent 403 after spoofing: transition to MANUAL_MONITORING_REQUIRED
            portal.status = PortalStatus.MANUAL_MONITORING_REQUIRED
            portal.health_status = HealthStatus.MANUAL_MONITORING_REQUIRED
            portal.is_active = False  # Stop automated checks entirely
            note_msg = "MANUAL MONITORING REQUIRED: Blocked by Cloudflare/Firewall (HTTP 403). Operator must check this portal manually once per week."
            if note_msg not in (portal.notes or ""):
                portal.notes = f"{portal.notes}\n{note_msg}".strip() if portal.notes else note_msg
            logger.warning(
                f"Portal marked as MANUAL MONITORING REQUIRED (HTTP 403 persistent block): "
                f"{portal.name} ({portal.url}). Deactivated automated checks."
            )
        else:
            # First-time 403: flag as BLOCKED for next check header spoofing
            portal.status = PortalStatus.BLOCKED
            portal.health_status = HealthStatus.BLOCKED
            logger.warning(
                f"Portal flagged as BLOCKED (HTTP 403): {portal.name} ({portal.url}). "
                "Next check will use browser header spoofing and randomized delay."
            )

        portal.save(update_fields=['last_checked_at', 'status', 'health_status', 'is_active', 'notes'])
        return

    if not success:
        portal.consecutive_failures += 1
        portal.check_interval_minutes = portal.calculate_backoff_interval_minutes()
        portal.poll_interval = portal.check_interval_minutes * 60

        if portal.consecutive_failures >= 10:
            portal.status = PortalStatus.DEGRADED
            portal.health_status = HealthStatus.DEGRADED
            logger.warning(
                f"Portal flagged as DEGRADED after {portal.consecutive_failures} consecutive failures: "
                f"{portal.name} ({portal.url}). Check interval adjusted to {portal.check_interval_minutes} minutes."
            )
        else:
            portal.status = PortalStatus.OFFLINE
            portal.health_status = HealthStatus.OFFLINE
            logger.warning(
                f"Portal check failed ({portal.consecutive_failures} consecutive failures): "
                f"{portal.name} ({portal.url}). Check interval adjusted to {portal.check_interval_minutes} minutes."
            )

        portal.save(update_fields=[
            'last_checked_at', 'status', 'health_status', 'consecutive_failures',
            'check_interval_minutes', 'poll_interval'
        ])
        return

    # ── Success path ─────────────────────────────────────────────────────────
    portal.last_successful_check_at = timezone.now()
    portal.consecutive_failures = 0
    portal.check_interval_minutes = 15
    portal.poll_interval = 900

    is_captcha_detected = (
        "captcha" in content.lower() or
        any(d in portal.url.lower() for d in ['finance.gov.ng', 'icpc.gov.ng', 'nafdac.gov.ng', 'nimasa.gov.ng'])
    )

    if is_captcha_detected:
        portal.status = PortalStatus.CAPTCHA_PROTECTED
        portal.health_status = HealthStatus.CAPTCHA_PROTECTED
        portal.check_interval_minutes = 360
        portal.poll_interval = 21600
        logger.info(
            f"Portal flagged as CAPTCHA PROTECTED: {portal.name} ({portal.url}). "
            "Automated check frequency reduced to 6 hours."
        )
        portal.save(update_fields=[
            'last_checked_at', 'status', 'health_status',
            'check_interval_minutes', 'poll_interval'
        ])
        Snapshot.objects.create(
            portal=portal,
            content_hash=compute_content_hash(clean_html_to_text(content, content_type=content_type)),
            raw_content=clean_html_to_text(content, content_type=content_type).replace('\x00', '') if content else '',
            status_code=status_code,
            response_time_ms=response_time_ms,
            scrape_method_used=portal.scrape_method,
            has_change=False,
            triggered_alert=False
        )
        return

    if status_code == 429:
        portal.status = PortalStatus.RATE_LIMITED
        portal.health_status = HealthStatus.RATE_LIMITED
    elif status_code == 503:
        portal.status = PortalStatus.MAINTENANCE
        portal.health_status = HealthStatus.MAINTENANCE
    else:
        portal.status = PortalStatus.ONLINE
        portal.health_status = HealthStatus.ONLINE

    normalized_text = clean_html_to_text(content, content_type=content_type)
    content_hash = compute_content_hash(normalized_text)

    # Get previous snapshot
    prev_snapshot = Snapshot.objects.filter(portal=portal).order_by('-created_at').first()

    has_change = False
    triggered_alert = False

    if prev_snapshot:
        if prev_snapshot.content_hash != content_hash:
            has_change = True
            portal.last_change_detected_at = timezone.now()

            # Guard: if raw_content was purged (>30 days old), skip the diff.
            # An empty raw_content would cause analyze_diff to treat the entire
            # page as newly added, producing a near-certain false positive alert.
            if not prev_snapshot.raw_content:
                logger.info(
                    f"Skipping diff for {portal.name}: previous snapshot raw_content was purged. "
                    "Treating as new baseline."
                )
            else:
                added_text = analyze_diff(prev_snapshot.raw_content, normalized_text)
                matched_data = match_recruitment_keywords(added_text)

                if matched_data['is_recruitment']:
                    create_alert_from_scrape(portal, content, matched_data)
                    triggered_alert = True
                else:
                    # Log a snippet so operators can audit missed alerts and
                    # decide if the keyword list needs expanding.
                    snippet = added_text[:300].replace('\n', ' ').strip()
                    logger.info(
                        f"Change detected for {portal.name} but no recruitment keywords matched. "
                        f"Confidence={matched_data['confidence']}. "
                        f"Added text sample: '{snippet}'"
                    )
    # else: first-ever snapshot : just establish baseline, nothing to compare yet.

    # ── Compute uptime from the last 100 snapshots (single aggregate query) ──
    # Previously iterated 100 Python objects; now one SQL COUNT with a filter.
    agg = Snapshot.objects.filter(portal=portal).order_by('-created_at')[:100].aggregate(
        total=Count('id'),
        ok=Count('id', filter=Q(status_code__isnull=False, status_code__lt=400)),
    )
    if agg['total']:
        portal.uptime_percentage = Decimal(str(round(agg['ok'] / agg['total'] * 100, 2)))

    # Update response time on the Portal model (API reads this, not just Snapshot)
    portal.response_time_ms = response_time_ms

    # Persist all portal health fields in a single save call.
    portal.save(update_fields=[
        'last_checked_at', 'last_successful_check_at', 'consecutive_failures',
        'check_interval_minutes', 'poll_interval',
        'status', 'health_status', 'last_change_detected_at',
        'uptime_percentage', 'response_time_ms',
    ])

    # Save current snapshot
    Snapshot.objects.create(
        portal=portal,
        content_hash=content_hash,
        raw_content=normalized_text.replace('\x00', '') if normalized_text else '',
        status_code=status_code,
        response_time_ms=response_time_ms,
        scrape_method_used=portal.scrape_method,
        has_change=has_change,
        triggered_alert=triggered_alert
    )

    logger.info(f"Portal check complete: {portal.name}. Change={has_change}, AlertTriggered={triggered_alert}")


@shared_task(ignore_result=True)
def check_high_priority_portals():
    """
    Fan out checks for HIGH priority portals (every 5 minutes).
    Filters out portals that are currently in exponential backoff and not yet due.
    """
    from apps.agencies.models import Portal, PortalPriority
    logger.info("Starting high priority portals check...")
    portals = [p.id for p in Portal.objects.filter(is_active=True, priority=PortalPriority.HIGH) if p.is_due_for_check]
    count = len(portals)
    logger.info(f"Found {count} active HIGH priority portals due to check.")
    for portal_id in portals:
        portal_check.apply_async(args=[portal_id], queue='crawl')
    logger.info(f"Queued {count} HIGH priority portal checks.")


@shared_task(ignore_result=True)
def check_standard_portals():
    """
    Fan out checks for MEDIUM priority portals (every 15 minutes).
    Filters out portals that are currently in exponential backoff and not yet due.
    """
    from apps.agencies.models import Portal, PortalPriority
    logger.info("Starting standard portals check...")
    portals = [p.id for p in Portal.objects.filter(is_active=True, priority=PortalPriority.MEDIUM) if p.is_due_for_check]
    count = len(portals)
    logger.info(f"Found {count} active MEDIUM priority portals due to check.")
    for portal_id in portals:
        portal_check.apply_async(args=[portal_id], queue='crawl')
    logger.info(f"Queued {count} MEDIUM priority portal checks.")


@shared_task(ignore_result=True)
def check_low_activity_portals():
    """
    Fan out checks for LOW priority portals (every 60 minutes).
    Filters out portals that are currently in exponential backoff and not yet due.
    """
    from apps.agencies.models import Portal, PortalPriority
    logger.info("Starting low activity portals check...")
    portals = [p.id for p in Portal.objects.filter(is_active=True, priority=PortalPriority.LOW) if p.is_due_for_check]
    count = len(portals)
    logger.info(f"Found {count} active LOW priority portals due to check.")
    for portal_id in portals:
        portal_check.apply_async(args=[portal_id], queue='crawl')
    logger.info(f"Queued {count} LOW priority portal checks.")


@shared_task(ignore_result=True)
def nightly_backup():
    """Export database to JSON and post to the backup channel."""
    logger.info("Starting nightly backup task...")
    success = export_and_backup()
    if success:
        logger.info("Nightly backup task completed successfully.")
    else:
        logger.error("Nightly backup task failed.")


@shared_task(ignore_result=True)
def daily_health_report():
    """Generate daily health report for YESTERDAY and notify super admins.

    Runs at 08:00. Counts yesterday's data so the report covers a full 24-hour
    window rather than the 8 hours that would have elapsed by 08:00 today.
    """
    logger.info("Generating daily health report...")
    from apps.monitor.models import Snapshot
    from apps.notifications.sender import send_message
    from django.conf import settings

    # Always report on YESTERDAY : not today (which is incomplete at 08:00).
    yesterday = timezone.now().date() - timedelta(days=1)

    agg = Snapshot.objects.filter(created_at__date=yesterday).aggregate(
        total=Count('id'),
        captcha=Count('id', filter=Q(portal__health_status__in=['CAPTCHA_PROTECTED', 'CAPTCHA']) | Q(portal__status__in=['CAPTCHA_PROTECTED', 'CAPTCHA'])),
        failed=Count('id', filter=Q(status_code__gte=400) & ~Q(portal__health_status__in=['CAPTCHA_PROTECTED', 'CAPTCHA'])),
        network_errors=Count('id', filter=Q(status_code__isnull=True)),
        changes=Count('id', filter=Q(has_change=True)),
    )
    total_checks = agg['total'] or 0
    captcha_checks = agg['captcha'] or 0
    failed_checks = agg['failed'] or 0
    network_errors = agg['network_errors'] or 0
    effective_total = max(0, total_checks - captcha_checks)
    successful_checks = max(0, effective_total - failed_checks - network_errors)
    changes_detected = agg['changes'] or 0

    success_rate = (successful_checks / effective_total * 100) if effective_total > 0 else 100.0

    report = (
        "<b>RecruitmentAlert Daily Health Report</b>\n\n"
        f"📅 Date: {yesterday.strftime('%d %B %Y')}\n"
        f"🔄 Total checks: {total_checks}\n"
        f"✅ Successful: {successful_checks}\n"
        f"🛡️ CAPTCHA Protected: {captcha_checks}\n"
        f"❌ Failed (HTTP 4xx/5xx): {failed_checks}\n"
        f"🔌 Network errors: {network_errors}\n"
        f"📈 Success Rate: {success_rate:.2f}%\n"
        f"⚡ Changes Detected: {changes_detected}\n"
    )

    backup_channel_id = getattr(settings, 'TELEGRAM_BACKUP_CHANNEL_ID', None)
    if backup_channel_id:
        send_message(chat_id=backup_channel_id, text=report)
        logger.info("Daily health report generated and sent.")
    else:
        logger.warning("TELEGRAM_BACKUP_CHANNEL_ID not set : skipping sending daily health report.")


@shared_task(ignore_result=True)
def aggregate_portal_health_logs():
    """Aggregate yesterday's Snapshots into PortalHealthLog entries.

    Runs nightly at 00:30 (after midnight so yesterday is fully complete).
    Uses update_or_create so re-runs are idempotent (safe to re-trigger manually).

    Previously fired 5 queries × N portals. Now uses a single batch annotate()
    query that returns all portal aggregates in one round-trip, then bulk
    upserts.  For 42 portals this drops ~210 queries to ~5.
    """
    from apps.agencies.models import Portal
    from apps.monitor.models import Snapshot, PortalHealthLog

    yesterday = timezone.now().date() - timedelta(days=1)
    logger.info(f"Aggregating portal health logs for {yesterday}...")

    # One query: aggregate all portal stats for yesterday at once.
    rows = (
        Snapshot.objects
        .filter(created_at__date=yesterday)
        .values('portal_id')
        .annotate(
            checks_total=Count('id'),
            checks_successful=Count('id', filter=Q(status_code__lt=400)),
            checks_failed=Count('id', filter=Q(status_code__gte=400)),
            avg_rt=Avg('response_time_ms', filter=Q(response_time_ms__isnull=False)),
            changes_detected=Count('id', filter=Q(has_change=True)),
            alerts_triggered=Count('id', filter=Q(triggered_alert=True)),
        )
    )

    created_count = 0
    updated_count = 0

    for row in rows:
        if row['checks_total'] == 0:
            continue

        uptime = Decimal(str(round(row['checks_successful'] / row['checks_total'] * 100, 2)))

        _, was_created = PortalHealthLog.objects.update_or_create(
            portal_id=row['portal_id'],
            date=yesterday,
            defaults={
                'checks_total': row['checks_total'],
                'checks_successful': row['checks_successful'],
                'checks_failed': row['checks_failed'],
                'avg_response_time_ms': int(row['avg_rt']) if row['avg_rt'] else None,
                'uptime_percentage': uptime,
                'changes_detected': row['changes_detected'],
                'alerts_triggered': row['alerts_triggered'],
            }
        )
        if was_created:
            created_count += 1
        else:
            updated_count += 1

    logger.info(
        f"PortalHealthLog aggregation complete for {yesterday}: "
        f"{created_count} created, {updated_count} updated."
    )


@shared_task(ignore_result=True)
def purge_old_snapshot_content():
    """Purge raw_content from Snapshots older than 30 days.

    Sets raw_content='' rather than deleting the row, preserving the hash,
    status_code, and timing data for historical analysis while reclaiming
    the bulk of the storage (the full page text).

    Safe to re-run : idempotent (empty strings are skipped by the filter).
    """
    from apps.monitor.models import Snapshot

    cutoff = timezone.now() - timedelta(days=30)
    updated = Snapshot.objects.filter(
        created_at__lt=cutoff,
        raw_content__gt=''  # Only update rows that still have content
    ).update(raw_content='')
    logger.info(f"Purged raw_content from {updated} Snapshots older than 30 days.")
