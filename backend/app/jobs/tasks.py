from app.jobs.celery_app import celery_app


@celery_app.task(
    name="send_email",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
)
def send_email(to: str, subject: str, body: str) -> dict:
    return {"status": "pending", "to": to, "subject": subject}


@celery_app.task(
    name="cleanup_expired_sessions",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
)
def cleanup_expired_sessions() -> dict:
    return {"status": "pending", "task": "cleanup_expired_sessions"}


@celery_app.task(
    name="process_audit_logs",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
)
def process_audit_logs() -> dict:
    return {"status": "pending", "task": "process_audit_logs"}


@celery_app.task(
    name="process_student_event_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
)
def process_student_event_task(user_id_str: str, event_type: str, payload: dict) -> dict:
    import asyncio
    import uuid
    from app.database.session import async_session_factory
    from app.services.student_intelligence import StudentIntelligenceService

    user_id = uuid.UUID(user_id_str)
    
    async def _run():
        async with async_session_factory() as session:
            await StudentIntelligenceService.process_student_event(session, user_id, event_type, payload)
            
    # Run the async loop inside Celery sync worker
    asyncio.run(_run())
    return {"status": "completed", "user_id": user_id_str, "event": event_type}
