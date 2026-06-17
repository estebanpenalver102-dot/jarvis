"""JARVIS Goal Engine — decomposes goals, hires agents, synthesizes results."""
from llm.client import chat_completion
from loguru import logger
import json

DECOMPOSE_PROMPT = """Break this goal into 1-5 concrete subtasks. Return ONLY JSON array:
[{"task": "...", "agent": "research|sales|coding|cto|operations|browser|general", "priority": 1}]
Goal: {goal}"""

AGENTS = {
    "research": "You are a research specialist. Search, analyze, and summarize concisely.",
    "sales": "You are a sales agent for a car dealership. Manage leads and CRM data.",
    "coding": "You are a coding agent. Write clean production-ready code.",
    "cto": "You are a CTO. Provide architecture and infrastructure guidance.",
    "operations": "You are an operations agent. Manage schedules and workflows.",
    "browser": "You are a browser automation agent. Navigate, extract, and monitor web content.",
    "general": "You are JARVIS, a personal AI OS. Be direct and actionable.",
}

async def execute_goal(goal: str, db=None) -> dict:
    decomp = await chat_completion(messages=[{"role":"user","content":DECOMPOSE_PROMPT.format(goal=goal)}], max_tokens=300)
    try:
        subtasks = json.loads(decomp.strip())
        if not isinstance(subtasks, list): raise ValueError
    except Exception:
        subtasks = [{"task": goal, "agent": "general", "priority": 1}]

    results = []
    for st in sorted(subtasks, key=lambda x: x.get("priority",3)):
        task_text = st.get("task", goal)
        agent = st.get("agent", "general")
        system = AGENTS.get(agent, AGENTS["general"])
        logger.info(f"[{agent}] {task_text[:60]}")
        result = await chat_completion(messages=[{"role":"user","content":task_text}], system_prompt=system, max_tokens=600)
        results.append({"task": task_text, "agent": agent, "result": result})

    synthesis = await chat_completion(
        messages=[{"role":"user","content":
            f"Goal: {goal}\n\nAgent results:\n" +
            "\n\n".join(f"[{r['agent'].upper()}] {r['result']}" for r in results) +
            "\n\nSynthesize into one final answer."}],
        max_tokens=800,
    )
    return {"goal": goal, "subtasks_executed": len(results),
            "agents_hired": list({r["agent"] for r in results}),
            "subtask_results": results, "synthesis": synthesis}
