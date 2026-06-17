"""
JARVIS LLM Client — multi-provider fallback chain.
Priority: OpenAI → OpenRouter (Kimi K2 / Hermes-3 / Llama-3) → Groq → Ollama → placeholder
"""
from openai import AsyncOpenAI
from config import settings
from loguru import logger
from typing import Optional
import httpx

# ── Provider configs ─────────────────────────────────────────────────────────
FREE_OPENROUTER_MODELS = [
    "moonshotai/kimi-k2:free",           # Kimi K2 — strong reasoning
    "nousresearch/hermes-3-llama-3.1-405b:free",  # Hermes-3
    "meta-llama/llama-3.1-8b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
]
GROQ_MODEL = "llama-3.1-8b-instant"
OLLAMA_MODEL = "llama3.2"

def _make_client(base_url: str = None, api_key: str = None) -> AsyncOpenAI:
    kwargs = {}
    if base_url:
        kwargs["base_url"] = base_url
    kwargs["api_key"] = api_key or "no-key"
    return AsyncOpenAI(**kwargs)


async def _try_completion(client: AsyncOpenAI, model: str, messages: list, max_tokens: int) -> Optional[str]:
    try:
        resp = await client.chat.completions.create(
            model=model, messages=messages, max_tokens=max_tokens
        )
        return resp.choices[0].message.content
    except Exception as e:
        logger.debug(f"Provider {model} failed: {str(e)[:80]}")
        return None


async def chat_completion(
    messages: list[dict],
    model: str = None,
    max_tokens: int = 1024,
    system_prompt: str = None,
) -> str:
    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    # 1️⃣ OpenAI (primary)
    if settings.openai_api_key:
        client = _make_client(api_key=settings.openai_api_key)
        result = await _try_completion(client, model or settings.openai_model, full_messages, max_tokens)
        if result:
            return result
        logger.warning("OpenAI failed — trying fallbacks")

    # 2️⃣ OpenRouter free models (Kimi, Hermes, Llama, Mistral)
    if settings.openrouter_api_key:
        client = _make_client(base_url=settings.openrouter_base_url, api_key=settings.openrouter_api_key)
        for free_model in FREE_OPENROUTER_MODELS:
            result = await _try_completion(client, free_model, full_messages, max_tokens)
            if result:
                logger.info(f"Used OpenRouter fallback: {free_model}")
                return result

    # 3️⃣ Groq (free tier — fast Llama)
    if settings.groq_api_key:
        client = _make_client(base_url=settings.groq_base_url, api_key=settings.groq_api_key)
        result = await _try_completion(client, GROQ_MODEL, full_messages, max_tokens)
        if result:
            logger.info("Used Groq fallback")
            return result

    # 4️⃣ Ollama (local — 100% free, no key)
    try:
        client = _make_client(base_url=f"{settings.ollama_base_url}/v1", api_key="ollama")
        result = await _try_completion(client, OLLAMA_MODEL, full_messages, max_tokens)
        if result:
            logger.info("Used Ollama local fallback")
            return result
    except Exception:
        pass

    return "[No LLM available — add OPENAI_API_KEY, OPENROUTER_API_KEY, or GROQ_API_KEY to .env]"


async def get_embedding(text: str) -> Optional[list[float]]:
    """Generate embedding. Falls back to None (disables vector search) if unavailable."""
    if not settings.openai_api_key:
        return None
    client = _make_client(api_key=settings.openai_api_key)
    try:
        resp = await client.embeddings.create(
            input=[text.replace("\n", " ")[:8000]],
            model=settings.openai_embedding_model
        )
        return resp.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        return None
