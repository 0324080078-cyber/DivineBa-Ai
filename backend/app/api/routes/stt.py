"""
STT (Speech-to-Text) endpoint.

Local option  : faster-whisper  (uncomment the import and implementation below)
Remote option : OpenAI Whisper API  (set STT_PROVIDER=openai in .env)
"""

import os
import tempfile

import httpx
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from app.models.schemas import STTResponse
from app.core.config import settings

router = APIRouter(tags=["stt"])

STT_PROVIDER = os.getenv("STT_PROVIDER", "openai")  # openai | local


@router.post("/stt", response_model=STTResponse)
async def stt(audio: UploadFile = File(...)) -> STTResponse:
    """
    Accept an audio file (webm/wav/mp3) and return transcribed text.

    STT_PROVIDER=openai  → forwards to OpenAI Whisper API (requires OPENAI_API_KEY)
    STT_PROVIDER=local   → uses faster-whisper locally (install the package first)
    """
    audio_bytes = await audio.read()

    if STT_PROVIDER == "openai":
        return await _openai_stt(audio_bytes, audio.filename or "audio.webm")

    if STT_PROVIDER == "local":
        return await _local_stt(audio_bytes)

    raise HTTPException(status_code=400, detail=f"Unknown STT_PROVIDER: {STT_PROVIDER}")


# ── OpenAI Whisper API ────────────────────────────────────────────────────────

async def _openai_stt(audio_bytes: bytes, filename: str) -> STTResponse:
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not set for STT.")

    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            files={"file": (filename, audio_bytes, "audio/webm")},
            data={"model": "whisper-1"},
        )
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return STTResponse(text=r.json().get("text", ""))


# ── Local faster-whisper ──────────────────────────────────────────────────────

async def _local_stt(audio_bytes: bytes) -> STTResponse:
    """
    Uses faster-whisper for local transcription.
    To enable: pip install faster-whisper  (also needs ffmpeg on PATH)
    """
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="faster-whisper not installed. Run: pip install faster-whisper",
        ) from exc

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        model = WhisperModel("base", compute_type="int8")
        segments, _ = model.transcribe(tmp_path)
        text = " ".join(seg.text for seg in segments).strip()
    finally:
        os.unlink(tmp_path)

    return STTResponse(text=text)
