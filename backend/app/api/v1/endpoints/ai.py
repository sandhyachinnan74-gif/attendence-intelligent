from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.models import Conversation, ConversationMessage, User, Employee
from app.schemas.schemas import MessageCreate, MessageResponse, ConversationResponse
from app.harness.orchestrator import ai_orchestrator
from app.api.deps import get_current_user, get_current_employee_profile

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Conversation)
        .where(
            and_(
                Conversation.user_id == user.id,
                Conversation.organization_id == user.organization_id
            )
        )
        .order_by(desc(Conversation.updated_at))
    )
    convs = (await db.execute(stmt)).scalars().all()
    output = []
    for c in convs:
        output.append({
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at,
            "messages": []
        })
    return output

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Conversation).where(
        and_(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id
        )
    )
    conv = (await db.execute(stmt)).scalars().first()
    if not conv:
        raise NotFoundException("Conversation not found")

    msg_stmt = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conv.id)
        .order_by(ConversationMessage.created_at)
    )
    messages = (await db.execute(msg_stmt)).scalars().all()

    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "tool_calls": m.tool_calls,
                "tool_results": m.tool_results,
                "citations": m.citations,
                "created_at": m.created_at
            }
            for m in messages
        ]
    }

@router.post("/chat")
async def chat(
    req: MessageCreate,
    conversation_id: Optional[str] = None,
    user: User = Depends(get_current_user),
    employee: Optional[Employee] = Depends(get_current_employee_profile),
    db: AsyncSession = Depends(get_db)
):
    # Resolve or create conversation
    conv = None
    if conversation_id:
        conv = (await db.execute(
            select(Conversation).where(
                and_(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user.id
                )
            )
        )).scalars().first()

    if not conv:
        # Title summary from first prompt
        title = req.content[:35] + "..." if len(req.content) > 35 else req.content
        conv = Conversation(
            organization_id=user.organization_id,
            user_id=user.id,
            title=title
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)

    # Fetch previous messages
    hist_stmt = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conv.id)
        .order_by(ConversationMessage.created_at)
    )
    history_records = (await db.execute(hist_stmt)).scalars().all()
    history = [{"role": m.role, "content": m.content} for m in history_records]

    # Save user message
    user_msg = ConversationMessage(
        conversation_id=conv.id,
        role="user",
        content=req.content
    )
    db.add(user_msg)
    await db.commit()

    # Execute AI turn with harness
    result = await ai_orchestrator.execute_turn(
        db=db,
        user=user,
        employee=employee,
        user_message=req.content,
        conversation_history=history
    )

    # Save assistant message
    asst_msg = ConversationMessage(
        conversation_id=conv.id,
        role="assistant",
        content=result["content"],
        tool_calls=result.get("tool_calls"),
        tool_results=result.get("tool_results"),
        citations=result.get("citations")
    )
    db.add(asst_msg)
    await db.commit()
    await db.refresh(asst_msg)

    return {
        "conversation_id": conv.id,
        "message": {
            "id": asst_msg.id,
            "role": asst_msg.role,
            "content": asst_msg.content,
            "tool_calls": asst_msg.tool_calls,
            "tool_results": asst_msg.tool_results,
            "citations": asst_msg.citations,
            "follow_ups": result.get("follow_ups", []),
            "created_at": asst_msg.created_at
        },
        "model": result.get("model"),
        "provider": result.get("provider"),
        "fallback_used": result.get("fallback_used", False)
    }

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Conversation).where(
        and_(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id
        )
    )
    conv = (await db.execute(stmt)).scalars().first()
    if not conv:
        raise NotFoundException("Conversation not found")

    await db.delete(conv)
    await db.commit()
    return {"message": "Conversation deleted"}
