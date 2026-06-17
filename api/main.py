"""JARVIS API — Phase 4: Voice + Browser Automation"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import engine, Base
from routers import health, memory, chat, tools, agents, voice, browser

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="JARVIS API",
    description="Personal AI Operating System — Phase 4: Voice + Browser Automation",
    version="0.4.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

for router in [health.router, memory.router, chat.router, tools.router, agents.router, voice.router, browser.router]:
    app.include_router(router)

@app.get("/")
async def root():
    return {
        "name": "JARVIS",
        "version": "0.4.0",
        "phase": "Phase 4 — Voice + Browser Automation",
        "capabilities": {
            "chat": "POST /chat — LLM with memory + agent routing",
            "voice": "POST /voice/turn | WS /voice/ws — Whisper STT + OpenAI TTS",
            "browser": "POST /browser/browse | /browser/search — Playwright automation",
            "agents": "POST /agents — 6 specialized agents (auto or direct)",
            "memory": "GET/POST /memory | /memory/search — pgvector semantic search",
        },
    }
