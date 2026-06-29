import re
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.syllabus import Concept, Topic
from app.models.books import Book
from app.models.mapping import ContentMapping


CITATION_PATTERNS = [
    r"(?:see|refer|according to|source|cite|reference)\s+\[(\d+)\]",
    r"\[(\d+)\]",
]


class HallucinationGuard:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def verify_citations(
        self, answer: str, evidence_ids: List[UUID]
    ) -> Tuple[bool, List[str]]:
        cited_indices = set()
        for pattern in CITATION_PATTERNS:
            for match in re.finditer(pattern, answer):
                try:
                    idx = int(match.group(1))
                    cited_indices.add(idx)
                except (ValueError, IndexError):
                    continue

        violations = []
        for idx in cited_indices:
            if idx < 1 or idx > len(evidence_ids):
                violations.append(f"Citation [{idx}] exceeds available evidence")

        return len(violations) == 0, violations

    async def verify_concepts(
        self, answer: str
    ) -> Tuple[bool, List[str]]:
        concept_names = re.findall(
            r"\b(Indus Valley|Vedic|Mauryan|Gupta|Mughal|Delhi Sultanate|Constitution|Fundamental Rights|DPSP|Monsoon|Biodiversity|Globalization|Liberalization|Green Revolution|Mandal Commission|Panchayati Raj|Federalism|Judicial Review|Writ|Secularism|Socialism)\b",
            answer,
        )
        violations = []
        for name in set(concept_names):
            result = await self.db.execute(
                select(Concept).where(
                    Concept.display_name.ilike(f"%{name}%")
                ).limit(1)
            )
            if not result.scalar_one_or_none():
                topic_result = await self.db.execute(
                    select(Topic).where(
                        Topic.display_name.ilike(f"%{name}%")
                    ).limit(1)
                )
                if not topic_result.scalar_one_or_none():
                    violations.append(f"Unverified concept: '{name}'")

        return len(violations) == 0, violations

    async def verify_book_refs(
        self, answer: str
    ) -> Tuple[bool, List[str]]:
        book_names = re.findall(
            r"\b(Laxmikanth|Spectrum|GC Leong|Shankar|Ramesh Singh|Nitin Singhania|India Year Book)\b",
            answer,
        )
        violations = []
        for name in set(book_names):
            result = await self.db.execute(
                select(Book).where(Book.author.ilike(f"%{name}%")).limit(1)
            )
            if not result.scalar_one_or_none():
                result = await self.db.execute(
                    select(Book).where(Book.title.ilike(f"%{name}%")).limit(1)
                )
                if not result.scalar_one_or_none():
                    violations.append(f"Unverified book reference: '{name}'")

        return len(violations) == 0, violations

    async def verify_pyq_refs(
        self, answer: str
    ) -> Tuple[bool, List[str]]:
        pattern = r"(?:20\d{2})\s+(?:Prelims|Mains|GS|Essay|Optional)"
        matches = re.findall(pattern, answer)
        return len(matches) == 0, []

    async def verify(
        self, answer: str, evidence: List[Any]
    ) -> Dict[str, Any]:
        evidence_ids = [e.content_id for e in evidence]

        cites_ok, cite_violations = await self.verify_citations(answer, evidence_ids)
        concepts_ok, concept_violations = await self.verify_concepts(answer)
        books_ok, book_violations = await self.verify_book_refs(answer)

        all_violations = cite_violations + concept_violations + book_violations
        passed = len(all_violations) == 0

        return {
            "passed": passed,
            "violations": all_violations,
            "citation_check": {"passed": cites_ok, "violations": cite_violations},
            "concept_check": {"passed": concepts_ok, "violations": concept_violations},
            "book_check": {"passed": books_ok, "violations": book_violations},
        }

    async def safe_response(
        self, guard_result: Dict[str, Any], fallback_text: str
    ) -> str:
        if guard_result["passed"]:
            return fallback_text

        violations = guard_result["violations"]
        note = "\n\n---\n*Note: The following claims could not be verified against the knowledge base:*\n"
        for v in violations[:3]:
            note += f"- {v}\n"
        return fallback_text + note
