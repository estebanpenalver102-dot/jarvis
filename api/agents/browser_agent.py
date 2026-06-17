"""
JARVIS Browser Agent — autonomous web research and automation.
"""
from agents.base_agent import BaseAgent
from browser.actions import browse_and_extract, search_and_browse, monitor_url
from llm.client import chat_completion
from loguru import logger

PLAN_PROMPT = """You are JARVIS Browser Agent. Given a goal requiring web access, produce a JSON plan.
Return ONLY JSON: {{"action": "browse|search|monitor", "url": "...", "query": "...", "check_for": "..."}}

goal: {goal}"""


class BrowserAgent(BaseAgent):
    name = "browser"
    description = "Web research, page extraction, URL monitoring, browser automation"

    async def run(self, goal: str, **kwargs) -> dict:
        # Let LLM decide the browser action
        plan_resp = await chat_completion(
            messages=[{"role": "user", "content": PLAN_PROMPT.format(goal=goal)}],
            max_tokens=150,
        )
        try:
            import json
            plan = json.loads(plan_resp.strip())
        except Exception:
            plan = {"action": "search", "query": goal}

        action = plan.get("action", "search")
        logger.info(f"Browser agent action: {action} for: {goal[:60]}")

        if action == "browse" and plan.get("url"):
            result = await browse_and_extract(plan["url"], goal)
        elif action == "monitor" and plan.get("url"):
            result = await monitor_url(plan["url"], plan.get("check_for", goal))
        else:
            result = await search_and_browse(plan.get("query", goal), goal)

        return {"agent": self.name, "result": result.get("analysis") or result.get("synthesis", str(result)[:500]), "data": result}
