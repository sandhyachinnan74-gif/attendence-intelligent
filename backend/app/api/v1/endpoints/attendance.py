from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException, ValidationException
from app.models.models import AttendanceRecord, AttendanceBreak, Employee, Department, User
from app.schemas.schemas import (
    ClockInRequest, ClockOutRequest, BreakRequest, AttendanceResponse, AttendanceCorrectionRequest, BreakResponse
)
from app.services.attendance_service import AttendanceService
from app.api.deps import get_current_user, get_current_hr_or_admin, get_current_employee_profile

router = APIRouter(prefix="/attendance", tags=["Attendance"])

@router.post("/clock-in", response_model=AttendanceResponse)
async def clock_in(
    req: ClockInRequest,
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
        raise ValidationException("No employee profile found for clock-in")

    record = await AttendanceService.clock_in(db, user.organization_id, target_emp_id)

    emp = (await db.execute(select(Employee).where(Employee.id == target_emp_id))).scalars().first()
    dept = (await db.execute(select(Department).where(Department.id == emp.department_id))).scalars().first() if emp and emp.department_id else None

    return {
        "id": record.id,
        "organization_id": record.organization_id,
        "employee_id": record.employee_id,
        "date": record.date,
        "clock_in": record.clock_in,
        "clock_out": record.clock_out,
        "worked_minutes": record.worked_minutes,
        "overtime_minutes": record.overtime_minutes,
        "late_minutes": record.late_minutes,
        "status": record.status,
        "is_corrected": record.is_corrected,
        "created_at": record.created_at,
        "employee_name": f"{emp.first_name} {emp.last_name}" if emp else None,
        "employee_code": emp.employee_code if emp else None,
        "department_name": dept.name if dept else "General",
        "breaks": []
    }

@router.post("/clock-out", response_model=AttendanceResponse)
async def clock_out(
    req: ClockOutRequest,
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
        raise ValidationException("No employee profile found for clock-out")

    record = await AttendanceService.clock_out(db, user.organization_id, target_emp_id)

    emp = (await db.execute(select(Employee).where(Employee.id == target_emp_id))).scalars().first()
    dept = (await db.execute(select(Department).where(Department.id == emp.department_id))).scalars().first() if emp and emp.department_id else None
    
    breaks = (await db.execute(select(AttendanceBreak).where(AttendanceBreak.attendance_record_id == record.id))).scalars().all()

    return {
        "id": record.id,
        "organization_id": record.organization_id,
        "employee_id": record.employee_id,
        "date": record.date,
        "clock_in": record.clock_in,
        "clock_out": record.clock_out,
        "worked_minutes": record.worked_minutes,
        "overtime_minutes": record.overtime_minutes,
        "late_minutes": record.late_minutes,
        "status": record.status,
        "is_corrected": record.is_corrected,
        "created_at": record.created_at,
        "employee_name": f"{emp.first_name} {emp.last_name}" if emp else None,
        "employee_code": emp.employee_code if emp else None,
        "department_name": dept.name if dept else "General",
        "breaks": [
            {
                "id": b.id,
                "break_start": b.break_start,
                "break_end": b.break_end,
                "duration_minutes": b.duration_minutes,
                "reason": b.reason
            }
            for b in breaks
        ]
    }

@router.post("/re-clock-in", response_model=AttendanceResponse)
@router.post("/resume-shift", response_model=AttendanceResponse)
async def re_clock_in(
    req: Optional[ClockInRequest] = None,
    user: User = Depends(get_current_user),
    employee: Optional[Employee] = Depends(get_current_employee_profile),
    db: AsyncSession = Depends(get_db)
):
    target_emp_id = None
    if user.role in ["admin", "hr_manager"] and req and req.employee_id:
        target_emp_id = req.employee_id
    elif employee:
        target_emp_id = employee.id
    else:
        raise ValidationException("No employee profile found for re-clock in")

    record = await AttendanceService.re_clock_in(db, user.organization_id, target_emp_id)

    emp = (await db.execute(select(Employee).where(Employee.id == target_emp_id))).scalars().first()
    dept = (await db.execute(select(Department).where(Department.id == emp.department_id))).scalars().first() if emp and emp.department_id else None
    breaks = (await db.execute(select(AttendanceBreak).where(AttendanceBreak.attendance_record_id == record.id))).scalars().all()

    return {
        "id": record.id,
        "organization_id": record.organization_id,
        "employee_id": record.employee_id,
        "date": record.date,
        "clock_in": record.clock_in,
        "clock_out": record.clock_out,
        "worked_minutes": record.worked_minutes,
        "overtime_minutes": record.overtime_minutes,
        "late_minutes": record.late_minutes,
        "status": record.status,
        "is_corrected": record.is_corrected,
        "created_at": record.created_at,
        "employee_name": f"{emp.first_name} {emp.last_name}" if emp else None,
        "employee_code": emp.employee_code if emp else None,
        "department_name": dept.name if dept else "General",
        "breaks": [
            {
                "id": b.id,
                "break_start": b.break_start,
                "break_end": b.break_end,
                "duration_minutes": b.duration_minutes,
                "reason": b.reason
            }
            for b in breaks
        ]
    }

@router.post("/break", response_model=BreakResponse)
async def toggle_break(
    req: BreakRequest,
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
        raise ValidationException("No employee profile found for break")

    b = await AttendanceService.toggle_break(db, user.organization_id, target_emp_id, reason=req.reason or "Normal Break")
    return {
        "id": b.id,
        "break_start": b.break_start,
        "break_end": b.break_end,
        "duration_minutes": b.duration_minutes,
        "reason": b.reason
    }

@router.get("", response_model=List[AttendanceResponse])
async def list_attendance(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    employee_id: Optional[str] = None,
    department_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    employee: Optional[Employee] = Depends(get_current_employee_profile),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(AttendanceRecord, Employee, Department)
        .join(Employee, Employee.id == AttendanceRecord.employee_id)
        .outerjoin(Department, Department.id == Employee.department_id)
        .where(AttendanceRecord.organization_id == user.organization_id)
    )

    # Scoped: Normal employee can ONLY view own records
    if user.role == "employee":
        if not employee:
            return []
        stmt = stmt.where(AttendanceRecord.employee_id == employee.id)
    elif employee_id:
        stmt = stmt.where(AttendanceRecord.employee_id == employee_id)

    if department_id:
        stmt = stmt.where(Employee.department_id == department_id)
    if start_date:
        stmt = stmt.where(AttendanceRecord.date >= start_date)
    if end_date:
        stmt = stmt.where(AttendanceRecord.date <= end_date)
    if status_filter:
        stmt = stmt.where(AttendanceRecord.status == status_filter)

    stmt = stmt.order_by(desc(AttendanceRecord.date), desc(AttendanceRecord.created_at)).offset(skip).limit(limit)
    res = await db.execute(stmt)

    output = []
    for r, emp, dept in res.all():
        output.append({
            "id": r.id,
            "organization_id": r.organization_id,
            "employee_id": r.employee_id,
            "date": r.date,
            "clock_in": r.clock_in,
            "clock_out": r.clock_out,
            "worked_minutes": r.worked_minutes,
            "overtime_minutes": r.overtime_minutes,
            "late_minutes": r.late_minutes,
            "status": r.status,
            "is_corrected": r.is_corrected,
            "created_at": r.created_at,
            "employee_name": f"{emp.first_name} {emp.last_name}",
            "employee_code": emp.employee_code,
            "department_name": dept.name if dept else "General",
            "breaks": []
        })
    return output

@router.get("/today", response_model=Optional[AttendanceResponse])
async def get_today_attendance(
    user: User = Depends(get_current_user),
    employee: Optional[Employee] = Depends(get_current_employee_profile),
    db: AsyncSession = Depends(get_db)
):
    if not employee:
        return None
    today = date.today()
    stmt = (
        select(AttendanceRecord)
        .where(
            and_(
                AttendanceRecord.employee_id == employee.id,
                AttendanceRecord.date == today
            )
        )
    )
    r = (await db.execute(stmt)).scalars().first()
    if not r:
        return None

    breaks = (await db.execute(select(AttendanceBreak).where(AttendanceBreak.attendance_record_id == r.id))).scalars().all()
    dept = (await db.execute(select(Department).where(Department.id == employee.department_id))).scalars().first() if employee.department_id else None

    return {
        "id": r.id,
        "organization_id": r.organization_id,
        "employee_id": r.employee_id,
        "date": r.date,
        "clock_in": r.clock_in,
        "clock_out": r.clock_out,
        "worked_minutes": r.worked_minutes,
        "overtime_minutes": r.overtime_minutes,
        "late_minutes": r.late_minutes,
        "status": r.status,
        "is_corrected": r.is_corrected,
        "created_at": r.created_at,
        "employee_name": f"{employee.first_name} {employee.last_name}",
        "employee_code": employee.employee_code,
        "department_name": dept.name if dept else "General",
        "breaks": [
            {
                "id": b.id,
                "break_start": b.break_start,
                "break_end": b.break_end,
                "duration_minutes": b.duration_minutes,
                "reason": b.reason
            }
            for b in breaks
        ]
    }

@router.post("/{record_id}/correct", response_model=AttendanceResponse)
async def correct_attendance(
    record_id: str,
    req: AttendanceCorrectionRequest,
    user: User = Depends(get_current_hr_or_admin),
    db: AsyncSession = Depends(get_db)
):
    record = await AttendanceService.correct_attendance(
        db=db,
        record_id=record_id,
        corrected_by=user.id,
        new_clock_in=req.clock_in,
        new_clock_out=req.clock_out,
        reason=req.reason
    )

    emp = (await db.execute(select(Employee).where(Employee.id == record.employee_id))).scalars().first()
    dept = (await db.execute(select(Department).where(Department.id == emp.department_id))).scalars().first() if emp and emp.department_id else None

    return {
        "id": record.id,
        "organization_id": record.organization_id,
        "employee_id": record.employee_id,
        "date": record.date,
        "clock_in": record.clock_in,
        "clock_out": record.clock_out,
        "worked_minutes": record.worked_minutes,
        "overtime_minutes": record.overtime_minutes,
        "late_minutes": record.late_minutes,
        "status": record.status,
        "is_corrected": record.is_corrected,
        "created_at": record.created_at,
        "employee_name": f"{emp.first_name} {emp.last_name}" if emp else None,
        "employee_code": emp.employee_code if emp else None,
        "department_name": dept.name if dept else "General",
        "breaks": []
    }
