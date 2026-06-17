"""
JARVIS Sales Agent — DealCenter CRM integration and lead management.
"""
from agents.base_agent import BaseAgent
from tools.base_tools import tool
from llm.client import chat_completion
from config import settings
import httpx

SYSTEM_PROMPT = """You are the JARVIS Sales Agent for a car dealership.
Capabilities: manage leads, update CRM, draft follow-up messages, analyze sales pipeline.
Be concise and action-oriented. Always reference specific lead data when available."""


class SalesAgent(BaseAgent):
    name = "sales"
    description = "Manages DealCenter CRM, leads, and sales pipeline"

    async def run(self, goal: str, **kwargs) -> dict:
        context = await self._get_crm_context(goal)
        result = await chat_completion(
            messages=[{"role": "user", "content": f"{goal}\n\nCRM Context:\n{context}"}],
            system_prompt=SYSTEM_PROMPT,
            max_tokens=1000,
        )
        return {"agent": self.name, "result": result}

    async def _get_crm_context(self, query: str) -> str:
        """Pull relevant CRM data — stub until DealCenter API is connected in Phase 5."""
        return "[DealCenter API not yet connected — configure DEALCENTER_API_URL in .env]"


@tool
async def create_lead(name: str, phone: str = "", email: str = "", notes: str = "") -> dict:
    """Create a new lead in DealCenter CRM."""
    if not settings.dealcenter_api_url:
        return {"status": "stub", "message": "DealCenter not configured — set DEALCENTER_API_URL"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.dealcenter_api_url}/leads",
            json={"name": name, "phone": phone, "email": email, "notes": notes},
            headers={"Authorization": f"Bearer {settings.dealcenter_api_key}"},
        )
        return resp.json()


@tool
async def search_leads(query: str, limit: int = 10) -> dict:
    """Search DealCenter CRM leads by name, email, or phone."""
    if not settings.dealcenter_api_url:
        return {"status": "stub", "leads": [], "message": "DealCenter not configured"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.dealcenter_api_url}/leads/search",
            params={"q": query, "limit": limit},
            headers={"Authorization": f"Bearer {settings.dealcenter_api_key}"},
        )
        return resp.json()
