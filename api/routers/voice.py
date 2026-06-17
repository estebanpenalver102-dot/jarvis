"""
JARVIS Voice Router — WebSocket + REST endpoints for voice interaction.
WebSocket: ws://localhost:8000/voice/ws
REST: POST /voice/transcribe, POST /voice/speak, POST /voice/turn
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from voice.pipeline import transcribe_audio, text_to_speech, voice_turn
from loguru import logger
import base64, json

router = APIRouter(prefix="/voice", tags=["voice"])


class SpeakRequest(BaseModel):
    text: str
    voice: str = "nova"  # alloy | echo | fable | onyx | nova | shimmer


class TranscribeRequest(BaseModel):
    audio_b64: str
    mime_type: str = "audio/webm"


class VoiceTurnRequest(BaseModel):
    audio_b64: str
    mime_type: str = "audio/webm"
    session_history: list = []


@router.post("/transcribe")
async def transcribe(body: TranscribeRequest):
    """STT: Base64 audio → transcript text."""
    audio_bytes = base64.b64decode(body.audio_b64)
    transcript = await transcribe_audio(audio_bytes, body.mime_type)
    return {"transcript": transcript}


@router.post("/speak")
async def speak(body: SpeakRequest):
    """TTS: Text → MP3 audio (returns binary)."""
    audio = await text_to_speech(body.text, body.voice)
    if not audio:
        raise HTTPException(503, "TTS unavailable — check OPENAI_API_KEY")
    return Response(content=audio, media_type="audio/mpeg")


@router.post("/turn")
async def voice_turn_rest(body: VoiceTurnRequest):
    """Full voice turn: audio in → transcript + response + audio out (base64)."""
    audio_bytes = base64.b64decode(body.audio_b64)
    result = await voice_turn(audio_bytes, body.session_history, body.mime_type)
    return result


@router.websocket("/ws")
async def voice_websocket(websocket: WebSocket):
    """
    Real-time voice WebSocket.
    Client sends: {"audio_b64": "...", "mime_type": "audio/webm", "history": [...]}
    Server sends: {"transcript": "...", "response_text": "...", "audio_b64": "..."}
    """
    await websocket.accept()
    session_history = []
    logger.info("Voice WebSocket connected")
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            audio_bytes = base64.b64decode(msg.get("audio_b64", ""))
            if not audio_bytes:
                await websocket.send_json({"error": "empty audio"})
                continue
            result = await voice_turn(audio_bytes, session_history, msg.get("mime_type", "audio/webm"))
            if result.get("transcript"):
                session_history.append({"role": "user", "content": result["transcript"]})
                session_history.append({"role": "assistant", "content": result["response_text"]})
                if len(session_history) > 20:
                    session_history = session_history[-20:]
            await websocket.send_json(result)
    except WebSocketDisconnect:
        logger.info("Voice WebSocket disconnected")
    except Exception as e:
        logger.error(f"Voice WebSocket error: {e}")
        await websocket.close()


@router.get("/voices")
async def list_voices():
    return {
        "voices": [
            {"id": "nova", "description": "Default — warm, natural (recommended for JARVIS)"},
            {"id": "alloy", "description": "Neutral, balanced"},
            {"id": "echo", "description": "Warm, conversational"},
            {"id": "fable", "description": "Expressive, dynamic"},
            {"id": "onyx", "description": "Deep, authoritative"},
            {"id": "shimmer", "description": "Clear, optimistic"},
        ],
        "current_default": "nova",
        "note": "Phase 5 upgrade: LiveKit for sub-800ms real-time streaming",
    }
