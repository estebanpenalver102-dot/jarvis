"""
JARVIS Browser Router — REST endpoints for browser automation.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from browser.actions import browse_and_extract, search_and_browse, monitor_url
from browser.controller import close_browser
from typing import Optional

router = APIRouter(prefix="/browser", tags=["browser"])


class BrowseRequest(BaseModel):
    url: str
    goal: str = "extract main content"


class SearchRequest(BaseModel):
    query: str
    goal: str = "find relevant information"
    num_results: int = 3


class MonitorRequest(BaseModel):
    url: str
    check_for: str


@router.post("/browse")
async def browse(body: BrowseRequest):
    """Navigate to URL and extract content relevant to goal."""
    try:
        return await browse_and_extract(body.url, body.goal)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/search")
async def search_browse(body: SearchRequest):
    """Search the web and synthesize an answer from top results."""
    try:
        return await search_and_browse(body.query, body.goal, body.num_results)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/monitor")
async def monitor(body: MonitorRequest):
    """Check if a condition is present on a URL."""
    try:
        return await monitor_url(body.url, body.check_for)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.delete("/session")
async def reset_browser():
    """Close and reset the browser session."""
    await close_browser()
    return {"status": "browser session reset"}
