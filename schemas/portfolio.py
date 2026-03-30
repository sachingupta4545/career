import uuid

from pydantic import BaseModel, Field


class PortfolioRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    bio: str
    avatar_url: str
    resume_url: str


class PortfolioUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    bio: str | None = None


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    tech_stack: list[str] = []


class ProjectRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: str
    tech_stack: list[str]
