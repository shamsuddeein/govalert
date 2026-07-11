import logging
from django.utils import timezone
from storage.backup import export_and_backup

logger = logging.getLogger(__name__)


def portal_check(portal_id: int):
    """
    Check a single portal for changes.
    If changes are detected and recruitment matches, creates an alert.
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

    portal.last_checked_at = timezone.now()
    if success:
        portal.last_successful_check_at = timezone.now()
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
        portal.consecutive_failures = 0
    else:
        portal.status = PortalStatus.OFFLINE
        portal.consecutive_failures += 1
    portal.save()

    if not success:
        return

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
            portal.save()

            # Analyze diff
            added_text = analyze_diff(prev_snapshot.raw_content, normalized_text)
            matched_data = match_recruitment_keywords(added_text)

            if matched_data['is_recruitment']:
                # Create alert
                create_alert_from_scrape(portal, content, matched_data)
                triggered_alert = True
    else:
        # Initial snapshot
        has_change = False

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


def check_high_priority_portals():
    """Scrape and check portals for high-priority agencies."""
    logger.info("Starting high priority portals check...")
    from apps.agencies.models import Portal
    portals = Portal.objects.filter(is_active=True, check_interval_minutes__lte=10)
    for p in portals:
        try:
            portal_check(p.id)
        except Exception as e:
            logger.error(f"Error checking high priority portal {p.id}: {e}")
    logger.info("Finished high priority portals check.")


def check_standard_portals():
    """Scrape and check portals for standard-priority agencies."""
    logger.info("Starting standard portals check...")
    from apps.agencies.models import Portal
    portals = Portal.objects.filter(is_active=True, check_interval_minutes=15)
    for p in portals:
        try:
            portal_check(p.id)
        except Exception as e:
            logger.error(f"Error checking standard portal {p.id}: {e}")
    logger.info("Finished standard portals check.")


def check_low_activity_portals():
    """Scrape and check portals for low-activity/low-priority agencies."""
    logger.info("Starting low activity portals check...")
    from apps.agencies.models import Portal
    portals = Portal.objects.filter(is_active=True, check_interval_minutes__gte=30)
    for p in portals:
        try:
            portal_check(p.id)
        except Exception as e:
            logger.error(f"Error checking low activity portal {p.id}: {e}")
    logger.info("Finished low activity portals check.")


def nightly_backup():
    """Export database to JSON and post to the backup channel."""
    logger.info("Starting nightly backup task...")
    success = export_and_backup()
    if success:
        logger.info("Nightly backup task completed successfully.")
    else:
        logger.error("Nightly backup task failed.")


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
