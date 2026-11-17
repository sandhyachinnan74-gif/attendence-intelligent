from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update, desc
from app.models.models import Notification, NotificationPreference, User

class NotificationService:
    @staticmethod
    def _format_time_ago(dt: datetime) -> str:
        if not dt:
            return ""
        now = datetime.utcnow()
        diff = now - dt
        seconds = diff.total_seconds()
        if seconds < 60:
            return "Just now"
        minutes = int(seconds // 60)
        if minutes < 60:
            return f"{minutes} min{'s' if minutes > 1 else ''} ago"
        hours = int(minutes // 60)
        if hours < 24:
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        days = int(hours // 24)
        if days == 1:
            return "Yesterday"
        return f"{days} days ago"

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        organization_id: str,
        user_id: str,
        title: str,
        message: str,
        category: str,
        priority: str = "information",
        link: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None
    ) -> Optional[Notification]:
        """
        Creates a notification with strict deduplication: avoids duplicate
        unread notifications for the same user within 15 minutes.
        """
        fifteen_mins_ago = datetime.utcnow() - timedelta(minutes=15)
        dup_check = await db.execute(
            select(Notification).where(
                and_(
                    Notification.user_id == user_id,
                    Notification.category == category,
                    Notification.title == title,
                    Notification.is_read == False,
                    Notification.created_at >= fifteen_mins_ago
                )
            )
        )
        if dup_check.scalars().first():
            return None  # Duplicate suppressed

        notif = Notification(
            organization_id=organization_id,
            user_id=user_id,
            title=title,
            message=message,
            category=category,
            priority=priority,
            link=link,
            metadata_json=metadata_json,
            is_read=False,
            is_archived=False,
            created_at=datetime.utcnow()
        )
        db.add(notif)
        await db.commit()
        await db.refresh(notif)
        return notif

    @staticmethod
    async def get_unread_count(db: AsyncSession, user_id: str) -> int:
        stmt = select(func.count(Notification.id)).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False,
                Notification.is_archived == False
            )
        )
        res = await db.execute(stmt)
        return res.scalar() or 0

    @classmethod
    async def get_notifications(
        cls,
        db: AsyncSession,
        user: User,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        unread_only: bool = False,
        search: Optional[str] = None,
        include_archived: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        # Seed defaults if user has none
        await cls.seed_default_notifications_if_needed(db, user)

        conditions = [Notification.user_id == user.id]
        if not include_archived:
            conditions.append(Notification.is_archived == False)
        if unread_only:
            conditions.append(Notification.is_read == False)
        if category and category != "all":
            conditions.append(Notification.category == category)
        if priority and priority != "all":
            conditions.append(Notification.priority == priority)
        if search:
            search_term = f"%{search}%"
            conditions.append(
                (Notification.title.ilike(search_term)) | (Notification.message.ilike(search_term))
            )

        # Count total
        count_stmt = select(func.count(Notification.id)).where(and_(*conditions))
        total = (await db.execute(count_stmt)).scalar() or 0

        # Query paginated
        skip = (page - 1) * page_size
        stmt = (
            select(Notification)
            .where(and_(*conditions))
            .order_by(desc(Notification.created_at))
            .offset(skip)
            .limit(page_size)
        )
        items = (await db.execute(stmt)).scalars().all()

        unread_count = await cls.get_unread_count(db, user.id)

        output_items = []
        for n in items:
            output_items.append({
                "id": n.id,
                "organization_id": n.organization_id,
                "user_id": n.user_id,
                "title": n.title,
                "message": n.message,
                "category": n.category,
                "priority": n.priority,
                "link": n.link,
                "is_read": n.is_read,
                "is_archived": n.is_archived,
                "created_at": n.created_at,
                "time_ago": cls._format_time_ago(n.created_at)
            })

        return {
            "items": output_items,
            "total": total,
            "unread_count": unread_count,
            "page": page,
            "page_size": page_size
        }

    @staticmethod
    async def mark_as_read(db: AsyncSession, notification_id: str, user_id: str) -> bool:
        stmt = (
            update(Notification)
            .where(and_(Notification.id == notification_id, Notification.user_id == user_id))
            .values(is_read=True)
        )
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount > 0

    @staticmethod
    async def mark_all_as_read(db: AsyncSession, user_id: str) -> int:
        stmt = (
            update(Notification)
            .where(and_(Notification.user_id == user_id, Notification.is_read == False))
            .values(is_read=True)
        )
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount

    @staticmethod
    async def archive_notification(db: AsyncSession, notification_id: str, user_id: str) -> bool:
        stmt = (
            update(Notification)
            .where(and_(Notification.id == notification_id, Notification.user_id == user_id))
            .values(is_archived=True)
        )
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount > 0

    @staticmethod
    async def get_preferences(db: AsyncSession, user_id: str) -> Dict[str, Any]:
        stmt = select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        pref = (await db.execute(stmt)).scalars().first()
        default_categories = {
            "attendance": True,
            "leave": True,
            "shifts": True,
            "anomalies": True,
            "approvals": True,
            "employee_management": True,
            "policies": True,
            "system": True,
            "ai": True
        }
        if not pref:
            return {
                "email_enabled": True,
                "in_app_enabled": True,
                "categories": default_categories
            }
        cats = default_categories.copy()
        if pref.categories and isinstance(pref.categories, dict):
            cats.update(pref.categories)
        return {
            "email_enabled": pref.email_enabled,
            "in_app_enabled": pref.in_app_enabled,
            "categories": cats
        }

    @staticmethod
    async def update_preferences(db: AsyncSession, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        stmt = select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        pref = (await db.execute(stmt)).scalars().first()
        if not pref:
            pref = NotificationPreference(
                user_id=user_id,
                email_enabled=data.get("email_enabled", True),
                in_app_enabled=data.get("in_app_enabled", True),
                categories=data.get("categories", {}),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(pref)
        else:
            if "email_enabled" in data and data["email_enabled"] is not None:
                pref.email_enabled = data["email_enabled"]
            if "in_app_enabled" in data and data["in_app_enabled"] is not None:
                pref.in_app_enabled = data["in_app_enabled"]
            if "categories" in data and data["categories"] is not None:
                current_cats = pref.categories or {}
                current_cats.update(data["categories"])
                pref.categories = current_cats
            pref.updated_at = datetime.utcnow()
        await db.commit()
        return await NotificationService.get_preferences(db, user_id)

    @staticmethod
    async def seed_default_notifications_if_needed(db: AsyncSession, user: User):
        """Seeds realistic initial notifications tailored to each role."""
        count_stmt = select(func.count(Notification.id)).where(Notification.user_id == user.id)
        count = (await db.execute(count_stmt)).scalar() or 0
        if count > 0:
            return

        now = datetime.utcnow()
        role = user.role
        seeds = []

        if role == "admin":
            seeds = [
                {
                    "title": "Unusual Overtime Detected",
                    "message": "3 employees in Customer Success exceeded 3.5 hours of overtime today.",
                    "category": "attendance",
                    "priority": "critical",
                    "link": "/analytics",
                    "created_at": now - timedelta(minutes=14)
                },
                {
                    "title": "Repeated Tardiness Pattern",
                    "message": "Marcus Vance flagged for 3rd late arrival this week.",
                    "category": "anomalies",
                    "priority": "warning",
                    "link": "/anomalies",
                    "created_at": now - timedelta(hours=1, minutes=20)
                },
                {
                    "title": "Policy Document Processed",
                    "message": "Employee Remote Work Guidelines PDF successfully extracted and indexed.",
                    "category": "policies",
                    "priority": "success",
                    "link": "/policies",
                    "created_at": now - timedelta(hours=3)
                },
                {
                    "title": "Monthly Workforce Summary Available",
                    "message": "Organization-wide punctuality rate reached 92.4% for the active period.",
                    "category": "attendance",
                    "priority": "information",
                    "link": "/",
                    "created_at": now - timedelta(days=1)
                }
            ]
        elif role == "hr_manager":
            seeds = [
                {
                    "title": "Pending Leave Application",
                    "message": "Sarah Jenkins submitted an Annual Leave request for Dec 1 - Dec 3.",
                    "category": "leave",
                    "priority": "warning",
                    "link": "/leave",
                    "created_at": now - timedelta(minutes=25)
                },
                {
                    "title": "Shift Schedule Published",
                    "message": "General (09:00 - 17:00) roster published for Engineering department.",
                    "category": "shifts",
                    "priority": "information",
                    "link": "/shifts",
                    "created_at": now - timedelta(hours=2)
                },
                {
                    "title": "Unverified Punch Flag",
                    "message": "1 employee has an open, unclocked shift requiring attendance review.",
                    "category": "attendance",
                    "priority": "warning",
                    "link": "/attendance",
                    "created_at": now - timedelta(hours=5)
                },
                {
                    "title": "Attendance Correction Approved",
                    "message": "David Chen's punch record adjustment has been recorded in the audit log.",
                    "category": "attendance",
                    "priority": "success",
                    "link": "/attendance",
                    "created_at": now - timedelta(days=1)
                }
            ]
        else:  # employee
            seeds = [
                {
                    "title": "Clock-In Confirmed",
                    "message": "Successfully recorded morning clock-in. Have a productive shift!",
                    "category": "attendance",
                    "priority": "success",
                    "link": "/attendance",
                    "created_at": now - timedelta(minutes=45)
                },
                {
                    "title": "Available Leave Balance",
                    "message": "You currently have 18 days of paid time off available for this year.",
                    "category": "leave",
                    "priority": "information",
                    "link": "/leave",
                    "created_at": now - timedelta(hours=4)
                },
                {
                    "title": "Upcoming Shift Reminder",
                    "message": "Assigned to General Shift (09:00 - 17:00) with 15-minute grace period.",
                    "category": "shifts",
                    "priority": "information",
                    "link": "/shifts",
                    "created_at": now - timedelta(days=1)
                },
                {
                    "title": "Policy Update Notice",
                    "message": "Please review the updated Attendance & Grace Period Guidelines in Policies.",
                    "category": "policies",
                    "priority": "warning",
                    "link": "/policies",
                    "created_at": now - timedelta(days=2)
                }
            ]

        for s in seeds:
            notif = Notification(
                organization_id=user.organization_id,
                user_id=user.id,
                title=s["title"],
                message=s["message"],
                category=s["category"],
                priority=s["priority"],
                link=s["link"],
                is_read=False,
                is_archived=False,
                created_at=s["created_at"]
            )
            db.add(notif)
        await db.commit()
