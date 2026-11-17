import time
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, desc
from app.core.database import get_db
from app.core.config import settings
from app.cache.redis_client import get_redis
from app.models.models import AuditLog, User
from app.api.deps import get_current_admin

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

@router.get("/audit-logs")
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    action: Optional[str] = None,
    user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(AuditLog)
        .where(AuditLog.organization_id == user.organization_id)
        .order_by(desc(AuditLog.created_at))
    )
    if action:
        stmt = stmt.where(AuditLog.action == action)
    stmt = stmt.offset(skip).limit(limit)
    res = await db.execute(stmt)
    logs = res.scalars().all()
    return [
        {
            "id": log.id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at
        }
        for log in logs
    ]
