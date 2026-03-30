from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.portfolio import Portfolio
from models.project import Project
from models.user import User
from schemas.portfolio import PortfolioUpdate, ProjectCreate
from services.storage_service import StorageService


class PortfolioService:
    async def get_portfolio(self, session: AsyncSession, user: User) -> Portfolio:
        portfolio = await session.scalar(select(Portfolio).where(Portfolio.user_id == user.id))
        if portfolio is None:
            portfolio = Portfolio(user_id=user.id, name="", bio="", avatar_url="", resume_url="")
            session.add(portfolio)
            await session.commit()
            await session.refresh(portfolio)
        return portfolio

    async def update_portfolio(self, session: AsyncSession, user: User, payload: PortfolioUpdate) -> Portfolio:
        portfolio = await self.get_portfolio(session=session, user=user)
        if payload.name is not None:
            portfolio.name = payload.name
        if payload.bio is not None:
            portfolio.bio = payload.bio
        session.add(portfolio)
        await session.commit()
        await session.refresh(portfolio)
        return portfolio

    async def upload_resume(self, session: AsyncSession, user: User, file, storage: StorageService) -> Portfolio:
        portfolio = await self.get_portfolio(session=session, user=user)
        url = await storage.save_resume(user_id=str(user.id), file=file)
        portfolio.resume_url = url
        session.add(portfolio)
        await session.commit()
        await session.refresh(portfolio)
        return portfolio

    async def add_project(self, session: AsyncSession, user: User, payload: ProjectCreate) -> Project:
        tech_stack_str = ",".join([t.strip() for t in payload.tech_stack if t.strip()])
        project = Project(
            user_id=user.id,
            title=payload.title,
            description=payload.description or "",
            tech_stack=tech_stack_str,
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        return project

    async def list_projects(self, session: AsyncSession, user: User) -> list[Project]:
        result = await session.scalars(select(Project).where(Project.user_id == user.id).order_by(Project.title.asc()))
        return list(result.all())

    async def delete_project(self, session: AsyncSession, user: User, project_id) -> None:
        await session.execute(delete(Project).where(Project.user_id == user.id, Project.id == project_id))
        await session.commit()
