"""
JARVIS Research Agent — web research using browser automation + LLM synthesis.
"""
from agents.base_agent import BaseAgent
from browser.actions import search_and_browse, browse_and_extract
from llm.client import chat_completion


class ResearchAgent(BaseAgent):
    name = "research"
    description = "Web research, data lookup, market analysis, competitor tracking"

    async def run(self, goal: str, url: str = None, **kwargs) -> dict:
        if url:
            result = await browse_and_extract(url, goal)
            return {"agent": self.name, "result": result.get("analysis", ""), "url": result.get("url")}
        else:
            result = await search_and_browse(goal, goal)
            return {
                "agent": self.name,
                "result": result.get("synthesis", ""),
                "sources": result.get("sources", []),
            }
