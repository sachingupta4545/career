from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    answer: str
    context: list[str] = []


class RagIngestTextRequest(BaseModel):
    text: str
    metadata: dict | None = None


class RagIngestQARequest(BaseModel):
    question: str
    answer: str
    metadata: dict | None = None


class RagSearchRequest(BaseModel):
    query: str
    top_k: int = 5


class RagSearchResult(BaseModel):
    text: str
    score: float
    source: str
    metadata: dict | None = None
