"""
JARVIS LLM Client — unified interface for OpenAI and Gemini.
Falls back gracefully if a provider key is missing.
"""
from openai import AsyncOpenAI
from config import settings
from loguru import logger
from typing import Optional

_openai: Optional[AsyncOpenAI] = None

def get_openai() -> Optional[AsyncOpenAI]:
    global _openai
    if not settings.openai_api_key:
        return None
    if _openai is None:
        _openai = AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai


async def chat_completion(
    messages: list[dict],
    model: str = "gpt-4o-mini",
    max_tokens: int = 1024,
    system_prompt: str = None,
) -> str:
    """Send messages to the LLM and return the response string."""
    client = get_openai()
    if not client:
        return "[LLM not configured — add OPENAI_API_KEY to .env to enable real responses]"

    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=full_messages,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return f"[LLM error: {str(e)[:100]}]"


async def get_embedding(text: str, model: str = "text-embedding-3-small") -> Optional[list[float]]:
    """Generate a 1536-dim embedding for text. Returns None if not configured."""
    client = get_openai()
    if not client:
        return None
    try:
        text = text.replace("\n", " ")[:8000]
        resp = await client.embeddings.create(input=[text], model=model)
        return resp.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        return None
