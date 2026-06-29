import uuid
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.content import ContentFactoryBase


class LessonFactory(ContentFactoryBase):
    content_type = "lesson"

    @classmethod
    def build_lesson_data(
        cls,
        title: str,
        learning_objectives: List[str],
        prerequisites: List[str],
        core_theory: List[Dict[str, Any]],
        examples: List[Dict[str, Any]],
        memory_tricks: List[str],
        mind_map: Optional[Dict[str, Any]],
        common_mistakes: List[str],
        pyq_references: List[Dict[str, Any]],
        revision_notes: List[str],
        flashcards: List[Dict[str, Any]],
        summary: str,
        references: List[str],
        difficulty: str = "medium",
        estimated_minutes: int = 30,
    ) -> Dict[str, Any]:
        return {
            "title": title,
            "difficulty": difficulty,
            "estimated_minutes": estimated_minutes,
            "learning_objectives": learning_objectives,
            "prerequisites": prerequisites,
            "core_theory": core_theory,
            "examples": examples,
            "memory_tricks": memory_tricks,
            "mind_map": mind_map,
            "common_mistakes": common_mistakes,
            "pyq_references": pyq_references,
            "revision_notes": revision_notes,
            "flashcard_data": flashcards,
            "summary": summary,
            "references": references,
        }

    async def create_lesson(
        self,
        title: str,
        lesson_data: Dict[str, Any],
        syllabus_node_id: UUID,
        syllabus_node_type: str = "topic",
        citations: Optional[List[Dict[str, Any]]] = None,
        source: Optional[str] = None,
        created_by: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        version = await self.store_content(
            title=title,
            content_data=lesson_data,
            syllabus_node_id=syllabus_node_id,
            syllabus_node_type=syllabus_node_type,
            citations=citations,
            source=source,
            created_by=created_by,
            change_summary=f"Lesson generated for {syllabus_node_type} {syllabus_node_id}",
            extra_metadata={"lesson_type": "structured", "has_flashcards": bool(lesson_data.get("flashcard_data"))},
        )
        await self.db.commit()
        return {
            "content_id": str(version.content_id),
            "version_id": str(version.id),
            "title": version.title,
            "content_type": self.content_type,
            "checksum": version.checksum,
        }
