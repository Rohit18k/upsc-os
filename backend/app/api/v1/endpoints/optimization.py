import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import get_current_user_id, get_current_user_role
from app.core.exception_handlers import NotFoundError
from app.core.response import success_response
from app.core.logging import audit_logger
from app.api.v1.endpoints.student_intelligence import check_row_level_auth
from app.services.optimization_engine import OptimizationEngineService

router = APIRouter()


@router.get("/plan")
async def get_plan(
    student_id: Optional[uuid.UUID] = None,
    goal: Optional[str] = None,
    daily_hours: Optional[float] = Query(None, description="Available hours per day"),
    days_until_exam: Optional[int] = Query(None, description="Days left until exam"),
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    plan = await OptimizationEngineService.get_active_plan(
        db, target_id, goal, daily_hours, days_until_exam
    )

    serialized_plan = {
        "id": str(plan.id),
        "user_id": str(plan.user_id),
        "goal": plan.goal,
        "priority": plan.priority,
        "reasoning_reference": plan.reasoning_reference,
        "decision_references": plan.decision_references,
        "ordered_actions": plan.ordered_actions,
        "expected_readiness_gain": plan.expected_readiness_gain,
        "expected_mastery_gain": plan.expected_mastery_gain,
        "expected_retention_gain": plan.expected_retention_gain,
        "estimated_completion_time": plan.estimated_completion_time,
        "confidence": plan.confidence,
        "expiry": plan.expiry.isoformat() if plan.expiry else None,
        "status": plan.status,
        "created_at": plan.created_at.isoformat() if plan.created_at else None
    }

    audit_logger.log(
        action="GET_OPTIMIZATION_PLAN",
        resource="/optimization/plan",
        resource_id=str(target_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(serialized_plan)


@router.post("/recalculate")
async def recalculate_plan(
    student_id: Optional[uuid.UUID] = None,
    goal: Optional[str] = None,
    daily_hours: Optional[float] = Query(None, description="Available hours per day"),
    days_until_exam: Optional[int] = Query(None, description="Days left until exam"),
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    plan = await OptimizationEngineService.generate_optimization_plan(
        db, target_id, goal, daily_hours, days_until_exam
    )

    serialized_plan = {
        "id": str(plan.id),
        "user_id": str(plan.user_id),
        "goal": plan.goal,
        "priority": plan.priority,
        "reasoning_reference": plan.reasoning_reference,
        "decision_references": plan.decision_references,
        "ordered_actions": plan.ordered_actions,
        "expected_readiness_gain": plan.expected_readiness_gain,
        "expected_mastery_gain": plan.expected_mastery_gain,
        "expected_retention_gain": plan.expected_retention_gain,
        "estimated_completion_time": plan.estimated_completion_time,
        "confidence": plan.confidence,
        "expiry": plan.expiry.isoformat() if plan.expiry else None,
        "status": plan.status,
        "created_at": plan.created_at.isoformat() if plan.created_at else None
    }

    audit_logger.log(
        action="RECALCULATE_OPTIMIZATION_PLAN",
        resource="/optimization/recalculate",
        resource_id=str(target_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(serialized_plan)


@router.get("/strategies")
async def get_strategies(
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    strategies = await OptimizationEngineService.get_strategies(db, target_id)
    
    audit_logger.log(
        action="GET_OPTIMIZATION_STRATEGIES",
        resource="/optimization/strategies",
        resource_id=str(target_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(strategies)


@router.get("/roi")
async def get_roi(
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    roi_metrics = await OptimizationEngineService.get_roi_metrics(db, target_id)
    
    audit_logger.log(
        action="GET_OPTIMIZATION_ROI",
        resource="/optimization/roi",
        resource_id=str(target_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(roi_metrics)


@router.get("/constraints")
async def get_constraints(
    student_id: Optional[uuid.UUID] = None,
    daily_hours: Optional[float] = Query(None),
    days_until_exam: Optional[int] = Query(None),
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    constraints = await OptimizationEngineService.get_constraints(
        db, target_id, daily_hours, days_until_exam
    )
    
    audit_logger.log(
        action="GET_OPTIMIZATION_CONSTRAINTS",
        resource="/optimization/constraints",
        resource_id=str(target_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(constraints)


@router.get("/explain/{plan_id}")
async def get_explain(
    plan_id: uuid.UUID,
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    explanation = await OptimizationEngineService.get_plan_explanation(db, target_id, plan_id)
    
    if not explanation:
        raise NotFoundError("Optimization plan not found or unauthorized")
        
    audit_logger.log(
        action="GET_PLAN_EXPLANATION",
        resource=f"/optimization/explain/{plan_id}",
        resource_id=str(plan_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(explanation)
