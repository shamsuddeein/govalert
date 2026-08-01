"""
GovAlert Scheduler Worker — standalone process for Railway.

Run this as a separate Railway service:
  python worker.py

This process:
  1. Bootstraps Django (settings, DB, apps)
  2. Creates an APScheduler backed by the PostgreSQL job store (DjangoJobStore)
     so job state survives process restarts and Railway dyno cycling.
  3. Registers all portal-crawling and maintenance jobs.
  4. Starts the scheduler and blocks until SIGTERM / SIGINT.

The web service (gunicorn) must NOT start APScheduler at all.
Set DISABLE_IN_PROCESS_SCHEDULER=true in the web service env vars.
"""
import os
import sys
import signal
import logging

# ── Bootstrap Django ────────────────────────────────────────────────────────────
# Must happen before any Django or app imports.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

import django
django.setup()

# ── Logging (after django.setup so the Django logging config is applied) ────────
logger = logging.getLogger('worker')

# ── APScheduler imports (after Django setup) ────────────────────────────────────
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django.conf import settings
from django.utils import timezone


# ── Job wrapper functions ────────────────────────────────────────────────────────
# Each wrapper catches all exceptions so a single job failure never kills the
# scheduler process.  Jobs import tasks lazily so Django models are only hit
# when the job actually fires (not at scheduler boot time).

def _run_high_priority_portals():
    try:
        from apps.monitor.tasks import check_high_priority_portals
        func = getattr(check_high_priority_portals, '__wrapped__', check_high_priority_portals)
        func()
    except Exception as exc:
        logger.error("Job error — check_high_priority_portals: %s", exc, exc_info=True)


def _run_standard_portals():
    try:
        from apps.monitor.tasks import check_standard_portals
        func = getattr(check_standard_portals, '__wrapped__', check_standard_portals)
        func()
    except Exception as exc:
        logger.error("Job error — check_standard_portals: %s", exc, exc_info=True)


def _run_low_activity_portals():
    try:
        from apps.monitor.tasks import check_low_activity_portals
        func = getattr(check_low_activity_portals, '__wrapped__', check_low_activity_portals)
        func()
    except Exception as exc:
        logger.error("Job error — check_low_activity_portals: %s", exc, exc_info=True)


def _run_retry_notifications():
    try:
        from apps.notifications.tasks import retry_failed_notifications
        func = getattr(retry_failed_notifications, '__wrapped__', retry_failed_notifications)
        func()
    except Exception as exc:
        logger.error("Job error — retry_failed_notifications: %s", exc, exc_info=True)


def _run_nightly_backup():
    try:
        from apps.monitor.tasks import nightly_backup
        func = getattr(nightly_backup, '__wrapped__', nightly_backup)
        func()
    except Exception as exc:
        logger.error("Job error — nightly_backup: %s", exc, exc_info=True)


def _run_daily_health_report():
    try:
        from apps.monitor.tasks import daily_health_report
        func = getattr(daily_health_report, '__wrapped__', daily_health_report)
        func()
    except Exception as exc:
        logger.error("Job error — daily_health_report: %s", exc, exc_info=True)


def _run_cleanup_inactive_users():
    try:
        from apps.accounts.tasks import cleanup_inactive_users
        func = getattr(cleanup_inactive_users, '__wrapped__', cleanup_inactive_users)
        func()
    except Exception as exc:
        logger.error("Job error — cleanup_inactive_users: %s", exc, exc_info=True)


def _run_aggregate_portal_health_logs():
    try:
        from apps.monitor.tasks import aggregate_portal_health_logs
        func = getattr(aggregate_portal_health_logs, '__wrapped__', aggregate_portal_health_logs)
        func()
    except Exception as exc:
        logger.error("Job error — aggregate_portal_health_logs: %s", exc, exc_info=True)


def _run_purge_old_snapshot_content():
    try:
        from apps.monitor.tasks import purge_old_snapshot_content
        func = getattr(purge_old_snapshot_content, '__wrapped__', purge_old_snapshot_content)
        func()
    except Exception as exc:
        logger.error("Job error — purge_old_snapshot_content: %s", exc, exc_info=True)


# ── Build and start the scheduler ────────────────────────────────────────────────

def build_scheduler() -> BlockingScheduler:
    """
    Create a BlockingScheduler backed by DjangoJobStore (PostgreSQL).

    DjangoJobStore persists job state in the django_apscheduler_djangojob and
    django_apscheduler_djangojobexecution tables which are part of the shared
    PostgreSQL database.  This means:
      - Jobs survive Railway dyno restarts.
      - next_run_time is stored in the DB; no job is lost even after a crash.
      - replace_existing=True ensures a redeploy refreshes the schedule without
        creating duplicate jobs.
    """
    from apscheduler.executors.pool import ThreadPoolExecutor

    executors = {
        'default': ThreadPoolExecutor(10),
        'high': ThreadPoolExecutor(10),
        'medium': ThreadPoolExecutor(5),
        'low': ThreadPoolExecutor(2),
    }

    job_stores = {
        'default': DjangoJobStore(),
    }

    scheduler = BlockingScheduler(
        jobstores=job_stores,
        executors=executors,
        timezone='Africa/Lagos',
    )
    return scheduler


def register_jobs(scheduler: BlockingScheduler) -> None:
    """Register all recurring jobs on the scheduler."""
    high_interval = getattr(settings, 'PORTAL_CHECK_INTERVAL_HIGH_PRIORITY', 5)
    std_interval = getattr(settings, 'PORTAL_CHECK_INTERVAL_MINUTES', 15)
    low_interval = getattr(settings, 'PORTAL_CHECK_INTERVAL_LOW_ACTIVITY', 60)

    # ── Portal monitoring ────────────────────────────────────────────────────────
    scheduler.add_job(
        _run_high_priority_portals,
        trigger=IntervalTrigger(minutes=high_interval),
        id='check_high_priority_portals',
        replace_existing=True,
        misfire_grace_time=60,
        executor='high',
    )

    scheduler.add_job(
        _run_standard_portals,
        trigger=IntervalTrigger(minutes=std_interval),
        id='check_standard_portals',
        replace_existing=True,
        misfire_grace_time=60,
        executor='high',
    )

    scheduler.add_job(
        _run_low_activity_portals,
        trigger=IntervalTrigger(minutes=low_interval),
        id='check_low_activity_portals',
        replace_existing=True,
        misfire_grace_time=300,
        executor='low',
    )

    # ── Notifications ────────────────────────────────────────────────────────────
    scheduler.add_job(
        _run_retry_notifications,
        trigger=IntervalTrigger(hours=1),
        id='retry_failed_notifications',
        replace_existing=True,
        executor='medium',
    )

    # ── Maintenance / cron jobs ──────────────────────────────────────────────────
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

    scheduler.add_job(
        _run_aggregate_portal_health_logs,
        trigger='cron',
        hour=0, minute=30,
        id='aggregate_portal_health_logs',
        replace_existing=True,
        timezone='Africa/Lagos',
        executor='low',
    )

    scheduler.add_job(
        _run_purge_old_snapshot_content,
        trigger='cron',
        hour=3, minute=0,
        id='purge_old_snapshot_content',
        replace_existing=True,
        timezone='Africa/Lagos',
        executor='low',
    )

    logger.info(
        "✅ Registered %d jobs: %s",
        len(scheduler.get_jobs()),
        [j.id for j in scheduler.get_jobs()],
    )


def main():
    logger.info("=" * 60)
    logger.info("GovAlert Scheduler Worker starting…")
    logger.info("Django settings: %s", os.environ.get('DJANGO_SETTINGS_MODULE'))
    logger.info("=" * 60)

    scheduler = build_scheduler()
    register_jobs(scheduler)

    # Trigger the high-priority job immediately on startup so portals are
    # checked right away rather than waiting up to 5 minutes.
    try:
        scheduler.get_job('check_high_priority_portals').modify(next_run_time=timezone.now())
        logger.info("⚡ Triggered initial high-priority portal check on startup.")
    except Exception as exc:
        logger.warning("Could not trigger initial check: %s", exc)

    # Graceful shutdown on SIGTERM (Railway sends this on deploy/stop).
    def _shutdown(signum, frame):
        logger.info("Received signal %s — shutting down scheduler…", signum)
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    logger.info("🚀 Scheduler started. Blocking until SIGTERM/SIGINT.")
    scheduler.start()  # BlockingScheduler.start() blocks here until shutdown()


if __name__ == '__main__':
    main()
