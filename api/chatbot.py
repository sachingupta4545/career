from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from db.session import get_db_session
from models.user import User
from schemas.chatbot import ChatRequest, ChatResponse
from schemas.user import ResponseEnvelope
from services.chatbot_service import ChatbotService
from services.embedding_service import EmbeddingService
from services.groq_service import GroqService
from services.qdrant_service import QdrantService
from services.rag_service import RagService

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.post("/chat", response_model=ResponseEnvelope)
async def chat(
    payload: ChatRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    service: ChatbotService = Depends(ChatbotService),
    rag: RagService = Depends(RagService),
    embedder: EmbeddingService = Depends(EmbeddingService),
    qdrant: QdrantService = Depends(QdrantService),
    groq: GroqService = Depends(GroqService),
) -> ResponseEnvelope:
    answer, ctx = await service.chat(
        session=session,
        user=current_user,
        query=payload.query,
        rag=rag,
        embedder=embedder,
        qdrant=qdrant,
        groq=groq,
    )
    data = ChatResponse(answer=answer, context=ctx).model_dump()
    return ResponseEnvelope(data=data, message="Chat response")
