"""JARVIS API v1.0 — Personal AI Operating System"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from database import engine, Base
from security import SecurityGuardMiddleware, RateLimitMiddleware
from routers import health, memory, chat, tools, agents, voice, browser, goals, screen, ingest

# ── Allowed origins — tighten in production ───────────────────────────────────
_ALLOWED_ORIGINS = [o.strip() for o in os.getenv(
    "CORS_ORIGINS",
    "https://jarvis.openroad-autos.com,https://openroad-autos.com,http://localhost:3000"
).split(",") if o.strip()]

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="JARVIS — Personal AI Operating System",
    description="v1.0 — Chat · Voice · Browser · Goals · Screen · GitHub Ingestion",
    version="1.0.0",
    lifespan=lifespan,
    # Hide /docs + /redoc in production
    docs_url=None if os.getenv("ENV", "production") == "production" else "/docs",
    redoc_url=None if os.getenv("ENV", "production") == "production" else "/redoc",
    openapi_url=None if os.getenv("ENV", "production") == "production" else "/openapi.json",
)

# Middleware — order matters: CORS → RateLimit → SecurityGuard
app.add_middleware(
    CORSMiddleware, allow_origins=_ALLOWED_ORIGINS, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityGuardMiddleware)

for router in [health.router, memory.router, chat.router, tools.router,
               agents.router, voice.router, browser.router, goals.router,
               screen.router, ingest.router]:
    app.include_router(router)


@app.get("/")
async def root():
    return {
        "name": "JARVIS", "version": "1.0.0", "status": "online",
        "endpoints": {
            "POST /chat":           "LLM chat with 5-tier memory",
            "POST /goals":          "Submit goal → auto-hire agents",
            "WS  /voice/ws":        "Real-time voice (Whisper + TTS)",
            "POST /browser/search": "Autonomous web research",
        }
    }
