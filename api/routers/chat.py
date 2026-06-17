from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from database import get_db
from models.chat import ChatSession, ChatMessage
from memory.store import save_memory
from agents.orchestrator import route_goal
from typing import Optional
import uuid

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    mode: str = "text"  # text | agent

class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    response: str
    agent_used: Optional[str] = None

@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Core JARVIS chat endpoint.
    - Saves user message to episodic memory
    - Routes to appropriate agent if mode=agent
    - Returns response
    """
    # Get or create session
    session_id = body.session_id or str(uuid.uuid4())
    session = await db.get(ChatSession, uuid.UUID(session_id))
    if not session:
        session = ChatSession(id=uuid.UUID(session_id), title=body.message[:50])
        db.add(session)

    # Save user message
    user_msg = ChatMessage(
        session_id=uuid.UUID(session_id),
        role="user",
        content=body.message,
    )
    db.add(user_msg)

    # Save to episodic memory
    await save_memory(db, f"User said: {body.message}", category="episodic",
                      metadata={"session_id": session_id, "role": "user"})

    # Route to agent or echo
    agent_used = None
    if body.mode == "agent":
        result = await route_goal(body.message, db=db)
        response_text = result.get("result", "Agent processed your request.")
        agent_used = result.get("agent")
    else:
        response_text = f"JARVIS received: '{body.message}'. (Connect an LLM provider in Phase 2 for full responses.)"

    # Save assistant message
    assist_msg = ChatMessage(
        session_id=uuid.UUID(session_id),
        role="assistant",
        content=response_text,
        metadata_={"agent": agent_used} if agent_used else {},
    )
    db.add(assist_msg)
    await db.commit()

    return ChatResponse(
        session_id=session_id,
        message_id=str(assist_msg.id),
        response=response_text,
        agent_used=agent_used,
    )

@router.get("/{session_id}/history")
async def get_history(session_id: str, limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Retrieve chat history for a session."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == uuid.UUID(session_id))
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return {
        "session_id": session_id,
        "messages": [
            {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
            for m in messages
        ],
    }
