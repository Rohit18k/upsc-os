import logging

from sqlalchemy import text

from app.database.session import engine

logger = logging.getLogger(__name__)


async def verify_database_connection() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
