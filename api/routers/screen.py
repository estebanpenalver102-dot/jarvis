from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from llm.client import chat_completion
from config import settings
from loguru import logger
import json

router = APIRouter(prefix="/screen", tags=["screen"])
PROMPT = "You are JARVIS Screen Analyst. Describe what you see and give 1-2 actionable suggestions. Be brief."

@router.websocket("/ws")
async def screen_ws(ws: WebSocket):
    await ws.accept()
    logger.info("Screen session started")
    try:
        while True:
            data = json.loads(await ws.receive_text())
            question = data.get("question", "What do you see?")
            b64 = data.get("screenshot_b64", "")
            if b64 and settings.openai_api_key:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=settings.openai_api_key)
                try:
                    resp = await client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role":"user","content":[
                            {"type":"text","text":f"{PROMPT}\nQuestion: {question}"},
                            {"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64}","detail":"low"}},
                        ]}], max_tokens=150)
                    analysis = resp.choices[0].message.content
                except Exception as e:
                    analysis = f"Screen error: {str(e)[:80]}"
            else:
                analysis = await chat_completion(messages=[{"role":"user","content":question}], system_prompt=PROMPT, max_tokens=100)
            await ws.send_json({"analysis": analysis})
    except WebSocketDisconnect:
        logger.info("Screen session ended")

@router.post("/analyze")
async def analyze(payload: dict):
    b64 = payload.get("screenshot_b64",""); q = payload.get("question","What do you see?")
    if b64 and settings.openai_api_key:
        from openai import AsyncOpenAI
        try:
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            resp = await client.chat.completions.create(model="gpt-4o-mini",
                messages=[{"role":"user","content":[
                    {"type":"text","text":q},
                    {"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64}","detail":"low"}}
                ]}], max_tokens=300)
            return {"analysis": resp.choices[0].message.content}
        except Exception as e:
            return {"error": str(e)}
    return {"analysis": "Screen analysis requires OPENAI_API_KEY"}
