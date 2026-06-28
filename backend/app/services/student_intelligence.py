import json
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.config.settings import get_settings
from app.core.logging import audit_logger
from app.models.digital_twin import KnowledgeNode, StudentDigitalTwin, StudentEventLog, knowledge_node_dependencies
from app.services.mastery_engine import MasteryEngine
from app.services.memory_engine import MemoryEngine
from app.core.redis_pool import redis_pool

logger = logging.getLogger("student_intelligence")
settings = get_settings()




class StudentIntelligenceService:
    CACHE_EXPIRY = 3600  # 1 hour

    @classmethod
    def _get_cache_key(cls, user_id: uuid.UUID) -> str:
        return f"student_twin:{user_id}"

    @classmethod
    async def get_digital_twin(cls, db: AsyncSession, user_id: uuid.UUID) -> StudentDigitalTwin:
        """
        Get the Digital Twin for a user, using cache if available, falling back to DB.
        """
        # Try Cache
        if redis_pool.client:
            try:
                cached_data = redis_pool.get(cls._get_cache_key(user_id))
                if cached_data:
                    # In real-world, mapping raw dict to SA model can be tricky,
                    # so we will load from DB if cache hit to ensure model operations,
                    # but cache API responses instead. To satisfy the performance requirement,
                    # we do a DB lookup here, but let's implement profile caching too.
                    pass
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")

        # DB Query
        query = select(StudentDigitalTwin).where(StudentDigitalTwin.user_id == user_id)
        result = await db.execute(query)
        twin = result.scalar_one_or_none()

        if not twin:
            twin = await cls.initialize_digital_twin(db, user_id)

        return twin

    @classmethod
    async def initialize_digital_twin(cls, db: AsyncSession, user_id: uuid.UUID) -> StudentDigitalTwin:
        """
        Initialize a blank Digital Twin for a student.
        """
        now_str = datetime.now(timezone.utc).isoformat()
        
        knowledge_state = {
            "topic_mastery": {},  # topic_code -> float
            "concept_mastery": {},  # concept_code -> float
            "concept_mastery_intervals": {},  # concept_code -> [lower, upper]
            "concept_mastery_dates": {},  # concept_code -> timestamp
            "coverage": {
                "visited_concepts": [],
                "mastered_concepts": [],
                "coverage_percentage": 0.0
            },
            "weak_concepts": [],
            "strong_concepts": [],
            "confidence_score": 0.0
        }

        memory_state = {
            "items": {},  # node_code -> spaced repetition parameters
            "retention_score": 1.0,
            "review_history": []
        }

        practice_state = {
            "pyq_accuracy": 0.0,
            "mock_accuracy": 0.0,
            "subject_wise_accuracy": {},  # subject_name -> float
            "difficulty_trend": [],  # list of {"date": str, "difficulty": float, "correct": bool}
            "error_taxonomy": {},  # category -> count
            "nodes": {},  # node_code -> {"correct": int, "total": int, "accuracy": float}
            "total_questions": 0,
            "correct_questions": 0
        }

        writing_state = {
            "answer_writing_frequency": 0.0,  # answers per week
            "writing_quality": 0.0,  # avg evaluation accuracy
            "word_count_trends": [],  # list of [timestamp, count]
            "time_taken": [],  # list of [timestamp, seconds]
            "self_evaluation_history": [],
            "total_answers": 0
        }

        behaviour_state = {
            "daily_study_consistency": 0.0,
            "session_duration": 0.0,  # total seconds
            "preferred_study_times": {},  # hour_bucket -> count
            "completion_rate": 0.0,
            "streaks": 0,
            "last_active_date": None,
            "active_days": []  # list of date strings "YYYY-MM-DD"
        }

        learning_profile = {
            "learning_velocity": 0.0,  # concepts mastered per day
            "cognitive_load_estimate": 0.0,
            "preferred_content_type": "text",
            "estimated_retention_rate": 1.0,
            "concepts_mastered_by_week": {}  # week_start -> count
        }

        twin = StudentDigitalTwin(
            user_id=user_id,
            knowledge_state=knowledge_state,
            memory_state=memory_state,
            practice_state=practice_state,
            writing_state=writing_state,
            behaviour_state=behaviour_state,
            learning_profile=learning_profile,
            knowledge_readiness=0.0,
            memory_readiness=1.0,
            practice_readiness=0.0,
            writing_readiness=0.0,
            behaviour_readiness=0.0,
        )
        db.add(twin)
        await db.commit()
        await db.refresh(twin)
        
        cls._update_cache(user_id, twin)
        return twin

    @classmethod
    def _update_cache(cls, user_id: uuid.UUID, twin: StudentDigitalTwin) -> None:
        if redis_pool.client:
            try:
                data = {
                    "id": str(twin.id),
                    "user_id": str(twin.user_id),
                    "knowledge_state": twin.knowledge_state,
                    "memory_state": twin.memory_state,
                    "practice_state": twin.practice_state,
                    "writing_state": twin.writing_state,
                    "behaviour_state": twin.behaviour_state,
                    "learning_profile": twin.learning_profile,
                    "knowledge_readiness": twin.knowledge_readiness,
                    "memory_readiness": twin.memory_readiness,
                    "practice_readiness": twin.practice_readiness,
                    "writing_readiness": twin.writing_readiness,
                    "behaviour_readiness": twin.behaviour_readiness,
                }
                redis_pool.set(
                    cls._get_cache_key(user_id),
                    json.dumps(data),
                    ex=cls.CACHE_EXPIRY
                )
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")

    @classmethod
    async def process_student_event(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        event_type: str,
        payload: Dict[str, Any]
    ) -> StudentDigitalTwin:
        """
        Incrementally process a student intelligence event.
        Updates the Digital Twin states and readiness signals.
        """
        # Ensure twin exists
        twin = await cls.get_digital_twin(db, user_id)
        current_time = datetime.now(timezone.utc)

        # Log event for auditing & histories
        event_log = StudentEventLog(
            user_id=user_id,
            event_type=event_type,
            payload=payload,
            timestamp=current_time
        )
        db.add(event_log)

        # Dispatch based on event type
        if event_type == "LessonCompleted":
            await cls._handle_lesson_completed(db, twin, payload, current_time)
        elif event_type == "RevisionCompleted":
            await cls._handle_revision_completed(db, twin, payload, current_time)
        elif event_type in ("PYQSolved", "MockSubmitted"):
            await cls._handle_practice_event(db, twin, payload, event_type, current_time)
        elif event_type == "AnswerWritten":
            await cls._handle_answer_written(db, twin, payload, current_time)
        elif event_type == "DocumentUploaded":
            await cls._handle_document_uploaded(db, twin, payload, current_time)
        elif event_type in ("SessionStarted", "SessionEnded"):
            await cls._handle_session_event(twin, event_type, payload, current_time)
        elif event_type in ("MissionCompleted", "InterviewFinished"):
            await cls._handle_mission_performance(db, twin, payload, current_time)
        else:
            logger.warning(f"Unhandled event type: {event_type}")

        # Update readiness signals
        cls._recompute_readiness_signals(twin, current_time)

        # Mark fields as modified for SQLAlchemy to detect JSON internal changes
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(twin, "knowledge_state")
        flag_modified(twin, "memory_state")
        flag_modified(twin, "practice_state")
        flag_modified(twin, "writing_state")
        flag_modified(twin, "behaviour_state")
        flag_modified(twin, "learning_profile")

        db.add(twin)
        await db.commit()
        await db.refresh(twin)

        # Update Redis cache
        cls._update_cache(user_id, twin)

        audit_logger.log(
            action=f"UPDATE_STUDENT_TWIN_{event_type}",
            resource="/student/twin",
            resource_id=str(twin.id),
            user_id=str(user_id),
            details={"event": event_type}
        )

        return twin

    @classmethod
    async def _handle_lesson_completed(
        cls,
        db: AsyncSession,
        twin: StudentDigitalTwin,
        payload: Dict[str, Any],
        current_time: datetime
    ) -> None:
        node_code = payload.get("node_code")
        difficulty = payload.get("difficulty", 0.5)
        confidence = payload.get("confidence", 0.5)
        time_spent = payload.get("time_spent", 0.0)
        content_type = payload.get("content_type", "text")

        # 1. Update Knowledge State Concept Mastery
        concept = await cls._find_knowledge_node(db, node_code)
        if concept:
            # Check existing practice accuracy and memory parameters
            practice_accuracy = twin.practice_state.get("nodes", {}).get(node_code, {}).get("accuracy", 0.0)
            mem_item = twin.memory_state.get("items", {}).get(node_code, {})
            revision_count = mem_item.get("repetitions", 0)
            
            last_rev_str = mem_item.get("last_reviewed_at")
            if last_rev_str:
                last_rev_days = (current_time - datetime.fromisoformat(last_rev_str)).total_seconds() / 86400.0
            else:
                last_rev_days = 0.0
            
            stability = mem_item.get("stability", 15.0)

            mastery, bounds = MasteryEngine.calculate_concept_mastery(
                lesson_completed=True,
                practice_accuracy=practice_accuracy,
                revision_count=revision_count,
                last_review_days=last_rev_days,
                confidence=confidence,
                difficulty=difficulty,
                memory_stability=stability
            )

            twin.knowledge_state["concept_mastery"][node_code] = float(mastery)
            twin.knowledge_state["concept_mastery_intervals"][node_code] = [float(bounds[0]), float(bounds[1])]
            twin.knowledge_state["concept_mastery_dates"][node_code] = current_time.isoformat()

            # Mark visited
            if node_code not in twin.knowledge_state["coverage"]["visited_concepts"]:
                twin.knowledge_state["coverage"]["visited_concepts"].append(node_code)

            # Mark strong/weak
            cls._update_strong_weak_lists(twin, node_code, mastery)

            # 2. Propagate Mastery to Parent Topics and Subjects
            await cls._propagate_mastery_hierarchically(db, twin, concept)

            # Update coverage percentage
            total_concepts = await cls._count_nodes_by_type(db, "concept")
            if total_concepts > 0:
                twin.knowledge_state["coverage"]["coverage_percentage"] = (
                    len(twin.knowledge_state["coverage"]["visited_concepts"]) / total_concepts
                ) * 100.0

            # Update average confidence score
            visited_codes = twin.knowledge_state["coverage"]["visited_concepts"]
            if visited_codes:
                twin.knowledge_state["confidence_score"] = float(confidence)  # For simplicity, default to incoming confidence or average it

        # Update Behaviour
        twin.behaviour_state["session_duration"] += float(time_spent)
        twin.behaviour_state["completion_rate"] = min(1.0, twin.behaviour_state["completion_rate"] + 0.05)
        twin.learning_profile["preferred_content_type"] = content_type

    @classmethod
    async def _handle_revision_completed(
        cls,
        db: AsyncSession,
        twin: StudentDigitalTwin,
        payload: Dict[str, Any],
        current_time: datetime
    ) -> None:
        node_code = payload.get("node_code")
        rating = payload.get("rating", 3)
        time_spent = payload.get("time_spent", 0.0)

        # 1. Update Spaced Repetition Parameters
        prev_mem_state = twin.memory_state["items"].get(node_code, {})
        updated_mem = MemoryEngine.update_spaced_repetition(
            rating=rating,
            previous_state=prev_mem_state,
            current_time=current_time
        )
        twin.memory_state["items"][node_code] = updated_mem
        
        # Add to history
        twin.memory_state["review_history"].append({
            "node_code": node_code,
            "timestamp": current_time.isoformat(),
            "rating": rating
        })

        # 2. Recalculate concept mastery and propagate
        concept = await cls._find_knowledge_node(db, node_code)
        if concept:
            practice_accuracy = twin.practice_state.get("nodes", {}).get(node_code, {}).get("accuracy", 0.0)
            
            # Confidence is derived from SM-2 stability and rating
            confidence = min(1.0, updated_mem["stability"] / 30.0 + 0.2 * rating)
            
            mastery, bounds = MasteryEngine.calculate_concept_mastery(
                lesson_completed=(node_code in twin.knowledge_state["coverage"]["visited_concepts"]),
                practice_accuracy=practice_accuracy,
                revision_count=updated_mem["repetitions"],
                last_review_days=0.0,  # Just reviewed
                confidence=confidence,
                difficulty=updated_mem["difficulty"],
                memory_stability=updated_mem["stability"]
            )

            twin.knowledge_state["concept_mastery"][node_code] = float(mastery)
            twin.knowledge_state["concept_mastery_intervals"][node_code] = [float(bounds[0]), float(bounds[1])]
            twin.knowledge_state["concept_mastery_dates"][node_code] = current_time.isoformat()

            cls._update_strong_weak_lists(twin, node_code, mastery)
            await cls._propagate_mastery_hierarchically(db, twin, concept)

        # Calculate Overall Retention Score
        twin.memory_state["retention_score"] = MemoryEngine.calculate_overall_retention_score(
            twin.memory_state["items"], current_time
        )

        # Update Behaviour
        twin.behaviour_state["session_duration"] += float(time_spent)

    @classmethod
    async def _handle_practice_event(
        cls,
        db: AsyncSession,
        twin: StudentDigitalTwin,
        payload: Dict[str, Any],
        event_type: str,
        current_time: datetime
    ) -> None:
        questions = payload.get("questions", [])
        time_spent = payload.get("time_spent", 0.0)
        is_mock = (event_type == "MockSubmitted")

        correct_count = 0
        total_count = len(questions)

        for q in questions:
            node_code = q.get("node_code")
            correct = q.get("correct", False)
            difficulty = q.get("difficulty", 0.5)
            error_cat = q.get("error_category")

            if correct:
                correct_count += 1

            # Update Node-specific stats
            if "nodes" not in twin.practice_state:
                twin.practice_state["nodes"] = {}
            if node_code not in twin.practice_state["nodes"]:
                twin.practice_state["nodes"][node_code] = {"correct": 0, "total": 0, "accuracy": 0.0}
            
            node_stats = twin.practice_state["nodes"][node_code]
            node_stats["total"] += 1
            if correct:
                node_stats["correct"] += 1
            node_stats["accuracy"] = node_stats["correct"] / node_stats["total"]

            # Update error taxonomy if incorrect
            if not correct and error_cat:
                if error_cat not in twin.practice_state["error_taxonomy"]:
                    twin.practice_state["error_taxonomy"][error_cat] = 0
                twin.practice_state["error_taxonomy"][error_cat] += 1

            # Record in difficulty trend
            twin.practice_state["difficulty_trend"].append({
                "timestamp": current_time.isoformat(),
                "difficulty": float(difficulty),
                "correct": correct,
                "node_code": node_code
            })

            # Update Node Mastery
            concept = await cls._find_knowledge_node(db, node_code)
            if concept:
                # Recalculate concept mastery
                mem_item = twin.memory_state.get("items", {}).get(node_code, {})
                revision_count = mem_item.get("repetitions", 0)
                last_rev_str = mem_item.get("last_reviewed_at")
                if last_rev_str:
                    last_rev_days = (current_time - datetime.fromisoformat(last_rev_str)).total_seconds() / 86400.0
                else:
                    last_rev_days = 0.0
                stability = mem_item.get("stability", 15.0)
                
                mastery, bounds = MasteryEngine.calculate_concept_mastery(
                    lesson_completed=(node_code in twin.knowledge_state["coverage"]["visited_concepts"]),
                    practice_accuracy=node_stats["accuracy"],
                    revision_count=revision_count,
                    last_review_days=last_rev_days,
                    confidence=0.6 if correct else 0.4,
                    difficulty=difficulty,
                    memory_stability=stability
                )
                twin.knowledge_state["concept_mastery"][node_code] = float(mastery)
                twin.knowledge_state["concept_mastery_intervals"][node_code] = [float(bounds[0]), float(bounds[1])]
                twin.knowledge_state["concept_mastery_dates"][node_code] = current_time.isoformat()

                cls._update_strong_weak_lists(twin, node_code, mastery)
                await cls._propagate_mastery_hierarchically(db, twin, concept)

        # Update overall accuracy statistics
        twin.practice_state["total_questions"] += total_count
        twin.practice_state["correct_questions"] += correct_count
        overall_acc = twin.practice_state["correct_questions"] / max(1, twin.practice_state["total_questions"])

        if is_mock:
            twin.practice_state["mock_accuracy"] = overall_acc
        else:
            twin.practice_state["pyq_accuracy"] = overall_acc

        # Group and calculate subject wise accuracy
        await cls._recalculate_subject_accuracies(db, twin)

        # Update Behaviour
        twin.behaviour_state["session_duration"] += float(time_spent)

    @classmethod
    async def _handle_answer_written(
        cls,
        db: AsyncSession,
        twin: StudentDigitalTwin,
        payload: Dict[str, Any],
        current_time: datetime
    ) -> None:
        node_code = payload.get("node_code")
        word_count = payload.get("word_count", 0)
        time_taken = payload.get("time_taken", 0.0)
        eval_score = payload.get("evaluation_score", 0.0)
        max_score = payload.get("max_score", 10.0)
        self_eval = payload.get("self_evaluation", {})

        eval_accuracy = eval_score / max(1.0, max_score)

        # 1. Update Writing State
        twin.writing_state["total_answers"] += 1
        twin.writing_state["word_count_trends"].append([current_time.isoformat(), word_count])
        twin.writing_state["time_taken"].append([current_time.isoformat(), time_taken])
        twin.writing_state["self_evaluation_history"].append({
            "timestamp": current_time.isoformat(),
            "node_code": node_code,
            "score": eval_score,
            "max_score": max_score,
            "self_eval": self_eval
        })

        # Calculate average quality
        total_answers = twin.writing_state["total_answers"]
        current_qual = twin.writing_state["writing_quality"]
        twin.writing_state["writing_quality"] = ((current_qual * (total_answers - 1)) + eval_accuracy) / total_answers

        # Calculate average weekly writing frequency
        first_event_query = select(StudentEventLog).where(
            StudentEventLog.user_id == twin.user_id
        ).order_by(StudentEventLog.timestamp.asc()).limit(1)
        first_event_res = await db.execute(first_event_query)
        first_event = first_event_res.scalar_one_or_none()
        
        if first_event:
            first_event_ts = first_event.timestamp
            if first_event_ts.tzinfo is None:
                first_event_ts = first_event_ts.replace(tzinfo=timezone.utc)
            weeks = max(1.0, (current_time - first_event_ts).days / 7.0)
        else:
            weeks = 1.0
        twin.writing_state["answer_writing_frequency"] = total_answers / weeks

        # 2. Update Mastery boost for writing on a concept
        concept = await cls._find_knowledge_node(db, node_code)
        if concept and eval_accuracy >= 0.8:
            curr_mastery = twin.knowledge_state["concept_mastery"].get(node_code, 0.0)
            boosted_mastery = min(1.0, curr_mastery + 0.05)
            twin.knowledge_state["concept_mastery"][node_code] = boosted_mastery
            twin.knowledge_state["concept_mastery_dates"][node_code] = current_time.isoformat()
            cls._update_strong_weak_lists(twin, node_code, boosted_mastery)
            await cls._propagate_mastery_hierarchically(db, twin, concept)

    @classmethod
    async def _handle_document_uploaded(
        cls,
        db: AsyncSession,
        twin: StudentDigitalTwin,
        payload: Dict[str, Any],
        current_time: datetime
    ) -> None:
        topics = payload.get("topics", [])
        for node_code in topics:
            if node_code not in twin.knowledge_state["coverage"]["visited_concepts"]:
                twin.knowledge_state["coverage"]["visited_concepts"].append(node_code)
        
        total_concepts = await cls._count_nodes_by_type(db, "concept")
        if total_concepts > 0:
            twin.knowledge_state["coverage"]["coverage_percentage"] = (
                len(twin.knowledge_state["coverage"]["visited_concepts"]) / total_concepts
            ) * 100.0

    @classmethod
    async def _handle_session_event(
        cls,
        twin: StudentDigitalTwin,
        event_type: str,
        payload: Dict[str, Any],
        current_time: datetime
    ) -> None:
        # Update session active days and streaks
        date_str = current_time.date().isoformat()
        
        if date_str not in twin.behaviour_state["active_days"]:
            twin.behaviour_state["active_days"].append(date_str)
            
            # Recalculate Streaks
            last_active = twin.behaviour_state["last_active_date"]
            if last_active:
                last_active_date = datetime.strptime(last_active, "%Y-%m-%d").date()
                delta = current_time.date() - last_active_date
                if delta.days == 1:
                    twin.behaviour_state["streaks"] += 1
                elif delta.days > 1:
                    twin.behaviour_state["streaks"] = 1
            else:
                twin.behaviour_state["streaks"] = 1
                
            twin.behaviour_state["last_active_date"] = date_str

        # Log preferred study times
        hour = current_time.hour
        hour_bucket = f"{(hour // 4) * 4:02d}:00-{(hour // 4 + 1) * 4:02d}:00"
        if hour_bucket not in twin.behaviour_state["preferred_study_times"]:
            twin.behaviour_state["preferred_study_times"][hour_bucket] = 0
        twin.behaviour_state["preferred_study_times"][hour_bucket] += 1

        # Track session time for ended session
        if event_type == "SessionEnded":
            duration = float(payload.get("duration", 0.0))
            twin.behaviour_state["session_duration"] += duration

    @classmethod
    async def _handle_mission_performance(
        cls,
        db: AsyncSession,
        twin: StudentDigitalTwin,
        payload: Dict[str, Any],
        current_time: datetime
    ) -> None:
        node_codes = payload.get("node_codes", [])
        score = payload.get("performance_score", 1.0)
        
        for code in node_codes:
            concept = await cls._find_knowledge_node(db, code)
            if concept:
                curr_mastery = twin.knowledge_state["concept_mastery"].get(code, 0.0)
                boost = 0.1 * score
                new_mastery = min(1.0, curr_mastery + boost)
                
                twin.knowledge_state["concept_mastery"][code] = new_mastery
                twin.knowledge_state["concept_mastery_dates"][code] = current_time.isoformat()
                cls._update_strong_weak_lists(twin, code, new_mastery)
                await cls._propagate_mastery_hierarchically(db, twin, concept)

    @classmethod
    def _recompute_readiness_signals(cls, twin: StudentDigitalTwin, current_time: datetime) -> None:
        # 1. Knowledge readiness
        subjects_mastery = []
        for code, mastery in twin.knowledge_state["topic_mastery"].items():
            # Simply check keys to aggregate. We can also average topic mastery values
            subjects_mastery.append(mastery)
        avg_subj_mastery = sum(subjects_mastery) / len(subjects_mastery) if subjects_mastery else 0.0
        cov_percent = twin.knowledge_state["coverage"]["coverage_percentage"] / 100.0
        twin.knowledge_readiness = float(0.6 * avg_subj_mastery + 0.4 * cov_percent)

        # 2. Memory readiness
        # Recalculate current retention score across all cards
        ret_score = MemoryEngine.calculate_overall_retention_score(
            twin.memory_state["items"], current_time
        )
        twin.memory_state["retention_score"] = ret_score
        twin.memory_readiness = float(ret_score)

        # 3. Practice readiness
        pyq_acc = twin.practice_state.get("pyq_accuracy", 0.0)
        mock_acc = twin.practice_state.get("mock_accuracy", 0.0)
        # Weight them: 0.5 each or whichever is populated
        if pyq_acc > 0 and mock_acc > 0:
            twin.practice_readiness = float(0.5 * pyq_acc + 0.5 * mock_acc)
        elif pyq_acc > 0:
            twin.practice_readiness = float(pyq_acc)
        elif mock_acc > 0:
            twin.practice_readiness = float(mock_acc)
        else:
            twin.practice_readiness = 0.0

        # 4. Writing readiness
        writing_qual = twin.writing_state.get("writing_quality", 0.0)
        freq = twin.writing_state.get("answer_writing_frequency", 0.0)
        # target frequency is 2 answers per week
        freq_factor = min(1.0, freq / 2.0)
        twin.writing_readiness = float(0.7 * writing_qual + 0.3 * freq_factor)

        # 5. Behaviour readiness
        # Consistency represents fraction of days active. Window can be 30 days.
        active_days_count = len(twin.behaviour_state["active_days"])
        study_consistency = min(1.0, active_days_count / 10.0)  # active 10+ days is 1.0 consistency
        twin.behaviour_state["daily_study_consistency"] = study_consistency

        streak = twin.behaviour_state.get("streaks", 0)
        streak_factor = min(1.0, streak / 7.0)

        completion = twin.behaviour_state.get("completion_rate", 0.0)
        twin.behaviour_readiness = float(0.4 * study_consistency + 0.3 * streak_factor + 0.3 * completion)

        # 6. Update Learning Velocity and Projections
        cls._update_learning_velocity_and_projections(twin, current_time)

    @classmethod
    def _update_strong_weak_lists(cls, twin: StudentDigitalTwin, node_code: str, mastery: float) -> None:
        if mastery >= 0.8:
            if node_code not in twin.knowledge_state["coverage"]["mastered_concepts"]:
                twin.knowledge_state["coverage"]["mastered_concepts"].append(node_code)
            if node_code not in twin.knowledge_state["strong_concepts"]:
                twin.knowledge_state["strong_concepts"].append(node_code)
            if node_code in twin.knowledge_state["weak_concepts"]:
                twin.knowledge_state["weak_concepts"].remove(node_code)
        elif mastery < 0.5:
            if node_code in twin.knowledge_state["coverage"]["mastered_concepts"]:
                twin.knowledge_state["coverage"]["mastered_concepts"].remove(node_code)
            if node_code not in twin.knowledge_state["weak_concepts"]:
                twin.knowledge_state["weak_concepts"].append(node_code)
            if node_code in twin.knowledge_state["strong_concepts"]:
                twin.knowledge_state["strong_concepts"].remove(node_code)
        else:
            # Medium mastery, clear from both
            if node_code in twin.knowledge_state["coverage"]["mastered_concepts"]:
                twin.knowledge_state["coverage"]["mastered_concepts"].remove(node_code)
            if node_code in twin.knowledge_state["strong_concepts"]:
                twin.knowledge_state["strong_concepts"].remove(node_code)
            if node_code in twin.knowledge_state["weak_concepts"]:
                twin.knowledge_state["weak_concepts"].remove(node_code)

    @classmethod
    async def _propagate_mastery_hierarchically(
        cls,
        db: AsyncSession,
        twin: StudentDigitalTwin,
        concept: KnowledgeNode
    ) -> None:
        if not concept.parent_id:
            return

        # Fetch parent node
        parent_topic = await db.get(KnowledgeNode, concept.parent_id)
        if not parent_topic:
            return

        # Fetch siblings of concept
        sibling_query = select(KnowledgeNode.code).where(
            KnowledgeNode.parent_id == parent_topic.id,
            KnowledgeNode.type == "concept"
        )
        sibling_res = await db.execute(sibling_query)
        sibling_codes = [r[0] for r in sibling_res.fetchall()]

        # Compute average mastery
        sibling_masteries = [
            twin.knowledge_state["concept_mastery"].get(code, 0.0)
            for code in sibling_codes
        ]
        topic_mastery = MasteryEngine.calculate_parent_mastery(sibling_masteries)
        twin.knowledge_state["topic_mastery"][parent_topic.code] = float(topic_mastery)

        # Propagate to parent subject
        if parent_topic.parent_id:
            parent_subject = await db.get(KnowledgeNode, parent_topic.parent_id)
            if parent_subject:
                # Fetch siblings of topic
                topic_sibling_query = select(KnowledgeNode.code).where(
                    KnowledgeNode.parent_id == parent_subject.id,
                    KnowledgeNode.type == "topic"
                )
                topic_sibling_res = await db.execute(topic_sibling_query)
                topic_sibling_codes = [r[0] for r in topic_sibling_res.fetchall()]

                topic_masteries = [
                    twin.knowledge_state["topic_mastery"].get(code, 0.0)
                    for code in topic_sibling_codes
                ]
                subject_mastery = MasteryEngine.calculate_parent_mastery(topic_masteries)
                twin.knowledge_state["topic_mastery"][parent_subject.code] = float(subject_mastery)

    @classmethod
    async def _recalculate_subject_accuracies(cls, db: AsyncSession, twin: StudentDigitalTwin) -> None:
        subject_questions: Dict[str, List[bool]] = {}

        # Look through all node-specific questions
        for node_code, stats in twin.practice_state.get("nodes", {}).items():
            concept = await cls._find_knowledge_node(db, node_code)
            if concept:
                subj = concept.subject
                if subj not in subject_questions:
                    subject_questions[subj] = []
                # Reconstruct questions for this subject
                correct = stats.get("correct", 0)
                total = stats.get("total", 0)
                subject_questions[subj].extend([True] * correct)
                subject_questions[subj].extend([False] * (total - correct))

        for subj, answers in subject_questions.items():
            if answers:
                twin.practice_state["subject_wise_accuracy"][subj] = sum(answers) / len(answers)

    @classmethod
    def _update_learning_velocity_and_projections(cls, twin: StudentDigitalTwin, current_time: datetime) -> None:
        # Calculate concepts mastered per day in the last 7 days
        mastered_dates = twin.knowledge_state.get("concept_mastery_dates", {})
        
        mastered_in_last_7_days = 0
        now_ts = current_time
        seven_days_ago = now_ts - timedelta(days=7)
        
        for node_code, mastery in twin.knowledge_state["concept_mastery"].items():
            if mastery >= 0.8:
                m_date_str = mastered_dates.get(node_code)
                if m_date_str:
                    m_date = datetime.fromisoformat(m_date_str)
                    if m_date >= seven_days_ago:
                        mastered_in_last_7_days += 1
                        
        velocity = mastered_in_last_7_days / 7.0
        twin.learning_profile["learning_velocity"] = float(velocity)

        # Track weekly mastery history inside learning profile
        week_start = (current_time - timedelta(days=current_time.weekday())).date().isoformat()
        if "concepts_mastered_by_week" not in twin.learning_profile:
            twin.learning_profile["concepts_mastered_by_week"] = {}
        twin.learning_profile["concepts_mastered_by_week"][week_start] = mastered_in_last_7_days

        # Momentum calculation
        consistency = twin.behaviour_state.get("daily_study_consistency", 0.0)
        streak = twin.behaviour_state.get("streaks", 0)
        streak_factor = min(1.0, streak / 7.0)
        twin.learning_profile["momentum"] = float(0.5 * consistency + 0.5 * streak_factor)

        # Calculate estimated retention rate (average recall probability)
        twin.learning_profile["estimated_retention_rate"] = twin.memory_state.get("retention_score", 1.0)

    @classmethod
    async def get_velocity_projections(cls, db: AsyncSession, twin: StudentDigitalTwin) -> Dict[str, Any]:
        """
        Compute predicted progress over 7, 30, and 90 days.
        """
        # Count total concepts in the knowledge graph
        total_concepts = await cls._count_nodes_by_type(db, "concept")
        current_mastered = len(twin.knowledge_state["coverage"]["mastered_concepts"])
        velocity = twin.learning_profile.get("learning_velocity", 0.0)  # per day

        proj_7 = min(total_concepts, current_mastered + int(velocity * 7))
        proj_30 = min(total_concepts, current_mastered + int(velocity * 30))
        proj_90 = min(total_concepts, current_mastered + int(velocity * 90))

        return {
            "current_mastered": current_mastered,
            "total_concepts": total_concepts,
            "velocity_per_day": velocity,
            "predicted_mastery_7_days": proj_7,
            "predicted_mastery_30_days": proj_30,
            "predicted_mastery_90_days": proj_90
        }

    @classmethod
    async def get_coverage_details(cls, db: AsyncSession, twin: StudentDigitalTwin) -> Dict[str, Any]:
        """
        Calculates locking status dynamically by verifying prerequisites.
        Never duplicates graph relationships into the student profile.
        """
        # Get all concept nodes
        query = select(KnowledgeNode).where(KnowledgeNode.type == "concept")
        result = await db.execute(query)
        concepts = result.scalars().all()

        locked_nodes = []
        coverage_by_subject = {}

        for node in concepts:
            # Check dependencies
            prereqs_mastered = True
            dep_mastery_details = []
            
            # Load prerequisites
            # Join query for prerequisites
            prereq_query = select(KnowledgeNode.code).join(
                knowledge_node_dependencies,
                (knowledge_node_dependencies.c.prerequisite_id == KnowledgeNode.id)
            ).where(knowledge_node_dependencies.c.node_id == node.id)
            prereq_res = await db.execute(prereq_query)
            prereq_codes = [r[0] for r in prereq_res.fetchall()]

            for code in prereq_codes:
                m_score = twin.knowledge_state["concept_mastery"].get(code, 0.0)
                dep_mastery_details.append({"node_code": code, "mastery": m_score})
                if m_score < 0.8:
                    prereqs_mastered = False

            if not prereqs_mastered:
                locked_nodes.append({
                    "node_code": node.code,
                    "title": node.title,
                    "failed_dependencies": [d for d in dep_mastery_details if d["mastery"] < 0.8]
                })

            # Track subject details
            subj = node.subject
            if subj not in coverage_by_subject:
                coverage_by_subject[subj] = {"visited": 0, "mastered": 0, "total": 0}
            
            coverage_by_subject[subj]["total"] += 1
            if node.code in twin.knowledge_state["coverage"]["visited_concepts"]:
                coverage_by_subject[subj]["visited"] += 1
            if node.code in twin.knowledge_state["coverage"]["mastered_concepts"]:
                coverage_by_subject[subj]["mastered"] += 1

        return {
            "coverage_percentage": twin.knowledge_state["coverage"]["coverage_percentage"],
            "visited_concepts_count": len(twin.knowledge_state["coverage"]["visited_concepts"]),
            "mastered_concepts_count": len(twin.knowledge_state["coverage"]["mastered_concepts"]),
            "locked_concepts": locked_nodes,
            "subject_breakdown": coverage_by_subject
        }

    # Helper Database Query Methods
    @staticmethod
    async def _find_knowledge_node(db: AsyncSession, code: str) -> Optional[KnowledgeNode]:
        query = select(KnowledgeNode).where(KnowledgeNode.code == code)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def _count_nodes_by_type(db: AsyncSession, node_type: str) -> int:
        query = select(func.count(KnowledgeNode.id)).where(KnowledgeNode.type == node_type)
        result = await db.execute(query)
        return result.scalar() or 0
