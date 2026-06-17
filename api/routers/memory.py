from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from database import get_db
from models.memory import Memory
from memory.store import save_memory, get_recent_memories, search_memories_semantic
from typing import Optional

router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryCreate(BaseModel):
    content: str
    category: str = "episodic"
    importance: float = 0.5
    metadata: dict = {}


@router.post("", status_code=201)
async def create_memory(body: MemoryCreate, db: AsyncSession = Depends(get_db)):
    mem = await save_memory(db, body.content, category=body.category,
                            importance=body.importance, metadata=body.metadata)
    return {"id": str(mem.id), "category": mem.category, "status": "saved"}


@router.get("")
async def list_memories(
    category: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    memories = await get_recent_memories(db, category=category, limit=limit)
    return {
        "memories": [
            {"id": str(m.id), "content": m.content, "category": m.category,
             "importance": m.importance, "has_embedding": m.embedding is not None,
             "created_at": m.created_at.isoformat() if m.created_at else None}
            for m in memories
        ],
        "count": len(memories),
    }


@router.get("/search")
async def semantic_search(
    q: str = Query(..., description="Natural language query"),
    category: Optional[str] = Query(None),
    limit: int = Query(5, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Vector similarity search — requires OPENAI_API_KEY to be set."""
    results = await search_memories_semantic(db, q, category=category, limit=limit)
    return {"query": q, "results": results, "count": len(results)}


@router.get("/stats")
async def memory_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Memory.category, func.count(Memory.id).label("count"),
               func.sum(func.case((Memory.embedding.isnot(None), 1), else_=0)).label("embedded"))
        .group_by(Memory.category)
    )
    rows = result.fetchall()
    return {
        "total": sum(r.count for r in rows),
        "by_category": {r.category: {"count": r.count, "embedded": r.embedded} for r in rows},
    }
