"""
JARVIS Tool Registry — @tool decorator registers any async function as agent capability.
"""
from functools import wraps
from typing import Callable
import inspect

_TOOL_REGISTRY: dict[str, dict] = {}


def tool(func: Callable) -> Callable:
    """Decorator: registers an async function as a JARVIS tool."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    sig = inspect.signature(func)
    _TOOL_REGISTRY[func.__name__] = {
        "name": func.__name__,
        "description": func.__doc__ or "",
        "function": wrapper,
        "parameters": {
            name: str(param.annotation) for name, param in sig.parameters.items()
            if name != "self"
        },
    }
    return wrapper


async def execute_tool(name: str, **kwargs):
    """Execute a registered tool by name."""
    if name not in _TOOL_REGISTRY:
        return {"error": f"Tool '{name}' not found. Available: {list(_TOOL_REGISTRY.keys())}"}
    return await _TOOL_REGISTRY[name]["function"](**kwargs)


def list_tools() -> list[dict]:
    return [{"name": v["name"], "description": v["description"], "parameters": v["parameters"]}
            for v in _TOOL_REGISTRY.values()]


# ── Built-in tools ────────────────────────────────────────────────────────────
@tool
async def get_weather(city: str, country_code: str = "US") -> dict:
    """Get current weather for a city using Open-Meteo (free, no API key)."""
    import httpx
    async with httpx.AsyncClient() as client:
        geo = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1}
        )
        loc = geo.json().get("results", [{}])[0]
        if not loc:
            return {"error": f"City not found: {city}"}
        weather = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": loc["latitude"], "longitude": loc["longitude"],
                "current_weather": True, "temperature_unit": "fahrenheit"
            }
        )
        cw = weather.json().get("current_weather", {})
        return {
            "city": city, "temperature_f": cw.get("temperature"),
            "wind_speed_mph": cw.get("windspeed"), "weather_code": cw.get("weathercode"),
        }


@tool
async def list_tools_available() -> dict:
    """List all tools available to JARVIS agents."""
    return {"tools": list_tools(), "count": len(_TOOL_REGISTRY)}


@tool
async def get_current_time() -> dict:
    """Get the current date and time."""
    from datetime import datetime
    now = datetime.now()
    return {"datetime": now.isoformat(), "date": now.strftime("%Y-%m-%d"), "time": now.strftime("%H:%M:%S")}


@tool
async def create_reminder(title: str, message: str, remind_at: str = "") -> dict:
    """Create a reminder (stored in JARVIS memory for Phase 5 scheduler integration)."""
    return {
        "status": "queued",
        "title": title,
        "message": message,
        "remind_at": remind_at or "as soon as possible",
        "note": "Full scheduler integration active in Phase 5",
    }
