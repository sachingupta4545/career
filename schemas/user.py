from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class ResponseEnvelope(BaseModel):
    success: bool = True
    data: Any = None
    message: str = ""


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
