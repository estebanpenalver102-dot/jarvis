"""
JARVIS — NVIDIA provider integration.

NVIDIA's build.nvidia.com endpoint is OpenAI-compatible, so we reuse AsyncOpenAI
pointed at the NVIDIA base URL. This module:
  1. Discovers which models the account is authorized for (GET /models)
  2. Benchmarks latency for each with a tiny probe prompt
  3. Persists results to the `provider_models` table (source of truth for routing)
  4. Exposes get_ranked_nvidia_models() for the router

Key is read ONLY from settings.nvidia_api_key (env: NVIDIA_API_KEY). Never hardcoded.
"""
from __future__ import annotations

import time
import asyncio
from typing import Optional

from openai import AsyncOpenAI
from sqlalchemy import text
from loguru import logger

from config import settings
from database import engine

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
_PROBE_MESSAGES = [{"role": "user", "content": "Reply with the single word: ok"}]


def _client() -> Optional[AsyncOpenAI]:
    if not settings.nvidia_api_key:
        return None
    return AsyncOpenAI(api_key=settings.nvidia_api_key, base_url=NVIDIA_BASE_URL)


async def _ensure_table() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS provider_models (
                provider     TEXT NOT NULL,
                model        TEXT NOT NULL,
                authorized   BOOLEAN DEFAULT TRUE,
                latency_ms   INTEGER,
                last_checked TIMESTAMPTZ DEFAULT now(),
                PRIMARY KEY (provider, model)
            )
        """))


async def discover_models() -> list[str]:
    """Return model ids the NVIDIA account is authorized for. Empty if no key / auth fails."""
    client = _client()
    if client is None:
        logger.info("[NVIDIA] No NVIDIA_API_KEY set — skipping discovery.")
        return []
    try:
        resp = await client.models.list()
        ids = [m.id for m in resp.data]
        logger.info(f"[NVIDIA] Discovered {len(ids)} authorized models.")
        return ids
    except Exception as e:
        logger.warning(f"[NVIDIA] Model discovery failed (auth/quota?): {str(e)[:120]}")
        return []


async def _benchmark(client: AsyncOpenAI, model: str) -> Optional[int]:
    start = time.perf_counter()
    try:
        await client.chat.completions.create(model=model, messages=_PROBE_MESSAGES, max_tokens=4)
        return int((time.perf_counter() - start) * 1000)
    except Exception as e:
        logger.debug(f"[NVIDIA] benchmark {model} failed: {str(e)[:80]}")
        return None


async def refresh_routing_table() -> dict:
    """Discover + benchmark + persist. Safe to call at startup and from the daily agent."""
    await _ensure_table()
    client = _client()
    if client is None:
        return {"provider": "nvidia", "authorized_models": 0, "note": "no NVIDIA_API_KEY"}

    models = await discover_models()
    results = await asyncio.gather(*[_benchmark(client, m) for m in models])

    ranked = 0
    async with engine.begin() as conn:
        # mark all nvidia rows stale first, then upsert fresh probes
        await conn.execute(text("UPDATE provider_models SET authorized = FALSE WHERE provider = 'nvidia'"))
        for model, latency in zip(models, results):
            await conn.execute(text("""
                INSERT INTO provider_models (provider, model, authorized, latency_ms, last_checked)
                VALUES ('nvidia', :m, TRUE, :lat, now())
                ON CONFLICT (provider, model) DO UPDATE
                SET authorized = TRUE, latency_ms = :lat, last_checked = now()
            """), {"m": model, "lat": latency})
            if latency is not None:
                ranked += 1
    logger.info(f"[NVIDIA] Routing table refreshed: {ranked}/{len(models)} models responded.")
    return {"provider": "nvidia", "authorized_models": len(models), "benchmarked_ok": ranked}


async def get_ranked_nvidia_models(limit: int = 3) -> list[str]:
    """Fastest authorized NVIDIA models first. Empty if none / table absent."""
    try:
        async with engine.begin() as conn:
            rows = await conn.execute(text("""
                SELECT model FROM provider_models
                WHERE provider = 'nvidia' AND authorized = TRUE AND latency_ms IS NOT NULL
                ORDER BY latency_ms ASC LIMIT :lim
            """), {"lim": limit})
            return [r[0] for r in rows.fetchall()]
    except Exception as e:
        logger.debug(f"[NVIDIA] ranked lookup skipped: {str(e)[:80]}")
        return []
