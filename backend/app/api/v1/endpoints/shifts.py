from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.core.exceptions import NotFoundException, ConflictException
from app.models.models import Shift, EmployeeShiftAssignment, User, Employee
from app.schemas.schemas import ShiftCreate, ShiftUpdate, ShiftResponse, ShiftAssignmentCreate, ShiftAssignmentResponse
from app.api.deps import get_current_user, get_current_hr_or_admin

router = APIRouter(prefix="/shifts", tags=["Shifts & Scheduling"])

@router.get("", response_model=List[ShiftResponse])
async def list_shifts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Shift).where(Shift.organization_id == user.organization_id)
    shifts = (await db.execute(stmt)).scalars().all()
    return shifts

@router.get("/my-shift")
async def get_my_shift(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    emp_stmt = select(Employee).where(Employee.user_id == user.id)
    emp = (await db.execute(emp_stmt)).scalars().first()
    
    shift = None
    assignment_info = None

    if emp:
        assign_stmt = (
            select(EmployeeShiftAssignment, Shift)
            .join(Shift, Shift.id == EmployeeShiftAssignment.shift_id)
            .where(
                and_(
                    EmployeeShiftAssignment.employee_id == emp.id,
                    EmployeeShiftAssignment.is_active == True
                )
            )
        )
        res = (await db.execute(assign_stmt)).first()
        if res:
            assign_obj, shift_obj = res
            shift = shift_obj
            assignment_info = {
                "id": assign_obj.id,
                "effective_from": str(assign_obj.effective_from),
                "effective_to": str(assign_obj.effective_to) if assign_obj.effective_to else None,
                "is_active": assign_obj.is_active
            }

    if not shift:
        shift = (await db.execute(select(Shift).where(Shift.organization_id == user.organization_id))).scalars().first()

    return {
        "shift": {
            "id": shift.id if shift else "default",
            "name": shift.name if shift else "General Standard Shift",
            "code": shift.code if shift else "GEN",
            "start_time": shift.start_time.strftime("%H:%M") if shift and hasattr(shift.start_time, "strftime") else str(shift.start_time)[:5] if shift else "09:00",
            "end_time": shift.end_time.strftime("%H:%M") if shift and hasattr(shift.end_time, "strftime") else str(shift.end_time)[:5] if shift else "17:00",
            "grace_period_minutes": shift.grace_period_minutes if shift else 15,
            "required_hours": shift.required_hours if shift else 8.0,
            "is_overnight": shift.is_overnight if shift else False
        } if shift else None,
        "assignment": assignment_info
    }

@router.post("", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED)
async def create_shift(
    req: ShiftCreate,
    user: User = Depends(get_current_hr_or_admin),
    db: AsyncSession = Depends(get_db)
):
    existing = (await db.execute(
        select(Shift).where(
            and_(
                Shift.organization_id == user.organization_id,
                Shift.code == req.code.upper().strip()
            )
        )
    )).scalars().first()
    if existing:
        raise ConflictException("Shift code already exists in organization")

    shift = Shift(
        organization_id=user.organization_id,
        name=req.name.strip(),
        code=req.code.upper().strip(),
        start_time=req.start_time,
        end_time=req.end_time,
        grace_period_minutes=req.grace_period_minutes,
        required_hours=req.required_hours,
        is_overnight=req.is_overnight
    )
    db.add(shift)
    await db.commit()
    await db.refresh(shift)
    return shift

@router.put("/{shift_id}", response_model=ShiftResponse)
async def update_shift(
    shift_id: str,
    req: ShiftUpdate,
    user: User = Depends(get_current_hr_or_admin),
    db: AsyncSession = Depends(get_db)
):
    shift = (await db.execute(
        select(Shift).where(
            and_(
                Shift.id == shift_id,
                Shift.organization_id == user.organization_id
            )
        )
    )).scalars().first()
    if not shift:
        raise NotFoundException("Shift not found")

    if req.name is not None:
        shift.name = req.name.strip()
    if req.start_time is not None:
        shift.start_time = req.start_time
    if req.end_time is not None:
        shift.end_time = req.end_time
    if req.grace_period_minutes is not None:
        shift.grace_period_minutes = req.grace_period_minutes
    if req.required_hours is not None:
        shift.required_hours = req.required_hours
    if req.is_overnight is not None:
        shift.is_overnight = req.is_overnight

    await db.commit()
    await db.refresh(shift)
    return shift

@router.post("/assign", response_model=ShiftAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_shift(
    req: ShiftAssignmentCreate,
    user: User = Depends(get_current_hr_or_admin),
    db: AsyncSession = Depends(get_db)
):
    assignment = EmployeeShiftAssignment(
        employee_id=req.employee_id,
        shift_id=req.shift_id,
        effective_from=req.effective_from,
        effective_to=req.effective_to,
        is_active=True
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)

    shift = (await db.execute(select(Shift).where(Shift.id == req.shift_id))).scalars().first()
    return {
        "id": assignment.id,
        "employee_id": assignment.employee_id,
        "shift_id": assignment.shift_id,
        "effective_from": assignment.effective_from,
        "effective_to": assignment.effective_to,
        "is_active": assignment.is_active,
        "shift_name": shift.name if shift else None
    }
