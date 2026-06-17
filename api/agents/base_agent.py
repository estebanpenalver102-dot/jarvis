"""
BaseAgent — foundation class for all JARVIS specialized agents.
Each agent inherits this, declares its tools, and overrides run().
"""
from sqlalchemy.ext.asyncio import AsyncSession
from memory.store import save_memory, get_recent_memories
from loguru import logger
from abc import ABC, abstractmethod
from typing import Optional
import uuid

class BaseAgent(ABC):
    name: str = "base"
    description: str = "Base JARVIS agent"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_id = str(uuid.uuid4())

    async def remember(self, content: str, category: str = "episodic",
                       importance: float = 0.5):
        """Save a memory from this agent's execution."""
        await save_memory(self.db, content, category=category,
                          importance=importance,
                          metadata={"agent": self.name, "task_id": self.task_id})

    async def recall(self, category: Optional[str] = None, limit: int = 10):
        """Recall recent memories relevant to this agent's domain."""
        return await get_recent_memories(self.db, category=category, limit=limit)

    @abstractmethod
    async def run(self, goal: str, context: dict = None) -> dict:
        """Execute the agent's primary task. Must be overridden."""
        pass

    async def log_task_start(self, goal: str):
        logger.info(f"[{self.name.upper()}] Starting task: {goal[:80]}")

    async def log_task_end(self, result: dict):
        logger.info(f"[{self.name.upper()}] Task complete: {str(result)[:80]}")
