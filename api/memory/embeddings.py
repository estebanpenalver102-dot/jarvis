"""
Auto-embedding layer — whenever a memory is saved, generate and attach its vector.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from llm.client import get_embedding
from loguru import logger
import json

async def embed_memory(db: AsyncSession, memory_id: str, content: str) -> bool:
    """Generate embedding for a memory and persist it."""
    vector = await get_embedding(content)
    if vector is None:
        logger.debug(f"Skipping embedding for {memory_id} — LLM not configured")
        return False
    await db.execute(
        text("UPDATE memories SET embedding = :vec WHERE id = :id"),
        {"vec": json.dumps(vector), "id": memory_id}
    )
    await db.commit()
    logger.debug(f"Embedded memory {memory_id}")
    return True
