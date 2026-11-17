import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings
from app.cache.redis_client import get_redis

router = APIRouter(prefix="/system", tags=["System & Monitoring"])

@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    start = time.perf_counter()
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    redis_ok = False
    try:
        r = await get_redis()
        pong = await r.ping()
        redis_ok = bool(pong)
    except Exception:
        redis_ok = False

    total_latency_ms = round((time.perf_counter() - start) * 1000, 2)

    return {
        "status": "healthy" if db_ok else "degraded",
        "timestamp": time.time(),
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
        "llm_provider": settings.LLM_PROVIDER,
        "latency_ms": total_latency_ms
    }

@router.get("/readiness")
async def readiness(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}

@router.get("/liveness")
async def liveness():
    return {"status": "alive"}
