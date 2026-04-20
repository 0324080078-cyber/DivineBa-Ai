"""
Vector memory: upsert messages into Qdrant and search by session.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any

from qdrant_client.http.models import (
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.core.config import settings
from app.db.qdrant import get_qdrant, ensure_collection
from app.services.provider_factory import get_provider


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def upsert_message(
    session_id: str,
    role: str,
    content: str,
    summary_chip: str,
) -> str:
    """Embed *content* and store it in Qdrant. Returns the new point id."""
    provider = get_provider()
    q = get_qdrant()

    vectors = await provider.embed([content], model=settings.CYRUS_EMBED_MODEL)
    vec = vectors[0]

    ensure_collection(q, vector_size=len(vec))

    point_id = str(uuid.uuid4())
    q.upsert(
        collection_name=settings.CYRUS_COLLECTION,
        points=[
            PointStruct(
                id=point_id,
                vector=vec,
                payload={
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "summary_chip": summary_chip,
                    "updated_at": _now_iso(),
                },
            )
        ],
    )
    return point_id


async def search_memory(
    session_id: str,
    query: str,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Semantic search within a session. Returns a list of payloads."""
    provider = get_provider()
    q = get_qdrant()

    vectors = await provider.embed([query], model=settings.CYRUS_EMBED_MODEL)
    vec = vectors[0]

    ensure_collection(q, vector_size=len(vec))

    hits = q.search(
        collection_name=settings.CYRUS_COLLECTION,
        query_vector=vec,
        limit=limit,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="session_id",
                    match=MatchValue(value=session_id),
                )
            ]
        ),
    )
    return [h.payload for h in hits]


async def list_session_messages(
    session_id: str,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Retrieve recent messages for a session (used for tiles).
    Uses scroll so we don't need a query vector.
    """
    q = get_qdrant()

    # Ensure collection exists before scrolling
    ensure_collection(q, vector_size=settings.CYRUS_EMBED_DIM)

    results, _ = q.scroll(
        collection_name=settings.CYRUS_COLLECTION,
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="session_id",
                    match=MatchValue(value=session_id),
                )
            ]
        ),
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )
    return [r.payload for r in results]
