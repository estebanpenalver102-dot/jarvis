"""
JARVIS Coding Agent — code generation, debugging, refactoring.
"""
from agents.base_agent import BaseAgent
from llm.client import chat_completion

SYSTEM_PROMPT = """You are the JARVIS Coding Agent. Expertise: Python, FastAPI, TypeScript,
SQL, Docker, shell scripting. Write production-ready code with error handling and type hints.
Always explain key decisions briefly. Prefer async patterns."""


class CodingAgent(BaseAgent):
    name = "coding"
    description = "Code generation, debugging, technical implementation"

    async def run(self, goal: str, **kwargs) -> dict:
        result = await chat_completion(
            messages=[{"role": "user", "content": goal}],
            system_prompt=SYSTEM_PROMPT,
            max_tokens=3000,
        )
        return {"agent": self.name, "result": result}
