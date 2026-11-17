from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import (
    NotificationListResponse, NotificationResponse,
    NotificationPreferenceResponse, NotificationPreferenceUpdate
)
from app.services.notification_service import NotificationService
from app.api.deps import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    category: Optional[str] = Query(None, description="Category filter (attendance, leave, shifts, etc.)"),
    priority: Optional[str] = Query(None, description="Priority filter (critical, warning, success, information)"),
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    search: Optional[str] = Query(None, description="Search keyword in title or message"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await NotificationService.get_notifications(
        db=db,
        user=user,
        category=category,
        priority=priority,
        unread_only=unread_only,
        search=search,
        page=page,
        page_size=page_size
    )

@router.get("/unread-count")
async def get_unread_count(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Ensure initial seed if needed
    await NotificationService.seed_default_notifications_if_needed(db, user)
    count = await NotificationService.get_unread_count(db, user.id)
    return {"unread_count": count}

@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    success = await NotificationService.mark_as_read(db, notification_id, user.id)
    return {"success": success}

@router.post("/read-all")
async def mark_all_as_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    updated = await NotificationService.mark_all_as_read(db, user.id)
    return {"success": True, "updated_count": updated}

@router.patch("/{notification_id}/archive")
async def archive_notification(
    notification_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    success = await NotificationService.archive_notification(db, notification_id, user.id)
    return {"success": success}

@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_preferences(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await NotificationService.get_preferences(db, user.id)

@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_preferences(
    req: NotificationPreferenceUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    data = req.model_dump(exclude_unset=True)
    return await NotificationService.update_preferences(db, user.id, data)
