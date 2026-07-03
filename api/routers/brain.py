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

# Neon free-tier storage cap (GiB), converted to bytes. Update this if the plan
# or provider changes — this is the number /api/brain/storage measures against.
STORAGE_CAP_BYTES = int(0.5 * 1024 * 1024 * 1024)  # 0.5 GiB
STORAGE_WARN_PCT = 70   # start telling the user
STORAGE_URGENT_PCT = 85  # push hard for cleanup before it becomes a hard stop


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


@router.get("/storage")
async def brain_storage():
    """
    Database storage usage against the free-tier cap, plus the oldest/least-active
    chat sessions and agent tasks — candidates the user can choose to delete to
    free up space before the cap forces a hard stop.

    Any autonomous JARVIS task/goal execution loop should check this before doing
    heavy writes (new chat sessions, memories, agent_tasks) once one exists, and
    should surface the same warn/urgent split to the user rather than erroring
    out when storage is actually exhausted.
    """
    async with engine.begin() as conn:
        size_bytes = await conn.scalar(text("SELECT pg_database_size(current_database())"))

        stale_sessions = (await conn.execute(text("""
            SELECT id, title, mode, last_active
            FROM chat_sessions
            ORDER BY last_active ASC NULLS FIRST
            LIMIT 10
        """))).fetchall()

        stale_tasks = (await conn.execute(text("""
            SELECT id, goal, status, updated_at
            FROM agent_tasks
            WHERE status IN ('completed', 'failed')
            ORDER BY updated_at ASC NULLS FIRST
            LIMIT 10
        """))).fetchall()

    pct_used = round((size_bytes / STORAGE_CAP_BYTES) * 100, 2)
    level = (
        "urgent" if pct_used >= STORAGE_URGENT_PCT
        else "warn" if pct_used >= STORAGE_WARN_PCT
        else "ok"
    )

    return {
        "size_bytes": size_bytes,
        "cap_bytes": STORAGE_CAP_BYTES,
        "pct_used": pct_used,
        "level": level,  # "ok" | "warn" | "urgent" — callers escalate to the user on warn/urgent
        "cleanup_candidates": {
            "chat_sessions": [
                {"id": str(r[0]), "title": r[1], "mode": r[2],
                 "last_active": r[3].isoformat() if r[3] else None}
                for r in stale_sessions
            ],
            "agent_tasks": [
                {"id": str(r[0]), "goal": r[1], "status": r[2],
                 "updated_at": r[3].isoformat() if r[3] else None}
                for r in stale_tasks
            ],
        },
    }
