from pydantic import BaseModel
from typing import Literal, List, Optional

Role = Literal["system", "user", "assistant"]


# ── Sessions ──────────────────────────────────────────────────────────────────

class SessionCreateOut(BaseModel):
    session_id: str


# ── Tiles ─────────────────────────────────────────────────────────────────────

class Tile(BaseModel):
    message_id: str
    summary_chip: str
    last_message_preview: str
    updated_at: str


class TilesResponse(BaseModel):
    session_id: str
    tiles: List[Tile]


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    message: str
    locale: str = "en"
    enable_search: bool = True


class ChatResponse(BaseModel):
    session_id: str
    assistant_message: str
    summary_chip: str


# ── STT ───────────────────────────────────────────────────────────────────────

class STTResponse(BaseModel):
    text: str


# ── TTS ───────────────────────────────────────────────────────────────────────

class TTSRequest(BaseModel):
    text: str
    locale: str = "en"
    voice: str = "default"
