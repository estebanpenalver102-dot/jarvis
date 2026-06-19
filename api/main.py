"""JARVIS API v1.0 — Personal AI Operating System"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from database import engine, Base
from security import SecurityGuardMiddleware
from routers import health, memory, chat, tools, agents, voice, browser, goals, screen, ingest


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        # Enable pgvector extension before creating tables (required for VECTOR type)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="JARVIS — Personal AI Operating System",
    description="v1.0 — Chat · Voice · Browser · Goals · Screen · GitHub Ingestion",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — registered first so pre-flight requests pass through cleanly
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# SecurityGuard — scans every outgoing response and redacts secrets
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
            "POST /chat": "LLM chat with 5-tier memory",
            "POST /goals": "Submit goal → auto-hire agents",
            "WS  /voice/ws": "Real-time voice (Whisper + TTS)",
            "POST /browser/search": "Autonomous web research",
            "WS  /screen/ws": "Screen share + vision analysis",
            "POST /ingest/github-file": "Drop GitHub file → JARVIS learns",
            "POST /ingest/github-repo": "Ingest entire repo folder",
            "POST /ingest/text": "Drop raw text → knowledge base",
            "GET  /ingest/knowledge": "List all ingested knowledge",
            "GET  /docs": "Full Swagger UI",
        },
    }
