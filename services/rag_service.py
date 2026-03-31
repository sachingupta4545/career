from __future__ import annotations

import asyncio
import logging

from fastapi import UploadFile

from schemas.chatbot import RagSearchResult
from services.embedding_service import EmbeddingService
from services.groq_service import GroqService
from services.pdf_service import PdfService
from services.qdrant_service import QdrantService
from utils.chunking import semantic_chunk_text

logger = logging.getLogger(__name__)

# Prompt used to ask the LLM to rewrite a raw chunk into a rich, embeddable passage.
_ENRICH_SYSTEM_PROMPT = (
    "You are a technical writer. Your job is to rewrite the following text excerpt "
    "into a clear, detailed, self-contained paragraph that captures ALL key facts, "
    "skills, roles, achievements, and context. "
    "Do NOT add any information that is not already present. "
    "Do NOT include introductory phrases like 'Here is a rewrite'. "
    "Return only the rewritten paragraph."
)


async def _enrich_chunk(content: str, groq: GroqService) -> str:
    """Use the LLM to produce a richer, more embeddable version of a raw chunk.

    Falls back to the original content on any error so ingestion never fails.
    """
    prompt = f"{_ENRICH_SYSTEM_PROMPT}\n\n---\n{content}\n---"
    try:
        enriched = await groq.generate(prompt)
        return enriched.strip() or content
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM enrichment failed for chunk (using raw text): %s", exc)
        return content


class RagService:
    async def ingest_text(
        self,
        *,
        user_id: str,
        text: str,
        metadata: dict | None,
        embedder: EmbeddingService,
        qdrant: QdrantService,
        source: str = "text",
        groq: GroqService | None = None,
        bypass_chunking: bool = False,
    ) -> int:
        """Chunk text, optionally enrich each chunk via LLM, embed, and upsert to Qdrant.

        Args:
            groq: When provided, each chunk is rewritten by the LLM before embedding.
                  The original chunk text is always stored in the Qdrant payload.
        """
        cleaned = (text or "").strip()
        if not cleaned:
            return 0

        if bypass_chunking:
            chunks = [{"section": "qa", "content": cleaned}]
        else:
            chunks = semantic_chunk_text(cleaned)
        vectors: list[list[float]] = []
        payloads: list[dict] = []

        # Enrich all chunks concurrently when an LLM is available.
        if groq is not None:
            enriched_texts = await asyncio.gather(
                *[_enrich_chunk(str(chunk.get("content", "")).strip(), groq) for chunk in chunks]
            )
        else:
            enriched_texts = [str(chunk.get("content", "")).strip() for chunk in chunks]

        for index, (chunk, enriched) in enumerate(zip(chunks, enriched_texts)):
            original_content = str(chunk.get("content", "")).strip()
            if not original_content:
                continue

            # Embed the LLM-enriched text for better semantic retrieval.
            vec = await embedder.embed(enriched or original_content)
            if not vec:
                continue

            vectors.append(vec)
            payloads.append(
                {
                    "user_id": user_id,
                    "source": source,
                    # The LLM-polished text is what the chatbot returns — richer and self-contained.
                    "text": enriched if groq is not None else original_content,
                    # Keep the raw extracted text for reference/debugging.
                    "original_text": original_content,
                    "metadata": {
                        **(metadata or {}),
                        "section": chunk.get("section", "other"),
                        "chunk_index": index,
                        "llm_enriched": groq is not None,
                    },
                }
            )

        await qdrant.upsert(vectors=vectors, payloads=payloads)
        return len(vectors)

    async def ingest_qa(
        self,
        *,
        user_id: str,
        question: str,
        answer: str,
        metadata: dict | None,
        embedder: EmbeddingService,
        qdrant: QdrantService,
        groq: GroqService | None = None,
    ) -> int:
        text = f"Q: {question.strip()}\nA: {answer.strip()}"
        return await self.ingest_text(
            user_id=user_id,
            text=text,
            metadata=metadata,
            embedder=embedder,
            qdrant=qdrant,
            source="qa",
            groq=groq,
            bypass_chunking=True,
        )


    async def ingest_pdf(
        self,
        *,
        user_id: str,
        file: UploadFile,
        metadata: dict | None,
        pdf: PdfService,
        embedder: EmbeddingService,
        qdrant: QdrantService,
        source: str = "pdf",
        replace_existing: bool = False,
        groq: GroqService | None = None,
    ) -> int:
        raw = await pdf.extract_text(file)
        cleaned = pdf.clean_text(raw)
        merged_meta = {**(metadata or {})}
        if file.filename:
            merged_meta.setdefault("filename", file.filename)

        if replace_existing:
            await qdrant.delete_by_filter(user_id=user_id, source=source)

        return await self.ingest_text(
            user_id=user_id,
            text=cleaned,
            metadata=merged_meta,
            embedder=embedder,
            qdrant=qdrant,
            source=source,
            groq=groq,
        )

    async def replace_resume(
        self,
        *,
        user_id: str,
        file: UploadFile,
        pdf: PdfService,
        embedder: EmbeddingService,
        qdrant: QdrantService,
        metadata: dict | None = None,
        groq: GroqService | None = None,
    ) -> int:
        return await self.ingest_pdf(
            user_id=user_id,
            file=file,
            metadata=metadata,
            pdf=pdf,
            embedder=embedder,
            qdrant=qdrant,
            source="resume",
            replace_existing=True,
            groq=groq,
        )

    async def search(
        self,
        *,
        user_id: str,
        query: str,
        top_k: int,
        embedder: EmbeddingService,
        qdrant: QdrantService,
    ) -> list[RagSearchResult]:
        vec = await embedder.embed(query)
        points = await qdrant.search(query_vector=vec, user_id=user_id, top_k=top_k)
        results: list[RagSearchResult] = []
        for p in points:
            payload = p.payload or {}
            results.append(
                RagSearchResult(
                    text=str(payload.get("text", "")),
                    score=float(p.score or 0.0),
                    source=str(payload.get("source", "")),
                    metadata=payload.get("metadata") or {},
                )
            )
        return results
