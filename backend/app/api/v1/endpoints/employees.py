from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from app.core.database import get_db
from app.core.security import hash_password
from app.core.exceptions import NotFoundException, ConflictException, ForbiddenException
from app.models.models import Employee, User, Department, Shift, EmployeeShiftAssignment, EmployeeOnboardingRequest
from app.schemas.schemas import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse,
    EmployeeOnboardingRequestCreate, EmployeeOnboardingReview, EmployeeOnboardingResponse
)
from app.services.notification_service import NotificationService
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

@router.post("/request", response_model=EmployeeOnboardingResponse, status_code=status.HTTP_201_CREATED)
async def request_employee_onboarding(
    req: EmployeeOnboardingRequestCreate,
    user: User = Depends(get_current_hr_or_admin),
    db: AsyncSession = Depends(get_db)
):
    # Check if code or email already exists
    existing_emp = (await db.execute(
        select(Employee).where(
            and_(
                Employee.organization_id == user.organization_id,
                or_(
                    Employee.employee_code == req.employee_code.strip().upper(),
                    Employee.email == req.email.lower().strip()
                )
            )
        )
    )).scalars().first()
    if existing_emp:
        raise ConflictException("An employee with this employee code or email already exists.")

    existing_req = (await db.execute(
        select(EmployeeOnboardingRequest).where(
            and_(
                EmployeeOnboardingRequest.organization_id == user.organization_id,
                EmployeeOnboardingRequest.status == "pending_approval",
                or_(
                    EmployeeOnboardingRequest.employee_code == req.employee_code.strip().upper(),
                    EmployeeOnboardingRequest.email == req.email.lower().strip()
                )
            )
        )
    )).scalars().first()
    if existing_req:
        raise ConflictException("A pending onboarding request with this code or email is already awaiting approval.")

    # If Admin submitted the request, automatically authorize & create directly
    if user.role == "admin":
        onboard_req = EmployeeOnboardingRequest(
            organization_id=user.organization_id,
            requested_by_id=user.id,
            employee_code=req.employee_code.strip().upper(),
            first_name=req.first_name.strip(),
            last_name=req.last_name.strip(),
            email=req.email.lower().strip(),
            phone=req.phone,
            department_id=req.department_id,
            designation=req.designation.strip(),
            date_of_joining=req.date_of_joining or date.today(),
            role=req.role or "employee",
            status="approved",
            reviewed_by_id=user.id,
            reviewed_at=datetime.utcnow()
        )
        db.add(onboard_req)

        # Create user & employee directly
        user_stmt = select(User).where(User.email == req.email.lower().strip())
        existing_user = (await db.execute(user_stmt)).scalars().first()
        if not existing_user:
            new_user = User(
                organization_id=user.organization_id,
                email=req.email.lower().strip(),
                hashed_password=hash_password("AttendAI@123"),
                role=req.role or "employee",
                is_active=True
            )
            db.add(new_user)
            await db.flush()
            user_id = new_user.id
        else:
            user_id = existing_user.id

        new_emp = Employee(
            organization_id=user.organization_id,
            department_id=req.department_id,
            user_id=user_id,
            employee_code=req.employee_code.strip().upper(),
            first_name=req.first_name.strip(),
            last_name=req.last_name.strip(),
            email=req.email.lower().strip(),
            phone=req.phone,
            designation=req.designation.strip(),
            date_of_joining=req.date_of_joining or date.today(),
            is_active=True
        )
        db.add(new_emp)
        await db.commit()
        await db.refresh(onboard_req)

        dept = (await db.execute(select(Department).where(Department.id == onboard_req.department_id))).scalars().first() if onboard_req.department_id else None
        return {
            "id": onboard_req.id,
            "organization_id": onboard_req.organization_id,
            "requested_by_id": onboard_req.requested_by_id,
            "requested_by_name": f"{user.email} (Admin)",
            "employee_code": onboard_req.employee_code,
            "first_name": onboard_req.first_name,
            "last_name": onboard_req.last_name,
            "email": onboard_req.email,
            "phone": onboard_req.phone,
            "department_id": onboard_req.department_id,
            "department_name": dept.name if dept else "General",
            "designation": onboard_req.designation,
            "date_of_joining": onboard_req.date_of_joining,
            "role": onboard_req.role,
            "status": onboard_req.status,
            "reviewed_by_id": onboard_req.reviewed_by_id,
            "reviewed_at": onboard_req.reviewed_at,
            "rejection_reason": None,
            "created_at": onboard_req.created_at
        }

    # If HR Manager submitted the request:
    onboard_req = EmployeeOnboardingRequest(
        organization_id=user.organization_id,
        requested_by_id=user.id,
        employee_code=req.employee_code.strip().upper(),
        first_name=req.first_name.strip(),
        last_name=req.last_name.strip(),
        email=req.email.lower().strip(),
        phone=req.phone,
        department_id=req.department_id,
        designation=req.designation.strip(),
        date_of_joining=req.date_of_joining or date.today(),
        role=req.role or "employee",
        status="pending_approval"
    )
    db.add(onboard_req)
    await db.commit()
    await db.refresh(onboard_req)

    # Notify all Admins in the organization
    admin_users = (await db.execute(select(User).where(and_(User.organization_id == user.organization_id, User.role == "admin")))).scalars().all()
    for adm in admin_users:
        await NotificationService.create_notification(
            db=db,
            organization_id=user.organization_id,
            user_id=adm.id,
            category="approvals",
            title="New Employee Onboarding Authorization",
            message=f"HR Manager submitted a request to add employee {req.first_name} {req.last_name} ({req.employee_code.strip().upper()}) as {req.designation}. Please review and authorize.",
            priority="high",
            link="/employees"
        )

    dept = (await db.execute(select(Department).where(Department.id == onboard_req.department_id))).scalars().first() if onboard_req.department_id else None
    return {
        "id": onboard_req.id,
        "organization_id": onboard_req.organization_id,
        "requested_by_id": onboard_req.requested_by_id,
        "requested_by_name": f"{user.email} (HR)",
        "employee_code": onboard_req.employee_code,
        "first_name": onboard_req.first_name,
        "last_name": onboard_req.last_name,
        "email": onboard_req.email,
        "phone": onboard_req.phone,
        "department_id": onboard_req.department_id,
        "department_name": dept.name if dept else "General",
        "designation": onboard_req.designation,
        "date_of_joining": onboard_req.date_of_joining,
        "role": onboard_req.role,
        "status": onboard_req.status,
        "reviewed_by_id": None,
        "reviewed_at": None,
        "rejection_reason": None,
        "created_at": onboard_req.created_at
    }

@router.get("/onboarding-requests", response_model=List[EmployeeOnboardingResponse])
async def list_onboarding_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    user: User = Depends(get_current_hr_or_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(EmployeeOnboardingRequest, Department.name.label("dept_name"), User.email.label("requester_email"))
        .outerjoin(Department, Department.id == EmployeeOnboardingRequest.department_id)
        .outerjoin(User, User.id == EmployeeOnboardingRequest.requested_by_id)
        .where(EmployeeOnboardingRequest.organization_id == user.organization_id)
    )
    if status_filter:
        stmt = stmt.where(EmployeeOnboardingRequest.status == status_filter)

    stmt = stmt.order_by(EmployeeOnboardingRequest.created_at.desc())
    results = (await db.execute(stmt)).all()

    output = []
    for req_obj, d_name, r_email in results:
        output.append({
            "id": req_obj.id,
            "organization_id": req_obj.organization_id,
            "requested_by_id": req_obj.requested_by_id,
            "requested_by_name": r_email or "HR Manager",
            "employee_code": req_obj.employee_code,
            "first_name": req_obj.first_name,
            "last_name": req_obj.last_name,
            "email": req_obj.email,
            "phone": req_obj.phone,
            "department_id": req_obj.department_id,
            "department_name": d_name or "General",
            "designation": req_obj.designation,
            "date_of_joining": req_obj.date_of_joining,
            "role": req_obj.role,
            "status": req_obj.status,
            "reviewed_by_id": req_obj.reviewed_by_id,
            "reviewed_at": req_obj.reviewed_at,
            "rejection_reason": req_obj.rejection_reason,
            "created_at": req_obj.created_at
        })
    return output

@router.post("/onboarding-requests/{request_id}/review", response_model=EmployeeOnboardingResponse)
async def review_onboarding_request(
    request_id: str,
    review: EmployeeOnboardingReview,
    user: User = Depends(get_current_hr_or_admin),
    db: AsyncSession = Depends(get_db)
):
    if user.role != "admin":
        raise ForbiddenException("Only Administrators can authorize new employee onboarding requests.")

    stmt = select(EmployeeOnboardingRequest).where(
        and_(
            EmployeeOnboardingRequest.id == request_id,
            EmployeeOnboardingRequest.organization_id == user.organization_id
        )
    )
    req_obj = (await db.execute(stmt)).scalars().first()
    if not req_obj:
        raise NotFoundException("Employee onboarding request not found.")

    if req_obj.status != "pending_approval":
        raise ConflictException(f"This onboarding request has already been reviewed ({req_obj.status}).")

    if review.status.lower() == "approved":
        user_stmt = select(User).where(User.email == req_obj.email)
        existing_user = (await db.execute(user_stmt)).scalars().first()
        if not existing_user:
            new_user = User(
                organization_id=user.organization_id,
                email=req_obj.email,
                hashed_password=hash_password("AttendAI@123"),
                role=req_obj.role,
                is_active=True
            )
            db.add(new_user)
            await db.flush()
            user_id = new_user.id
        else:
            user_id = existing_user.id

        emp = Employee(
            organization_id=user.organization_id,
            department_id=req_obj.department_id,
            user_id=user_id,
            employee_code=req_obj.employee_code,
            first_name=req_obj.first_name,
            last_name=req_obj.last_name,
            email=req_obj.email,
            phone=req_obj.phone,
            designation=req_obj.designation,
            date_of_joining=req_obj.date_of_joining,
            is_active=True
        )
        db.add(emp)
        await db.flush()

        def_shift = (await db.execute(select(Shift).where(Shift.organization_id == user.organization_id))).scalars().first()
        if def_shift:
            assign = EmployeeShiftAssignment(
                employee_id=emp.id,
                shift_id=def_shift.id,
                effective_from=req_obj.date_of_joining,
                is_active=True
            )
            db.add(assign)

        req_obj.status = "approved"
        req_obj.reviewed_by_id = user.id
        req_obj.reviewed_at = datetime.utcnow()

        if req_obj.requested_by_id:
            await NotificationService.create_notification(
                db=db,
                organization_id=user.organization_id,
                user_id=req_obj.requested_by_id,
                category="approvals",
                title="Employee Onboarding Approved",
                message=f"Admin authorized and created employee record for {req_obj.first_name} {req_obj.last_name} ({req_obj.employee_code}).",
                priority="success",
                link="/employees"
            )
    else:
        req_obj.status = "rejected"
        req_obj.rejection_reason = review.rejection_reason or "Not authorized by Administrator."
        req_obj.reviewed_by_id = user.id
        req_obj.reviewed_at = datetime.utcnow()

        if req_obj.requested_by_id:
            await NotificationService.create_notification(
                db=db,
                organization_id=user.organization_id,
                user_id=req_obj.requested_by_id,
                category="approvals",
                title="Employee Onboarding Rejected",
                message=f"Admin rejected employee onboarding request for {req_obj.first_name} {req_obj.last_name} ({req_obj.employee_code}): {req_obj.rejection_reason}",
                priority="warning",
                link="/employees"
            )

    await db.commit()
    await db.refresh(req_obj)

    dept = (await db.execute(select(Department).where(Department.id == req_obj.department_id))).scalars().first() if req_obj.department_id else None
    return {
        "id": req_obj.id,
        "organization_id": req_obj.organization_id,
        "requested_by_id": req_obj.requested_by_id,
        "requested_by_name": "HR Requester",
        "employee_code": req_obj.employee_code,
        "first_name": req_obj.first_name,
        "last_name": req_obj.last_name,
        "email": req_obj.email,
        "phone": req_obj.phone,
        "department_id": req_obj.department_id,
        "department_name": dept.name if dept else "General",
        "designation": req_obj.designation,
        "date_of_joining": req_obj.date_of_joining,
        "role": req_obj.role,
        "status": req_obj.status,
        "reviewed_by_id": req_obj.reviewed_by_id,
        "reviewed_at": req_obj.reviewed_at,
        "rejection_reason": req_obj.rejection_reason,
        "created_at": req_obj.created_at
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
