"""
GovAlert APScheduler — Phase 1 task scheduler.
Replaces Celery. No Redis needed. Runs in-process.

Started by the Django app via AppConfig.ready() in apps/monitor/apps.py.

Executor assignment strategy (to reduce SQLite contention):
  high   — portal monitoring (time-sensitive, high throughput)
  medium — notification retries (important but not latency-critical)
  low    — maintenance tasks: cleanup, backup, health reports

The SQLite "database is locked" warning from django_apscheduler occurs when
two executor threads try to write the job's next_run_time simultaneously.
Keeping maintenance jobs on the low executor (2 threads) minimises this.
For a permanent fix, migrate to PostgreSQL (Phase 2).
"""
import logging
from django.utils import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django_apscheduler.jobstores import DjangoJobStore

logger = logging.getLogger(__name__)

_scheduler = None


def get_scheduler() -> BackgroundScheduler:
    """Return the singleton scheduler instance with in-memory jobstore."""
    global _scheduler
    if _scheduler is None:
        from apscheduler.executors.pool import ThreadPoolExecutor
        executors = {
            'default': ThreadPoolExecutor(10),
            'high': ThreadPoolExecutor(10),
            'medium': ThreadPoolExecutor(5),
            'low': ThreadPoolExecutor(2),
        }
        # In-memory jobstore avoids SQLite lock contention and pickling issues
        _scheduler = BackgroundScheduler(executors=executors, timezone='Africa/Lagos')
    return _scheduler


# ── Job Wrapper Functions ───────────────────────────────────────────────────────
def _run_high_priority_portals():
    try:
        from apps.monitor.tasks import check_high_priority_portals
        func = getattr(check_high_priority_portals, '__wrapped__', check_high_priority_portals)
        func()
    except Exception as exc:
        logger.error("Scheduler error in check_high_priority_portals: %s", exc)

def _run_standard_portals():
    try:
        from apps.monitor.tasks import check_standard_portals
        func = getattr(check_standard_portals, '__wrapped__', check_standard_portals)
        func()
    except Exception as exc:
        logger.error("Scheduler error in check_standard_portals: %s", exc)

def _run_low_activity_portals():
    try:
        from apps.monitor.tasks import check_low_activity_portals
        func = getattr(check_low_activity_portals, '__wrapped__', check_low_activity_portals)
        func()
    except Exception as exc:
        logger.error("Scheduler error in check_low_activity_portals: %s", exc)

def _run_retry_notifications():
    try:
        from apps.notifications.tasks import retry_failed_notifications
        func = getattr(retry_failed_notifications, '__wrapped__', retry_failed_notifications)
        func()
    except Exception as exc:
        logger.error("Scheduler error in retry_failed_notifications: %s", exc)

def _run_nightly_backup():
    try:
        from apps.monitor.tasks import nightly_backup
        func = getattr(nightly_backup, '__wrapped__', nightly_backup)
        func()
    except Exception as exc:
        logger.error("Scheduler error in nightly_backup: %s", exc)

def _run_daily_health_report():
    try:
        from apps.monitor.tasks import daily_health_report
        func = getattr(daily_health_report, '__wrapped__', daily_health_report)
        func()
    except Exception as exc:
        logger.error("Scheduler error in daily_health_report: %s", exc)

def _run_cleanup_inactive_users():
    try:
        from apps.accounts.tasks import cleanup_inactive_users
        func = getattr(cleanup_inactive_users, '__wrapped__', cleanup_inactive_users)
        func()
    except Exception as exc:
        logger.error("Scheduler error in cleanup_inactive_users: %s", exc)


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
        _run_high_priority_portals,
        trigger=IntervalTrigger(minutes=settings.PORTAL_CHECK_INTERVAL_HIGH_PRIORITY),
        id='check_high_priority_portals',
        replace_existing=True,
        misfire_grace_time=60,
        executor='high',
    )

    # Standard portals: every 15 minutes
    scheduler.add_job(
        _run_standard_portals,
        trigger=IntervalTrigger(minutes=settings.PORTAL_CHECK_INTERVAL_MINUTES),
        id='check_standard_portals',
        replace_existing=True,
        misfire_grace_time=60,
        executor='high',
    )

    # Low-activity portals: every 60 minutes
    scheduler.add_job(
        _run_low_activity_portals,
        trigger=IntervalTrigger(minutes=settings.PORTAL_CHECK_INTERVAL_LOW_ACTIVITY),
        id='check_low_activity_portals',
        replace_existing=True,
        misfire_grace_time=300,
        executor='low',
    )

    # ── Verification and Retries (MEDIUM priority) ──────────────────────────────
    scheduler.add_job(
        _run_retry_notifications,
        trigger=IntervalTrigger(hours=1),
        id='retry_failed_notifications',
        replace_existing=True,
        executor='medium',
    )

    # ── Cleanup and Maintenance (LOW priority) ──────────────────────────────────
    scheduler.add_job(
        _run_nightly_backup,
        trigger='cron',
        hour=1, minute=0,
        id='nightly_backup',
        replace_existing=True,
        timezone='Africa/Lagos',
        executor='low',
    )

    scheduler.add_job(
        _run_daily_health_report,
        trigger='cron',
        hour=8, minute=0,
        id='daily_health_report',
        replace_existing=True,
        timezone='Africa/Lagos',
        executor='low',
    )

    scheduler.add_job(
        _run_cleanup_inactive_users,
        trigger=IntervalTrigger(hours=24),
        id='cleanup_inactive_users',
        replace_existing=True,
        executor='low',
    )

    scheduler.start()
    logger.info("✅ APScheduler started in-memory with %d jobs.", len(scheduler.get_jobs()))

    # Trigger only the high-priority job immediately on startup.
    # Standard (MEDIUM) portals run 42 portals serially — triggering that
    # immediately on startup causes a boot-time spike and competes with the
    # scheduler's own DB writes, worsening the SQLite lock warning.
    try:
        scheduler.get_job('check_high_priority_portals').modify(next_run_time=timezone.now())
        logger.info("⚡ Triggered initial high-priority portal check on startup.")
    except Exception as e:
        logger.warning("Could not trigger initial checks: %s", e)


def stop():
    """Gracefully stop the scheduler on Django shutdown."""
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped.")
