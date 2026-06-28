import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user_id, get_current_user_role
from app.core.exception_handlers import NotFoundError
from app.core.response import success_response
from app.core.logging import audit_logger
from app.api.v1.endpoints.student_intelligence import check_row_level_auth
from app.services.cognitive_reasoning import CognitiveReasoningService

router = APIRouter()


@router.get("/diagnosis")
async def get_diagnosis(
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    diagnosis = await CognitiveReasoningService.diagnose_student(db, target_id)
    
    audit_logger.log(
        action="GET_STUDENT_DIAGNOSIS",
        resource="/reasoning/diagnosis",
        resource_id=str(target_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(diagnosis)


@router.get("/bottlenecks")
async def get_bottlenecks(
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    bottlenecks = await CognitiveReasoningService.get_bottlenecks(db, target_id)
    
    audit_logger.log(
        action="GET_STUDENT_BOTTLENECKS",
        resource="/reasoning/bottlenecks",
        resource_id=str(target_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(bottlenecks)


@router.get("/interventions")
async def get_interventions(
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    interventions = await CognitiveReasoningService.get_candidate_interventions(db, target_id)
    
    audit_logger.log(
        action="GET_STUDENT_INTERVENTIONS",
        resource="/reasoning/interventions",
        resource_id=str(target_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(interventions)


@router.get("/predictions")
async def get_predictions(
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    predictions = await CognitiveReasoningService.get_predictions(db, target_id)
    
    audit_logger.log(
        action="GET_STUDENT_PREDICTIONS",
        resource="/reasoning/predictions",
        resource_id=str(target_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(predictions)


@router.get("/decisions")
async def get_decisions(
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    decisions = await CognitiveReasoningService.generate_decisions(db, target_id)
    
    # Map model objects to dicts for clean JSON serialization
    serialized_decisions = []
    for d in decisions:
        serialized_decisions.append({
            "id": str(d.id),
            "user_id": str(d.user_id),
            "category": d.category,
            "priority": d.priority,
            "reasoning": d.reasoning,
            "evidence": d.evidence,
            "confidence": d.confidence,
            "expected_gain": d.expected_gain,
            "estimated_time": d.estimated_time,
            "dependencies": d.dependencies,
            "risk": d.risk,
            "expiry": d.expiry.isoformat() if d.expiry else None,
            "created_at": d.created_at.isoformat() if d.created_at else None
        })

    audit_logger.log(
        action="GET_STUDENT_DECISIONS",
        resource="/reasoning/decisions",
        resource_id=str(target_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id), "count": len(decisions)}
    )
    return success_response(serialized_decisions)


@router.get("/explain/{decision_id}")
async def get_explain(
    decision_id: uuid.UUID,
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    explanation = await CognitiveReasoningService.get_decision_explanation(db, target_id, decision_id)
    
    if not explanation:
        raise NotFoundError("Decision object not found or unauthorized")
        
    audit_logger.log(
        action="GET_DECISION_EXPLANATION",
        resource=f"/reasoning/explain/{decision_id}",
        resource_id=str(decision_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(explanation)
