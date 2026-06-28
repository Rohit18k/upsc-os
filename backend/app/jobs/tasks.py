from app.jobs.celery_app import celery_app


@celery_app.task(name="send_email")
def send_email(to: str, subject: str, body: str) -> dict:
    return {"status": "pending", "to": to, "subject": subject}


@celery_app.task(name="cleanup_expired_sessions")
def cleanup_expired_sessions() -> dict:
    return {"status": "pending", "task": "cleanup_expired_sessions"}


@celery_app.task(name="process_audit_logs")
def process_audit_logs() -> dict:
    return {"status": "pending", "task": "process_audit_logs"}
