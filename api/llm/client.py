"""
JARVIS LLM Client — smart routing: free models for easy tasks, premium for complex.
Priority for COMPLEX: OpenAI GPT-4o-mini → OpenRouter Kimi K2 → Groq → Ollama
Priority for SIMPLE:  OpenRouter free (Gemini Flash → Llama-3) → Groq → OpenAI → Ollama
"""
from openai import AsyncOpenAI
from config import settings
from loguru import logger
from typing import Optional

# ── Model tiers ───────────────────────────────────────────────────────────────
PREMIUM_OPENAI_MODEL    = "gpt-4o-mini"          # Best balance: smart + cheap
PREMIUM_OPENAI_COMPLEX  = "gpt-4o"               # Full power for heavy reasoning

FREE_OPENROUTER_MODELS = [
    "google/gemini-2.0-flash-exp:free",          # Fast + capable free tier
    "moonshotai/kimi-k2:free",                    # Strong reasoning, free
    "nousresearch/hermes-3-llama-3.1-405b:free",  # Hermes-3
    "meta-llama/llama-3.1-8b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
]
GROQ_MODELS = [
    "llama-3.1-70b-versatile",   # Best Groq free model
    "llama-3.1-8b-instant",      # Fallback
]
OLLAMA_MODEL = "llama3.2"

# ── Keywords that indicate a complex task ─────────────────────────────────────
_COMPLEX_KEYWORDS = {
    "code", "debug", "analyze", "compare", "explain", "implement",
    "optimize", "review", "architecture", "design", "write", "generate",
    "research", "plan", "strategy", "report", "summarize", "financial",
}


def estimate_complexity(message: str) -> str:
    """Returns 'complex' or 'simple' based on message heuristics."""
    msg_lower = message.lower()
    word_count = len(message.split())
    if word_count > 60 or any(kw in msg_lower for kw in _COMPLEX_KEYWORDS):
        return "complex"
    return "simple"


def _make_client(base_url: str = None, api_key: str = None) -> AsyncOpenAI:
    kwargs = {"api_key": api_key or "no-key"}
    if base_url:
        kwargs["base_url"] = base_url
    return AsyncOpenAI(**kwargs)


async def _try_completion(
    client: AsyncOpenAI, model: str, messages: list, max_tokens: int
) -> Optional[str]:
    try:
        resp = await client.chat.completions.create(
            model=model, messages=messages, max_tokens=max_tokens
        )
        content = resp.choices[0].message.content
        logger.info(f"[JARVIS LLM] ✅ {model} responded ({len(content or '')} chars)")
        return content
    except Exception as e:
        logger.debug(f"[JARVIS LLM] ❌ {model} failed: {str(e)[:80]}")
        return None


async def chat_completion(
    messages: list[dict],
    model: str = None,
    max_tokens: int = 1024,
    system_prompt: str = None,
    complexity: str = None,     # 'simple' | 'complex' | None (auto-detect)
) -> str:
    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    # Auto-detect complexity from last user message if not specified
    if complexity is None:
        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"), ""
        )
        complexity = estimate_complexity(last_user)

    logger.info(f"[JARVIS LLM] Task complexity: {complexity}")

    if complexity == "complex":
        # ── COMPLEX path: premium first ───────────────────────────────────────
        # 1. OpenAI GPT-4o-mini (or explicit model)
        if settings.openai_api_key:
            chosen = model or PREMIUM_OPENAI_MODEL
            result = await _try_completion(
                _make_client(api_key=settings.openai_api_key),
                chosen, full_messages, max_tokens
            )
            if result:
                return result
            logger.warning("[JARVIS LLM] OpenAI failed — trying free fallbacks")

        # 2. OpenRouter Kimi K2 (best free reasoning)
        if settings.openrouter_api_key:
            client = _make_client(
                base_url=settings.openrouter_base_url,
                api_key=settings.openrouter_api_key
            )
            for m in FREE_OPENROUTER_MODELS[:2]:  # Kimi + Gemini for complex
                result = await _try_completion(client, m, full_messages, max_tokens)
                if result:
                    return result

        # 3. Groq
        if settings.groq_api_key:
            client = _make_client(base_url=settings.groq_base_url, api_key=settings.groq_api_key)
            result = await _try_completion(client, GROQ_MODELS[0], full_messages, max_tokens)
            if result:
                return result

    else:
        # ── SIMPLE path: free models first ────────────────────────────────────
        # 1. OpenRouter free tier (Gemini Flash → Kimi → Llama)
        if settings.openrouter_api_key:
            client = _make_client(
                base_url=settings.openrouter_base_url,
                api_key=settings.openrouter_api_key
            )
            for free_model in FREE_OPENROUTER_MODELS:
                result = await _try_completion(client, free_model, full_messages, max_tokens)
                if result:
                    return result
            logger.warning("[JARVIS LLM] All OpenRouter free models failed")

        # 2. Groq (free + fast)
        if settings.groq_api_key:
            client = _make_client(base_url=settings.groq_base_url, api_key=settings.groq_api_key)
            for groq_model in GROQ_MODELS:
                result = await _try_completion(client, groq_model, full_messages, max_tokens)
                if result:
                    return result

        # 3. OpenAI fallback even for simple tasks
        if settings.openai_api_key:
            result = await _try_completion(
                _make_client(api_key=settings.openai_api_key),
                PREMIUM_OPENAI_MODEL, full_messages, max_tokens
            )
            if result:
                return result

    # ── Final fallback: Ollama (local, no key needed) ─────────────────────────
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30) as http:
            r = await http.post(
                "http://localhost:11434/api/chat",
                json={"model": OLLAMA_MODEL, "messages": full_messages, "stream": False},
            )
            data = r.json()
            return data.get("message", {}).get("content", "")
    except Exception:
        pass

    return (
        "I'm having trouble connecting to my AI providers right now. "
        "All models in the chain are unavailable. Please try again in a moment."
    )
