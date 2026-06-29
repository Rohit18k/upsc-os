import time
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.versioning import ContentVersion
from app.models.pyq import PYQ
from app.models.syllabus import Subject, Module, Topic, Concept
from app.models.mapping import ContentMapping
from app.services.brain.models import Evidence, SearchResult


class HybridRetriever:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(
        self,
        query: str,
        content_types: Optional[List[str]] = None,
        syllabus_node_id: Optional[UUID] = None,
        limit: int = 20,
    ) -> SearchResult:
        start = time.time()
        q = query.lower().strip()
        pattern = f"%{q}%"
        all_evidence: List[Evidence] = []

        content_ev = await self._search_content(q, pattern, content_types, limit)
        all_evidence.extend(content_ev)

        pyq_ev = await self._search_pyqs(q, pattern, limit)
        all_evidence.extend(pyq_ev)

        syllabus_ev = await self._search_syllabus(q, pattern, limit)
        all_evidence.extend(syllabus_ev)

        if syllabus_node_id:
            mapped = await self._search_by_node(syllabus_node_id, limit)
            all_evidence.extend(mapped)

        all_evidence.sort(key=lambda e: e.score, reverse=True)
        all_evidence = self._deduplicate(all_evidence)[:limit]
        elapsed = time.time() - start

        return SearchResult(
            query=query,
            results=all_evidence,
            total_found=len(all_evidence),
            latency_ms=round(elapsed * 1000, 1),
            sources=list(set(e.source for e in all_evidence)),
        )

    async def _search_content(
        self,
        q: str,
        pattern: str,
        content_types: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Evidence]:
        query = select(ContentVersion).where(
            ContentVersion.title.ilike(pattern)
        )
        if content_types:
            query = query.where(ContentVersion.content_type.in_(content_types))
        query = query.order_by(ContentVersion.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return [
            Evidence(
                content_id=v.content_id,
                content_type=v.content_type,
                title=v.title,
                snippet=str(v.content_data)[:300] if v.content_data else v.title,
                source=v.content_type.replace("_", " ").title(),
                score=0.8 if q in v.title.lower() else 0.5,
                metadata={"version": v.version_number, "checksum": v.checksum},
            )
            for v in items
        ]

    async def _search_pyqs(
        self, q: str, pattern: str, limit: int = 10
    ) -> List[Evidence]:
        query = select(PYQ).where(
            or_(
                PYQ.question_text.ilike(pattern),
                PYQ.subject.ilike(pattern),
                PYQ.topic.ilike(pattern),
            )
        ).limit(limit)
        result = await self.db.execute(query)
        pyqs = result.scalars().all()

        return [
            Evidence(
                content_id=p.id,
                content_type="pyq",
                title=f"PYQ {p.year} - {p.subject}",
                snippet=p.question_text[:300],
                source="PYQ",
                score=0.9 if q in p.question_text.lower() else 0.6,
                syllabus_node_id=p.syllabus_node_id,
                syllabus_node_type=p.syllabus_node_type,
                metadata={"year": p.year, "difficulty": p.difficulty},
            )
            for p in pyqs
        ]

    async def _search_syllabus(
        self, q: str, pattern: str, limit: int = 10
    ) -> List[Evidence]:
        evidence = []

        topics = await self.db.execute(
            select(Topic).where(Topic.display_name.ilike(pattern)).limit(limit)
        )
        for t in topics.scalars().all():
            evidence.append(Evidence(
                content_id=t.id,
                content_type="topic",
                title=t.display_name,
                snippet=t.description or t.display_name,
                source="syllabus",
                score=0.7 if q in t.display_name.lower() else 0.4,
                syllabus_node_id=t.id,
                syllabus_node_type="topic",
            ))

        concepts = await self.db.execute(
            select(Concept).where(Concept.display_name.ilike(pattern)).limit(limit)
        )
        for c in concepts.scalars().all():
            evidence.append(Evidence(
                content_id=c.id,
                content_type="concept",
                title=c.display_name,
                snippet=c.definition or c.display_name,
                source="syllabus",
                score=0.7 if q in c.display_name.lower() else 0.4,
                syllabus_node_id=c.id,
                syllabus_node_type="concept",
            ))

        return evidence

    async def _search_by_node(
        self, node_id: UUID, limit: int = 10
    ) -> List[Evidence]:
        result = await self.db.execute(
            select(ContentMapping)
            .where(ContentMapping.syllabus_node_id == node_id)
            .order_by(ContentMapping.signal_strength.desc())
            .limit(limit)
        )
        mappings = result.scalars().all()
        evidence = []
        for m in mappings:
            version = await self.db.execute(
                select(ContentVersion).where(
                    ContentVersion.content_id == m.content_id,
                    ContentVersion.content_type == m.content_type,
                ).order_by(ContentVersion.version_number.desc()).limit(1)
            )
            v = version.scalar_one_or_none()
            if v:
                evidence.append(Evidence(
                    content_id=v.content_id,
                    content_type=v.content_type,
                    title=v.title,
                    snippet=str(v.content_data)[:300] if v.content_data else v.title,
                    source=v.content_type.replace("_", " ").title(),
                    score=m.signal_strength,
                    syllabus_node_id=node_id,
                    syllabus_node_type=m.syllabus_node_type,
                ))
        return evidence

    def _deduplicate(self, items: List[Evidence]) -> List[Evidence]:
        seen: set = set()
        unique = []
        for item in items:
            key = (item.content_id, item.content_type)
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique

    async def retrieve(
        self,
        query: str,
        node_id: Optional[UUID] = None,
        limit: int = 20,
    ) -> List[Evidence]:
        result = await self.search(query, limit=limit, syllabus_node_id=node_id)
        return result.results
