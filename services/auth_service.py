from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import create_access_token, hash_password, verify_password
from models.portfolio import Portfolio
from models.user import User
from schemas.user import UserCreate


class AuthService:
    async def signup(self, session: AsyncSession, payload: UserCreate) -> User:
        existing = await session.scalar(select(User).where(User.email == payload.email))
        if existing is not None:
            raise ValueError("Email already registered")

        user = User(email=payload.email, hashed_password=hash_password(payload.password))
        session.add(user)
        await session.commit()
        await session.refresh(user)

        profile = Portfolio(user_id=user.id, name="", bio="", avatar_url="")
        session.add(profile)
        await session.commit()

        return user

    async def authenticate(self, session: AsyncSession, email: str, password: str) -> User:
        user = await session.scalar(select(User).where(User.email == email))
        if user is None or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        return user

    async def issue_token(self, user: User) -> str:
        return create_access_token(subject=str(user.id))
