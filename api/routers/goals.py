from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from database import get_db
from agents.goal_engine import execute_goal
from memory.store import save_memory
from typing import Optional

router = APIRouter(prefix="/goals", tags=["goals"])

class GoalRequest(BaseModel):
    goal: str
    context: Optional[str] = None

@router.post("")
async def submit_goal(body: GoalRequest, db: AsyncSession = Depends(get_db)):
    full_goal = f"{body.goal}\nContext: {body.context}" if body.context else body.goal
    result = await execute_goal(full_goal, db=db)
    await save_memory(db, f"Goal: {body.goal}\nResult: {result['synthesis'][:300]}",
                      category="project", importance=0.9, metadata={"agents": result["agents_hired"]})
    return result

@router.get("/agents")
async def list_agents():
    return {"agents": [
        {"name": "research", "specialty": "Web research, market analysis, competitor tracking"},
        {"name": "sales", "specialty": "CRM, DealCenter leads, customer follow-ups"},
        {"name": "coding", "specialty": "Code generation, debugging, implementation"},
        {"name": "cto", "specialty": "Architecture, infrastructure, code review"},
        {"name": "operations", "specialty": "Scheduling, task management, reminders"},
        {"name": "browser", "specialty": "Web automation, data extraction, monitoring"},
        {"name": "general", "specialty": "Conversation, analysis, anything else"},
    ], "note": "JARVIS auto-selects the best agent(s) for your goal"}
