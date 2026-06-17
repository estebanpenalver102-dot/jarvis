from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from tools.base_tools import _TOOL_REGISTRY, list_tools

router = APIRouter(prefix="/tools", tags=["tools"])

class ToolCallRequest(BaseModel):
    tool: str
    args: dict = {}

@router.get("")
async def get_tools():
    """List all registered JARVIS tools."""
    return {"tools": list_tools()}

@router.post("/call")
async def call_tool(body: ToolCallRequest):
    """Execute a named tool with provided arguments."""
    if body.tool not in _TOOL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Tool '{body.tool}' not found")
    fn = _TOOL_REGISTRY[body.tool]["fn"]
    try:
        result = await fn(**body.args)
        return {"tool": body.tool, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
