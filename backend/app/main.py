from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.middleware.metrics import MetricsMiddleware
from app.core.metrics import metrics_registry
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST


from app.config.settings import get_settings
from app.config.environment import EnvironmentValidator
from app.core.logging import configure_logging
from app.core.exception_handlers import register_exception_handlers
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.audit import AuditMiddleware
from app.middleware.request_size import RequestSizeLimitMiddleware
from app.middleware.idempotency import IdempotencyMiddleware
from app.api.v1.router import api_v1_router
from app.database.session import engine, Base
from app.database.health import verify_database_connection

settings = get_settings()



@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    EnvironmentValidator.validate()
    await verify_database_connection()
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-CSRF-Token",
    ],
    expose_headers=["X-Request-ID"],
    max_age=600,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuditMiddleware)


register_exception_handlers(app)

app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}


@app.get("/readiness")
async def readiness_check():
    if settings.TESTING:
        return {
            "status": "ready",
            "database": "connected",
            "redis": "connected",
        }

    db_healthy = await verify_database_connection()
    from app.core.redis_pool import redis_pool
    redis_healthy = redis_pool.ping()

    overall = db_healthy and redis_healthy
    return {
        "status": "ready" if overall else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "redis": "connected" if redis_healthy else "disconnected",
    }


@app.get("/metrics")
def get_metrics():
    return Response(generate_latest(metrics_registry), media_type=CONTENT_TYPE_LATEST)


@app.get("/liveness")
async def liveness_check():
    return {"status": "alive"}
