import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from api.deps import get_current_user
from models.user import User
from schemas.chatbot import RagIngestQARequest, RagIngestTextRequest, RagSearchRequest
from schemas.user import ResponseEnvelope
from services.embedding_service import EmbeddingService
from services.groq_service import GroqService
from services.pdf_service import PdfService
from services.qdrant_service import QdrantService
from services.rag_service import RagService

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/ingest/text", response_model=ResponseEnvelope)
async def ingest_text(
    payload: RagIngestTextRequest,
    current_user: User = Depends(get_current_user),
    service: RagService = Depends(RagService),
    embedder: EmbeddingService = Depends(EmbeddingService),
    qdrant: QdrantService = Depends(QdrantService),
    groq: GroqService = Depends(GroqService),
) -> ResponseEnvelope:
    count = await service.ingest_text(
        user_id=str(current_user.id),
        text=payload.text,
        metadata=payload.metadata,
        embedder=embedder,
        qdrant=qdrant,
        source="text",
        groq=groq,
    )
    return ResponseEnvelope(data={"chunks": count}, message="Text ingested")


@router.post("/ingest/qa", response_model=ResponseEnvelope)
async def ingest_qa(
    payload: RagIngestQARequest,
    current_user: User = Depends(get_current_user),
    service: RagService = Depends(RagService),
    embedder: EmbeddingService = Depends(EmbeddingService),
    qdrant: QdrantService = Depends(QdrantService),
    groq: GroqService = Depends(GroqService),
) -> ResponseEnvelope:
    count = await service.ingest_qa(
        user_id=str(current_user.id),
        question=payload.question,
        answer=payload.answer,
        metadata=payload.metadata,
        embedder=embedder,
        qdrant=qdrant,
        groq=groq,
    )
    return ResponseEnvelope(data={"chunks": count}, message="Q&A ingested")


@router.post("/ingest/pdf", response_model=ResponseEnvelope)
async def ingest_pdf(
    file: UploadFile = File(...),
    metadata: str | None = Form(default=None),
    source: str = Form(default="pdf"),
    replace_existing: bool = Form(default=False),
    current_user: User = Depends(get_current_user),
    service: RagService = Depends(RagService),
    pdf: PdfService = Depends(PdfService),
    embedder: EmbeddingService = Depends(EmbeddingService),
    qdrant: QdrantService = Depends(QdrantService),
    groq: GroqService = Depends(GroqService),
) -> ResponseEnvelope:
    pdf.validate_upload(file)

    parsed_metadata: dict | None = None
    if metadata:
        try:
            loaded = json.loads(metadata)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="metadata must be valid JSON.",
            ) from exc
        if not isinstance(loaded, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="metadata must be a JSON object.",
            )
        parsed_metadata = loaded

    normalized_source = (source or "pdf").strip() or "pdf"
    count = await service.ingest_pdf(
        user_id=str(current_user.id),
        file=file,
        metadata=parsed_metadata,
        pdf=pdf,
        embedder=embedder,
        qdrant=qdrant,
        source=normalized_source,
        replace_existing=replace_existing,
        groq=groq,
    )
    return ResponseEnvelope(
        data={
            "chunks": count,
            "filename": file.filename,
            "source": normalized_source,
            "replace_existing": replace_existing,
        },
        message="PDF ingested",
    )


@router.post("/search", response_model=ResponseEnvelope)
async def search(
    payload: RagSearchRequest,
    current_user: User = Depends(get_current_user),
    service: RagService = Depends(RagService),
    embedder: EmbeddingService = Depends(EmbeddingService),
    qdrant: QdrantService = Depends(QdrantService),
) -> ResponseEnvelope:
    results = await service.search(
        user_id=str(current_user.id),
        query=payload.query,
        top_k=payload.top_k,
        embedder=embedder,
        qdrant=qdrant,
    )
    return ResponseEnvelope(data=[r.model_dump() for r in results], message="Search results")
