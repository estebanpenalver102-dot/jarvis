"""
Web search tool — uses SerpAPI if configured, falls back to DuckDuckGo HTML scraping.
"""
from tools.base_tools import tool
from config import settings
import httpx

@tool
async def search_web(query: str, num_results: int = 5) -> dict:
    """Search the web for information. Returns titles, URLs, and snippets."""
    # Try SerpAPI first
    if settings.serpapi_key:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://serpapi.com/search",
                params={"q": query, "num": num_results, "api_key": settings.serpapi_key, "engine": "google"},
                timeout=10,
            )
            data = resp.json()
            results = [
                {"title": r.get("title"), "url": r.get("link"), "snippet": r.get("snippet")}
                for r in data.get("organic_results", [])[:num_results]
            ]
            return {"query": query, "results": results, "source": "serpapi"}

    # Fallback: DuckDuckGo Instant Answer API (free, no key)
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
                timeout=8,
            )
            data = resp.json()
            results = []
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", query),
                    "url": data.get("AbstractURL", ""),
                    "snippet": data["AbstractText"][:300],
                })
            for rt in data.get("RelatedTopics", [])[:num_results-1]:
                if isinstance(rt, dict) and rt.get("Text"):
                    results.append({
                        "title": rt.get("Text", "")[:60],
                        "url": rt.get("FirstURL", ""),
                        "snippet": rt.get("Text", "")[:200],
                    })
            return {"query": query, "results": results[:num_results], "source": "duckduckgo"}
    except Exception as e:
        return {"query": query, "results": [], "error": str(e)}
