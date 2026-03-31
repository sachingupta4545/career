from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.portfolio import Portfolio
from models.project import Project
from models.user import User
from services.embedding_service import EmbeddingService
from services.groq_service import GroqService
from services.qdrant_service import QdrantService
from services.rag_service import RagService


class ChatbotService:
    async def chat(
        self,
        *,
        session: AsyncSession,
        user: User,
        query: str,
        rag: RagService,
        embedder: EmbeddingService,
        qdrant: QdrantService,
        groq: GroqService,
    ) -> tuple[str, list[str]]:
        q = (query or "").strip()
        q_lower = q.lower()

        if "project" in q_lower or "projects" in q_lower:
            projects = await session.scalars(select(Project).where(Project.user_id == user.id))
            items = list(projects.all())
            if not items:
                return "No projects found.", []
            text = "\n".join([f"- {p.title}: {p.description}" for p in items])
            return text, []

        if "technolog" in q_lower or "tech stack" in q_lower:
            projects = await session.scalars(select(Project).where(Project.user_id == user.id))
            techs: set[str] = set()
            for p in projects.all():
                for t in (p.tech_stack or "").split(","):
                    t = t.strip()
                    if t:
                        techs.add(t)
            if not techs:
                return "No technologies found.", []
            return "\n".join(sorted(techs)), []

        if "resume" in q_lower:
            portfolio = await session.scalar(select(Portfolio).where(Portfolio.user_id == user.id))
            if not portfolio or not portfolio.resume_url:
                return "No resume uploaded.", []

        results = await rag.search(
            user_id=str(user.id),
            query=q,
            top_k=5,
            embedder=embedder,
            qdrant=qdrant,
        )
        context_chunks = [r.text for r in results if r.text]
        if not context_chunks:
            return "I could not find relevant information in the indexed resume or RAG documents.", []

        context = "\n\n".join(context_chunks)
        prompt = (
            "You are an AI portfolio assistant.\n"
            "Answer based only on the provided context.\n\n"
            f"Context:\n{context}\n\n"
            f"User Question:\n{q}"
        )

        answer = await groq.generate(prompt)
        return answer, context_chunks
