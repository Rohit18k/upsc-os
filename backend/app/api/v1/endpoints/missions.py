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
from app.services.mission_engine import MissionEngineService

router = APIRouter()


@router.get("/today")
async def get_today_mission(
    student_id: Optional[uuid.UUID] = None,
    daily_hours: Optional[float] = Query(None),
    days_until_exam: Optional[int] = Query(None),
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    mission = await MissionEngineService.get_today_mission(
        db, target_id, daily_hours, days_until_exam
    )

    serialized_mission = serialize_mission(mission)
    audit_logger.log(
        action="GET_TODAY_MISSION",
        resource="/missions/today",
        resource_id=str(target_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(serialized_mission)


@router.get("/week")
async def get_weekly_mission(
    student_id: Optional[uuid.UUID] = None,
    daily_hours: Optional[float] = Query(None),
    days_until_exam: Optional[int] = Query(None),
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    mission = await MissionEngineService.get_weekly_mission(
        db, target_id, daily_hours, days_until_exam
    )

    serialized_mission = serialize_mission(mission)
    audit_logger.log(
        action="GET_WEEKLY_MISSION",
        resource="/missions/week",
        resource_id=str(target_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(serialized_mission)


@router.get("/history")
async def get_history(
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    history = await MissionEngineService.get_mission_history(db, target_id)
    
    serialized_history = [serialize_mission(m) for m in history]
    audit_logger.log(
        action="GET_MISSION_HISTORY",
        resource="/missions/history",
        resource_id=str(target_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id), "count": len(history)}
    )
    return success_response(serialized_history)


@router.get("/{id}")
async def get_mission_by_id(
    id: uuid.UUID,
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    
    # Query specific mission
    from sqlalchemy.future import select
    from app.models.mission import StudentMission
    query = select(StudentMission).where(
        StudentMission.id == id,
        StudentMission.user_id == target_id
    )
    res = await db.execute(query)
    mission = res.scalar_one_or_none()
    
    if not mission:
        raise NotFoundError("Mission not found or unauthorized")
        
    serialized_mission = serialize_mission(mission)
    audit_logger.log(
        action="GET_MISSION_BY_ID",
        resource=f"/missions/{id}",
        resource_id=str(id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(serialized_mission)


@router.post("/{id}/complete")
async def complete_mission(
    id: uuid.UUID,
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    mission = await MissionEngineService.complete_mission(db, target_id, id)
    
    if not mission:
        raise NotFoundError("Mission not found or unauthorized")
        
    serialized_mission = serialize_mission(mission)
    audit_logger.log(
        action="COMPLETE_MISSION",
        resource=f"/missions/{id}/complete",
        resource_id=str(id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(serialized_mission)


@router.post("/{id}/skip")
async def skip_mission(
    id: uuid.UUID,
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    mission = await MissionEngineService.skip_mission(db, target_id, id)
    
    if not mission:
        raise NotFoundError("Mission not found or unauthorized")
        
    serialized_mission = serialize_mission(mission)
    audit_logger.log(
        action="SKIP_MISSION",
        resource=f"/missions/{id}/skip",
        resource_id=str(id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(serialized_mission)


@router.post("/recalculate")
async def recalculate_mission(
    student_id: Optional[uuid.UUID] = None,
    daily_hours: Optional[float] = Query(None),
    days_until_exam: Optional[int] = Query(None),
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    mission = await MissionEngineService.generate_mission(
        db, target_id, "daily", daily_hours, days_until_exam
    )

    serialized_mission = serialize_mission(mission)
    audit_logger.log(
        action="RECALCULATE_MISSION",
        resource="/missions/recalculate",
        resource_id=str(target_id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(serialized_mission)


@router.get("/explain/{id}")
async def get_explain(
    id: uuid.UUID,
    student_id: Optional[uuid.UUID] = None,
    user_id_str: str = Depends(get_current_user_id),
    role_str: str = Depends(get_current_user_role),
    db: AsyncSession = Depends(get_db)
):
    target_id = check_row_level_auth(user_id_str, role_str, student_id)
    explanation = await MissionEngineService.get_mission_explanation(db, target_id, id)
    
    if not explanation:
        raise NotFoundError("Mission not found or unauthorized")
        
    audit_logger.log(
        action="GET_MISSION_EXPLANATION",
        resource=f"/missions/explain/{id}",
        resource_id=str(id),
        user_id=user_id_str,
        details={"target_student_id": str(target_id)}
    )
    return success_response(explanation)


def serialize_mission(mission) -> dict:
    if not mission:
        return {}
    return {
        "id": str(mission.id),
        "user_id": str(mission.user_id),
        "optimization_plan_id": str(mission.optimization_plan_id) if mission.optimization_plan_id else None,
        "type": mission.type,
        "title": mission.title,
        "goal": mission.goal,
        "ordered_tasks": mission.ordered_tasks,
        "status": mission.status,
        "difficulty_level": mission.difficulty_level,
        "estimated_time": mission.estimated_time,
        "expected_readiness_gain": mission.expected_readiness_gain,
        "expected_mastery_gain": mission.expected_mastery_gain,
        "actual_readiness_gain": mission.actual_readiness_gain,
        "actual_mastery_gain": mission.actual_mastery_gain,
        "completion_percentage": mission.completion_percentage,
        "quality_score": mission.quality_score,
        "execution_quality": mission.execution_quality,
        "consistency_score": mission.consistency_score,
        "dependencies": mission.dependencies,
        "completion_criteria": mission.completion_criteria,
        "success_metrics": mission.success_metrics,
        "evidence": mission.evidence,
        "expiry": mission.expiry.isoformat() if mission.expiry else None,
        "created_at": mission.created_at.isoformat() if mission.created_at else None
    }
