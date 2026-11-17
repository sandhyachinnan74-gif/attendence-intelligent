import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.core.security import (
    verify_password, hash_password, create_access_token, create_refresh_token, decode_token
)
from app.core.exceptions import UnauthorizedException, ValidationException
from app.models.models import User, Employee, RefreshToken, Organization
from app.schemas.schemas import (
    LoginRequest, TokenResponse, RefreshTokenRequest, PasswordChangeRequest, UserResponse
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

def hash_rt(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == req.email.lower().strip())
    user = (await db.execute(stmt)).scalars().first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise UnauthorizedException("Invalid email or password")
    if not user.is_active:
        raise UnauthorizedException("Account is disabled")

    # Fetch associated employee profile if any
    emp_stmt = select(Employee).where(Employee.user_id == user.id)
    emp = (await db.execute(emp_stmt)).scalars().first()

    org_stmt = select(Organization).where(Organization.id == user.organization_id)
    org = (await db.execute(org_stmt)).scalars().first()

    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "org_id": user.organization_id
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Save refresh token
    rt_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_rt(refresh_token),
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db.add(rt_record)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "organization_id": user.organization_id,
            "organization_name": org.name if org else "AttendAI Org",
            "employee_id": emp.id if emp else None,
            "first_name": emp.first_name if emp else user.email.split("@")[0].capitalize(),
            "last_name": emp.last_name if emp else "",
            "employee_code": emp.employee_code if emp else None,
            "designation": emp.designation if emp else "Staff"
        }
    }

@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid token type")
    except Exception:
        raise UnauthorizedException("Invalid or expired refresh token")

    rt_hash = hash_rt(req.refresh_token)
    stmt = select(RefreshToken).where(
        and_(
            RefreshToken.token_hash == rt_hash,
            RefreshToken.is_revoked == False
        )
    )
    saved_rt = (await db.execute(stmt)).scalars().first()
    if not saved_rt:
        raise UnauthorizedException("Refresh token has been revoked or is invalid")

    # Rotate refresh token
    saved_rt.is_revoked = True

    user_id = payload.get("sub")
    user = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if not user or not user.is_active:
        raise UnauthorizedException("User not found or inactive")

    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "org_id": user.organization_id
    }
    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)

    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_rt(new_refresh),
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None)
    ))
    await db.commit()

    emp = (await db.execute(select(Employee).where(Employee.user_id == user.id))).scalars().first()

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "organization_id": user.organization_id,
            "employee_id": emp.id if emp else None,
            "first_name": emp.first_name if emp else user.email.split("@")[0].capitalize(),
            "last_name": emp.last_name if emp else "",
            "employee_code": emp.employee_code if emp else None
        }
    }

@router.post("/logout")
async def logout(req: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    rt_hash = hash_rt(req.refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == rt_hash)
    saved_rt = (await db.execute(stmt)).scalars().first()
    if saved_rt:
        saved_rt.is_revoked = True
        await db.commit()
    return {"message": "Successfully logged out"}

@router.get("/me")
async def get_me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    emp = (await db.execute(select(Employee).where(Employee.user_id == user.id))).scalars().first()
    org = (await db.execute(select(Organization).where(Organization.id == user.organization_id))).scalars().first()
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "organization_id": user.organization_id,
        "organization_name": org.name if org else "AttendAI Org",
        "employee_id": emp.id if emp else None,
        "first_name": emp.first_name if emp else user.email.split("@")[0].capitalize(),
        "last_name": emp.last_name if emp else "",
        "employee_code": emp.employee_code if emp else None,
        "designation": emp.designation if emp else "Staff"
    }

@router.post("/change-password")
async def change_password(
    req: PasswordChangeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not verify_password(req.current_password, user.hashed_password):
        raise ValidationException("Current password is incorrect")
    if len(req.new_password) < 8:
        raise ValidationException("New password must be at least 8 characters long")
    user.hashed_password = hash_password(req.new_password)
    await db.commit()
    return {"message": "Password changed successfully"}
