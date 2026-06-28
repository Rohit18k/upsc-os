from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, users, student_intelligence, reasoning, optimization, missions, tutor, mentor, admin

api_v1_router = APIRouter()

api_v1_router.include_router(health.router, tags=["health"])
api_v1_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_v1_router.include_router(users.router, prefix="/users", tags=["users"])
api_v1_router.include_router(student_intelligence.router, prefix="/student", tags=["student-intelligence"])
api_v1_router.include_router(reasoning.router, prefix="/reasoning", tags=["reasoning"])
api_v1_router.include_router(optimization.router, prefix="/optimization", tags=["optimization"])
api_v1_router.include_router(missions.router, prefix="/missions", tags=["missions"])
api_v1_router.include_router(tutor.router, prefix="/tutor", tags=["tutor"])
api_v1_router.include_router(mentor.router, prefix="/mentor", tags=["mentor"])
api_v1_router.include_router(admin.router, prefix="/admin", tags=["admin"])







