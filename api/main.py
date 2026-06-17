"""
JARVIS API — Phase 1 Walking Skeleton
FastAPI application with PostgreSQL + pgvector, memory system, agent routing
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from config import settings
from routers import health, memory, chat, tools

# Import tools to register them
import tools.base_tools  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"JARVIS API starting — env={settings.app_env}")
    logger.info("Phase 1: Walking Skeleton | Memory ✓ | Agents ✓ | Tools ✓")
    yield
    logger.info("JARVIS API shutdown")


app = FastAPI(
    title="JARVIS — Personal AI Operating System",
    description="Phase 1: Foundation — FastAPI + PostgreSQL + pgvector + Multi-Agent Scaffold",
    version="0.1.0-phase1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(memory.router)
app.include_router(chat.router)
app.include_router(tools.router)


@app.get("/")
async def root():
    return {
        "system": "JARVIS",
        "status": "online",
        "phase": "1 — Foundation",
        "endpoints": {
            "health":  "/health",
            "pgvector": "/health/pgvector",
            "chat":    "/chat",
            "memory":  "/memory",
            "tools":   "/tools",
            "docs":    "/docs",
        },
    }
