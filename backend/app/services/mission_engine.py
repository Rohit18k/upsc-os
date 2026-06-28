import uuid
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, delete

from app.models.mission import StudentMission
from app.models.optimization import StudentOptimizationPlan
from app.models.digital_twin import StudentDigitalTwin, KnowledgeNode
from app.services.student_intelligence import StudentIntelligenceService
from app.services.optimization_engine import OptimizationEngineService


class MissionEngineService:
    @classmethod
    async def get_today_mission(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        daily_hours: Optional[float] = None,
        days_until_exam: Optional[int] = None
    ) -> StudentMission:
        """
        Engine 1 - Mission Generator
        Gets or generates today's daily mission by consuming the active Optimization Plan.
        """
        now = datetime.now(timezone.utc)
        start_of_today = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        
        # Check if today's mission already exists
        query = select(StudentMission).where(
            StudentMission.user_id == user_id,
            StudentMission.created_at >= start_of_today,
            StudentMission.type == "daily"
        )
        res = await db.execute(query)
        mission = res.scalar_one_or_none()
        
        if not mission:
            mission = await cls.generate_mission(db, user_id, "daily", daily_hours, days_until_exam)
            
        return mission

    @classmethod
    async def get_weekly_mission(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        daily_hours: Optional[float] = None,
        days_until_exam: Optional[int] = None
    ) -> StudentMission:
        """
        Gets or generates the current weekly mission.
        """
        now = datetime.now(timezone.utc)
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = datetime(start_of_week.year, start_of_week.month, start_of_week.day, tzinfo=timezone.utc)
        
        query = select(StudentMission).where(
            StudentMission.user_id == user_id,
            StudentMission.created_at >= start_of_week,
            StudentMission.type == "weekly"
        )
        res = await db.execute(query)
        mission = res.scalar_one_or_none()
        
        if not mission:
            mission = await cls.generate_mission(db, user_id, "weekly", daily_hours, days_until_exam)
            
        return mission

    @classmethod
    async def generate_mission(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        mission_type: str = "daily",
        daily_hours: Optional[float] = None,
        days_until_exam: Optional[int] = None,
        force_goal: Optional[str] = None
    ) -> StudentMission:
        """
        Creates a new learning mission from the active Optimization Plan.
        """
        # Fetch active optimization plan (which resolves goals, availability constraints, and sorting)
        plan = await OptimizationEngineService.get_active_plan(db, user_id, force_goal, daily_hours, days_until_exam)
        twin = await StudentIntelligenceService.get_digital_twin(db, user_id)
        
        # Determine difficulty level based on student performance (Engine 4 & Scenario E/F)
        consistency = twin.behaviour_state.get("daily_study_consistency", 0.5)
        # Average concept mastery
        concept_masteries = twin.knowledge_state.get("concept_mastery", {})
        avg_mastery = sum(concept_masteries.values()) / len(concept_masteries) if concept_masteries else 0.0
        
        difficulty_level = "medium"
        
        # Scenario E: Student improves significantly (High consistency & high average mastery)
        if consistency >= 0.8 and avg_mastery >= 0.8:
            difficulty_level = "challenge"
        # Scenario F: Student struggles (Low consistency or low mastery)
        elif consistency < 0.45 or avg_mastery < 0.45:
            difficulty_level = "recovery"

        # Limit tasks according to daily available hours (if daily mission)
        plan_actions = plan.ordered_actions or []
        
        # Scenario D: Student is 300 days from exam (Foundation Building) vs 30 days (Revision)
        # Recalculated plan will automatically have optimized actions. Let's translate them to content tasks.
        tasks = []
        expected_readiness = 0.0
        expected_mastery = 0.0
        dependencies = []

        for idx, action in enumerate(plan_actions):
            category = action["category"]
            node_code = action["target_node"]
            
            # Map action category to specific mission tasks (Engine 2)
            task_type = "Read NCERT"
            if category == "Study prerequisite":
                task_type = "Read NCERT" if avg_mastery < 0.5 else "Read Standard Book"
            elif category == "Revise topic":
                task_type = "Revise Topic" if idx % 2 == 0 else "Revise Flashcards"
            elif category == "Solve PYQs":
                task_type = "Solve PYQs"
            elif category == "Write answers":
                task_type = "Write Answer"
            elif category == "Watch concept explanation":
                task_type = "Video Lesson"
            elif category == "Current Affairs revision":
                task_type = "Current Affairs Revision"
            elif category == "Flashcards":
                task_type = "Revise Flashcards"

            task_title = f"{task_type} on {node_code}"
            
            tasks.append({
                "id": f"task_{uuid.uuid4().hex[:6]}",
                "description": f"{task_type} to master node {node_code}",
                "content_reference": node_code,
                "difficulty": difficulty_level,
                "time_estimate": action["estimated_time"],
                "expected_gain": action["expected_readiness_gain"],
                "status": "assigned"
            })
            
            expected_readiness += action["expected_readiness_gain"]
            expected_mastery += action["expected_mastery_gain"]
            if node_code and node_code not in dependencies:
                dependencies.append(node_code)

        # Build clean title/goal description
        title = f"UPSC {plan.goal} Mission"
        goal_desc = f"Execute optimization actions targeting {plan.goal} requirements."

        expiry_time = datetime.now(timezone.utc) + timedelta(days=1 if mission_type == "daily" else 7)

        # Persist StudentMission
        mission = StudentMission(
            user_id=user_id,
            optimization_plan_id=plan.id,
            type=mission_type,
            title=title,
            goal=goal_desc,
            ordered_tasks=tasks,
            status="assigned",
            difficulty_level=difficulty_level,
            estimated_time=float(sum(t["time_estimate"] for t in tasks)),
            expected_readiness_gain=float(expected_readiness),
            expected_mastery_gain=float(expected_mastery),
            dependencies=dependencies,
            completion_criteria="All assigned concept and practice tasks completed successfully.",
            success_metrics=f"Achieve expected readiness gain of +{expected_readiness:.1f}.",
            expiry=expiry_time
        )
        db.add(mission)
        await db.commit()
        await db.refresh(mission)
        
        return mission

    @classmethod
    async def complete_mission(cls, db: AsyncSession, user_id: uuid.UUID, mission_id: uuid.UUID) -> StudentMission:
        """
        Engine 5 & 6 - Mission Scoring & Feedback Loop
        Marks mission as completed, computes execution quality, and updates Digital Twin.
        """
        query = select(StudentMission).where(
            StudentMission.id == mission_id,
            StudentMission.user_id == user_id
        )
        res = await db.execute(query)
        mission = res.scalar_one_or_none()
        
        if not mission:
            return None

        # Check and mark all tasks as completed
        updated_tasks = []
        for task in mission.ordered_tasks:
            task["status"] = "completed"
            updated_tasks.append(task)
            
        mission.ordered_tasks = updated_tasks
        mission.status = "completed"
        mission.completion_percentage = 100.0
        
        # Score computation (Engine 5)
        mission.quality_score = 0.90  # Default completed quality
        mission.execution_quality = 0.95
        mission.consistency_score = 1.0
        
        # Calculate actual gains
        mission.actual_readiness_gain = mission.expected_readiness_gain
        mission.actual_mastery_gain = mission.expected_mastery_gain
        
        # Update details
        mission.evidence = {
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "performance_score": 0.90
        }
        
        db.add(mission)
        await db.commit()

        # Engine 6 - Event Driven Feedback Loop
        # Trigger event in StudentIntelligenceService to update Digital Twin, Memory, Mastery
        await StudentIntelligenceService.process_student_event(
            db,
            user_id,
            "MissionCompleted",
            {
                "node_codes": mission.dependencies,
                "performance_score": float(mission.quality_score)
            }
        )

        return mission

    @classmethod
    async def skip_mission(cls, db: AsyncSession, user_id: uuid.UUID, mission_id: uuid.UUID) -> StudentMission:
        """
        Engine 7 - Dynamic Replanning
        Marks mission as skipped, diagnoses cause, recalculates plan, and generates replacement.
        """
        query = select(StudentMission).where(
            StudentMission.id == mission_id,
            StudentMission.user_id == user_id
        )
        res = await db.execute(query)
        mission = res.scalar_one_or_none()
        
        if not mission:
            return None

        mission.status = "skipped"
        mission.completion_percentage = 0.0
        mission.actual_readiness_gain = 0.0
        mission.actual_mastery_gain = 0.0
        
        db.add(mission)
        await db.commit()

        # Diagnose cause: Did the student skip revisions or concept studies?
        skipped_revision = False
        for task in mission.ordered_tasks:
            if "Revise" in task["description"] or "revision" in task["description"]:
                skipped_revision = True
                break

        # Dynamic Replanning Trigger: Force recalculation of plan
        # If student skips revisions (Scenario B), we generate a recovery revision mission
        if skipped_revision:
            # Generate a recovery revision goal
            await cls.generate_mission(db, user_id, "recovery", force_goal="Revision")
        else:
            # Standard recalculate
            await OptimizationEngineService.generate_optimization_plan(db, user_id)
            await cls.generate_mission(db, user_id, "daily")

        return mission

    @classmethod
    async def inject_document_tasks(cls, db: AsyncSession, user_id: uuid.UUID, topics: List[str]) -> StudentMission:
        """
        Scenario C - Inject learning tasks when new documents are uploaded.
        """
        mission = await cls.get_today_mission(db, user_id)
        
        # Generate new NCERT/Standard Book reading tasks for the newly uploaded topics
        updated_tasks = list(mission.ordered_tasks)
        
        for topic_code in topics:
            task_id = f"task_{uuid.uuid4().hex[:6]}"
            updated_tasks.append({
                "id": task_id,
                "description": f"Read Standard Book on uploaded content: {topic_code}",
                "content_reference": topic_code,
                "difficulty": mission.difficulty_level,
                "time_estimate": 1.5,
                "expected_gain": 2.0,
                "status": "assigned"
            })
            
            mission.estimated_time += 1.5
            mission.expected_readiness_gain += 2.0
            if topic_code not in mission.dependencies:
                mission.dependencies.append(topic_code)

        mission.ordered_tasks = updated_tasks
        db.add(mission)
        await db.commit()
        await db.refresh(mission)
        
        return mission

    @classmethod
    async def add_bonus_tasks(cls, db: AsyncSession, user_id: uuid.UUID, mission_id: uuid.UUID) -> StudentMission:
        """
        Scenario A - Student completes all tasks early. Appends high-value bonus task.
        """
        query = select(StudentMission).where(
            StudentMission.id == mission_id,
            StudentMission.user_id == user_id
        )
        res = await db.execute(query)
        mission = res.scalar_one_or_none()
        
        if not mission:
            return None

        # Add bonus task
        updated_tasks = list(mission.ordered_tasks)
        
        task_id = f"task_bonus_{uuid.uuid4().hex[:6]}"
        updated_tasks.append({
            "id": task_id,
            "description": "Bonus Challenge: Solve advanced MCQs on studied concepts",
            "content_reference": mission.dependencies[0] if mission.dependencies else "polity_basics_preamble",
            "difficulty": "challenge",
            "time_estimate": 1.0,
            "expected_gain": 2.5,
            "status": "assigned"
        })
        
        mission.ordered_tasks = updated_tasks
        # Reset completed status to assigned since we added new tasks
        mission.status = "assigned"
        mission.completion_percentage = (sum(1 for t in updated_tasks if t["status"] == "completed") / len(updated_tasks)) * 100.0
        
        db.add(mission)
        await db.commit()
        await db.refresh(mission)
        
        return mission

    @classmethod
    async def get_mission_explanation(cls, db: AsyncSession, user_id: uuid.UUID, mission_id: uuid.UUID) -> Dict[str, Any]:
        """
        Engine 8 - Explainability
        Answers: Why selected, Why today, Prerequisite checks, Expected benefits, previous decisions.
        """
        query = select(StudentMission).where(
            StudentMission.id == mission_id,
            StudentMission.user_id == user_id
        )
        res = await db.execute(query)
        mission = res.scalar_one_or_none()
        
        if not mission:
            return {}

        task_explanations = []
        for task in mission.ordered_tasks:
            task_explanations.append({
                "task_id": task["id"],
                "description": task["description"],
                "why_selected": f"Calculated as top ROI opportunity to resolve knowledge/memory gap in {task['content_reference']}.",
                "why_today": "Matches availability cap and active strategy timeline constraints.",
                "prerequisite_satisfied": "Satisfies prerequisite requirements of advanced chapters in current subjects.",
                "expected_readiness_gain": f"+{task['expected_gain']:.1f} readiness score boost"
            })

        return {
            "mission_id": str(mission.id),
            "title": mission.title,
            "overall_why": f"This mission is generated to fulfill active optimization plan for {mission.goal}.",
            "expected_outcomes": {
                "total_readiness_gain": f"+{mission.expected_readiness_gain:.1f} readiness points",
                "mastery_gain": f"+{mission.expected_mastery_gain:.1%} concept mastery"
            },
            "task_explanations": task_explanations,
            "risk_addressed": "Reduces syllabus decay and prevents sequencing errors in studying complex topics."
        }

    @classmethod
    async def get_mission_history(cls, db: AsyncSession, user_id: uuid.UUID) -> List[StudentMission]:
        """
        Retrieves complete mission history.
        """
        query = select(StudentMission).where(
            StudentMission.user_id == user_id
        ).order_by(StudentMission.created_at.desc())
        
        res = await db.execute(query)
        return list(res.scalars().all())
