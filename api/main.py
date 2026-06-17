"""JARVIS API — Phase 3: Multi-Agent System"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import engine, Base
from routers import health, memory, chat, tools, agents

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="JARVIS API",
    description="Personal AI Operating System — Phase 3: Multi-Agent System",
    version="0.3.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

for router in [health.router, memory.router, chat.router, tools.router, agents.router]:
    app.include_router(router)

@app.get("/")
async def root():
    return {
        "name": "JARVIS",
        "version": "0.3.0",
        "phase": "Phase 3 — Multi-Agent System",
        "agents": ["cto", "sales", "coding", "research", "operations"],
        "endpoints": {
            "chat": "POST /chat",
            "agents": "POST /agents",
            "memory": "GET/POST /memory",
            "memory_search": "GET /memory/search?q=...",
            "tools": "GET /tools",
            "health": "GET /health",
            "docs": "GET /docs",
        },
    }
