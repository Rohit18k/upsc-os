from fastapi import APIRouter

from app.core.response import success_response

router = APIRouter()


@router.get("/health")
async def health():
    return success_response({"status": "healthy"})


@router.get("/readiness")
async def readiness():
    return success_response({"status": "ready"})


@router.get("/liveness")
async def liveness():
    return success_response({"status": "alive"})
