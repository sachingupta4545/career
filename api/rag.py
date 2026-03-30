from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from db.session import get_db_session
from models.user import User
from schemas.chatbot import RagIngestQARequest, RagIngestTextRequest, RagSearchRequest
from schemas.user import ResponseEnvelope
from services.embedding_service import EmbeddingService
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
) -> ResponseEnvelope:
    count = await service.ingest_text(
        user_id=str(current_user.id),
        text=payload.text,
        metadata=payload.metadata,
        embedder=embedder,
        qdrant=qdrant,
        source="text",
    )
    return ResponseEnvelope(data={"chunks": count}, message="Text ingested")


@router.post("/ingest/qa", response_model=ResponseEnvelope)
async def ingest_qa(
    payload: RagIngestQARequest,
    current_user: User = Depends(get_current_user),
    service: RagService = Depends(RagService),
    embedder: EmbeddingService = Depends(EmbeddingService),
    qdrant: QdrantService = Depends(QdrantService),
) -> ResponseEnvelope:
    count = await service.ingest_qa(
        user_id=str(current_user.id),
        question=payload.question,
        answer=payload.answer,
        metadata=payload.metadata,
        embedder=embedder,
        qdrant=qdrant,
    )
    return ResponseEnvelope(data={"chunks": count}, message="Q&A ingested")


@router.post("/ingest/pdf", response_model=ResponseEnvelope)
async def ingest_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: RagService = Depends(RagService),
    pdf: PdfService = Depends(PdfService),
    embedder: EmbeddingService = Depends(EmbeddingService),
    qdrant: QdrantService = Depends(QdrantService),
) -> ResponseEnvelope:
    count = await service.ingest_pdf(
        user_id=str(current_user.id),
        file=file,
        metadata=None,
        pdf=pdf,
        embedder=embedder,
        qdrant=qdrant,
    )
    return ResponseEnvelope(data={"chunks": count}, message="PDF ingested")


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
