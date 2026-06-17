"""
JARVIS Ingestion Router — drop any GitHub file/repo into JARVIS knowledge base.
JARVIS reads, summarizes, and stores it as searchable memory so it can learn from it.

Endpoints:
  POST /ingest/github-file   { url: "https://github.com/.../file.py" }
  POST /ingest/github-repo   { owner, repo, path (optional), branch }
  POST /ingest/text          { title, content, category }
  GET  /ingest/knowledge     list all ingested knowledge
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from database import get_db
from llm.client import chat_completion, get_embedding
from config import settings
from typing import Optional
import httpx, base64, json
from loguru import logger

router = APIRouter(prefix="/ingest", tags=["ingest"])

SUMMARIZE_PROMPT = """You are JARVIS knowledge extractor. A file was just dropped into your system.
Analyze it and extract:
1. What it does (1-2 sentences)
2. Key functions/classes/patterns (bullet list)
3. How JARVIS could use or improve from this (1-2 sentences)

File: {filename}
Content (first 4000 chars):
{content}"""


def _raw_url(github_url: str) -> str:
    """Convert github.com URL to raw.githubusercontent.com"""
    url = github_url.replace("https://github.com/", "https://raw.githubusercontent.com/")
    url = url.replace("/blob/", "/")
    return url


async def _fetch_and_store(db: AsyncSession, filename: str, content: str, source_url: str = "", category: str = "knowledge"):
    """Summarize content with LLM + store in knowledge base."""
    summary = await chat_completion(
        messages=[{"role": "user", "content": SUMMARIZE_PROMPT.format(filename=filename, content=content[:4000])}],
        max_tokens=400,
    )
    embedding = await get_embedding(f"{filename} {summary}")
    embedding_json = json.dumps(embedding) if embedding else None
    await db.execute(
        text("""INSERT INTO memories (content, category, importance, metadata, embedding)
                VALUES (:content, :category, :importance, :metadata, :embedding::vector)"""),
        {
            "content": f"[INGESTED: {filename}]\n\n{summary}\n\nSource: {source_url}",
            "category": category,
            "importance": 0.85,
            "metadata": json.dumps({"filename": filename, "source_url": source_url, "raw_length": len(content)}),
            "embedding": embedding_json,
        }
    )
    await db.commit()
    return summary


class GitHubFileRequest(BaseModel):
    url: str                        # full github.com or raw URL
    category: str = "knowledge"

class GitHubRepoRequest(BaseModel):
    owner: str
    repo: str
    path: str = ""                  # folder path inside repo (empty = root)
    branch: str = "main"
    extensions: list = [".py", ".ts", ".js", ".md", ".txt", ".json"]
    max_files: int = 20

class TextIngestRequest(BaseModel):
    title: str
    content: str
    category: str = "knowledge"
    source_url: str = ""


@router.post("/github-file")
async def ingest_github_file(body: GitHubFileRequest, db: AsyncSession = Depends(get_db)):
    """Drop a single GitHub file into JARVIS knowledge base."""
    raw_url = _raw_url(body.url)
    filename = raw_url.split("/")[-1]
    async with httpx.AsyncClient() as client:
        resp = await client.get(raw_url, timeout=15, follow_redirects=True)
        if resp.status_code != 200:
            raise HTTPException(400, f"Could not fetch file (HTTP {resp.status_code}): {raw_url}")
        content = resp.text
    summary = await _fetch_and_store(db, filename, content, body.url, body.category)
    logger.info(f"Ingested GitHub file: {filename} ({len(content)} chars)")
    return {"status": "ingested", "filename": filename, "chars": len(content), "summary": summary}


@router.post("/github-repo")
async def ingest_github_repo(body: GitHubRepoRequest, db: AsyncSession = Depends(get_db)):
    """Ingest all matching files from a GitHub repo folder."""
    api_url = f"https://api.github.com/repos/{body.owner}/{body.repo}/git/trees/{body.branch}?recursive=1"
    async with httpx.AsyncClient(headers={"User-Agent": "JARVIS-Ingestion"}) as client:
        tree_resp = await client.get(api_url, timeout=15)
        if tree_resp.status_code != 200:
            raise HTTPException(400, f"GitHub API error: {tree_resp.text[:200]}")
        tree = tree_resp.json().get("tree", [])

    files_to_fetch = [
        f for f in tree
        if f["type"] == "blob"
        and (not body.path or f["path"].startswith(body.path))
        and any(f["path"].endswith(ext) for ext in body.extensions)
    ][:body.max_files]

    results = []
    async with httpx.AsyncClient() as client:
        for file_info in files_to_fetch:
            raw_url = f"https://raw.githubusercontent.com/{body.owner}/{body.repo}/{body.branch}/{file_info['path']}"
            try:
                resp = await client.get(raw_url, timeout=10)
                if resp.status_code == 200:
                    summary = await _fetch_and_store(db, file_info["path"], resp.text, raw_url)
                    results.append({"file": file_info["path"], "status": "ingested"})
                    logger.info(f"Ingested: {file_info['path']}")
            except Exception as e:
                results.append({"file": file_info["path"], "status": f"error: {str(e)[:60]}"})

    return {
        "status": "complete",
        "repo": f"{body.owner}/{body.repo}",
        "files_ingested": len([r for r in results if r["status"] == "ingested"]),
        "results": results,
    }


@router.post("/text")
async def ingest_text(body: TextIngestRequest, db: AsyncSession = Depends(get_db)):
    """Drop raw text directly into JARVIS knowledge base."""
    summary = await _fetch_and_store(db, body.title, body.content, body.source_url, body.category)
    return {"status": "ingested", "title": body.title, "summary": summary}


@router.get("/knowledge")
async def list_knowledge(db: AsyncSession = Depends(get_db), limit: int = 50):
    """List all ingested knowledge entries."""
    result = await db.execute(
        text("SELECT id, content, category, importance, created_at FROM memories WHERE content LIKE '[INGESTED:%' ORDER BY created_at DESC LIMIT :limit"),
        {"limit": limit}
    )
    rows = result.fetchall()
    return {
        "count": len(rows),
        "knowledge": [{"id": str(r.id), "preview": r.content[:120], "category": r.category, "ingested_at": str(r.created_at)} for r in rows]
    }
