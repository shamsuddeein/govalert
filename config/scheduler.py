"""
GovAlert APScheduler — Phase 1 task scheduler.
Replaces Celery. No Redis needed. Runs in-process.

Started by the Django app via AppConfig.ready() in apps/monitor/apps.py.
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django_apscheduler.jobstores import DjangoJobStore

logger = logging.getLogger(__name__)

_scheduler = None


def get_scheduler() -> BackgroundScheduler:
    """Return the singleton scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone='Africa/Lagos')
        _scheduler.add_jobstore(DjangoJobStore(), 'default')
    return _scheduler


def start():
    """
    Start the APScheduler and register all recurring jobs.
    Called once from MonitorConfig.ready() when Django boots.
    """
    from django.conf import settings

    scheduler = get_scheduler()

    if scheduler.running:
        logger.info("Scheduler already running — skipping start.")
        return

    # ── Portal monitoring jobs ─────────────────────────────────────────────────
    # High-priority agencies: every 10 minutes
    scheduler.add_job(
        'apps.monitor.tasks:check_high_priority_portals',
        trigger=IntervalTrigger(minutes=settings.PORTAL_CHECK_INTERVAL_HIGH_PRIORITY),
        id='check_high_priority_portals',
        replace_existing=True,
        misfire_grace_time=60,
    )

    # Standard portals: every 15 minutes
    scheduler.add_job(
        'apps.monitor.tasks:check_standard_portals',
        trigger=IntervalTrigger(minutes=settings.PORTAL_CHECK_INTERVAL_MINUTES),
        id='check_standard_portals',
        replace_existing=True,
        misfire_grace_time=60,
    )

    # Low-activity portals: every 30 minutes
    scheduler.add_job(
        'apps.monitor.tasks:check_low_activity_portals',
        trigger=IntervalTrigger(minutes=settings.PORTAL_CHECK_INTERVAL_LOW_ACTIVITY),
        id='check_low_activity_portals',
        replace_existing=True,
        misfire_grace_time=120,
    )

    # ── Maintenance jobs ───────────────────────────────────────────────────────
    # Nightly DB backup to Telegram at 1 AM
    scheduler.add_job(
        'apps.monitor.tasks:nightly_backup',
        trigger='cron',
        hour=1, minute=0,
        id='nightly_backup',
        replace_existing=True,
        timezone='Africa/Lagos',
    )

    # Daily health report at 8 AM
    scheduler.add_job(
        'apps.monitor.tasks:daily_health_report',
        trigger='cron',
        hour=8, minute=0,
        id='daily_health_report',
        replace_existing=True,
        timezone='Africa/Lagos',
    )

    # Mark inactive users every 24 hours
    scheduler.add_job(
        'apps.accounts.tasks:cleanup_inactive_users',
        trigger=IntervalTrigger(hours=24),
        id='cleanup_inactive_users',
        replace_existing=True,
    )

    # Retry failed notifications every hour
    scheduler.add_job(
        'apps.notifications.tasks:retry_failed_notifications',
        trigger=IntervalTrigger(hours=1),
        id='retry_failed_notifications',
        replace_existing=True,
    )

    scheduler.start()
    logger.info("✅ APScheduler started with %d jobs.", len(scheduler.get_jobs()))


def stop():
    """Gracefully stop the scheduler on Django shutdown."""
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped.")
