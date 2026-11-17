from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.core.database import get_db
from app.core.exceptions import NotFoundException, ConflictException
from app.models.models import Department, Employee, User
from app.schemas.schemas import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from app.api.deps import get_current_user, get_current_hr_or_admin

router = APIRouter(prefix="/departments", tags=["Departments"])

@router.get("", response_model=List[DepartmentResponse])
async def list_departments(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(
            Department,
            func.count(Employee.id).label("employee_count")
        )
        .outerjoin(Employee, Employee.department_id == Department.id)
        .where(Department.organization_id == user.organization_id)
        .group_by(Department.id)
    )
    res = await db.execute(stmt)
    output = []
    for dept, count in res.all():
        output.append({
            "id": dept.id,
            "organization_id": dept.organization_id,
            "name": dept.name,
            "code": dept.code,
            "manager_id": dept.manager_id,
            "created_at": dept.created_at,
            "employee_count": count or 0
        })
    return output

@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    req: DepartmentCreate,
    user: User = Depends(get_current_hr_or_admin),
    db: AsyncSession = Depends(get_db)
):
    existing = (await db.execute(
        select(Department).where(
            and_(
                Department.organization_id == user.organization_id,
                Department.code == req.code.upper().strip()
            )
        )
    )).scalars().first()
    if existing:
        raise ConflictException("Department code already exists in organization")

    dept = Department(
        organization_id=user.organization_id,
        name=req.name.strip(),
        code=req.code.upper().strip(),
        manager_id=req.manager_id
    )
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return {
        "id": dept.id,
        "organization_id": dept.organization_id,
        "name": dept.name,
        "code": dept.code,
        "manager_id": dept.manager_id,
        "created_at": dept.created_at,
        "employee_count": 0
    }

@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: str,
    req: DepartmentUpdate,
    user: User = Depends(get_current_hr_or_admin),
    db: AsyncSession = Depends(get_db)
):
    dept = (await db.execute(
        select(Department).where(
            and_(
                Department.id == department_id,
                Department.organization_id == user.organization_id
            )
        )
    )).scalars().first()
    if not dept:
        raise NotFoundException("Department not found")

    if req.name is not None:
        dept.name = req.name.strip()
    if req.code is not None:
        dept.code = req.code.upper().strip()
    if req.manager_id is not None:
        dept.manager_id = req.manager_id

    await db.commit()
    await db.refresh(dept)

    # count employees
    emp_count = (await db.execute(
        select(func.count(Employee.id)).where(Employee.department_id == dept.id)
    )).scalar_one()

    return {
        "id": dept.id,
        "organization_id": dept.organization_id,
        "name": dept.name,
        "code": dept.code,
        "manager_id": dept.manager_id,
        "created_at": dept.created_at,
        "employee_count": emp_count or 0
    }
