import uuid
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.content import ContentFactoryBase


FLASHCARD_TYPES = [
    "definition", "fact", "concept", "comparison",
    "article", "committee", "case_study", "revision_card",
]


class FlashcardFactory(ContentFactoryBase):
    content_type = "flashcard"

    @classmethod
    def build_flashcard(
        cls,
        front: str,
        back: str,
        card_type: str = "definition",
        tags: Optional[List[str]] = None,
        difficulty: str = "medium",
        source_reference: Optional[str] = None,
        related_concepts: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return {
            "front": front,
            "back": back,
            "card_type": card_type,
            "tags": tags or [],
            "difficulty": difficulty,
            "source_reference": source_reference,
            "related_concepts": related_concepts or [],
        }

    async def create_flashcard(
        self,
        front: str,
        back: str,
        card_type: str = "definition",
        syllabus_node_id: Optional[UUID] = None,
        syllabus_node_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        difficulty: str = "medium",
        source_reference: Optional[str] = None,
        related_concepts: Optional[List[str]] = None,
        created_by: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        flashcard_data = self.build_flashcard(
            front=front,
            back=back,
            card_type=card_type,
            tags=tags,
            difficulty=difficulty,
            source_reference=source_reference,
            related_concepts=related_concepts,
        )
        version = await self.store_content(
            title=f"Flashcard: {front[:80]}",
            content_data=flashcard_data,
            syllabus_node_id=syllabus_node_id,
            syllabus_node_type=syllabus_node_type,
            source=source_reference,
            created_by=created_by,
            extra_metadata={
                "card_type": card_type,
                "difficulty": difficulty,
                "tags": tags,
            },
            skip_duplicate_check=True,
        )
        await self.db.commit()
        return {
            "content_id": str(version.content_id),
            "version_id": str(version.id),
            "front": front,
            "card_type": card_type,
        }

    async def bulk_create(
        self,
        flashcards: List[Dict[str, Any]],
        syllabus_node_id: Optional[UUID] = None,
        syllabus_node_type: Optional[str] = None,
        created_by: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        results = []
        for card in flashcards:
            result = await self.create_flashcard(
                front=card["front"],
                back=card["back"],
                card_type=card.get("card_type", "definition"),
                syllabus_node_id=syllabus_node_id,
                syllabus_node_type=syllabus_node_type,
                tags=card.get("tags"),
                difficulty=card.get("difficulty", "medium"),
                source_reference=card.get("source_reference"),
                related_concepts=card.get("related_concepts"),
                created_by=created_by,
            )
            results.append(result)
        return results
