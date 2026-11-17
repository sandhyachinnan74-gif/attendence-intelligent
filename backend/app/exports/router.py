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
            {"id": "csv", "label": "CSV Document (.csv)", "desc": "Clean UTF-8 spreadsheet for tabular data analysis"},
            {"id": "pdf", "label": "Printable PDF (.pdf)", "desc": "Executive document with table styling and page numbering"}
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
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    file_path, filename, media_type = await ExportService.get_export_for_download(db, user, export_id)
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# -------------------------------------------------------------
# Backwards-compatible legacy quick export endpoints
# -------------------------------------------------------------
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
    s_date = start_date or (date.today() - timedelta(days=30))
    e_date = end_date or date.today()

    target_emp_id = None
    if user.role == "employee":
        emp_stmt = select(Employee).where(Employee.user_id == user.id)
        emp = (await db.execute(emp_stmt)).scalars().first()
        target_emp_id = emp.id if emp else "__not_found__"
        filename = f"my_attendance_{s_date}_{e_date}.csv"
    else:
        target_emp_id = employee_id
        filename = f"attendai_attendance_{s_date}_{e_date}.csv"

    csv_stream = await LegacyExportService.export_attendance_csv(
        db=db,
        organization_id=user.organization_id,
        start_date=s_date,
        end_date=e_date,
        employee_id=target_emp_id
    )

    content = csv_stream.getvalue().encode("utf-8")
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
    s_date = start_date or (date.today() - timedelta(days=30))
    e_date = end_date or date.today()

    target_emp_id = None
    if user.role == "employee":
        emp_stmt = select(Employee).where(Employee.user_id == user.id)
        emp = (await db.execute(emp_stmt)).scalars().first()
        target_emp_id = emp.id if emp else "__not_found__"
        filename = f"my_attendance_{s_date}_{e_date}.xlsx"
    else:
        target_emp_id = employee_id
        filename = f"attendai_attendance_{s_date}_{e_date}.xlsx"

    xlsx_stream = await LegacyExportService.export_attendance_xlsx(
        db=db,
        organization_id=user.organization_id,
        start_date=s_date,
        end_date=e_date,
        employee_id=target_emp_id
    )

    content = xlsx_stream.getvalue()
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Content-Length": str(len(content))
        }
    )
