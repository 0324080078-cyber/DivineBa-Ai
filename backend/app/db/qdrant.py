from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from app.core.config import settings


def get_qdrant() -> QdrantClient:
    return QdrantClient(url=settings.QDRANT_URL)


def ensure_collection(client: QdrantClient, vector_size: int) -> None:
    """Create the Qdrant collection if it doesn't already exist."""
    existing = {c.name for c in client.get_collections().collections}
    if settings.CYRUS_COLLECTION not in existing:
        client.create_collection(
            collection_name=settings.CYRUS_COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
