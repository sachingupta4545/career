from __future__ import annotations

import re
import uuid
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator

from core.security import BCRYPT_MAX_PASSWORD_BYTES


PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).+$")
PASSWORD_RULE_MESSAGE = (
    "Password must be 8-72 characters and include at least one uppercase letter, "
    "one lowercase letter, one number, and one special character."
)


class ResponseEnvelope(BaseModel):
    success: bool = True
    data: Any = None
    message: str = ""


class UserCreate(BaseModel):
    email: EmailStr = Field(
        description="User email address.",
        examples=["shine@example.com"],
    )
    password: str = Field(
        min_length=8,
        description=PASSWORD_RULE_MESSAGE,
        examples=["Shine@123"],
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
            raise ValueError("Password cannot be longer than 72 bytes.")
        if not PASSWORD_REGEX.match(value):
            raise ValueError(PASSWORD_RULE_MESSAGE)
        return value


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
