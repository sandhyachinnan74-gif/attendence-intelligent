import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.models.models import User, Employee, ExportRecord, Organization
from app.core.exceptions import NotFoundException, ForbiddenException, ValidationException
from app.exports.schemas import (
    ReportPreviewRequest, ReportPreviewResponse,
    ReportGenerateRequest, ReportGenerateResponse,
    ExportHistoryResponse
)
from app.exports.permissions import (
    get_report_types_for_user, get_columns_for_report_type, resolve_date_range
)
from app.exports.query_builder import ExportQueryBuilder
from app.exports.generators.csv_generator import generate_csv_bytes
from app.exports.generators.excel_generator import generate_excel_bytes
from app.exports.generators.pdf_generator import generate_pdf_bytes

EXPORT_STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports_storage"))
os.makedirs(EXPORT_STORAGE_DIR, exist_ok=True)

class ExportService:
    @staticmethod
    def _resolve_report_title(report_type: str, custom_title: Optional[str], user: User) -> str:
        if custom_title and custom_title.strip():
            return custom_title.strip()
        types = get_report_types_for_user(user)
        match = next((t for t in types if t["id"] == report_type), None)
        return match["name"] if match else report_type.replace("_", " ").title()

    @staticmethod
    def _resolve_columns(report_type: str, requested_columns: Optional[List[str]], user_role: str) -> List[Dict[str, str]]:
        all_cols = get_columns_for_report_type(report_type, user_role)
        if not requested_columns or len(requested_columns) == 0:
            # Default columns
            selected = [c for c in all_cols if c.get("is_default", True)]
            return selected if selected else all_cols
        
        # Filter requested columns in order
        col_map = {c["id"]: c for c in all_cols}
        result = []
        for cid in requested_columns:
            if cid in col_map:
                result.append(col_map[cid])
        return result if result else all_cols

    @staticmethod
    async def preview_report(
        db: AsyncSession,
        user: User,
        current_employee: Optional[Employee],
        req: ReportPreviewRequest
    ) -> ReportPreviewResponse:
        start_d, end_d = resolve_date_range(req.date_preset, req.start_date, req.end_date)
        report_title = ExportService._resolve_report_title(req.report_type, None, user)
        selected_cols = ExportService._resolve_columns(req.report_type, req.columns, user.role)

        rows, meta = await ExportQueryBuilder.fetch_report_data(
            db=db,
            user=user,
            current_employee=current_employee,
            report_type=req.report_type,
            scope_type=req.scope_type,
            department_ids=req.department_ids,
            employee_ids=req.employee_ids,
            start_date=start_d,
            end_date=end_d,
            filters=req.filters
        )

        return ReportPreviewResponse(
            report_type=req.report_type,
            report_title=report_title,
            scope_summary=meta["scope_summary"],
            start_date=start_d,
            end_date=end_d,
            employees_count=meta["employees_count"],
            departments_count=meta["departments_count"],
            selected_columns_count=len(selected_cols),
            record_count=meta["total_records"],
            format=req.format.lower(),
            is_authorized=True
        )

    @staticmethod
    async def generate_report(
        db: AsyncSession,
        user: User,
        current_employee: Optional[Employee],
        req: ReportGenerateRequest
    ) -> ReportGenerateResponse:
        start_d, end_d = resolve_date_range(req.date_preset, req.start_date, req.end_date)
        report_title = ExportService._resolve_report_title(req.report_type, req.report_title, user)
        selected_cols = ExportService._resolve_columns(req.report_type, req.columns, user.role)

        rows, meta = await ExportQueryBuilder.fetch_report_data(
            db=db,
            user=user,
            current_employee=current_employee,
            report_type=req.report_type,
            scope_type=req.scope_type,
            department_ids=req.department_ids,
            employee_ids=req.employee_ids,
            start_date=start_d,
            end_date=end_d,
            filters=req.filters
        )

        fmt = req.format.lower().strip()
        if fmt not in ["csv", "xlsx"]:
            raise ValidationException("Unsupported format. Allowed formats: csv, xlsx.")

        # Organization Name
        org_name = "AttendAI Global Technologies"
        org = (await db.execute(select(Organization).where(Organization.id == user.organization_id))).scalars().first()
        if org:
            org_name = org.name

        # Generate File Bytes
        if fmt == "csv":
            file_bytes = generate_csv_bytes(rows, selected_cols)
            ext = "csv"
        else: # xlsx
            split_dept = (req.scope_type in ["organization", "multi_department", "multiple_departments"])
            gen_by = "System Administrator"
            if current_employee and getattr(current_employee, "first_name", None):
                gen_by = f"{current_employee.first_name} {current_employee.last_name}"
            elif getattr(user, "email", None):
                gen_by = user.email.split("@")[0].replace(".", " ").title()
            if getattr(user, "role", None) == "admin":
                gen_by = "System Administrator"

            file_bytes = generate_excel_bytes(
                rows=rows,
                columns=selected_cols,
                report_title=report_title,
                scope_summary=meta["scope_summary"],
                start_date=str(start_d),
                end_date=str(end_d),
                organization_name=org_name,
                split_by_department=split_dept,
                report_type=req.report_type,
                generated_by=gen_by
            )
            ext = "xlsx"

        # Create persistent export record with meaningful filename
        clean_title = "".join(c for c in report_title.replace(" ", "_") if c.isalnum() or c == "_")
        if start_d.month == end_d.month and start_d.year == end_d.year:
            date_part = start_d.strftime("%B_%Y")
        else:
            date_part = f"{start_d.strftime('%Y%m%d')}_{end_d.strftime('%Y%m%d')}"
        filename = f"AttendAI_{clean_title}_{date_part}.{ext}"
        target_path = os.path.join(EXPORT_STORAGE_DIR, filename)

        with open(target_path, "wb") as f:
            f.write(file_bytes)

        file_size = len(file_bytes)

        record = ExportRecord(
            organization_id=user.organization_id,
            user_id=user.id,
            role=user.role,
            report_name=report_title,
            report_type=req.report_type,
            scope_type=req.scope_type,
            scope_summary=meta["scope_summary"],
            date_preset=req.date_preset,
            start_date=start_d,
            end_date=end_d,
            format=fmt,
            columns_selected=[c["id"] for c in selected_cols],
            filters_applied=req.filters,
            record_count=len(rows),
            file_path=target_path,
            file_size_bytes=file_size,
            status="completed"
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)

        return ReportGenerateResponse(
            export_id=record.id,
            report_name=report_title,
            report_type=req.report_type,
            scope_summary=meta["scope_summary"],
            format=fmt,
            record_count=len(rows),
            file_size_bytes=file_size,
            status="completed",
            download_url=f"/api/v1/exports/{record.id}/download",
            created_at=record.created_at
        )

    @staticmethod
    async def list_history(db: AsyncSession, user: User) -> List[ExportHistoryResponse]:
        stmt = select(ExportRecord).where(ExportRecord.organization_id == user.organization_id)
        
        # Role isolation:
        # Employees only see their own exports
        if user.role == "employee":
            stmt = stmt.where(ExportRecord.user_id == user.id)
        elif user.role == "hr_manager":
            # HR can see own exports and HR-scoped exports
            stmt = stmt.where(or_(ExportRecord.user_id == user.id, ExportRecord.role.in_(["hr_manager", "employee"])))

        stmt = stmt.order_by(desc(ExportRecord.created_at)).limit(100)
        results = (await db.execute(stmt)).scalars().all()

        return [
            ExportHistoryResponse(
                id=r.id,
                report_name=r.report_name,
                report_type=r.report_type,
                scope_type=r.scope_type,
                scope_summary=r.scope_summary,
                date_preset=r.date_preset,
                start_date=r.start_date,
                end_date=r.end_date,
                format=r.format,
                record_count=r.record_count,
                file_size_bytes=r.file_size_bytes,
                status=r.status,
                download_url=f"/api/v1/exports/{r.id}/download",
                created_at=r.created_at
            )
            for r in results
        ]

    @staticmethod
    async def get_export_for_download(db: AsyncSession, user: User, export_id: str) -> Tuple[str, str, str]:
        stmt = select(ExportRecord).where(
            and_(
                ExportRecord.id == export_id,
                ExportRecord.organization_id == user.organization_id
            )
        )
        record = (await db.execute(stmt)).scalars().first()
        if not record:
            raise NotFoundException("Export record not found.")

        # Role authorization check:
        # Employee cannot download an export requested by someone else
        if user.role == "employee" and record.user_id != user.id:
            raise ForbiddenException("You are not authorized to download this export.")

        if not record.file_path or not os.path.exists(record.file_path):
            raise NotFoundException("Export file has expired or was removed from storage.")

        filename = os.path.basename(record.file_path)
        media_types = {
            "csv": "text/csv; charset=utf-8",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "pdf": "application/pdf"
        }
        media_type = media_types.get(record.format, "application/octet-stream")
        return record.file_path, filename, media_type
