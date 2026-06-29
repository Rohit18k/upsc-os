import uuid
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.content import ContentFactoryBase

REVISION_TYPES = [
    "one_page_notes",
    "two_minute_revision",
    "one_hour_revision",
    "last_week_revision",
    "exam_day_revision",
]


class RevisionFactory(ContentFactoryBase):
    content_type = "revision_note"

    @classmethod
    def build_revision_note(
        cls,
        note_type: str,
        title: str,
        key_points: List[str],
        detailed_notes: Optional[str] = None,
        mnemonics: Optional[List[str]] = None,
        quick_references: Optional[List[Dict[str, str]]] = None,
        common_mistakes: Optional[List[str]] = None,
        exam_tips: Optional[List[str]] = None,
        last_minute_tips: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return {
            "note_type": note_type,
            "title": title,
            "key_points": key_points,
            "detailed_notes": detailed_notes,
            "mnemonics": mnemonics or [],
            "quick_references": quick_references or [],
            "common_mistakes": common_mistakes or [],
            "exam_tips": exam_tips or [],
            "last_minute_tips": last_minute_tips or [],
        }

    async def create_revision_note(
        self,
        note_type: str,
        title: str,
        key_points: List[str],
        syllabus_node_id: UUID,
        syllabus_node_type: str = "topic",
        detailed_notes: Optional[str] = None,
        mnemonics: Optional[List[str]] = None,
        quick_references: Optional[List[Dict[str, str]]] = None,
        common_mistakes: Optional[List[str]] = None,
        exam_tips: Optional[List[str]] = None,
        last_minute_tips: Optional[List[str]] = None,
        citations: Optional[List[Dict[str, Any]]] = None,
        created_by: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        note_data = self.build_revision_note(
            note_type=note_type,
            title=title,
            key_points=key_points,
            detailed_notes=detailed_notes,
            mnemonics=mnemonics,
            quick_references=quick_references,
            common_mistakes=common_mistakes,
            exam_tips=exam_tips,
            last_minute_tips=last_minute_tips,
        )
        version = await self.store_content(
            title=title,
            content_data=note_data,
            syllabus_node_id=syllabus_node_id,
            syllabus_node_type=syllabus_node_type,
            citations=citations,
            created_by=created_by,
            change_summary=f"Revision note ({note_type}) generated for {syllabus_node_type}",
            extra_metadata={"note_type": note_type},
        )
        await self.db.commit()
        return {
            "content_id": str(version.content_id),
            "version_id": str(version.id),
            "title": version.title,
            "note_type": note_type,
        }
