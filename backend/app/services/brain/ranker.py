import time
from typing import List, Optional
from uuid import UUID

from app.services.brain.models import Evidence, StudentContext


class ContextRanker:
    def __init__(self):
        self.WEIGHTS = {
            "semantic": 0.25,
            "kg_distance": 0.15,
            "student_weakness": 0.20,
            "pyq_frequency": 0.10,
            "book_authority": 0.10,
            "freshness": 0.05,
            "citation_confidence": 0.05,
            "mission_priority": 0.05,
            "marks_contribution": 0.05,
        }

    async def rank(
        self,
        evidence: List[Evidence],
        student_context: Optional[StudentContext] = None,
        query_topic_id: Optional[UUID] = None,
    ) -> List[Evidence]:
        scored = []
        for e in evidence:
            score = e.score * self.WEIGHTS["semantic"]

            if student_context and e.syllabus_node_id:
                node_key = str(e.syllabus_node_id)
                if node_key in student_context.mastery_scores:
                    mastery = student_context.mastery_scores[node_key]
                    if mastery < 0.4:
                        score += 0.2 * self.WEIGHTS["student_weakness"]
                    if mastery > 0.8:
                        score += 0.05

                if student_context.weak_subjects and e.title.lower() in [
                    w.lower() for w in student_context.weak_subjects
                ]:
                    score += 0.15 * self.WEIGHTS["student_weakness"]

            if e.source in ("Book", "NCERT", "Standard"):
                score += 0.1 * self.WEIGHTS["book_authority"]

            if e.source == "PYQ":
                score += 0.1 * self.WEIGHTS["pyq_frequency"]

            if e.metadata and e.metadata.get("version", 1) > 1:
                score += 0.05 * self.WEIGHTS["freshness"]

            scored.append((score, e))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored]

    async def rerank_with_query(
        self, evidence: List[Evidence], query: str
    ) -> List[Evidence]:
        q = query.lower()
        for e in evidence:
            boost = 0.0
            if q in e.title.lower():
                boost += 0.2
            if q in e.snippet.lower():
                boost += 0.1
            if e.syllabus_node_type == "concept" and q in e.title.lower():
                boost += 0.15
            e.score += boost
        evidence.sort(key=lambda e: e.score, reverse=True)
        return evidence
