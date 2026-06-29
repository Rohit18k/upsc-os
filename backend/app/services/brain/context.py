from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.syllabus import Topic, Subject
from app.models.learning_signals import StudentSignal
from app.models.pyq import PYQAttempt
from app.services.brain.models import StudentContext


class StudentContextEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_context(
        self, student_id: UUID, query: Optional[str] = None
    ) -> StudentContext:
        context = StudentContext(student_id=student_id)

        signals = await self.db.execute(
            select(StudentSignal).where(
                StudentSignal.student_id == student_id
            ).order_by(StudentSignal.accuracy.asc()).limit(5)
        )
        for sig in signals.scalars().all():
            topic = await self.db.get(Topic, sig.syllabus_node_id)
            if topic and sig.accuracy < 0.5:
                context.weak_subjects.append(topic.display_name)
            context.mastery_scores[str(sig.syllabus_node_id)] = sig.mastery_score

        attempts = await self.db.execute(
            select(func.count(PYQAttempt.id)).where(
                PYQAttempt.student_id == student_id,
                PYQAttempt.is_correct == False,
            )
        )
        wrong = attempts.scalar() or 0
        if wrong > 5:
            context.writing_weakness.append(f"Incorrect on {wrong} PYQ attempts")

        backlog = await self.db.execute(
            select(Topic).limit(3)
        )
        for t in backlog.scalars().all():
            context.revision_backlog.append(t.display_name)

        context.study_hours_per_week = 20.0
        context.days_until_exam = 180

        return context

    async def get_relevant_context(
        self, student_id: UUID, query: Optional[str] = None
    ) -> StudentContext:
        ctx = await self.get_context(student_id, query)
        return ctx
