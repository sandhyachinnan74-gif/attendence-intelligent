from typing import Optional, Tuple
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.models.models import User, Employee

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None)
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException("Missing or invalid Authorization header")

    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token)
    except Exception:
        raise UnauthorizedException("Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Token missing user subject")

    stmt = select(User).where(User.id == user_id)
    user = (await db.execute(stmt)).scalars().first()
    if not user or not user.is_active:
        raise UnauthorizedException("User account is inactive or not found")

    return user

async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != "admin":
        raise ForbiddenException("Requires Administrator privileges")
    return current_user

async def get_current_hr_or_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role not in ["admin", "hr_manager"]:
        raise ForbiddenException("Requires HR Manager or Administrator privileges")
    return current_user

async def get_current_employee_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Optional[Employee]:
    stmt = select(Employee).where(Employee.user_id == current_user.id)
    emp = (await db.execute(stmt)).scalars().first()
    return emp
