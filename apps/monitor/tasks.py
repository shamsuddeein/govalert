import logging
from django.utils import timezone
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
    from apps.agencies.models import Portal, PortalStatus
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
        portal.consecutive_failures += 1

        if portal.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            # Auto-suspend — stop wasting scrape budget on dead portals.
            portal.is_active = False
            portal.save(update_fields=[
                'last_checked_at', 'status', 'consecutive_failures', 'is_active'
            ])
            logger.warning(
                f"Portal SUSPENDED after {portal.consecutive_failures} consecutive failures: "
                f"{portal.name} ({portal.url}). "
                f"Set is_active=True in Django admin to re-enable."
            )
        else:
            portal.save(update_fields=['last_checked_at', 'status', 'consecutive_failures'])
        return

    # ── Success path ─────────────────────────────────────────────────────────
    portal.last_successful_check_at = timezone.now()
    portal.consecutive_failures = 0

    if status_code in [403, 401]:
        portal.status = PortalStatus.BLOCKED
    elif status_code == 429:
        portal.status = PortalStatus.RATE_LIMITED
    elif status_code == 503:
        portal.status = PortalStatus.MAINTENANCE
    elif "captcha" in content.lower():
        portal.status = PortalStatus.CAPTCHA
    else:
        portal.status = PortalStatus.ONLINE

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

    # Persist all portal health fields in a single save call.
    portal.save(update_fields=[
        'last_checked_at', 'last_successful_check_at', 'consecutive_failures',
        'status', 'last_change_detected_at',
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
    """Generate daily health report and notify super admins."""
    logger.info("Generating daily health report...")
    from apps.monitor.models import Snapshot
    from apps.notifications.sender import send_message
    from django.conf import settings

    total_checks = Snapshot.objects.filter(created_at__date=timezone.now().date()).count()
    failed_checks = Snapshot.objects.filter(created_at__date=timezone.now().date(), status_code__gte=400).count()
    successful_checks = total_checks - failed_checks

    success_rate = (successful_checks / total_checks * 100) if total_checks > 0 else 100.0
    changes_detected = Snapshot.objects.filter(created_at__date=timezone.now().date(), has_change=True).count()

    report = (
        "<b>GovAlert Daily Health Report</b>\n\n"
        f"📅 Date: {timezone.now().date().strftime('%d %B %Y')}\n"
        f"🔄 Total checks: {total_checks}\n"
        f"✅ Successful: {successful_checks}\n"
        f"❌ Failed: {failed_checks}\n"
        f"📈 Success Rate: {success_rate:.2f}%\n"
        f"⚡ Changes Detected: {changes_detected}\n"
    )

    backup_channel_id = getattr(settings, 'TELEGRAM_BACKUP_CHANNEL_ID', None)
    if backup_channel_id:
        send_message(chat_id=backup_channel_id, text=report)
        logger.info("Daily health report generated and sent.")
    else:
        logger.warning("TELEGRAM_BACKUP_CHANNEL_ID not set — skipping sending daily health report.")
