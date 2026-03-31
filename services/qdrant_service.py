import uuid
from functools import lru_cache

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from core.config import get_settings


@lru_cache
def _get_client() -> AsyncQdrantClient:
    settings = get_settings()
    if not settings.qdrant_url:
        raise RuntimeError("QDRANT_URL is not set")
    return AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)


class QdrantService:
    async def ensure_collection(self, vector_size: int) -> None:
        settings = get_settings()
        client = _get_client()
        exists = await client.collection_exists(collection_name=settings.qdrant_collection)
        if exists:
            return

        await client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )

    async def upsert(
        self,
        *,
        vectors: list[list[float]],
        payloads: list[dict],
    ) -> None:
        if not vectors:
            return
        settings = get_settings()
        client = _get_client()
        await self.ensure_collection(vector_size=len(vectors[0]))

        points = [
            models.PointStruct(id=str(uuid.uuid4()), vector=vectors[i], payload=payloads[i])
            for i in range(len(vectors))
        ]
        await client.upsert(collection_name=settings.qdrant_collection, points=points)

    async def delete_by_filter(self, *, user_id: str, source: str | None = None) -> None:
        settings = get_settings()
        client = _get_client()
        exists = await client.collection_exists(collection_name=settings.qdrant_collection)
        if not exists:
            return

        conditions: list[models.FieldCondition] = [
            models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))
        ]
        if source:
            conditions.append(models.FieldCondition(key="source", match=models.MatchValue(value=source)))

        await client.delete(
            collection_name=settings.qdrant_collection,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=conditions,
                )
            ),
        )

    async def search(self, *, query_vector: list[float], user_id: str, top_k: int) -> list[models.ScoredPoint]:
        if not query_vector:
            return []
        settings = get_settings()
        client = _get_client()
        await self.ensure_collection(vector_size=len(query_vector))

        filt = models.Filter(
            must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
        )

        response = await client.query_points(
            collection_name=settings.qdrant_collection,
            query=query_vector,
            limit=top_k,
            query_filter=filt,
            with_payload=True,
        )
        return response.points
