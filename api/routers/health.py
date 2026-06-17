from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database import get_db
import time

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    """System-wide health check — verifies API + database connectivity."""
    start = time.time()
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
        db_msg = "connected"
    except Exception as e:
        db_ok = False
        db_msg = str(e)

    latency_ms = int((time.time() - start) * 1000)
    return {
        "status": "healthy" if db_ok else "degraded",
        "services": {
            "api": {"status": "healthy"},
            "database": {"status": "healthy" if db_ok else "down", "message": db_msg},
        },
        "latency_ms": latency_ms,
        "version": "0.1.0-phase1",
    }

@router.get("/pgvector")
async def pgvector_check(db: AsyncSession = Depends(get_db)):
    """Verify pgvector extension is active."""
    result = await db.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'"))
    row = result.fetchone()
    if row:
        return {"status": "ok", "extension": row[0], "version": row[1]}
    return {"status": "error", "message": "pgvector extension not found"}
