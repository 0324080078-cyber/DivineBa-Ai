"""
TTS (Text-to-Speech) endpoint.

Local option  : Piper TTS  (uncomment the implementation below)
Remote option : OpenAI TTS API  (set TTS_PROVIDER=openai in .env)
"""

import os

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import TTSRequest
from app.core.config import settings

router = APIRouter(tags=["tts"])

TTS_PROVIDER = os.getenv("TTS_PROVIDER", "openai")  # openai | local


@router.post("/tts")
async def tts(req: TTSRequest):
    """
    Generate speech audio from text and stream it back as audio/mpeg.

    TTS_PROVIDER=openai  → OpenAI TTS API (requires OPENAI_API_KEY)
    TTS_PROVIDER=local   → Piper TTS (install piper-tts locally)
    """
    if TTS_PROVIDER == "openai":
        return await _openai_tts(req)

    if TTS_PROVIDER == "local":
        return await _local_tts(req)

    raise HTTPException(status_code=400, detail=f"Unknown TTS_PROVIDER: {TTS_PROVIDER}")


# ── OpenAI TTS ────────────────────────────────────────────────────────────────

# Map locale → recommended OpenAI voice (feel free to extend)
_LOCALE_VOICE_MAP = {
    "en": "alloy",
    "fr": "nova",
    "es": "shimmer",
    "de": "echo",
    "zh": "fable",
    "ar": "onyx",
}


async def _openai_tts(req: TTSRequest) -> StreamingResponse:
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not set for TTS.")

    voice = req.voice if req.voice != "default" else _LOCALE_VOICE_MAP.get(req.locale, "alloy")

    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            "https://api.openai.com/v1/audio/speech",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={
                "model": "tts-1",
                "voice": voice,
                "input": req.text,
            },
        )
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        audio_bytes = r.content

    return StreamingResponse(
        iter([audio_bytes]),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=speech.mp3"},
    )


# ── Local Piper TTS ───────────────────────────────────────────────────────────

async def _local_tts(req: TTSRequest) -> StreamingResponse:
    """
    Uses Piper TTS for local synthesis.
    To enable:
      pip install piper-tts
      Download a voice model from https://huggingface.co/rhasspy/piper-voices
      Set PIPER_MODEL=/path/to/model.onnx in .env
    """
    piper_model = os.getenv("PIPER_MODEL", "")
    if not piper_model:
        raise HTTPException(
            status_code=503,
            detail="PIPER_MODEL env var not set. Point it to your .onnx model file.",
        )

    try:
        from piper import PiperVoice  # type: ignore
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="piper-tts not installed. Run: pip install piper-tts",
        ) from exc

    import io
    import wave

    voice = PiperVoice.load(piper_model)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        voice.synthesize(req.text, wav_file)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="audio/wav",
        headers={"Content-Disposition": "inline; filename=speech.wav"},
    )
