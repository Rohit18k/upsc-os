import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.versioning import ContentVersion, Citation, DuplicateRecord, VerificationRecord
from app.models.mapping import ContentMapping


class ContentFactoryBase:
    content_type: str = "generic"

    def __init__(self, db: AsyncSession):
        self.db = db

    def _compute_checksum(self, data: Dict[str, Any]) -> str:
        raw = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    async def _find_duplicate(self, checksum: str) -> Optional[ContentVersion]:
        result = await self.db.execute(
            select(ContentVersion).where(
                ContentVersion.checksum == checksum,
                ContentVersion.content_type == self.content_type,
            )
        )
        return result.scalar_one_or_none()

    async def _record_duplicate(
        self,
        existing: ContentVersion,
        new_data: Dict[str, Any],
        similarity: float = 1.0,
    ) -> DuplicateRecord:
        dup = DuplicateRecord(
            primary_content_id=existing.id,
            primary_content_type=self.content_type,
            duplicate_content_id=existing.id,
            duplicate_content_type=self.content_type,
            similarity_score=similarity,
            detection_method="checksum",
            resolved=True,
        )
        self.db.add(dup)
        await self.db.flush()
        return dup

    async def store_content(
        self,
        title: str,
        content_data: Dict[str, Any],
        syllabus_node_id: Optional[UUID] = None,
        syllabus_node_type: Optional[str] = None,
        citations: Optional[List[Dict[str, Any]]] = None,
        source: Optional[str] = None,
        created_by: Optional[UUID] = None,
        change_summary: Optional[str] = None,
        skip_duplicate_check: bool = False,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> ContentVersion:
        checksum = self._compute_checksum(content_data)

        if not skip_duplicate_check:
            existing = await self._find_duplicate(checksum)
            if existing:
                await self._record_duplicate(existing, content_data)
                return existing

        content_id = uuid.uuid4()

        version = ContentVersion(
            content_id=content_id,
            content_type=self.content_type,
            version_number=1,
            title=title,
            content_data=content_data,
            change_summary=change_summary,
            created_by=created_by,
            source=source,
            checksum=checksum,
            extra_metadata=extra_metadata,
        )
        self.db.add(version)
        await self.db.flush()

        if syllabus_node_id and syllabus_node_type:
            mapping = ContentMapping(
                syllabus_node_id=syllabus_node_id,
                syllabus_node_type=syllabus_node_type,
                content_id=content_id,
                content_type=self.content_type,
                relevance_score=1.0,
                signal_strength=1.0,
                signal_source="generated",
                is_verified=True,
                mapped_by="content_factory",
            )
            self.db.add(mapping)

        if citations:
            for cit in citations:
                citation = Citation(
                    content_version_id=version.id,
                    source_type=cit.get("source_type", "book"),
                    source_id=cit.get("source_id"),
                    source_title=cit.get("source_title", ""),
                    source_url=cit.get("source_url"),
                    page_reference=cit.get("page_reference"),
                    excerpt=cit.get("excerpt"),
                    confidence=cit.get("confidence", 1.0),
                    is_verified=cit.get("is_verified", False),
                )
                self.db.add(citation)

        await self.db.flush()
        return version

    async def store_validation(
        self,
        content_id: UUID,
        content_type: str,
        status: str = "pending",
        confidence: float = 0.0,
        matched_sources: Optional[List[str]] = None,
        verification_details: Optional[Dict[str, Any]] = None,
        discrepancies: Optional[List[str]] = None,
        source: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> VerificationRecord:
        record = VerificationRecord(
            content_id=content_id,
            content_type=content_type,
            status=status,
            confidence=confidence,
            matched_sources=matched_sources or [],
            verification_details=verification_details or {},
            discrepancies=discrepancies or [],
            verified_at=datetime.now(timezone.utc),
            verified_by=source,
            source=source,
            notes=notes,
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def count_by_syllabus_node(
        self, node_id: UUID, node_type: str
    ) -> int:
        result = await self.db.execute(
            select(ContentMapping).where(
                ContentMapping.syllabus_node_id == node_id,
                ContentMapping.syllabus_node_type == node_type,
                ContentMapping.content_type == self.content_type,
            )
        )
        mappings = result.scalars().all()
        return len(mappings)

    async def get_by_syllabus_node(
        self, node_id: UUID, node_type: str
    ) -> List[ContentVersion]:
        mappings_result = await self.db.execute(
            select(ContentMapping.content_id).where(
                ContentMapping.syllabus_node_id == node_id,
                ContentMapping.syllabus_node_type == node_type,
                ContentMapping.content_type == self.content_type,
            )
        )
        content_ids = [row[0] for row in mappings_result.all()]
        if not content_ids:
            return []
        versions = await self.db.execute(
            select(ContentVersion).where(
                ContentVersion.content_id.in_(content_ids),
                ContentVersion.content_type == self.content_type,
            )
        )
        return list(versions.scalars().all())
