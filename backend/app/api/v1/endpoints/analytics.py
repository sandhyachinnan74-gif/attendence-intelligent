from datetime import date
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import DashboardResponse
from app.services.analytics_service import AnalyticsService
from app.api.deps import get_current_hr_or_admin

router = APIRouter(prefix="/analytics", tags=["Analytics & Reports"])

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    target_date: Optional[date] = None,
    department_id: Optional[str] = None,
    user: User = Depends(get_current_hr_or_admin),
    db: AsyncSession = Depends(get_db)
):
    data = await AnalyticsService.get_dashboard_data(
        db=db,
        organization_id=user.organization_id,
        target_date=target_date,
        department_id=department_id
    )
    return data
