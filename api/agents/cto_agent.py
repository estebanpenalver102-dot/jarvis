"""
JARVIS CTO Agent — architecture decisions, infrastructure, code review.
"""
from agents.base_agent import BaseAgent
from llm.client import chat_completion

SYSTEM_PROMPT = """You are the JARVIS CTO Agent. Expertise: system architecture, Docker/K8s,
FastAPI, PostgreSQL, security, performance. Provide specific, actionable technical guidance.
Reference code files and patterns from the JARVIS codebase when relevant."""


class CTOAgent(BaseAgent):
    name = "cto"
    description = "Architecture decisions, infrastructure guidance, code review"

    async def run(self, goal: str, **kwargs) -> dict:
        result = await chat_completion(
            messages=[{"role": "user", "content": goal}],
            system_prompt=SYSTEM_PROMPT,
            max_tokens=2000,
        )
        return {"agent": self.name, "result": result}
