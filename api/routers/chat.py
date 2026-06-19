"""
JARVIS Chat Router — Phase 2: real LLM responses + ETS pipeline.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from database import get_db
from models.chat import ChatSession, ChatMessage
from memory.store import save_memory, search_memories_semantic
from memory.extractor import extract_and_store
from llm.client import chat_completion
from agents.orchestrator import route_goal
from security import SECURITY_SYSTEM_PROMPT, contains_secret_request
from typing import Optional
import uuid

router = APIRouter(prefix="/chat", tags=["chat"])

JARVIS_SYSTEM_PROMPT = """You are JARVIS, a personal AI Operating System. You are stateful,
multimodal, and proactive. You help manage businesses, websites, communications, research,
automations, and personal workflows. Be concise, direct, and actionable.
You have memory of past conversations — use it to personalize responses.""" + SECURITY_SYSTEM_PROMPT


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    mode: str = "text"  # text | agent


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    response: str
    agent_used: Optional[str] = None
    memories_used: int = 0


@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest, db: AsyncSession = Depends(get_db)):
    session_id = body.session_id or str(uuid.uuid4())

    # ── Security gate: refuse requests that ask for secrets ───────────────────
    if contains_secret_request(body.message):
        return ChatResponse(
            session_id=session_id,
            message_id=str(uuid.uuid4()),
            response=(
                "I'm not able to share API keys, credentials, or environment "
                "variables — that information is protected for your security. "
                "If you need to rotate a key, please visit your provider's "
                "dashboard directly."
            ),
            memories_used=0,
        )

    session = await db.get(ChatSession, uuid.UUID(session_id))
    if not session:
        session = ChatSession(id=uuid.UUID(session_id), title=body.message[:50])
        db.add(session)

    # Save user message
    user_msg = ChatMessage(session_id=uuid.UUID(session_id), role="user", content=body.message)
    db.add(user_msg)
    await save_memory(db, f"User: {body.message}", category="episodic",
                      metadata={"session_id": session_id})

    # Retrieve relevant memories for context
    relevant = await search_memories_semantic(db, body.message, limit=3)
    memory_context = ""
    if relevant:
        facts = [r["content"] for r in relevant]
        memory_context = "\n\nRelevant memories:\n" + "\n".join(f"- {f}" for f in facts)

    agent_used = None
    if body.mode == "agent":
        result = await route_goal(body.message, db=db)
        response_text = result.get("result", "Agent processed your request.")
        agent_used = result.get("agent")
    else:
        # Build conversation history (last 10 messages)
        history_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == uuid.UUID(session_id))
            .order_by(ChatMessage.created_at.desc())
            .limit(10)
        )
        history = list(reversed(history_result.scalars().all()))
        messages = [{"role": m.role, "content": m.content} for m in history
                    if m.role in ("user", "assistant")]

        system = JARVIS_SYSTEM_PROMPT + memory_context
        response_text = await chat_completion(messages, system_prompt=system)

    # Save assistant response + run ETS pipeline
    assist_msg = ChatMessage(
        session_id=uuid.UUID(session_id),
        role="assistant",
        content=response_text,
        metadata_={"agent": agent_used} if agent_used else {},
    )
    db.add(assist_msg)
    await db.commit()

    # ETS: extract semantic facts from user message (async, best-effort)
    try:
        await extract_and_store(db, body.message)
    except Exception:
        pass

    return ChatResponse(
        session_id=session_id,
        message_id=str(assist_msg.id),
        response=response_text,
        agent_used=agent_used,
        memories_used=len(relevant),
    )


@router.get("/{session_id}/history")
async def get_history(session_id: str, limit: int = 50, db: AsyncSession = Depends(get_db)):
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
