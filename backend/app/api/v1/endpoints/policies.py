import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.core.database import get_db
from app.core.config import settings
from app.core.exceptions import NotFoundException, ValidationException
from app.models.models import Policy, PolicyChunk, User
from app.schemas.schemas import PolicyResponse, PolicyChunkResponse
from app.services.policy_service import PolicyService
from app.api.deps import get_current_user, get_current_hr_or_admin

router = APIRouter(prefix="/policies", tags=["Policies & Documents"])

@router.get("", response_model=List[PolicyResponse])
async def list_policies(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Policy, func.count(PolicyChunk.id).label("chunk_count"))
        .outerjoin(PolicyChunk, PolicyChunk.policy_id == Policy.id)
        .where(Policy.organization_id == user.organization_id)
        .group_by(Policy.id)
    )
    res = await db.execute(stmt)
    output = []
    for pol, count in res.all():
        output.append({
            "id": pol.id,
            "organization_id": pol.organization_id,
            "title": pol.title,
            "category": pol.category,
            "file_path": pol.file_path,
            "file_size": pol.file_size,
            "status": pol.status,
            "chunk_count": count or 0,
            "created_at": pol.created_at
        })
    return output

@router.post("/upload", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def upload_policy(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form("Attendance & Leave"),
    user: User = Depends(get_current_hr_or_admin),
    db: AsyncSession = Depends(get_db)
):
    allowed_exts = [".pdf", ".docx", ".doc", ".txt"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise ValidationException(f"Unsupported file type '{ext}'. Allowed: {', '.join(allowed_exts)}")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    saved_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, saved_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)

    policy = await PolicyService.process_document(
        db=db,
        organization_id=user.organization_id,
        title=title,
        category=category,
        file_path=file_path,
        file_size=file_size
    )

    chunk_count = (await db.execute(select(func.count(PolicyChunk.id)).where(PolicyChunk.policy_id == policy.id))).scalar_one()

    return {
        "id": policy.id,
        "organization_id": policy.organization_id,
        "title": policy.title,
        "category": policy.category,
        "file_path": policy.file_path,
        "file_size": policy.file_size,
        "status": policy.status,
        "chunk_count": chunk_count,
        "created_at": policy.created_at
    }

@router.get("/search", response_model=List[PolicyChunkResponse])
async def search_policies(
    query: str = Query(..., min_length=2),
    limit: int = Query(5, ge=1, le=20),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    results = await PolicyService.search_policies(
        db=db,
        organization_id=user.organization_id,
        query=query,
        limit=limit
    )
    return results

@router.delete("/{policy_id}")
async def delete_policy(
    policy_id: str,
    user: User = Depends(get_current_hr_or_admin),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Policy).where(
        and_(
            Policy.id == policy_id,
            Policy.organization_id == user.organization_id
        )
    )
    pol = (await db.execute(stmt)).scalars().first()
    if not pol:
        raise NotFoundException("Policy not found")

    if pol.file_path and os.path.exists(pol.file_path):
        try:
            os.remove(pol.file_path)
        except Exception:
            pass

    await db.delete(pol)
    await db.commit()
    return {"message": "Policy document deleted successfully"}
