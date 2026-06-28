import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user_id, get_current_user_role
from app.core.exception_handlers import NotFoundError
from app.core.response import success_response
from app.core.logging import audit_logger
from app.api.v1.endpoints.student_intelligence import check_row_level_auth
from app.services.mentor_intelligence import MentorIntelligenceService

router = APIRouter()


@router.get("/briefing")
async def get_morning_briefing(
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    brief = await MentorIntelligenceService.generate_briefing(db, target_id)
    
    audit_logger.log(
        action="GET_MENTOR_BRIEFING",
        resource="/mentor/briefing",
        resource_id=str(target_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(brief)


@router.get("/review")
async def get_evening_review(
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    review = await MentorIntelligenceService.generate_review(db, target_id)
    
    audit_logger.log(
        action="GET_MENTOR_REVIEW",
        resource="/mentor/review",
        resource_id=str(target_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(review)


@router.post("/chat")
async def mentor_chat(
    student_id: Optional[uuid.UUID] = None,
    message: str = Body(..., embed=True),
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    interaction = await MentorIntelligenceService.mentor_chat(db, target_id, message)

    serialized = serialize_interaction(interaction)
    audit_logger.log(
        action="POST_MENTOR_CHAT",
        resource="/mentor/chat",
        resource_id=str(interaction.id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id), "cache_hit": interaction.cache_hit}
    )
    return success_response(serialized)


@router.post("/socratic")
async def mentor_socratic(
    student_id: Optional[uuid.UUID] = None,
    message: str = Body(..., embed=True),
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    result = await MentorIntelligenceService.mentor_socratic(db, target_id, message)
    
    audit_logger.log(
        action="POST_MENTOR_SOCRATIC",
        resource="/mentor/socratic",
        resource_id=str(result["interaction_id"]),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(result)


@router.post("/answer-review")
async def mentor_answer_review(
    student_id: Optional[uuid.UUID] = None,
    answer: str = Body(..., embed=True),
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    result = await MentorIntelligenceService.mentor_answer_review(db, target_id, answer)

    audit_logger.log(
        action="POST_MENTOR_ANSWER_REVIEW",
        resource="/mentor/answer-review",
        resource_id=str(result["interaction_id"]),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(result)


@router.post("/gap-simulation")
async def mentor_gap_simulation(
    student_id: Optional[uuid.UUID] = None,
    subject: str = Body(..., embed=True),
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    result = await MentorIntelligenceService.mentor_gap_simulation(db, target_id, subject)

    audit_logger.log(
        action="POST_MENTOR_GAP_SIMULATION",
        resource="/mentor/gap-simulation",
        resource_id=str(target_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id), "simulated_subject": subject}
    )
    return success_response(result)


@router.get("/memory")
async def get_mentor_memory(
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    memory = await MentorIntelligenceService.get_or_create_mentor_memory(db, target_id)

    serialized = {
        "weak_concepts": list(memory.weak_concepts.keys()) if isinstance(memory.weak_concepts, dict) else [],
        "learning_preferences": memory.learning_preferences,
        "repeated_mistakes": memory.repeated_mistakes,
        "writing_weaknesses": memory.writing_weaknesses,
        "revision_habits": memory.revision_habits,
        "confidence_trends": memory.confidence_trends,
        "burnout_history": memory.burnout_history
    }
    
    audit_logger.log(
        action="GET_MENTOR_MEMORY",
        resource="/mentor/memory",
        resource_id=str(target_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(serialized)


@router.get("/history")
async def get_history(
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    history = await MentorIntelligenceService.get_interaction_history(db, target_id)
    
    serialized_history = [serialize_interaction(h) for h in history]
    audit_logger.log(
        action="GET_MENTOR_HISTORY",
        resource="/mentor/history",
        resource_id=str(target_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id), "count": len(history)}
    )
    return success_response(serialized_history)


@router.get("/explain/{interaction_id}")
async def get_explain(
    interaction_id: uuid.UUID,
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    explanation = await MentorIntelligenceService.get_interaction_explanation(db, target_id, interaction_id)
    
    if not explanation:
        raise NotFoundError("Interaction not found or unauthorized")
        
    audit_logger.log(
        action="GET_MENTOR_INTERACTION_EXPLANATION",
        resource=f"/mentor/explain/{interaction_id}",
        resource_id=str(interaction_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(explanation)


def serialize_interaction(inter) -> dict:
    if not inter:
        return {}
    return {
        "id": str(inter.id),
        "user_id": str(inter.user_id),
        "query": inter.query,
        "response": inter.response,
        "mode": inter.mode,
        "cache_hit": inter.cache_hit,
        "citation": inter.citation,
        "cost_metrics": {
            "tokens_prompt": inter.tokens_prompt,
            "tokens_completion": inter.tokens_completion,
            "cost_usd": inter.cost,
            "latency_seconds": inter.latency
        },
        "created_at": inter.created_at.isoformat() if inter.created_at else None
    }
