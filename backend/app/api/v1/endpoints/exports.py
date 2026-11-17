from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.models.models import User
from app.services.export_service import ExportService

router = APIRouter(prefix="/exports", tags=["Exports"])

async def get_export_user(
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
        raise UnauthorizedException("Missing Authorization header or token parameter")

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

    if user.role not in ["admin", "hr_manager"]:
        raise ForbiddenException("Requires HR Manager or Administrator privileges")

    return user

@router.get("/attendance/csv")
async def export_attendance_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user: User = Depends(get_export_user),
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
async def export_attendance_xlsx(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user: User = Depends(get_export_user),
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
