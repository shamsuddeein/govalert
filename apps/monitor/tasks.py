import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Q
from storage.backup import export_and_backup
from celery import shared_task

logger = logging.getLogger(__name__)

# Number of consecutive failures before a portal is automatically suspended.
# Covers DNS failures, persistent timeouts, and dead domains. Operators can
# re-enable a portal by setting is_active=True via the Django admin.
MAX_CONSECUTIVE_FAILURES = 10


@shared_task
def portal_check(portal_id: int):
    """
    Check a single portal for changes.
    If changes are detected and recruitment keywords match, creates an alert.

    Design notes:
    - Uses a single portal.save() per execution path to avoid redundant DB writes.
    - Auto-suspends portals that have failed MAX_CONSECUTIVE_FAILURES times in a
      row so dead domains don't waste the scrape budget indefinitely.
    - Logs a content snippet when a change is detected but no keywords matched,
      allowing operators to audit whether the keyword list needs expanding.
    """
    from apps.agencies.models import Portal, PortalStatus, HealthStatus
    from apps.monitor.scraper import scrape_portal
    from apps.monitor.parser import clean_html_to_text, analyze_diff, match_recruitment_keywords
    from apps.monitor.models import Snapshot
    from apps.alerts.services import create_alert_from_scrape
    from core.utils import compute_content_hash
    from core.exceptions import ScraperException

    try:
        portal = Portal.objects.get(pk=portal_id)
    except Portal.DoesNotExist:
        logger.error(f"Portal {portal_id} not found.")
        return

    logger.info(f"Checking portal: {portal.name} ({portal.url}) using {portal.scrape_method}...")

    from core.plugins import get_scraper_backend

    try:
        scraper = get_scraper_backend(portal.scrape_method)
        content, status_code, response_time_ms = scraper.scrape(portal.url)
        success = True
    except ScraperException as e:
        logger.warning(f"Scraper failed for {portal.url}: {e}")
        content = ""
        status_code = 500
        response_time_ms = 0
        success = False

    # ── Update portal health ─────────────────────────────────────────────────
    portal.last_checked_at = timezone.now()

    if not success:
        portal.status = PortalStatus.OFFLINE
        portal.health_status = HealthStatus.OFFLINE  # Keep deprecated+current in sync
        portal.consecutive_failures += 1

        if portal.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            # Auto-suspend — stop wasting scrape budget on dead portals.
            portal.is_active = False
            portal.save(update_fields=[
                'last_checked_at', 'status', 'health_status', 'consecutive_failures', 'is_active'
            ])
            logger.warning(
                f"Portal SUSPENDED after {portal.consecutive_failures} consecutive failures: "
                f"{portal.name} ({portal.url}). "
                f"Set is_active=True in Django admin to re-enable."
            )
        else:
            portal.save(update_fields=['last_checked_at', 'status', 'health_status', 'consecutive_failures'])
        return

    # ── Success path ─────────────────────────────────────────────────────────
    portal.last_successful_check_at = timezone.now()
    portal.consecutive_failures = 0

    if status_code in [403, 401]:
        portal.status = PortalStatus.BLOCKED
        portal.health_status = HealthStatus.BLOCKED
    elif status_code == 429:
        portal.status = PortalStatus.RATE_LIMITED
        portal.health_status = HealthStatus.RATE_LIMITED
    elif status_code == 503:
        portal.status = PortalStatus.MAINTENANCE
        portal.health_status = HealthStatus.MAINTENANCE
    elif "captcha" in content.lower():
        portal.status = PortalStatus.CAPTCHA
        portal.health_status = HealthStatus.CAPTCHA
    else:
        portal.status = PortalStatus.ONLINE
        portal.health_status = HealthStatus.ONLINE

    normalized_text = clean_html_to_text(content)
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
    # else: first-ever snapshot — just establish baseline, nothing to compare yet.

    # Compute uptime from the last 100 snapshots (rolling window)
    recent = Snapshot.objects.filter(portal=portal).order_by('-created_at')[:100]
    total_recent = recent.count()
    if total_recent > 0:
        ok_recent = sum(1 for s in recent if s.status_code is not None and s.status_code < 400)
        from decimal import Decimal
        portal.uptime_percentage = Decimal(str(round(ok_recent / total_recent * 100, 2)))

    # Update response time on the Portal model (API reads this, not just Snapshot)
    portal.response_time_ms = response_time_ms

    # Persist all portal health fields in a single save call.
    portal.save(update_fields=[
        'last_checked_at', 'last_successful_check_at', 'consecutive_failures',
        'status', 'health_status', 'last_change_detected_at',
        'uptime_percentage', 'response_time_ms',
    ])

    # Save current snapshot
    Snapshot.objects.create(
        portal=portal,
        content_hash=content_hash,
        raw_content=normalized_text,
        status_code=status_code,
        response_time_ms=response_time_ms,
        scrape_method_used=portal.scrape_method,
        has_change=has_change,
        triggered_alert=triggered_alert
    )

    logger.info(f"Portal check complete: {portal.name}. Change={has_change}, AlertTriggered={triggered_alert}")


@shared_task
def check_high_priority_portals():
    """
    Check portals marked as HIGH priority (every 5 minutes).

    Previously filtered by check_interval_minutes__lte=10, which matched no
    portals in production because all portals are stored with check_interval_minutes=15.
    Now correctly filters on the `priority` field, which IS populated.
    """
    from apps.agencies.models import Portal, PortalPriority
    logger.info("Starting high priority portals check...")
    portals = Portal.objects.filter(is_active=True, priority=PortalPriority.HIGH)
    count = portals.count()
    logger.info(f"Found {count} active HIGH priority portals to check.")
    for p in portals:
        try:
            portal_check(p.id)
        except Exception as e:
            logger.error(f"Error checking high priority portal {p.id} ({p.name}): {e}")
    logger.info("Finished high priority portals check.")


@shared_task
def check_standard_portals():
    """
    Check portals marked as MEDIUM priority (every 20 minutes).

    Previously filtered by check_interval_minutes=15, which was the only value
    in the DB so all portals ended up here regardless of their intended priority.
    Now correctly filters on the `priority` field.
    """
    from apps.agencies.models import Portal, PortalPriority
    logger.info("Starting standard portals check...")
    portals = Portal.objects.filter(is_active=True, priority=PortalPriority.MEDIUM)
    count = portals.count()
    logger.info(f"Found {count} active MEDIUM priority portals to check.")
    for p in portals:
        try:
            portal_check(p.id)
        except Exception as e:
            logger.error(f"Error checking standard portal {p.id} ({p.name}): {e}")
    logger.info("Finished standard portals check.")


@shared_task
def check_low_activity_portals():
    """
    Check portals marked as LOW priority (every 60 minutes).

    Previously filtered by check_interval_minutes__gte=30, which matched no
    portals because all portals had check_interval_minutes=15.
    Now correctly filters on the `priority` field.
    """
    from apps.agencies.models import Portal, PortalPriority
    logger.info("Starting low activity portals check...")
    portals = Portal.objects.filter(is_active=True, priority=PortalPriority.LOW)
    count = portals.count()
    logger.info(f"Found {count} active LOW priority portals to check.")
    for p in portals:
        try:
            portal_check(p.id)
        except Exception as e:
            logger.error(f"Error checking low activity portal {p.id} ({p.name}): {e}")
    logger.info("Finished low activity portals check.")


@shared_task
def nightly_backup():
    """Export database to JSON and post to the backup channel."""
    logger.info("Starting nightly backup task...")
    success = export_and_backup()
    if success:
        logger.info("Nightly backup task completed successfully.")
    else:
        logger.error("Nightly backup task failed.")


@shared_task
def daily_health_report():
    """Generate daily health report for YESTERDAY and notify super admins.

    Runs at 08:00. Counts yesterday's data so the report covers a full 24-hour
    window rather than the 8 hours that would have elapsed by 08:00 today.
    """
    logger.info("Generating daily health report...")
    from apps.monitor.models import Snapshot
    from apps.notifications.sender import send_message
    from django.conf import settings

    # Always report on YESTERDAY — not today (which is incomplete at 08:00).
    yesterday = timezone.now().date() - timedelta(days=1)

    total_checks = Snapshot.objects.filter(created_at__date=yesterday).count()
    # Count failed and successful independently to avoid NULL status_code inflation.
    failed_checks = Snapshot.objects.filter(
        created_at__date=yesterday, status_code__gte=400
    ).count()
    network_errors = Snapshot.objects.filter(
        created_at__date=yesterday, status_code__isnull=True
    ).count()
    successful_checks = total_checks - failed_checks - network_errors

    success_rate = (successful_checks / total_checks * 100) if total_checks > 0 else 100.0
    changes_detected = Snapshot.objects.filter(created_at__date=yesterday, has_change=True).count()

    report = (
        "<b>GovAlert Daily Health Report</b>\n\n"
        f"📅 Date: {yesterday.strftime('%d %B %Y')}\n"
        f"🔄 Total checks: {total_checks}\n"
        f"✅ Successful: {successful_checks}\n"
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
        logger.warning("TELEGRAM_BACKUP_CHANNEL_ID not set — skipping sending daily health report.")


@shared_task
def aggregate_portal_health_logs():
    """Aggregate yesterday's Snapshots into PortalHealthLog entries.

    Runs nightly at 00:30 (after midnight so yesterday is fully complete).
    Uses update_or_create so re-runs are idempotent (safe to re-trigger manually).
    """
    from decimal import Decimal
    from apps.agencies.models import Portal
    from apps.monitor.models import Snapshot, PortalHealthLog

    yesterday = timezone.now().date() - timedelta(days=1)
    logger.info(f"Aggregating portal health logs for {yesterday}...")

    portals = Portal.objects.filter(is_active=True)
    created_count = 0
    updated_count = 0

    for portal in portals:
        day_snaps = Snapshot.objects.filter(portal=portal, created_at__date=yesterday)
        checks_total = day_snaps.count()
        if checks_total == 0:
            continue

        checks_successful = day_snaps.filter(status_code__lt=400).count()
        checks_failed = day_snaps.filter(status_code__gte=400).count()
        avg_rt = day_snaps.filter(
            response_time_ms__isnull=False
        ).aggregate(avg=Avg('response_time_ms'))['avg']
        changes_detected = day_snaps.filter(has_change=True).count()
        alerts_triggered = day_snaps.filter(triggered_alert=True).count()
        uptime = Decimal(str(round(checks_successful / checks_total * 100, 2)))

        _, was_created = PortalHealthLog.objects.update_or_create(
            portal=portal,
            date=yesterday,
            defaults={
                'checks_total': checks_total,
                'checks_successful': checks_successful,
                'checks_failed': checks_failed,
                'avg_response_time_ms': int(avg_rt) if avg_rt else None,
                'uptime_percentage': uptime,
                'changes_detected': changes_detected,
                'alerts_triggered': alerts_triggered,
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


@shared_task
def purge_old_snapshot_content():
    """Purge raw_content from Snapshots older than 30 days.

    Sets raw_content='' rather than deleting the row, preserving the hash,
    status_code, and timing data for historical analysis while reclaiming
    the bulk of the storage (the full page text).

    Safe to re-run — idempotent (empty strings are skipped by the filter).
    """
    from apps.monitor.models import Snapshot

    cutoff = timezone.now() - timedelta(days=30)
    updated = Snapshot.objects.filter(
        created_at__lt=cutoff,
        raw_content__gt=''  # Only update rows that still have content
    ).update(raw_content='')
    logger.info(f"Purged raw_content from {updated} Snapshots older than 30 days.")
