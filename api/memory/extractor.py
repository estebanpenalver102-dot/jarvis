"""
ETS Pipeline (Extract-Transform-Store) — Mem0-inspired semantic fact extraction.
Monitors episodic memory and asynchronously extracts semantic facts.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from memory.store import save_memory
from memory.embeddings import embed_memory
from llm.client import chat_completion
from loguru import logger
import json

EXTRACT_PROMPT = """You are a memory extraction system. Given a conversation message, extract any
durable facts worth remembering long-term (preferences, personal details, commitments, goals, key info).

Return a JSON array of fact strings. Return [] if nothing durable is present.
Be concise. Examples:
- "User prefers Python over JavaScript"
- "User owns a car dealership named OpenRoad Auto Group"
- "User wants automated YouTube videos for children ages 2-12"

Message: {message}

Return ONLY valid JSON array, no extra text."""


async def extract_and_store(db: AsyncSession, user_message: str, user_id: str = None) -> list[str]:
    """Run the ETS pipeline on a user message. Returns list of extracted fact strings."""
    try:
        resp = await chat_completion(
            messages=[{"role": "user", "content": EXTRACT_PROMPT.format(message=user_message[:500])}],
            max_tokens=256,
        )
        # Parse JSON response
        resp = resp.strip()
        if resp.startswith("["):
            facts = json.loads(resp)
        else:
            return []

        saved = []
        for fact in facts[:5]:  # cap at 5 facts per message
            if isinstance(fact, str) and len(fact) > 5:
                mem = await save_memory(
                    db,
                    content=fact,
                    category="semantic",
                    importance=0.7,
                    metadata={"source": "ets_pipeline", "original_message": user_message[:100]},
                )
                await embed_memory(db, str(mem.id), fact)
                saved.append(fact)

        if saved:
            logger.info(f"ETS extracted {len(saved)} semantic facts")
        return saved

    except Exception as e:
        logger.error(f"ETS pipeline error: {e}")
        return []
