from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import UploadFile

from models.portfolio import Portfolio
from models.user import User
from schemas.portfolio import PortfolioUpdate
from services.storage_service import StorageService


class UserService:
    async def get_profile(self, session: AsyncSession, user: User) -> Portfolio:
        profile = await session.scalar(select(Portfolio).where(Portfolio.user_id == user.id))
        if profile is None:
            profile = Portfolio(user_id=user.id, name="", bio="", avatar_url="")
            session.add(profile)
            await session.commit()
            await session.refresh(profile)
        return profile

    async def update_profile(self, session: AsyncSession, user: User, payload: PortfolioUpdate) -> Portfolio:
        profile = await self.get_profile(session=session, user=user)

        if payload.name is not None:
            profile.name = payload.name
        if payload.bio is not None:
            profile.bio = payload.bio

        session.add(profile)
        await session.commit()
        await session.refresh(profile)
        return profile

    async def upload_avatar(
        self,
        session: AsyncSession,
        user: User,
        file: UploadFile,
        storage: StorageService,
    ) -> Portfolio:
        profile = await self.get_profile(session=session, user=user)
        url = await storage.save_avatar(user_id=str(user.id), file=file)
        profile.avatar_url = url
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
        return profile
