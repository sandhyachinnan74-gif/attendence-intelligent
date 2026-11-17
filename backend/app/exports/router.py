from datetime import date
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status, Header
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.models.models import User, Employee, Department
from app.api.deps import get_current_user, get_current_employee_profile
from app.exports.schemas import (
    ReportPreviewRequest, ReportPreviewResponse,
    ReportGenerateRequest, ReportGenerateResponse,
    ExportHistoryResponse
)
from app.exports.permissions import (
    get_report_types_for_user, get_columns_for_report_type, COLUMNS_REGISTRY
)
from app.exports.service import ExportService
from app.services.export_service import ExportService as LegacyExportService

router = APIRouter(prefix="/exports", tags=["Custom Exports & Reporting"])

async def get_legacy_export_user(
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None)
) -> User:
    raw_token = None
    if authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split(" ")[1]
    elif token:
        raw_token = token

    if not raw_token:
        from app.core.exceptions import UnauthorizedException
        raise UnauthorizedException("Missing Authorization header or token parameter")

    from app.core.security import decode_token
    from app.core.exceptions import UnauthorizedException
    try:
        payload = decode_token(raw_token)
    except Exception:
        raise UnauthorizedException("Invalid or expired authentication token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Token missing user subject")

    stmt = select(User).where(User.id == user_id)
    user = (await db.execute(stmt)).scalars().first()
    if not user or not user.is_active:
        raise UnauthorizedException("User account is inactive or not found")
    return user

@router.get("/config")
async def get_export_config(
    user: User = Depends(get_current_user),
    employee: Optional[Employee] = Depends(get_current_employee_profile),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns available report types, departments, and employees authorized for the requesting role.
    """
    report_types = get_report_types_for_user(user)

    # Scoped departments & employees
    departments = []
    employees = []

    if user.role in ["admin", "hr_manager"]:
        dept_stmt = select(Department).where(Department.organization_id == user.organization_id)
        if user.role == "hr_manager" and employee and employee.department_id:
            dept_stmt = dept_stmt.where(Department.id == employee.department_id)
        dept_res = (await db.execute(dept_stmt)).scalars().all()
        departments = [{"id": d.id, "name": d.name, "code": d.code} for d in dept_res]

        emp_stmt = select(Employee).where(and_(Employee.organization_id == user.organization_id, Employee.is_active == True))
        if user.role == "hr_manager" and employee and employee.department_id:
            emp_stmt = emp_stmt.where(Employee.department_id == employee.department_id)
        emp_stmt = emp_stmt.order_by(Employee.first_name, Employee.last_name)
        emp_res = (await db.execute(emp_stmt)).scalars().all()
        employees = [
            {
                "id": e.id,
                "code": e.employee_code,
                "name": f"{e.first_name} {e.last_name}",
                "designation": e.designation or "Employee",
                "department_id": e.department_id
            }
            for e in emp_res
        ]

    # Prepopulate column definitions for each report type
    columns_map = {}
    for rt in report_types:
        columns_map[rt["id"]] = get_columns_for_report_type(rt["id"], user.role)

    return {
        "role": user.role,
        "report_types": report_types,
        "departments": departments,
        "employees": employees,
        "columns_map": columns_map,
        "date_presets": [
            {"id": "today", "label": "Today"},
            {"id": "yesterday", "label": "Yesterday"},
            {"id": "this_week", "label": "This Week"},
            {"id": "last_week", "label": "Last Week"},
            {"id": "this_month", "label": "This Month"},
            {"id": "last_month", "label": "Last Month"},
            {"id": "last_7_days", "label": "Last 7 Days"},
            {"id": "last_30_days", "label": "Last 30 Days"},
            {"id": "last_90_days", "label": "Last 90 Days"},
            {"id": "this_quarter", "label": "This Quarter"},
            {"id": "this_year", "label": "This Year"},
            {"id": "custom", "label": "Custom Date Range"}
        ],
        "formats": [
            {"id": "xlsx", "label": "Excel Workbook (.xlsx)", "desc": "Structured workbook with summary stats and multi-department tabs"},
            {"id": "csv", "label": "CSV Document (.csv)", "desc": "Clean UTF-8 spreadsheet for tabular data analysis"}
        ]
    }

@router.post("/preview", response_model=ReportPreviewResponse)
async def preview_custom_report(
    req: ReportPreviewRequest,
    user: User = Depends(get_current_user),
    employee: Optional[Employee] = Depends(get_current_employee_profile),
    db: AsyncSession = Depends(get_db)
):
    return await ExportService.preview_report(db, user, employee, req)

@router.post("/generate", response_model=ReportGenerateResponse)
async def generate_custom_report(
    req: ReportGenerateRequest,
    user: User = Depends(get_current_user),
    employee: Optional[Employee] = Depends(get_current_employee_profile),
    db: AsyncSession = Depends(get_db)
):
    return await ExportService.generate_report(db, user, employee, req)

@router.get("/history", response_model=List[ExportHistoryResponse])
async def list_export_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await ExportService.list_history(db, user)

@router.get("/{export_id}/download")
async def download_export_file(
    export_id: str,
    user: User = Depends(get_legacy_export_user),
    db: AsyncSession = Depends(get_db)
):
    file_path, filename, media_type = await ExportService.get_export_for_download(db, user, export_id)
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition, Content-Length"
        }
    )

# -------------------------------------------------------------
# Backwards-compatible legacy quick export endpoints
# -------------------------------------------------------------

@router.get("/attendance/csv")
async def legacy_export_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    department_id: Optional[str] = Query(None),
    employee_id: Optional[str] = Query(None),
    user: User = Depends(get_legacy_export_user),
    db: AsyncSession = Depends(get_db)
):
    from datetime import timedelta
    from app.exports.query_builder import ExportQueryBuilder
    from app.exports.generators.csv_generator import generate_csv_bytes

    s_date = start_date or (date.today() - timedelta(days=30))
    e_date = end_date or date.today()

    current_emp = (await db.execute(select(Employee).where(Employee.user_id == user.id))).scalars().first()

    if user.role == "employee":
        report_type = "personal_attendance"
        scope_type = "personal"
        target_dept_ids = None
        target_emp_ids = [current_emp.id] if current_emp else None
        filename = f"AttendAI_My_Attendance_{s_date}_{e_date}.csv"
    else:
        report_type = "attendance"
        if employee_id:
            scope_type = "individual_employee"
            target_dept_ids = None
            target_emp_ids = [employee_id]
        elif department_id:
            scope_type = "department"
            target_dept_ids = [department_id]
            target_emp_ids = None
        else:
            scope_type = "organization"
            target_dept_ids = None
            target_emp_ids = None
        filename = f"AttendAI_Attendance_{s_date}_{e_date}.csv"

    selected_cols = ExportService._resolve_columns(report_type, None, user.role)
    rows, meta = await ExportQueryBuilder.fetch_report_data(
        db=db,
        user=user,
        current_employee=current_emp,
        report_type=report_type,
        scope_type=scope_type,
        department_ids=target_dept_ids,
        employee_ids=target_emp_ids,
        start_date=s_date,
        end_date=e_date
    )

    content = generate_csv_bytes(rows, selected_cols)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Content-Length": str(len(content))
        }
    )

@router.get("/attendance/xlsx")
async def legacy_export_xlsx(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    department_id: Optional[str] = Query(None),
    employee_id: Optional[str] = Query(None),
    user: User = Depends(get_legacy_export_user),
    db: AsyncSession = Depends(get_db)
):
    from datetime import timedelta
    from app.exports.query_builder import ExportQueryBuilder
    from app.exports.generators.excel_generator import generate_excel_bytes
    from app.models.models import Organization

    s_date = start_date or (date.today() - timedelta(days=30))
    e_date = end_date or date.today()

    current_emp = (await db.execute(select(Employee).where(Employee.user_id == user.id))).scalars().first()

    org_name = "AttendAI Global Technologies"
    org = (await db.execute(select(Organization).where(Organization.id == user.organization_id))).scalars().first()
    if org:
        org_name = org.name

    if user.role == "employee":
        report_type = "personal_attendance"
        scope_type = "personal"
        target_dept_ids = None
        target_emp_ids = [current_emp.id] if current_emp else None
        report_title = "My Daily Attendance Report"
        filename = f"AttendAI_My_Attendance_{s_date}_{e_date}.xlsx"
        gen_by = f"{current_emp.first_name} {current_emp.last_name}" if current_emp else "Employee"
    else:
        report_type = "attendance"
        if employee_id:
            scope_type = "individual_employee"
            target_dept_ids = None
            target_emp_ids = [employee_id]
            report_title = "Employee Attendance Report"
        elif department_id:
            scope_type = "department"
            target_dept_ids = [department_id]
            target_emp_ids = None
            report_title = "Department Attendance Report"
        else:
            scope_type = "organization"
            target_dept_ids = None
            target_emp_ids = None
            report_title = "Workforce Attendance Report"
        filename = f"AttendAI_Attendance_{s_date}_{e_date}.xlsx"
        gen_by = "System Administrator" if user.role == "admin" else "HR Manager"

    selected_cols = ExportService._resolve_columns(report_type, None, user.role)
    rows, meta = await ExportQueryBuilder.fetch_report_data(
        db=db,
        user=user,
        current_employee=current_emp,
        report_type=report_type,
        scope_type=scope_type,
        department_ids=target_dept_ids,
        employee_ids=target_emp_ids,
        start_date=s_date,
        end_date=e_date
    )

    file_bytes = generate_excel_bytes(
        rows=rows,
        columns=selected_cols,
        report_title=report_title,
        scope_summary=meta["scope_summary"],
        start_date=str(s_date),
        end_date=str(e_date),
        organization_name=org_name,
        split_by_department=(scope_type == "organization"),
        report_type=report_type,
        generated_by=gen_by
    )

    return Response(
        content=file_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Content-Length": str(len(file_bytes))
        }
    )
