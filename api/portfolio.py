import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from db.session import get_db_session
from models.user import User
from schemas.portfolio import PortfolioRead, PortfolioUpdate, ProjectCreate, ProjectRead
from schemas.user import ResponseEnvelope
from services.portfolio_service import PortfolioService
from services.storage_service import StorageService

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get("/me", response_model=ResponseEnvelope)
async def get_my_portfolio(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(PortfolioService),
) -> ResponseEnvelope:
    p = await service.get_portfolio(session=session, user=current_user)
    data = PortfolioRead(
        id=p.id,
        user_id=p.user_id,
        name=p.name,
        bio=p.bio,
        avatar_url=p.avatar_url,
        resume_url=p.resume_url,
    ).model_dump()
    return ResponseEnvelope(data=data, message="Portfolio fetched")


@router.put("/me", response_model=ResponseEnvelope)
async def update_my_portfolio(
    payload: PortfolioUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(PortfolioService),
) -> ResponseEnvelope:
    p = await service.update_portfolio(session=session, user=current_user, payload=payload)
    data = PortfolioRead(
        id=p.id,
        user_id=p.user_id,
        name=p.name,
        bio=p.bio,
        avatar_url=p.avatar_url,
        resume_url=p.resume_url,
    ).model_dump()
    return ResponseEnvelope(data=data, message="Portfolio updated")


@router.post("/me/resume", response_model=ResponseEnvelope)
async def upload_resume(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(PortfolioService),
    storage: StorageService = Depends(StorageService),
) -> ResponseEnvelope:
    p = await service.upload_resume(session=session, user=current_user, file=file, storage=storage)
    data = PortfolioRead(
        id=p.id,
        user_id=p.user_id,
        name=p.name,
        bio=p.bio,
        avatar_url=p.avatar_url,
        resume_url=p.resume_url,
    ).model_dump()
    return ResponseEnvelope(data=data, message="Resume uploaded")


@router.get("/me/projects", response_model=ResponseEnvelope)
async def list_projects(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(PortfolioService),
) -> ResponseEnvelope:
    projects = await service.list_projects(session=session, user=current_user)
    data = [
        ProjectRead(
            id=p.id,
            user_id=p.user_id,
            title=p.title,
            description=p.description,
            tech_stack=[t for t in (p.tech_stack or "").split(",") if t],
        ).model_dump()
        for p in projects
    ]
    return ResponseEnvelope(data=data, message="Projects fetched")


@router.post("/me/projects", response_model=ResponseEnvelope)
async def add_project(
    payload: ProjectCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(PortfolioService),
) -> ResponseEnvelope:
    p = await service.add_project(session=session, user=current_user, payload=payload)
    data = ProjectRead(
        id=p.id,
        user_id=p.user_id,
        title=p.title,
        description=p.description,
        tech_stack=[t for t in (p.tech_stack or "").split(",") if t],
    ).model_dump()
    return ResponseEnvelope(data=data, message="Project added")


@router.delete("/me/projects/{project_id}", response_model=ResponseEnvelope)
async def delete_project(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(PortfolioService),
) -> ResponseEnvelope:
    await service.delete_project(session=session, user=current_user, project_id=project_id)
    return ResponseEnvelope(data={}, message="Project deleted")
