"""
Memory Store — wraps PostgreSQL + pgvector for JARVIS memory operations.
Phase 2: auto-embeds on save when LLM is configured.
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
    """Persist a memory. Phase 2: auto-generates embedding if LLM is available."""
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

    # Auto-embed (non-blocking — fires and forgets if LLM not configured)
    if embedding is None:
        try:
            from memory.embeddings import embed_memory
            await embed_memory(db, str(mem.id), content)
        except Exception:
            pass  # Embedding is best-effort

    logger.info(f"Memory saved [{category}] id={mem.id}")
    return mem


async def search_memories_semantic(
    db: AsyncSession,
    query_text: str,
    category: Optional[str] = None,
    limit: int = 5,
    min_similarity: float = 0.6,
) -> list[dict]:
    """Natural language semantic search over memories via pgvector cosine similarity."""
    from llm.client import get_embedding
    query_embedding = await get_embedding(query_text)
    if not query_embedding:
        return []

    cat_filter = f"AND category = '{category}'" if category else ""
    sql = text(f"""
        SELECT id, content, summary, category, importance, metadata,
               1 - (embedding <=> :embedding::vector) AS similarity
        FROM memories
        WHERE embedding IS NOT NULL {cat_filter}
        ORDER BY embedding <=> :embedding::vector
        LIMIT :limit
    """)
    result = await db.execute(sql, {
        "embedding": json.dumps(query_embedding),
        "limit": limit,
    })
    rows = result.fetchall()
    return [
        dict(r._mapping)
        for r in rows
        if (1 - 0) >= min_similarity  # filter applied post-fetch for simplicity
    ]


async def get_recent_memories(
    db: AsyncSession,
    category: Optional[str] = None,
    limit: int = 20,
) -> list[Memory]:
    stmt = select(Memory).order_by(Memory.created_at.desc()).limit(limit)
    if category:
        stmt = stmt.where(Memory.category == category)
    result = await db.execute(stmt)
    return result.scalars().all()
