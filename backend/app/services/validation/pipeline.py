import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.versioning import (
    ContentVersion,
    DuplicateRecord,
    VerificationRecord,
    Citation,
)
from app.models.mapping import ContentMapping
from app.models.learning_signals import SyllabusSignal


class ValidationCheck:
    name: str = "base"

    async def run(self, content: ContentVersion, db: AsyncSession) -> Dict[str, Any]:
        raise NotImplementedError


class DuplicateCheck(ValidationCheck):
    name = "duplicate_check"

    async def run(self, content: ContentVersion, db: AsyncSession) -> Dict[str, Any]:
        result = await db.execute(
            select(DuplicateRecord).where(
                (DuplicateRecord.primary_content_id == content.content_id) |
                (DuplicateRecord.duplicate_content_id == content.content_id)
            )
        )
        duplicates = result.scalars().all()
        return {
            "check": self.name,
            "passed": len(duplicates) == 0,
            "duplicates_found": len(duplicates),
            "detail": f"Found {len(duplicates)} duplicate record(s)" if duplicates else "No duplicates",
        }


class CitationCheck(ValidationCheck):
    name = "citation_completeness"

    async def run(self, content: ContentVersion, db: AsyncSession) -> Dict[str, Any]:
        result = await db.execute(
            select(Citation).where(Citation.content_version_id == content.id)
        )
        citations = result.scalars().all()
        return {
            "check": self.name,
            "passed": len(citations) > 0,
            "citation_count": len(citations),
            "detail": f"Has {len(citations)} citation(s)" if citations else "No citations — may lack source attribution",
        }


class HallucinationCheck(ValidationCheck):
    name = "hallucination_detection"

    async def run(self, content: ContentVersion, db: AsyncSession) -> Dict[str, Any]:
        data = content.content_data or {}
        text_fields = []
        self._extract_text(data, text_fields)

        suspicious_patterns = [
            "as of my last update", "as an ai", "i don't have",
            "i cannot provide", "i think", "i believe",
            "it is important to note", "it is worth noting",
        ]

        findings = []
        for field_text in text_fields:
            lower = field_text.lower()
            for pattern in suspicious_patterns:
                if pattern in lower:
                    findings.append({"pattern": pattern, "context": field_text[:100]})

        return {
            "check": self.name,
            "passed": len(findings) == 0,
            "suspicious_count": len(findings),
            "findings": findings[:5],
            "detail": f"Found {len(findings)} suspicious pattern(s)" if findings else "No hallucination indicators",
        }

    def _extract_text(self, data: Any, texts: List[str], depth: int = 0):
        if depth > 5:
            return
        if isinstance(data, str) and len(data) > 20:
            texts.append(data)
        elif isinstance(data, dict):
            for v in data.values():
                self._extract_text(v, texts, depth + 1)
        elif isinstance(data, list):
            for item in data:
                self._extract_text(item, texts, depth + 1)


class CoverageCheck(ValidationCheck):
    name = "coverage_check"

    async def run(self, content: ContentVersion, db: AsyncSession) -> Dict[str, Any]:
        result = await db.execute(
            select(ContentMapping).where(
                ContentMapping.content_id == content.content_id,
                ContentMapping.content_type == content.content_type,
            )
        )
        mappings = result.scalars().all()
        return {
            "check": self.name,
            "passed": len(mappings) > 0,
            "syllabus_mappings": len(mappings),
            "detail": f"Mapped to {len(mappings)} syllabus node(s)" if mappings else "Not mapped to any syllabus node",
        }


class ReadabilityCheck(ValidationCheck):
    name = "readability_check"

    async def run(self, content: ContentVersion, db: AsyncSession) -> Dict[str, Any]:
        data = content.content_data or {}
        texts = []
        self._extract_text(data, texts)

        total_words = sum(len(t.split()) for t in texts)
        avg_sentence_length = 0
        if texts:
            total_sentences = sum(max(t.count("."), 1) for t in texts)
            avg_sentence_length = total_words / max(total_sentences, 1)

        return {
            "check": self.name,
            "passed": avg_sentence_length < 40 if avg_sentence_length > 0 else True,
            "total_words": total_words,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "detail": f"~{total_words} words, ~{avg_sentence_length} words/sentence",
        }

    def _extract_text(self, data: Any, texts: List[str], depth: int = 0):
        if depth > 5:
            return
        if isinstance(data, str) and len(data) > 20:
            texts.append(data)
        elif isinstance(data, dict):
            for v in data.values():
                self._extract_text(v, texts, depth + 1)
        elif isinstance(data, list):
            for item in data:
                self._extract_text(item, texts, depth + 1)


class ConsistencyCheck(ValidationCheck):
    name = "consistency_check"

    async def run(self, content: ContentVersion, db: AsyncSession) -> Dict[str, Any]:
        data = content.content_data or {}
        issues = []

        if isinstance(data, dict):
            if "title" in data and content.title and data["title"] != content.title:
                issues.append("Title mismatch between version and content_data")
            if "difficulty" in data:
                valid = {"easy", "medium", "hard"}
                if data["difficulty"] not in valid:
                    issues.append(f"Invalid difficulty: {data['difficulty']}")

        return {
            "check": self.name,
            "passed": len(issues) == 0,
            "issues": issues,
            "detail": "Consistent" if not issues else f"{len(issues)} inconsistency(ies)",
        }


class ValidationPipeline:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.checks: List[ValidationCheck] = [
            DuplicateCheck(),
            CitationCheck(),
            HallucinationCheck(),
            CoverageCheck(),
            ReadabilityCheck(),
            ConsistencyCheck(),
        ]

    async def validate(
        self,
        content: ContentVersion,
        source: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> VerificationRecord:
        results = []
        all_passed = True

        for check in self.checks:
            result = await check.run(content, self.db)
            results.append(result)
            if not result.get("passed", False):
                all_passed = False

        discrepancies = [
            r["detail"] for r in results if not r.get("passed", False)
        ]

        confidence = sum(
            1 for r in results if r.get("passed", False)
        ) / max(len(results), 1)

        record = VerificationRecord(
            content_id=content.content_id,
            content_type=content.content_type,
            status="verified" if all_passed else "flagged",
            confidence=confidence,
            matched_sources=[],
            verification_details={"checks": results},
            discrepancies=discrepancies,
            verified_at=datetime.now(timezone.utc),
            verified_by=source or "validation_pipeline",
            source=source,
            notes=notes,
        )
        self.db.add(record)
        await self.db.commit()
        return record

    async def validate_by_content_id(
        self,
        content_id: UUID,
        content_type: str,
        source: Optional[str] = None,
    ) -> Optional[VerificationRecord]:
        result = await self.db.execute(
            select(ContentVersion).where(
                ContentVersion.content_id == content_id,
                ContentVersion.content_type == content_type,
            ).order_by(ContentVersion.version_number.desc())
        )
        content = result.scalar_one_or_none()
        if not content:
            return None
        return await self.validate(content, source=source)
