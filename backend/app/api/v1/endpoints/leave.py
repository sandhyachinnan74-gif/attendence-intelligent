from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException, ValidationException
from app.models.models import LeaveRecord, Employee, Department, User
from app.schemas.schemas import LeaveCreate, LeaveReviewRequest, LeaveResponse
from app.api.deps import get_current_user, get_current_hr_or_admin, get_current_employee_profile

router = APIRouter(prefix="/leave", tags=["Leave Management"])

@router.post("", response_model=LeaveResponse, status_code=status.HTTP_201_CREATED)
async def apply_leave(
    req: LeaveCreate,
    user: User = Depends(get_current_user),
    employee: Optional[Employee] = Depends(get_current_employee_profile),
    db: AsyncSession = Depends(get_db)
):
    target_emp_id = None
    if user.role in ["admin", "hr_manager"] and req.employee_id:
        target_emp_id = req.employee_id
    elif employee:
        target_emp_id = employee.id
    else:
        raise ValidationException("Employee profile not found")

    if req.end_date < req.start_date:
        raise ValidationException("End date cannot precede start date")

    days_count = max(1.0, float((req.end_date - req.start_date).days + 1))

    leave = LeaveRecord(
        organization_id=user.organization_id,
        employee_id=target_emp_id,
        leave_type=req.leave_type,
        start_date=req.start_date,
        end_date=req.end_date,
        days_count=days_count,
        reason=req.reason,
        status="pending"
    )
    db.add(leave)
    await db.commit()
    await db.refresh(leave)

    emp = (await db.execute(select(Employee).where(Employee.id == target_emp_id))).scalars().first()
    dept = (await db.execute(select(Department).where(Department.id == emp.department_id))).scalars().first() if emp and emp.department_id else None

    return {
        "id": leave.id,
        "organization_id": leave.organization_id,
        "employee_id": leave.employee_id,
        "leave_type": leave.leave_type,
        "start_date": leave.start_date,
        "end_date": leave.end_date,
        "days_count": leave.days_count,
        "reason": leave.reason,
        "status": leave.status,
        "reviewed_by": leave.reviewed_by,
        "reviewed_at": leave.reviewed_at,
        "resolution_notes": leave.resolution_notes,
        "created_at": leave.created_at,
        "employee_name": f"{emp.first_name} {emp.last_name}" if emp else None,
        "employee_code": emp.employee_code if emp else None,
        "department_name": dept.name if dept else "General"
    }

@router.get("", response_model=List[LeaveResponse])
async def list_leave(
    status_filter: Optional[str] = None,
    employee_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    employee: Optional[Employee] = Depends(get_current_employee_profile),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(LeaveRecord, Employee, Department)
        .join(Employee, Employee.id == LeaveRecord.employee_id)
        .outerjoin(Department, Department.id == Employee.department_id)
        .where(LeaveRecord.organization_id == user.organization_id)
    )

    if user.role == "employee":
        if not employee:
            return []
        stmt = stmt.where(LeaveRecord.employee_id == employee.id)
    elif employee_id:
        stmt = stmt.where(LeaveRecord.employee_id == employee_id)

    if status_filter:
        stmt = stmt.where(LeaveRecord.status == status_filter)

    stmt = stmt.order_by(desc(LeaveRecord.created_at)).offset(skip).limit(limit)
    res = await db.execute(stmt)

    output = []
    for l, emp, dept in res.all():
        output.append({
            "id": l.id,
            "organization_id": l.organization_id,
            "employee_id": l.employee_id,
            "leave_type": l.leave_type,
            "start_date": l.start_date,
            "end_date": l.end_date,
            "days_count": l.days_count,
            "reason": l.reason,
            "status": l.status,
            "reviewed_by": l.reviewed_by,
            "reviewed_at": l.reviewed_at,
            "resolution_notes": l.resolution_notes,
            "created_at": l.created_at,
            "employee_name": f"{emp.first_name} {emp.last_name}",
            "employee_code": emp.employee_code,
            "department_name": dept.name if dept else "General"
        })
    return output

@router.put("/{leave_id}/review", response_model=LeaveResponse)
async def review_leave(
    leave_id: str,
    req: LeaveReviewRequest,
    user: User = Depends(get_current_hr_or_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(LeaveRecord).where(
        and_(
            LeaveRecord.id == leave_id,
            LeaveRecord.organization_id == user.organization_id
        )
    )
    leave = (await db.execute(stmt)).scalars().first()
    if not leave:
        raise NotFoundException("Leave request not found")

    leave.status = req.status
    leave.resolution_notes = req.resolution_notes
    leave.reviewed_by = user.id
    leave.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()
    await db.refresh(leave)

    emp = (await db.execute(select(Employee).where(Employee.id == leave.employee_id))).scalars().first()
    dept = (await db.execute(select(Department).where(Department.id == emp.department_id))).scalars().first() if emp and emp.department_id else None

    return {
        "id": leave.id,
        "organization_id": leave.organization_id,
        "employee_id": leave.employee_id,
        "leave_type": leave.leave_type,
        "start_date": leave.start_date,
        "end_date": leave.end_date,
        "days_count": leave.days_count,
        "reason": leave.reason,
        "status": leave.status,
        "reviewed_by": leave.reviewed_by,
        "reviewed_at": leave.reviewed_at,
        "resolution_notes": leave.resolution_notes,
        "created_at": leave.created_at,
        "employee_name": f"{emp.first_name} {emp.last_name}" if emp else None,
        "employee_code": emp.employee_code if emp else None,
        "department_name": dept.name if dept else "General"
    }
