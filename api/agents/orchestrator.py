"""
JARVIS Orchestrator — routes goals to the correct specialized agent.
Implements the Logic Delegation pattern: LLM decides agent, orchestrator executes.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from agents.research_agent import ResearchAgent
from agents.operations_agent import OperationsAgent
from loguru import logger
from typing import Optional

AGENT_REGISTRY = {
    "research":   ResearchAgent,
    "operations": OperationsAgent,
}

AGENT_DESCRIPTIONS = {
    "research":   "web research, information gathering, market analysis, competitor research",
    "operations": "scheduling, reminders, task management, calendar, workflow coordination",
}

async def route_goal(goal: str, db: AsyncSession, llm_client=None) -> dict:
    """
    Determine which agent should handle a goal and execute it.
    Falls back to 'operations' if no clear match is found.
    """
    agent_type = _classify_goal(goal)
    logger.info(f"Routing goal to [{agent_type}] agent: {goal[:60]}")

    AgentClass = AGENT_REGISTRY.get(agent_type, OperationsAgent)
    agent = AgentClass(db=db, llm_client=llm_client)
    result = await agent.run(goal=goal)
    return {"agent": agent_type, **result}


def _classify_goal(goal: str) -> str:
    """Simple keyword-based classifier — replaced by LLM routing in Phase 3."""
    goal_lower = goal.lower()
    if any(w in goal_lower for w in ["search", "research", "find", "look up", "web", "browse"]):
        return "research"
    return "operations"
