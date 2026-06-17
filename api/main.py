"""JARVIS API v1.0 — Complete AI Operating System"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import engine, Base
from routers import health, memory, chat, tools, agents, voice, browser, goals, screen

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="JARVIS", description="Personal AI Operating System v1.0", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
for r in [health.router, memory.router, chat.router, tools.router, agents.router, voice.router, browser.router, goals.router, screen.router]:
    app.include_router(r)

@app.get("/")
async def root():
    return {"name":"JARVIS","version":"1.0.0","status":"online","docs":"/docs",
            "endpoints":{"POST /chat":"LLM + memory","POST /goals":"Submit goal → auto agent hiring",
                         "WS /voice/ws":"Real-time voice","POST /browser/search":"Web research",
                         "WS /screen/ws":"Screen takeover","GET /memory/search":"Semantic search"}}
