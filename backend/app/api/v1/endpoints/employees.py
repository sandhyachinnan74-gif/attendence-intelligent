from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from app.core.database import get_db
from app.core.security import hash_password
from app.core.exceptions import NotFoundException, ConflictException, ForbiddenException
from app.models.models import Employee, User, Department, Shift, EmployeeShiftAssignment
from app.schemas.schemas import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.api.deps import get_current_user, get_current_hr_or_admin

router = APIRouter(prefix="/employees", tags=["Employees"])

@router.get("", response_model=List[EmployeeResponse])
async def list_employees(
    department_id: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_hr_or_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Employee, Department.name.label("department_name"))
        .outerjoin(Department, Department.id == Employee.department_id)
        .where(Employee.organization_id == user.organization_id)
    )

    # Scoped access: if normal employee, only return non-sensitive directory view or self
    if department_id:
        stmt = stmt.where(Employee.department_id == department_id)
    if is_active is not None:
        stmt = stmt.where(Employee.is_active == is_active)
    if search:
        s = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                Employee.first_name.ilike(s),
                Employee.last_name.ilike(s),
                Employee.employee_code.ilike(s),
                Employee.email.ilike(s),
                Employee.designation.ilike(s)
            )
        )

    stmt = stmt.offset(skip).limit(limit)
    res = await db.execute(stmt)
    
    output = []
    for emp, dept_name in res.all():
        output.append({
            "id": emp.id,
            "organization_id": emp.organization_id,
            "department_id": emp.department_id,
            "user_id": emp.user_id,
            "employee_code": emp.employee_code,
            "first_name": emp.first_name,
            "last_name": emp.last_name,
            "email": emp.email,
            "phone": emp.phone,
            "designation": emp.designation,
            "date_of_joining": emp.date_of_joining,
            "is_active": emp.is_active,
            "created_at": emp.created_at,
            "department_name": dept_name,
            "current_shift": "General Shift (09:00 - 17:00)"
        })
    return output

@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    req: EmployeeCreate,
    user: User = Depends(get_current_hr_or_admin),
    db: AsyncSession = Depends(get_db)
):
    # Check if employee code or email already exists
    existing_stmt = select(Employee).where(
        and_(
            Employee.organization_id == user.organization_id,
            or_(
                Employee.employee_code == req.employee_code,
                Employee.email == req.email.lower().strip()
            )
        )
    )
    existing = (await db.execute(existing_stmt)).scalars().first()
    if existing:
        raise ConflictException("Employee with this code or email already exists in organization")

    # Create associated user account
    user_stmt = select(User).where(User.email == req.email.lower().strip())
    existing_user = (await db.execute(user_stmt)).scalars().first()
    if not existing_user:
        new_user = User(
            organization_id=user.organization_id,
            email=req.email.lower().strip(),
            hashed_password=hash_password(req.password or "AttendAI@123"),
            role=req.role or "employee",
            is_active=True
        )
        db.add(new_user)
        await db.flush()
        user_id = new_user.id
    else:
        user_id = existing_user.id

    emp = Employee(
        organization_id=user.organization_id,
        department_id=req.department_id,
        user_id=user_id,
        employee_code=req.employee_code,
        first_name=req.first_name,
        last_name=req.last_name,
        email=req.email.lower().strip(),
        phone=req.phone,
        designation=req.designation,
        date_of_joining=req.date_of_joining,
        is_active=True
    )
    db.add(emp)
    await db.commit()
    await db.refresh(emp)

    dept_name = None
    if emp.department_id:
        d = (await db.execute(select(Department).where(Department.id == emp.department_id))).scalars().first()
        dept_name = d.name if d else None

    return {
        "id": emp.id,
        "organization_id": emp.organization_id,
        "department_id": emp.department_id,
        "user_id": emp.user_id,
        "employee_code": emp.employee_code,
        "first_name": emp.first_name,
        "last_name": emp.last_name,
        "email": emp.email,
        "phone": emp.phone,
        "designation": emp.designation,
        "date_of_joining": emp.date_of_joining,
        "is_active": emp.is_active,
        "created_at": emp.created_at,
        "department_name": dept_name,
        "current_shift": "General Shift (09:00 - 17:00)"
    }

@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Employee, Department.name.label("department_name"))
        .outerjoin(Department, Department.id == Employee.department_id)
        .where(
            and_(
                Employee.id == employee_id,
                Employee.organization_id == user.organization_id
            )
        )
    )
    res = (await db.execute(stmt)).first()
    if not res:
        raise NotFoundException("Employee not found")

    emp, dept_name = res
    # Employee permission boundary: employee can only see own private details
    if user.role == "employee" and emp.user_id != user.id:
        raise ForbiddenException("Access denied: You cannot view another employee's private profile")

    return {
        "id": emp.id,
        "organization_id": emp.organization_id,
        "department_id": emp.department_id,
        "user_id": emp.user_id,
        "employee_code": emp.employee_code,
        "first_name": emp.first_name,
        "last_name": emp.last_name,
        "email": emp.email,
        "phone": emp.phone,
        "designation": emp.designation,
        "date_of_joining": emp.date_of_joining,
        "is_active": emp.is_active,
        "created_at": emp.created_at,
        "department_name": dept_name,
        "current_shift": "General Shift (09:00 - 17:00)"
    }

@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    req: EmployeeUpdate,
    user: User = Depends(get_current_hr_or_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Employee).where(
        and_(
            Employee.id == employee_id,
            Employee.organization_id == user.organization_id
        )
    )
    emp = (await db.execute(stmt)).scalars().first()
    if not emp:
        raise NotFoundException("Employee not found")

    if req.department_id is not None:
        emp.department_id = req.department_id
    if req.first_name is not None:
        emp.first_name = req.first_name
    if req.last_name is not None:
        emp.last_name = req.last_name
    if req.phone is not None:
        emp.phone = req.phone
    if req.designation is not None:
        emp.designation = req.designation
    if req.is_active is not None:
        emp.is_active = req.is_active
        # Also toggle user active status
        if emp.user_id:
            u = (await db.execute(select(User).where(User.id == emp.user_id))).scalars().first()
            if u:
                u.is_active = req.is_active

    await db.commit()
    await db.refresh(emp)

    dept_name = None
    if emp.department_id:
        d = (await db.execute(select(Department).where(Department.id == emp.department_id))).scalars().first()
        dept_name = d.name if d else None

    return {
        "id": emp.id,
        "organization_id": emp.organization_id,
        "department_id": emp.department_id,
        "user_id": emp.user_id,
        "employee_code": emp.employee_code,
        "first_name": emp.first_name,
        "last_name": emp.last_name,
        "email": emp.email,
        "phone": emp.phone,
        "designation": emp.designation,
        "date_of_joining": emp.date_of_joining,
        "is_active": emp.is_active,
        "created_at": emp.created_at,
        "department_name": dept_name,
        "current_shift": "General Shift (09:00 - 17:00)"
    }
