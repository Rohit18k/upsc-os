from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.jobs.tasks import cleanup_expired_sessions, process_audit_logs

scheduler = AsyncIOScheduler()


def start_scheduler():
    scheduler.add_job(
        cleanup_expired_sessions.delay,
        IntervalTrigger(hours=24),
        id="cleanup_sessions",
        name="Clean up expired sessions",
        replace_existing=True,
    )

    scheduler.add_job(
        process_audit_logs.delay,
        IntervalTrigger(hours=6),
        id="process_audit_logs",
        name="Process and archive audit logs",
        replace_existing=True,
    )

    scheduler.start()


def stop_scheduler():
    scheduler.shutdown(wait=False)
