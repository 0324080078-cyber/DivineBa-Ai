import uuid
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    SessionCreateOut,
    ChatRequest,
    ChatResponse,
    TilesResponse,
    Tile,
)
from app.services.provider_factory import get_provider
from app.services.summarizer import make_summary_chip
from app.services.memory import upsert_message, search_memory, list_session_messages
from app.core.config import settings

router = APIRouter(tags=["sessions"])

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Cyrus AI, a helpful, friendly, and knowledgeable assistant \
created for students and developers. You speak the same language as the user. \
You can write code in any programming language and explain concepts clearly. \
You are honest, concise, and never make up facts. \
If asked to do something illegal or that violates terms of service \
(e.g. clone a website without permission), politely refuse and suggest a legal alternative."""


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/sessions", response_model=SessionCreateOut)
def create_session() -> SessionCreateOut:
    """Create a new chat session and return its ID."""
    return SessionCreateOut(session_id=str(uuid.uuid4()))


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """
    Send a message and get a reply from Cyrus AI.
    Optionally retrieves semantically similar past messages as context.
    """
    provider = get_provider()

    # 1. Generate a chip for the user message
    user_chip = await make_summary_chip(req.message, locale=req.locale)

    # 2. Store the user message in vector memory
    await upsert_message(req.session_id, "user", req.message, user_chip)

    # 3. Optionally retrieve relevant memory snippets for context
    context_block = ""
    if req.enable_search:
        hits = await search_memory(req.session_id, req.message, limit=5)
        if hits:
            snippets = "\n".join(f"- {h.get('content', '')}" for h in hits)
            context_block = (
                f"\n\nRelevant conversation history:\n{snippets}"
            )

    # 4. Build prompt and call provider
    user_content = req.message + context_block

    try:
        assistant_text = await provider.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            model=settings.CYRUS_CHAT_MODEL,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Provider error: {exc}") from exc

    # 5. Generate chip for assistant reply and store it
    assistant_chip = await make_summary_chip(assistant_text, locale=req.locale)
    await upsert_message(req.session_id, "assistant", assistant_text, assistant_chip)

    return ChatResponse(
        session_id=req.session_id,
        assistant_message=assistant_text,
        summary_chip=assistant_chip,
    )


@router.get("/sessions/{session_id}/tiles", response_model=TilesResponse)
async def get_tiles(session_id: str) -> TilesResponse:
    """
    Return history tiles for a session.
    Each tile has a summary chip (replaces the date badge) and a preview line.
    """
    messages = await list_session_messages(session_id, limit=50)

    # Sort by timestamp ascending
    messages.sort(key=lambda m: m.get("updated_at", ""))

    tiles = []
    for i, msg in enumerate(messages):
        content = msg.get("content", "")
        preview = content[:100] + ("…" if len(content) > 100 else "")
        tiles.append(
            Tile(
                message_id=str(i),
                summary_chip=msg.get("summary_chip", "…"),
                last_message_preview=preview,
                updated_at=msg.get("updated_at", ""),
            )
        )

    return TilesResponse(session_id=session_id, tiles=tiles)
