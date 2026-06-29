import uuid
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pyq import PYQ, QuestionPaper, PYQAttempt
from app.models.syllabus import Subject, Concept
from app.models.mapping import ContentMapping
from app.models.learning_signals import PYQSignal, SyllabusSignal


SUBJECT_TOPIC_MAP = {
    "history": [
        "ancient_history", "medieval_history", "modern_history",
        "art_culture", "world_history",
    ],
    "geography": [
        "physical_geography", "human_geography", "indian_geography",
        "environment_ecology",
    ],
    "polity": [
        "constitution", "governance", "judiciary", "federalism",
        "rights_duties", "amendments",
    ],
    "economics": [
        "macroeconomics", "microeconomics", "indian_economy",
        "budget", "banking", "finance",
    ],
    "environment": [
        "ecology", "biodiversity", "climate_change", "conservation",
    ],
    "science_tech": [
        "physics", "chemistry", "biology", "space_tech",
        "defence_tech", "it_computers",
    ],
    "society": [
        "social_issues", "demographics", "urbanization", "health_education",
    ],
}

DIFFICULTY_DISTRIBUTION = {"easy": 0.25, "medium": 0.50, "hard": 0.25}


class PYQImporter:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_sample_pyqs(
        self,
        subject_map: Dict[str, UUID],
        topic_map: Dict[str, Dict[str, UUID]],
        years: Optional[List[int]] = None,
    ) -> Dict[str, int]:
        if years is None:
            years = list(range(2013, 2025))

        stats = {"questions": 0, "papers": 0, "signals": 0}

        for subject_name, topics in SUBJECT_TOPIC_MAP.items():
            syllabus_subject_id = subject_map.get(subject_name)
            if not syllabus_subject_id:
                continue

            for year in years:
                for paper_type in ["prelims", "mains"]:
                    qp = QuestionPaper(
                        year=year,
                        paper_type=paper_type,
                        exam_type="upsc",
                        subject=subject_name,
                        gs_paper=f"GS-{(years.index(year) % 4) + 1}",
                        total_marks=200 if paper_type == "prelims" else 250,
                        duration_minutes=120 if paper_type == "prelims" else 180,
                    )
                    self.db.add(qp)
                    stats["papers"] += 1
                    await self.db.flush()

                    qs_per_paper = 20 if paper_type == "prelims" else 5
                    import random
                    rng = random.Random(f"{subject_name}_{year}_{paper_type}")

                    for qn in range(1, qs_per_paper + 1):
                        topic_name = topics[qn % len(topics)]
                        topic_id = topic_map.get(subject_name, {}).get(topic_name)

                        difficulty = rng.choices(
                            ["easy", "medium", "hard"],
                            weights=[0.25, 0.50, 0.25],
                        )[0]

                        pyq = PYQ(
                            question_paper_id=qp.id,
                            year=year,
                            paper_type=paper_type,
                            exam_type="upsc",
                            subject=subject_name,
                            topic=topic_name.replace("_", " ").title(),
                            question_number=qn,
                            question_text=f"Sample {paper_type} question {qn} on {topic_name.replace('_', ' ')} ({year}).",
                            question_type="mcq" if paper_type == "prelims" else "descriptive",
                            options=(
                                {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}
                                if paper_type == "prelims" else None
                            ),
                            correct_answer="A" if paper_type == "prelims" else "Sample answer text",
                            answer_explanation=f"This is a sample explanation for question {qn}.",
                            difficulty=difficulty,
                            concepts_tested=[topic_name],
                            marks=2 if paper_type == "prelims" else 15,
                            negative_marks=0.66 if paper_type == "prelims" else None,
                            syllabus_node_id=topic_id,
                            syllabus_node_type="topic",
                            source=f"UPSC {year} {paper_type.title()}",
                        )
                        self.db.add(pyq)
                        stats["questions"] += 1

                await self.db.flush()

        await self.db.commit()
        return stats

    async def compute_signals(self) -> Dict[str, int]:
        stats = {"pyq_signals": 0, "syllabus_signals": 0}

        result = await self.db.execute(
            select(
                PYQ.syllabus_node_id,
                PYQ.syllabus_node_type,
                func.count(PYQ.id),
            ).where(
                PYQ.syllabus_node_id.isnot(None),
            ).group_by(PYQ.syllabus_node_id, PYQ.syllabus_node_type)
        )
        rows = result.all()

        total_count = max(sum(r[2] for r in rows), 1) if rows else 1

        for node_id, node_type, count in rows:
            existing = await self.db.execute(
                select(PYQSignal).where(
                    PYQSignal.node_id == node_id,
                    PYQSignal.node_type == node_type,
                )
            )
            if existing.scalar_one_or_none():
                continue

            signal = PYQSignal(
                node_id=node_id,
                node_type=node_type,
                year=2024,
                paper_type="prelims",
                exam_type="upsc",
                question_count=count,
                total_marks=count * 2,
                avg_difficulty=0.5,
                signal_weight=count / total_count,
            )
            self.db.add(signal)
            stats["pyq_signals"] += 1

        syllabus_rows = rows

        for node_id, node_type, count in syllabus_rows:
            existing = await self.db.execute(
                select(SyllabusSignal).where(
                    SyllabusSignal.node_id == node_id,
                    SyllabusSignal.node_type == node_type,
                )
            )
            if existing.scalar_one_or_none():
                continue

            signal = SyllabusSignal(
                node_id=node_id,
                node_type=node_type,
                total_pyqs=count,
                pyq_frequency_score=min(count / 10.0, 1.0),
                weightage_score=min(count / 20.0, 1.0),
                difficulty_score=0.5,
                recency_score=0.8,
                coverage_score=min(count / 15.0, 1.0),
                overall_importance=min(
                    (count / 10.0) * 0.4 + 0.3 + 0.2 + 0.1,
                    1.0,
                ),
                trend_direction="stable",
            )
            self.db.add(signal)
            stats["syllabus_signals"] += 1

        await self.db.commit()
        return stats
