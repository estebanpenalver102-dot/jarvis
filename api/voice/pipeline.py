"""
JARVIS Voice Pipeline — VAD → STT (Whisper) → LLM → TTS → Audio
Phase 4: WebSocket streaming. Phase 5: LiveKit upgrade for sub-800ms latency.
"""
from openai import AsyncOpenAI
from llm.client import chat_completion, get_openai
from config import settings
from loguru import logger
from pathlib import Path
import tempfile, base64, io

JARVIS_VOICE_PROMPT = """You are JARVIS voice assistant. Respond conversationally and concisely
— keep answers under 3 sentences for voice. Be direct and actionable."""


async def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
    """STT: Whisper API — transcribe audio bytes to text."""
    client = get_openai()
    if not client:
        return "[Voice requires OPENAI_API_KEY]"
    try:
        ext = "webm" if "webm" in mime_type else "wav" if "wav" in mime_type else "mp3"
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name
        with open(tmp_path, "rb") as audio_file:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
            )
        Path(tmp_path).unlink(missing_ok=True)
        return str(transcript).strip()
    except Exception as e:
        logger.error(f"STT error: {e}")
        return ""


async def text_to_speech(text: str, voice: str = "nova") -> bytes:
    """TTS: OpenAI TTS — convert text to MP3 bytes.
    Voices: alloy, echo, fable, onyx, nova (default), shimmer
    """
    client = get_openai()
    if not client:
        return b""
    try:
        response = await client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text[:4096],
        )
        return response.content
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return b""


async def voice_turn(audio_bytes: bytes, session_history: list = None, mime_type: str = "audio/webm") -> dict:
    """Full voice turn: audio in → transcript + LLM response + audio out."""
    transcript = await transcribe_audio(audio_bytes, mime_type)
    if not transcript:
        return {"transcript": "", "response_text": "", "audio_b64": "", "error": "transcription failed"}

    logger.info(f"Voice transcript: {transcript[:80]}")

    messages = (session_history or []) + [{"role": "user", "content": transcript}]
    response_text = await chat_completion(
        messages=messages,
        system_prompt=JARVIS_VOICE_PROMPT,
        max_tokens=200,
    )

    audio_bytes_out = await text_to_speech(response_text)
    audio_b64 = base64.b64encode(audio_bytes_out).decode() if audio_bytes_out else ""

    return {
        "transcript": transcript,
        "response_text": response_text,
        "audio_b64": audio_b64,
        "audio_format": "mp3",
    }
