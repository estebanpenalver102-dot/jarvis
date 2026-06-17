"""
JARVIS Agents Router — direct agent invocation endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from database import get_db
from agents.orchestrator import route_goal
from agents.cto_agent import CTOAgent
from agents.sales_agent import SalesAgent
from agents.coding_agent import CodingAgent
from agents.research_agent import ResearchAgent
from agents.operations_agent import OperationsAgent

router = APIRouter(prefix="/agents", tags=["agents"])

AGENT_MAP = {
    "cto": CTOAgent,
    "sales": SalesAgent,
    "coding": CodingAgent,
    "research": ResearchAgent,
    "operations": OperationsAgent,
}


class AgentRequest(BaseModel):
    goal: str
    agent: str = "auto"  # "auto" = LLM routing, or specify agent name


@router.get("")
async def list_agents():
    return {
        "agents": [
            {"name": name, "description": cls.description}
            for name, cls in AGENT_MAP.items()
        ],
        "routing": "POST /agents with agent='auto' for LLM-based routing",
    }


@router.post("")
async def invoke_agent(body: AgentRequest, db: AsyncSession = Depends(get_db)):
    if body.agent == "auto":
        return await route_goal(body.goal, db=db)
    agent_cls = AGENT_MAP.get(body.agent)
    if not agent_cls:
        return {"error": f"Unknown agent: {body.agent}. Available: {list(AGENT_MAP.keys())}"}
    agent = agent_cls()
    return await agent.run(body.goal, db=db)
