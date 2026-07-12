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
        from apscheduler.executors.pool import ThreadPoolExecutor
        executors = {
            'default': ThreadPoolExecutor(10),
            'high': ThreadPoolExecutor(10),
            'medium': ThreadPoolExecutor(5),
            'low': ThreadPoolExecutor(2),
        }
        _scheduler = BackgroundScheduler(executors=executors, timezone='Africa/Lagos')
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

    # ── Portal monitoring jobs (HIGH priority) ──────────────────────────────────
    # High-priority agencies: every 10 minutes
    scheduler.add_job(
        'apps.monitor.tasks:check_high_priority_portals',
        trigger=IntervalTrigger(minutes=settings.PORTAL_CHECK_INTERVAL_HIGH_PRIORITY),
        id='check_high_priority_portals',
        replace_existing=True,
        misfire_grace_time=60,
        executor='high',
    )

    # Standard portals: every 15 minutes
    scheduler.add_job(
        'apps.monitor.tasks:check_standard_portals',
        trigger=IntervalTrigger(minutes=settings.PORTAL_CHECK_INTERVAL_MINUTES),
        id='check_standard_portals',
        replace_existing=True,
        misfire_grace_time=60,
        executor='high',
    )

    # Low-activity portals: every 30 minutes
    scheduler.add_job(
        'apps.monitor.tasks:check_low_activity_portals',
        trigger=IntervalTrigger(minutes=settings.PORTAL_CHECK_INTERVAL_LOW_ACTIVITY),
        id='check_low_activity_portals',
        replace_existing=True,
        misfire_grace_time=120,
        executor='high',
    )

    # ── Verification and Retries (MEDIUM priority) ──────────────────────────────
    # Retry failed notifications every hour
    scheduler.add_job(
        'apps.notifications.tasks:retry_failed_notifications',
        trigger=IntervalTrigger(hours=1),
        id='retry_failed_notifications',
        replace_existing=True,
        executor='medium',
    )

    # ── Cleanup and Maintenance (LOW priority) ──────────────────────────────────
    # Nightly DB backup to Telegram at 1 AM
    scheduler.add_job(
        'apps.monitor.tasks:nightly_backup',
        trigger='cron',
        hour=1, minute=0,
        id='nightly_backup',
        replace_existing=True,
        timezone='Africa/Lagos',
        executor='low',
    )

    # Daily health report at 8 AM
    scheduler.add_job(
        'apps.monitor.tasks:daily_health_report',
        trigger='cron',
        hour=8, minute=0,
        id='daily_health_report',
        replace_existing=True,
        timezone='Africa/Lagos',
        executor='low',
    )

    # Mark inactive users every 24 hours
    scheduler.add_job(
        'apps.accounts.tasks:cleanup_inactive_users',
        trigger=IntervalTrigger(hours=24),
        id='cleanup_inactive_users',
        replace_existing=True,
        executor='low',
    )

    scheduler.start()
    logger.info("✅ APScheduler started with %d jobs.", len(scheduler.get_jobs()))

    # Trigger initial portal checks immediately on startup in background executors
    try:
        from django.utils import timezone
        scheduler.get_job('check_high_priority_portals').modify(next_run_time=timezone.now())
        scheduler.get_job('check_standard_portals').modify(next_run_time=timezone.now())
        logger.info("⚡ Triggered initial portal checks immediately on startup.")
    except Exception as e:
        logger.warning("Could not trigger initial checks: %s", e)


def stop():
    """Gracefully stop the scheduler on Django shutdown."""
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped.")
