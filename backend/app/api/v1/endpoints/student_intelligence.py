import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user_id, get_current_user_role
from app.core.exception_handlers import AuthorizationError, NotFoundError
from app.core.response import success_response
from app.core.logging import audit_logger
from app.services.student_intelligence import StudentIntelligenceService
from app.schemas.digital_twin import DigitalTwinResponse, StudentEventPayload

router = APIRouter()


def check_row_level_auth(
    requesting_user_id_str: str,
    requesting_user_role: str,
    target_student_id: Optional[uuid.UUID]
) -> uuid.UUID:
    """
    Prevent cross-user profile leakage.
    Only admins and managers can view other students' profiles.
    """
    req_uuid = uuid.UUID(requesting_user_id_str)
    if not target_student_id:
        return req_uuid
    if target_student_id != req_uuid:
        if requesting_user_role not in ("admin", "manager"):
            raise AuthorizationError("Cross-user profile access is forbidden")
        return target_student_id
    return req_uuid


@router.get("/twin", response_model=DigitalTwinResponse)
async def get_digital_twin(
    request: Request,
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    twin = await StudentIntelligenceService.get_digital_twin(db, target_id)
    
    audit_logger.log(
        action="GET_STUDENT_TWIN",
        resource="/student/twin",
        resource_id=str(twin.id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return twin


@router.get("/knowledge-state")
async def get_knowledge_state(
    request: Request,
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    twin = await StudentIntelligenceService.get_digital_twin(db, target_id)
    return twin.knowledge_state


@router.get("/memory-state")
async def get_memory_state(
    request: Request,
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    twin = await StudentIntelligenceService.get_digital_twin(db, target_id)
    return twin.memory_state


@router.get("/practice-state")
async def get_practice_state(
    request: Request,
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    twin = await StudentIntelligenceService.get_digital_twin(db, target_id)
    return twin.practice_state


@router.get("/behaviour-state")
async def get_behaviour_state(
    request: Request,
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    twin = await StudentIntelligenceService.get_digital_twin(db, target_id)
    return twin.behaviour_state


@router.get("/coverage")
async def get_coverage(
    request: Request,
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    twin = await StudentIntelligenceService.get_digital_twin(db, target_id)
    details = await StudentIntelligenceService.get_coverage_details(db, twin)
    return details


@router.get("/learning-velocity")
async def get_learning_velocity(
    request: Request,
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    twin = await StudentIntelligenceService.get_digital_twin(db, target_id)
    projections = await StudentIntelligenceService.get_velocity_projections(db, twin)
    return {
        "learning_profile": twin.learning_profile,
        "projections": projections
    }


@router.get("/trends")
async def get_trends(
    request: Request,
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    twin = await StudentIntelligenceService.get_digital_twin(db, target_id)
    
    # Extract trend details
    trends = {
        "knowledge_readiness": twin.knowledge_readiness,
        "memory_readiness": twin.memory_readiness,
        "practice_readiness": twin.practice_readiness,
        "writing_readiness": twin.writing_readiness,
        "behaviour_readiness": twin.behaviour_readiness,
        "word_count_trends": twin.writing_state.get("word_count_trends", []),
        "time_taken_trends": twin.writing_state.get("time_taken", []),
        "difficulty_trend": twin.practice_state.get("difficulty_trend", []),
        "concepts_mastered_by_week": twin.learning_profile.get("concepts_mastered_by_week", {})
    }
    return trends


@router.post("/events", response_model=DigitalTwinResponse)
async def publish_student_event(
    event_payload: StudentEventPayload,
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    """
    Publish an event to update the student's Digital Twin immediately.
    """
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    
    # Incremental update
    updated_twin = await StudentIntelligenceService.process_student_event(
        db,
        target_id,
        event_payload.event_type,
        event_payload.payload
    )
    
    return updated_twin
