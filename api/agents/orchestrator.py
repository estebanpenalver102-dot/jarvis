"""
JARVIS Orchestrator — LLM-based intent routing to specialized agents.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from llm.client import chat_completion
from loguru import logger
import json
import re

ROUTER_PROMPT = """You are the JARVIS routing system. Given a user goal, decide which agent should handle it.

Available agents:
- research: web research, data lookup, market analysis, competitor tracking
- sales: CRM leads, DealCenter, customer follow-ups, sales pipeline
- coding: code generation, debugging, technical implementation
- cto: system architecture, infrastructure, code review
- operations: scheduling, calendar, tasks, reminders
- general: everything else — conversation, questions, analysis

Respond with ONLY a JSON object: {"agent": "<name>", "reason": "<one line>"}

Goal: {goal}"""

AGENT_SYSTEM_PROMPTS = {
    "research": "You are a research specialist. Search, analyze, and summarize information concisely with sources.",
    "sales": "You are a sales agent. Manage leads, CRM records, and customer relationships for a car dealership.",
    "coding": "You are a coding agent. Write clean, production-ready code. Always include error handling.",
    "cto": "You are a CTO. Provide architecture decisions, code reviews, and infrastructure guidance.",
    "operations": "You are an operations agent. Manage schedules, tasks, and workflows efficiently.",
    "general": "You are JARVIS, a personal AI OS. Be direct, helpful, and proactive.",
}


async def route_goal(goal: str, db: AsyncSession = None) -> dict:
    """Route a goal to the correct agent and execute it."""
    # Route
    routing_resp = await chat_completion(
        messages=[{"role": "user", "content": ROUTER_PROMPT.replace("{goal}", goal)}],
        max_tokens=100,
    )
    agent_name = "general"
    try:
        raw = (routing_resp or "").strip()
        # Strip ```json ... ``` fences some models add, then grab the first {...} block
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            routing = json.loads(m.group(0))
            agent_name = routing.get("agent", "general")
    except Exception:
        agent_name = "general"

    if agent_name not in AGENT_SYSTEM_PROMPTS:
        agent_name = "general"

    logger.info(f"Routing to agent: {agent_name}")

    # Execute with specialized prompt
    result = await chat_completion(
        messages=[{"role": "user", "content": goal}],
        system_prompt=AGENT_SYSTEM_PROMPTS[agent_name],
        max_tokens=1500,
    )

    return {"agent": agent_name, "result": result}
