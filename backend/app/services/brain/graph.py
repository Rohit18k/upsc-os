import uuid
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.syllabus import Subject, Module, Topic, Concept
from app.models.mapping import KnowledgeEdge, CrossReference, ContentMapping
from app.services.brain.models import Evidence


class KnowledgeGraphTraverser:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_concept(self, name: str) -> Optional[Concept]:
        result = await self.db.execute(
            select(Concept).where(
                or_(
                    Concept.name.ilike(f"%{name}%"),
                    Concept.display_name.ilike(f"%{name}%"),
                )
            )
        )
        return result.scalar_one_or_none()

    async def find_topic(self, name: str) -> Optional[Topic]:
        result = await self.db.execute(
            select(Topic).where(
                or_(
                    Topic.name.ilike(f"%{name}%"),
                    Topic.display_name.ilike(f"%{name}%"),
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_prerequisites(
        self, concept_id: UUID, max_depth: int = 2
    ) -> List[Evidence]:
        visited: Set[UUID] = set()
        results: List[Evidence] = []
        queue: List[Tuple[UUID, int]] = [(concept_id, 0)]

        while queue:
            cid, depth = queue.pop(0)
            if depth >= max_depth or cid in visited:
                continue
            visited.add(cid)

            edges = await self.db.execute(
                select(KnowledgeEdge).where(
                    KnowledgeEdge.target_concept_id == cid,
                    KnowledgeEdge.edge_type == "prerequisite",
                )
            )
            for edge in edges.scalars().all():
                src = await self.db.get(Concept, edge.source_concept_id)
                if src:
                    results.append(Evidence(
                        content_id=src.id,
                        content_type="concept",
                        title=src.display_name,
                        snippet=src.definition or src.display_name,
                        source="knowledge_graph",
                        score=edge.weight,
                        syllabus_node_id=src.id,
                        syllabus_node_type="concept",
                    ))
                queue.append((edge.source_concept_id, depth + 1))

        return results

    async def get_dependents(
        self, concept_id: UUID, max_depth: int = 2
    ) -> List[Evidence]:
        visited: Set[UUID] = set()
        results: List[Evidence] = []
        queue: List[Tuple[UUID, int]] = [(concept_id, 0)]

        while queue:
            cid, depth = queue.pop(0)
            if depth >= max_depth or cid in visited:
                continue
            visited.add(cid)

            edges = await self.db.execute(
                select(KnowledgeEdge).where(
                    KnowledgeEdge.source_concept_id == cid,
                    KnowledgeEdge.edge_type == "prerequisite",
                )
            )
            for edge in edges.scalars().all():
                tgt = await self.db.get(Concept, edge.target_concept_id)
                if tgt:
                    results.append(Evidence(
                        content_id=tgt.id,
                        content_type="concept",
                        title=tgt.display_name,
                        snippet=tgt.definition or tgt.display_name,
                        source="knowledge_graph",
                        score=edge.weight,
                        syllabus_node_id=tgt.id,
                        syllabus_node_type="concept",
                    ))
                queue.append((edge.target_concept_id, depth + 1))

        return results

    async def get_related(
        self, concept_id: UUID
    ) -> List[Evidence]:
        results: List[Evidence] = []
        edges = await self.db.execute(
            select(KnowledgeEdge).where(
                (KnowledgeEdge.source_concept_id == concept_id) |
                (KnowledgeEdge.target_concept_id == concept_id)
            )
        )
        for edge in edges.scalars().all():
            other_id = (
                edge.target_concept_id
                if edge.source_concept_id == concept_id
                else edge.source_concept_id
            )
            other = await self.db.get(Concept, other_id)
            if other:
                results.append(Evidence(
                    content_id=other.id,
                    content_type="concept",
                    title=other.display_name,
                    snippet=f"Related via {edge.edge_type}",
                    source="knowledge_graph",
                    score=edge.weight,
                    syllabus_node_id=other.id,
                    syllabus_node_type="concept",
                    metadata={"edge_type": edge.edge_type},
                ))
        return results

    async def get_topic_hierarchy(
        self, topic_id: UUID
    ) -> Dict[str, Any]:
        topic = await self.db.get(Topic, topic_id)
        if not topic:
            return {}
        module = await self.db.get(Module, topic.module_id)
        subject = await self.db.get(Subject, module.subject_id) if module else None
        concepts = await self.db.execute(
            select(Concept).where(Concept.topic_id == topic_id)
        )
        return {
            "subject": subject.display_name if subject else None,
            "module": module.display_name if module else None,
            "topic": topic.display_name,
            "concepts": [c.display_name for c in concepts.scalars().all()],
        }
