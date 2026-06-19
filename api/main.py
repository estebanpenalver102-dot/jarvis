"""JARVIS API v1.0 — Personal AI Operating System"""
import os
import secrets
import hashlib
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from database import engine, Base
from security import SecurityGuardMiddleware, RateLimitMiddleware, set_admin_token

logger = logging.getLogger("jarvis.startup")

# ── Allowed origins ────────────────────────────────────────────────────────────
_ALLOWED_ORIGINS = [o.strip() for o in os.getenv(
    "CORS_ORIGINS",
    "https://jarvis.openroad-autos.com,https://openroad-autos.com,http://localhost:3000"
).split(",") if o.strip()]

# ── RLS migration SQL ──────────────────────────────────────────────────────────
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

DO $$
DECLARE t text;
BEGIN
  FOR t IN SELECT unnest(ARRAY[
    'memories','projects','tasks','businesses',
    'delegations','execution_history','knowledge_graph','events',
    'chat_sessions','chat_messages'
  ])
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS jarvis_backend_only ON %I', t);
    EXECUTE format(
      $p$CREATE POLICY jarvis_backend_only ON %I
         USING (current_user = ''postgres''
                OR current_user = ''jarvis''
                OR current_user = current_setting(''app.db_user'', true))$p$,
      t
    );
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
  END LOOP;
END $$;
"""


async def _bootstrap_admin_token(conn) -> str:
    """Load or generate the JARVIS admin token — stored in jarvis_admin table."""
    # Create admin table if not exists
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS jarvis_admin (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """))
    # Check if token already exists
    result = await conn.execute(
        text("SELECT value FROM jarvis_admin WHERE key = 'admin_token'")
    )
    row = result.fetchone()
    if row:
        return row[0]
    # Generate a new random token and persist it
    token = secrets.token_hex(32)
    await conn.execute(text("""
        INSERT INTO jarvis_admin (key, value) VALUES ('admin_token', :t)
        ON CONFLICT (key) DO NOTHING
    """), {"t": token})
    return token


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        # 1. Enable pgvector
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # 2. Create all ORM tables
        await conn.run_sync(Base.metadata.create_all)
        # 3. Apply RLS migration (idempotent — IF EXISTS guards handle re-runs)
        try:
            await conn.execute(text(_RLS_SQL))
            logger.info("[JARVIS] RLS policies applied successfully.")
        except Exception as e:
            logger.warning(f"[JARVIS] RLS migration warning (non-fatal): {e}")
        # 4. Bootstrap admin token — generate once, persist forever
        env_token = os.getenv("JARVIS_ADMIN_TOKEN")
        if env_token:
            admin_token = env_token
        else:
            admin_token = await _bootstrap_admin_token(conn)
        set_admin_token(admin_token)
        # Log token once so owner can retrieve it from Render Logs
        logger.info(
            f"[JARVIS ADMIN TOKEN] {admin_token[:8]}...{admin_token[-8:]} "
            f"(full token in /admin/token endpoint)"
        )
    yield


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

from routers import health, memory, chat, tools, agents, voice, browser, goals, screen, ingest
for router in [health.router, memory.router, chat.router, tools.router,
               agents.router, voice.router, browser.router, goals.router,
               screen.router, ingest.router]:
    app.include_router(router)


@app.get("/")
async def root():
    return {
        "name": "JARVIS", "version": "1.0.0", "status": "online",
        "deploy": "v2-secure",
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
        return {"error": "Admin token not yet initialized — restart service or check startup logs"}
    return {
        "hint": f"{token[:8]}...{token[-8:]}",
        "length": len(token),
        "note": "Full token logged at service startup — check Render Logs tab."
    }
