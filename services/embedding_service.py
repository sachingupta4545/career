from functools import lru_cache

import anyio
from fastembed import TextEmbedding

from core.config import get_settings


@lru_cache
def _get_model() -> TextEmbedding:
    settings = get_settings()
    return TextEmbedding(model_name=settings.embedding_model)


class EmbeddingService:
    async def embed(self, text: str) -> list[float]:
        if not text:
            return []

        def _embed() -> list[float]:
            model = _get_model()
            vec = next(model.embed([text]))
            return [float(x) for x in vec]

        return await anyio.to_thread.run_sync(_embed)
