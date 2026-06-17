"""
JARVIS Tool Registry — any Python function decorated with @tool becomes
an agent capability. Tools are auto-discovered and listed in /api/tools.
"""
import httpx
from loguru import logger
from functools import wraps
from typing import Callable

_TOOL_REGISTRY: dict[str, dict] = {}

def tool(name: str, description: str):
    """Decorator to register a function as a JARVIS tool."""
    def decorator(fn: Callable):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            logger.info(f"[TOOL] Executing: {name}")
            return await fn(*args, **kwargs)
        _TOOL_REGISTRY[name] = {
            "fn": wrapper,
            "description": description,
            "name": name,
        }
        return wrapper
    return decorator

def list_tools() -> list[dict]:
    return [{"name": k, "description": v["description"]} for k, v in _TOOL_REGISTRY.items()]


# ─── Built-in Tools ──────────────────────────────────────────────────────────

@tool("get_weather", "Get current weather for a city")
async def get_weather(city: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://wttr.in/{city}?format=j1", timeout=10.0
        )
        if resp.status_code == 200:
            data = resp.json()
            current = data["current_condition"][0]
            return {
                "city": city,
                "temp_c": current["temp_C"],
                "temp_f": current["temp_F"],
                "description": current["weatherDesc"][0]["value"],
            }
    return {"error": f"Could not fetch weather for {city}"}


@tool("search_web", "Search the web and return top results (placeholder — Playwright in Phase 4)")
async def search_web(query: str) -> dict:
    return {
        "query": query,
        "note": "Web search tool placeholder. Full browser automation wired in Phase 4.",
        "status": "scaffolded",
    }


@tool("list_tools_available", "List all tools available to JARVIS agents")
async def list_tools_available() -> dict:
    return {"tools": list_tools()}
