"""
Memory Store — wraps PostgreSQL + pgvector for JARVIS memory operations.
Supports all 5 memory tiers: episodic, semantic, project, business, preference.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from models.memory import Memory
from loguru import logger
from typing import Optional
import json

MEMORY_CATEGORIES = {"episodic", "semantic", "project", "business", "preference"}

async def save_memory(
    db: AsyncSession,
    content: str,
    category: str = "episodic",
    embedding: Optional[list] = None,
    summary: Optional[str] = None,
    importance: float = 0.5,
    metadata: dict = None,
) -> Memory:
    """Persist a memory to PostgreSQL."""
    if category not in MEMORY_CATEGORIES:
        category = "episodic"

    mem = Memory(
        content=content,
        category=category,
        embedding=embedding,
        summary=summary or content[:200],
        importance=importance,
        metadata_=metadata or {},
    )
    db.add(mem)
    await db.commit()
    await db.refresh(mem)
    logger.info(f"Memory saved [{category}] id={mem.id}")
    return mem


async def search_memories_semantic(
    db: AsyncSession,
    query_embedding: list,
    category: Optional[str] = None,
    limit: int = 5,
    min_similarity: float = 0.7,
) -> list[dict]:
    """Vector similarity search over memories."""
    cat_filter = f"AND category = '{category}'" if category else ""
    sql = text(f"""
        SELECT id, content, summary, category, importance, metadata,
               1 - (embedding <=> :embedding) AS similarity
        FROM memories
        WHERE embedding IS NOT NULL {cat_filter}
        HAVING 1 - (embedding <=> :embedding) >= :min_sim
        ORDER BY embedding <=> :embedding
        LIMIT :limit
    """)
    result = await db.execute(sql, {
        "embedding": json.dumps(query_embedding),
        "min_sim": min_similarity,
        "limit": limit,
    })
    rows = result.fetchall()
    return [dict(r._mapping) for r in rows]


async def get_recent_memories(
    db: AsyncSession,
    category: Optional[str] = None,
    limit: int = 20,
) -> list[Memory]:
    """Fetch most recent memories, optionally filtered by category."""
    stmt = select(Memory).order_by(Memory.created_at.desc()).limit(limit)
    if category:
        stmt = stmt.where(Memory.category == category)
    result = await db.execute(stmt)
    return result.scalars().all()
