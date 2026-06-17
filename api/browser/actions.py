"""
JARVIS Browser Actions — higher-level automation tasks built on BrowserSession.
"""
from browser.controller import BrowserSession
from llm.client import chat_completion
from loguru import logger

EXTRACT_PROMPT = """You browsed: {url}
Page content (first 3000 chars):
{content}

Goal: {goal}
Extract only what's needed to achieve the goal. Be concise."""


async def browse_and_extract(url: str, goal: str) -> dict:
    """Navigate to URL, extract relevant content for the goal using LLM."""
    async with BrowserSession() as session:
        nav = await session.navigate(url)
        content = await session.extract_text()
        content = content[:3000]
        screenshot_b64 = await session.screenshot()

        analysis = await chat_completion(
            messages=[{"role": "user", "content": EXTRACT_PROMPT.format(
                url=nav["url"], content=content, goal=goal
            )}],
            max_tokens=600,
        )
        return {
            "url": nav["url"],
            "title": nav["title"],
            "analysis": analysis,
            "screenshot_b64": screenshot_b64,
            "content_length": len(content),
        }


async def search_and_browse(query: str, goal: str, num_results: int = 3) -> dict:
    """Google search + browse top results + synthesize answer."""
    async with BrowserSession() as session:
        await session.navigate(f"https://www.google.com/search?q={query}")
        links = await session.extract_links()
        # Filter to real result links
        result_links = [
            l for l in links
            if "google.com" not in l["href"] and l["href"].startswith("http")
        ][:num_results]

        results = []
        for link in result_links:
            try:
                nav = await session.navigate(link["href"])
                text = (await session.extract_text())[:1500]
                results.append({"url": nav["url"], "title": nav["title"], "content": text})
            except Exception as e:
                logger.debug(f"Skip {link['href']}: {e}")

        if not results:
            return {"query": query, "synthesis": "Could not retrieve results", "sources": []}

        combined = "\n\n---\n\n".join(
            f"Source: {r['url']}\n{r['content']}" for r in results
        )
        synthesis = await chat_completion(
            messages=[{"role": "user", "content":
                f"Goal: {goal}\n\nResearch from {len(results)} sources:\n{combined[:4000]}\n\nProvide a concise, sourced answer."
            }],
            max_tokens=800,
        )
        return {
            "query": query,
            "synthesis": synthesis,
            "sources": [{"url": r["url"], "title": r["title"]} for r in results],
        }


async def monitor_url(url: str, check_for: str) -> dict:
    """Visit a URL and check if a condition is present."""
    async with BrowserSession() as session:
        nav = await session.navigate(url)
        content = (await session.extract_text())[:2000]
        found = check_for.lower() in content.lower()
        return {
            "url": nav["url"],
            "check_for": check_for,
            "found": found,
            "snippet": content[:500],
        }
