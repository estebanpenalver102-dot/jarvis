from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from database import get_db
from models.memory import Memory
from memory.store import save_memory, get_recent_memories
from typing import Optional

router = APIRouter(prefix="/memory", tags=["memory"])

class MemoryCreate(BaseModel):
    content: str
    category: str = "episodic"
    importance: float = 0.5
    metadata: dict = {}

class MemoryResponse(BaseModel):
    id: str
    content: str
    summary: Optional[str]
    category: str
    importance: float
    created_at: str

    class Config:
        from_attributes = True

@router.post("", status_code=201)
async def create_memory(body: MemoryCreate, db: AsyncSession = Depends(get_db)):
    """Save a new memory to JARVIS."""
    mem = await save_memory(
        db,
        content=body.content,
        category=body.category,
        importance=body.importance,
        metadata=body.metadata,
    )
    return {"id": str(mem.id), "category": mem.category, "status": "saved"}

@router.get("")
async def list_memories(
    category: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List recent memories, optionally filtered by category."""
    memories = await get_recent_memories(db, category=category, limit=limit)
    return {
        "memories": [
            {
                "id": str(m.id),
                "content": m.content,
                "category": m.category,
                "importance": m.importance,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in memories
        ],
        "count": len(memories),
    }

@router.get("/stats")
async def memory_stats(db: AsyncSession = Depends(get_db)):
    """Memory system statistics by category."""
    result = await db.execute(
        select(Memory.category, func.count(Memory.id).label("count"))
        .group_by(Memory.category)
    )
    rows = result.fetchall()
    return {
        "total": sum(r.count for r in rows),
        "by_category": {r.category: r.count for r in rows},
    }
