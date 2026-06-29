import uuid
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.answers import (
    ModelAnswer,
    AnswerStructure,
    AnswerKeyword,
    AnswerReference,
    ConclusionTemplate,
)
from app.models.mapping import ContentMapping


ANSWER_CATEGORIES = [
    "gs_model_answer", "essay_structure", "ethics_case_study",
    "introduction", "conclusion", "diagram", "flowchart",
    "committee_reference", "constitutional_reference",
]


class AnswerWritingFactory:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_model_answer(
        self,
        title: str,
        question_text: str,
        structures: List[Dict[str, Any]],
        keywords: List[Dict[str, Any]],
        references: Optional[List[Dict[str, Any]]] = None,
        exam_type: str = "mains",
        gs_paper: Optional[str] = None,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        marks: int = 15,
        word_limit: int = 250,
        difficulty: str = "medium",
        year: Optional[int] = None,
        is_pyq: bool = False,
        syllabus_node_id: Optional[UUID] = None,
        syllabus_node_type: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> ModelAnswer:
        answer = ModelAnswer(
            title=title,
            question_text=question_text,
            exam_type=exam_type,
            gs_paper=gs_paper,
            subject=subject,
            topic=topic,
            marks=marks,
            word_limit=word_limit,
            difficulty=difficulty,
            year=year,
            is_pyq=is_pyq,
            syllabus_node_id=syllabus_node_id,
            syllabus_node_type=syllabus_node_type,
            extra_metadata=extra_metadata,
        )
        self.db.add(answer)
        await self.db.flush()

        for i, struct in enumerate(structures):
            s = AnswerStructure(
                model_answer_id=answer.id,
                section=struct.get("section", ""),
                content=struct.get("content", ""),
                sort_order=struct.get("sort_order", i),
                word_count=struct.get("word_count"),
            )
            self.db.add(s)

        for kw in keywords:
            k = AnswerKeyword(
                model_answer_id=answer.id,
                keyword=kw.get("keyword", ""),
                importance=kw.get("importance", "essential"),
                context=kw.get("context"),
            )
            self.db.add(k)

        if references:
            for ref in references:
                r = AnswerReference(
                    model_answer_id=answer.id,
                    reference_type=ref.get("reference_type", "book"),
                    reference_value=ref.get("reference_value", ""),
                    description=ref.get("description"),
                    relevance=ref.get("relevance"),
                )
                self.db.add(r)

        if syllabus_node_id and syllabus_node_type:
            mapping = ContentMapping(
                syllabus_node_id=syllabus_node_id,
                syllabus_node_type=syllabus_node_type,
                content_id=answer.id,
                content_type="model_answer",
                relevance_score=1.0,
                signal_strength=1.0,
                signal_source="generated",
                is_verified=True,
                mapped_by="answer_factory",
            )
            self.db.add(mapping)

        await self.db.commit()
        return answer

    @classmethod
    def build_conclusion_template(
        cls,
        title: str,
        template_text: str,
        category: str,
        tone: str = "balanced",
        word_count: int = 50,
        tags: Optional[List[str]] = None,
    ) -> ConclusionTemplate:
        return ConclusionTemplate(
            title=title,
            template_text=template_text,
            category=category,
            tone=tone,
            word_count=word_count,
            tags=tags,
        )

    async def get_conclusion_templates(
        self, category: Optional[str] = None
    ) -> List[ConclusionTemplate]:
        query = select(ConclusionTemplate)
        if category:
            query = query.where(ConclusionTemplate.category == category)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_answers_by_subject(self, subject: str) -> int:
        result = await self.db.execute(
            select(ModelAnswer).where(ModelAnswer.subject == subject)
        )
        return len(result.scalars().all())
