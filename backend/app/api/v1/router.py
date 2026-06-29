from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, users, student_intelligence, reasoning, optimization, missions, tutor, mentor, admin
from app.api.v1.endpoints import syllabus, pyqs, books, concepts, content_intelligence, content, dashboard, population, brain

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

api_v1_router.include_router(syllabus.router, prefix="/syllabus", tags=["syllabus"])
api_v1_router.include_router(pyqs.router, prefix="/pyqs", tags=["previous-year-questions"])
api_v1_router.include_router(books.router, prefix="/books", tags=["books"])
api_v1_router.include_router(concepts.router, prefix="/concepts", tags=["content-intelligence"])
api_v1_router.include_router(content_intelligence.router, prefix="/content-intelligence", tags=["content-intelligence"])
api_v1_router.include_router(content.router, prefix="/content", tags=["content"])
api_v1_router.include_router(dashboard.router, prefix="/dashboard", tags=["quality-dashboard"])
api_v1_router.include_router(population.router, prefix="/population", tags=["population"])
api_v1_router.include_router(brain.router, prefix="/brain", tags=["ai-brain"])







