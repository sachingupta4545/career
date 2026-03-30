from fastapi import UploadFile

from schemas.chatbot import RagSearchResult
from services.embedding_service import EmbeddingService
from services.pdf_service import PdfService
from services.qdrant_service import QdrantService
from utils.chunking import chunk_text


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
    ) -> int:
        cleaned = (text or "").strip()
        if not cleaned:
            return 0
        chunks = chunk_text(cleaned)
        vectors: list[list[float]] = []
        payloads: list[dict] = []
        for ch in chunks:
            vec = await embedder.embed(ch)
            if not vec:
                continue
            vectors.append(vec)
            payloads.append({
                "user_id": user_id,
                "source": source,
                "text": ch,
                "metadata": metadata or {},
            })
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
    ) -> int:
        text = f"Q: {question.strip()} A: {answer.strip()}"
        return await self.ingest_text(
            user_id=user_id,
            text=text,
            metadata=metadata,
            embedder=embedder,
            qdrant=qdrant,
            source="qa",
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
    ) -> int:
        raw = await pdf.extract_text(file)
        cleaned = pdf.clean_text(raw)
        merged_meta = {**(metadata or {})}
        if file.filename:
            merged_meta.setdefault("filename", file.filename)
        return await self.ingest_text(
            user_id=user_id,
            text=cleaned,
            metadata=merged_meta,
            embedder=embedder,
            qdrant=qdrant,
            source="pdf",
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
