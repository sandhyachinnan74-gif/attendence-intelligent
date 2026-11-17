from datetime import date
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.models import User, Employee
from app.schemas.schemas import DashboardResponse, EmployeeDashboardResponse
from app.services.analytics_service import AnalyticsService
from app.api.deps import get_current_hr_or_admin, get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics & Reports"])

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    target_date: Optional[date] = None,
    department_id: Optional[str] = None,
    user: User = Depends(get_current_hr_or_admin),
    db: AsyncSession = Depends(get_db)
):
    # If HR Manager has a specific assigned department, scope automatically
    effective_dept_id = department_id
    if user.role == "hr_manager" and not effective_dept_id:
        emp_stmt = select(Employee).where(Employee.user_id == user.id)
        emp = (await db.execute(emp_stmt)).scalars().first()
        if emp and emp.department_id:
            effective_dept_id = emp.department_id

    data = await AnalyticsService.get_dashboard_data(
        db=db,
        organization_id=user.organization_id,
        target_date=target_date,
        department_id=effective_dept_id
    )
    return data

@router.get("/employee-dashboard", response_model=EmployeeDashboardResponse)
async def get_employee_dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    emp_stmt = select(Employee).where(Employee.user_id == user.id)
    emp = (await db.execute(emp_stmt)).scalars().first()
    if not emp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee profile not found for authenticated user."
        )

    data = await AnalyticsService.get_employee_dashboard_data(
        db=db,
        organization_id=user.organization_id,
        employee_id=emp.id
    )
    return data
