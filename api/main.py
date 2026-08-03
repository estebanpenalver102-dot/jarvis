"""
ROBUST main.py — ALL startup operations are safe, non-fatal.
Service will ALWAYS start even if DB ops fail at startup.
"""

import os
import time
import asyncio
import secrets
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from database import engine, Base
# ── Import all ORM models so Base.metadata is populated before create_all ──
import models.memory  # noqa: F401
import models.chat    # noqa: F401
from security import SecurityGuardMiddleware, RateLimitMiddleware, set_admin_token

logger = logging.getLogger("jarvis.startup")

# ── Cold-start instrumentation ────────────────────────────────────────────────
# _BOOT_START marks process start (module import time) — the earliest possible
# reference point. The first request the process ever serves logs the real
# elapsed time, replacing guesswork ("~30-60s") with actual observed data.
_BOOT_START = time.monotonic()
_first_request_logged = False

# ── Allowed origins ──────────────────────────────────────────────────────────
_ALLOWED_ORIGINS = [o.strip() for o in os.getenv(
    "CORS_ORIGINS",
    "https://jarvis.openroad-autos.com,https://openroad-autos.com,http://localhost:3000"
).split(",") if o.strip()]

# ── RLS migration SQL (idempotent) ───────────────────────────────────────────
_RLS_SQL = """
ALTER TABLE IF EXISTS memories          ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS projects          ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS tasks             ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS businesses        ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS delegations       ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS execution_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS knowledge_graph   ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS events            ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS chat_sessions     ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS chat_messages     ENABLE ROW LEVEL SECURITY;
"""

# ── Pre-set admin token from env var (if available) ──────────────────────────
_PRESET_ADMIN_TOKEN = os.getenv("JARVIS_ADMIN_TOKEN", "")


async def _bootstrap_admin_token(conn) -> str:
    """Idempotent: create jarvis_admin table + return/generate persistent token."""
    try:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS jarvis_admin (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """))
        result = await conn.execute(
            text("SELECT value FROM jarvis_admin WHERE key = 'admin_token'")
        )
        row = result.fetchone()
        if row:
            return row[0]
        token = secrets.token_hex(32)
        await conn.execute(text("""
            INSERT INTO jarvis_admin (key, value) VALUES ('admin_token', :t)
            ON CONFLICT (key) DO NOTHING
        """), {"t": token})
        return token
    except Exception as e:
        logger.warning(f"[JARVIS] Admin token DB bootstrap failed (using session token): {e}")
        return secrets.token_hex(32)


async def _run_db_bootstrap():
    """Enable pgvector → create tables → RLS → admin token → NVIDIA routing table.
    Runs as a BACKGROUND task, not awaited by lifespan. Fixes the cold-start hang:
    previously this whole sequence ran INSIDE lifespan before `yield`, so if Neon
    (or the DB pool) was slow to respond after idle, the ASGI server never signaled
    "startup complete" and NOT EVEN /health could be served — every request just
    hung with no error, matching the reported symptom exactly. Now the port binds
    and requests are served immediately; DB-dependent routes still wait on their
    own `Depends(get_db)` per request, but liveness/root/health endpoints don't.
    ALL non-fatal — a DB hiccup here never prevents the service from serving."""
    try:
        async with engine.begin() as conn:
            # 1. pgvector
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            except Exception as e:
                logger.warning(f"[JARVIS] pgvector warning: {e}")

            # 2. ORM tables
            try:
                await conn.run_sync(Base.metadata.create_all)
            except Exception as e:
                logger.warning(f"[JARVIS] Table creation warning: {e}")

            # 3. RLS migration
            try:
                await conn.execute(text(_RLS_SQL))
                logger.info("[JARVIS] RLS policies applied.")
            except Exception as e:
                logger.warning(f"[JARVIS] RLS warning (non-fatal): {e}")

            # 4. Admin token — env var takes priority, then DB, then session fallback
            if _PRESET_ADMIN_TOKEN:
                admin_token = _PRESET_ADMIN_TOKEN
                logger.info("[JARVIS] Admin token loaded from environment.")
            else:
                admin_token = await _bootstrap_admin_token(conn)

            set_admin_token(admin_token)
            logger.info(
                f"[JARVIS ADMIN TOKEN] {admin_token[:8]}...{admin_token[-8:]} "
                f"| hint available at /admin/token"
            )
    except Exception as e:
        logger.error(f"[JARVIS] DB bootstrap error (non-fatal — service already serving requests): {e}")
        # Session-only fallback so admin-gated routes still work even if DB never comes up.
        if not _PRESET_ADMIN_TOKEN:
            fallback = secrets.token_hex(32)
            set_admin_token(fallback)
            logger.info(f"[JARVIS ADMIN TOKEN fallback] {fallback[:8]}...{fallback[-8:]}")

    # 5. NVIDIA routing table — separately backgrounded (unchanged behavior),
    #    kept after DB bootstrap so it doesn't race table creation.
    try:
        from llm.nvidia import refresh_routing_table
        result = await refresh_routing_table()
        logger.info(f"[JARVIS] NVIDIA routing table: {result}")
    except Exception as e:
        logger.warning(f"[JARVIS] NVIDIA routing table refresh failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: set a temporary admin token immediately (never blocks), then kick
    off the real DB bootstrap in the background. `yield` happens right away, so
    Uvicorn/Render see "startup complete" almost instantly and begin serving
    requests — including the new zero-dependency /health/live — before the
    database has necessarily finished waking up."""
    if _PRESET_ADMIN_TOKEN:
        set_admin_token(_PRESET_ADMIN_TOKEN)
    else:
        set_admin_token(secrets.token_hex(32))  # temporary; DB bootstrap may replace with the persisted one

    asyncio.create_task(_run_db_bootstrap())
    logger.info("[JARVIS] Lifespan startup complete — serving requests; DB bootstrap continues in background.")

    yield  # App runs


app = FastAPI(
    title="JARVIS — Personal AI Operating System",
    description="v1.0 — Chat · Voice · Browser · Goals · Screen · GitHub Ingestion",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if os.getenv("ENV", "production") == "production" else "/docs",
    redoc_url=None if os.getenv("ENV", "production") == "production" else "/redoc",
    openapi_url=None if os.getenv("ENV", "production") == "production" else "/openapi.json",
)

# Middleware — CORS → RateLimit → SecurityGuard
app.add_middleware(
    CORSMiddleware, allow_origins=_ALLOWED_ORIGINS, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityGuardMiddleware)


@app.middleware("http")
async def _log_cold_start_once(request: Request, call_next):
    """Logs real cold-start duration (process start → first request handled),
    once per process. Grounds future wake-time UI claims in actual data instead
    of a guess."""
    global _first_request_logged
    if not _first_request_logged:
        _first_request_logged = True
        elapsed = time.monotonic() - _BOOT_START
        logger.info(f"[JARVIS] COLD_START_DURATION_SECONDS={elapsed:.2f} first_path={request.url.path}")
    return await call_next(request)

from routers import health, memory, chat, tools, agents, voice, browser, goals, screen, ingest, brain
for router in [health.router, memory.router, chat.router, tools.router,
               agents.router, voice.router, browser.router, goals.router,
               screen.router, ingest.router, brain.router]:
    app.include_router(router)


@app.get("/")
async def root():
    return {
        "name": "JARVIS", "version": "1.0.0", "status": "online",
        "deploy": "v3-robust",
        "endpoints": {
            "POST /chat":           "LLM chat with 5-tier memory",
            "POST /goals":          "Submit goal → auto-hire agents",
            "WS  /voice/ws":        "Real-time voice (Whisper + TTS)",
            "POST /browser/search": "Autonomous web research",
        }
    }


@app.get("/admin/token")
async def get_admin_token():
    """Returns a partial hint of the admin token (full token in Render Logs at startup)."""
    import security as _sec
    token = _sec._ADMIN_TOKEN
    if not token:
        return {"error": "Admin token not yet initialized"}
    return {
        "hint": f"{token[:8]}...{token[-8:]}",
        "length": len(token),
        "note": "Full token logged at service startup — check Render Logs tab."
    }

