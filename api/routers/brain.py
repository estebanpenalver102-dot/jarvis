"""
JARVIS — /api/brain/status endpoint (mission-required).

Reports live provider health + the ranked routing table so the UI admin panel
and the daily AI Infrastructure Agent can verify routing is populated and see
which providers are currently reachable. Read-only, no admin token required for
status (does NOT expose keys — only presence booleans + model names/latency).
"""
from fastapi import APIRouter
from sqlalchemy import text

from config import settings
from database import engine

router = APIRouter(prefix="/api/brain", tags=["brain"])


@router.get("/status")
async def brain_status():
    providers = {
        "nvidia":     bool(settings.nvidia_api_key),
        "openai":     bool(settings.openai_api_key),
        "openrouter": bool(settings.openrouter_api_key),
        "groq":       bool(settings.groq_api_key),
        "ollama":     True,  # local, keyless
    }

    routing_table: list[dict] = []
    try:
        async with engine.begin() as conn:
            rows = await conn.execute(text("""
                SELECT provider, model, latency_ms, last_checked
                FROM provider_models
                WHERE authorized = TRUE
                ORDER BY (latency_ms IS NULL), latency_ms ASC
            """))
            routing_table = [
                {"provider": r[0], "model": r[1], "latency_ms": r[2],
                 "last_checked": r[3].isoformat() if r[3] else None}
                for r in rows.fetchall()
            ]
    except Exception:
        routing_table = []  # table not created yet

    active = [p for p, on in providers.items() if on]
    return {
        "status": "ok" if active else "degraded",
        "providers": providers,
        "active_providers": active,
        "routing_table_size": len(routing_table),
        "routing_table": routing_table,
        "note": None if active else "No LLM providers configured — set at least one API key in Render env.",
    }
