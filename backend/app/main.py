from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, sessions, stt, tts

app = FastAPI(
    title="Cyrus AI Backend",
    description=(
        "FastAPI backend for Cyrus AI: chat, sessions, memory search, STT, and TTS. "
        "Supports multiple LLM providers via a plug-in interface."
    ),
    version="0.1.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow the Next.js frontend to call the API.
# In production, replace ["*"] with your actual frontend domain(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(stt.router, prefix="/api")
app.include_router(tts.router, prefix="/api")
