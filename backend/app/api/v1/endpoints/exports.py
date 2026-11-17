from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.models import User
from app.services.export_service import ExportService
from app.api.deps import get_current_user, get_current_hr_or_admin

router = APIRouter(prefix="/exports", tags=["Exports"])

@router.get("/attendance/csv")
async def export_attendance_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user: User = Depends(get_current_hr_or_admin),
    db: AsyncSession = Depends(get_db)
):
    s_date = start_date or (date.today() - timedelta(days=30))
    e_date = end_date or date.today()

    csv_stream = await ExportService.export_attendance_csv(
        db=db,
        organization_id=user.organization_id,
        start_date=s_date,
        end_date=e_date
    )

    filename = f"attendai_attendance_{s_date}_{e_date}.csv"
    return Response(
        content=csv_stream.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/attendance/xlsx")
async def export_attendance_xlsx(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user: User = Depends(get_current_hr_or_admin),
    db: AsyncSession = Depends(get_db)
):
    s_date = start_date or (date.today() - timedelta(days=30))
    e_date = end_date or date.today()

    xlsx_stream = await ExportService.export_attendance_xlsx(
        db=db,
        organization_id=user.organization_id,
        start_date=s_date,
        end_date=e_date
    )

    filename = f"attendai_attendance_{s_date}_{e_date}.xlsx"
    return Response(
        content=xlsx_stream.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
