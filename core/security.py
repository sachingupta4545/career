from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from core.config import get_settings


BCRYPT_MAX_PASSWORD_BYTES = 72
PASSWORD_TOO_LONG_MESSAGE = (
    "Password must be between 8 and 72 bytes when encoded as UTF-8."
)


def validate_password_length(password: str) -> None:
    """Raise ValueError if the password exceeds bcrypt's 72-byte hard limit."""
    if len(password.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(PASSWORD_TOO_LONG_MESSAGE)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt after validating its byte length."""
    validate_password_length(password)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash.

    Returns False (rather than raising) when the password is too long,
    so callers don't leak which constraint was violated.
    """
    try:
        validate_password_length(plain_password)
    except ValueError:
        return False
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    expire_minutes = expires_minutes or settings.access_token_expire_minutes
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expire_minutes)
    to_encode: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
