from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from db.session import get_db_session
from models.user import User
from schemas.portfolio import PortfolioRead, PortfolioUpdate
from schemas.user import ResponseEnvelope
from services.storage_service import StorageService
from services.user_service import UserService


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=ResponseEnvelope)
async def get_me(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(UserService),
) -> ResponseEnvelope:
    profile = await service.get_profile(session=session, user=current_user)
    data = PortfolioRead(
        id=profile.id,
        user_id=profile.user_id,
        name=profile.name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        resume_url=profile.resume_url,
    ).model_dump()
    return ResponseEnvelope(data=data, message="Profile fetched")


@router.put("/me", response_model=ResponseEnvelope)
async def update_me(
    payload: PortfolioUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(UserService),
) -> ResponseEnvelope:
    profile = await service.update_profile(session=session, user=current_user, payload=payload)
    data = PortfolioRead(
        id=profile.id,
        user_id=profile.user_id,
        name=profile.name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        resume_url=profile.resume_url,
    ).model_dump()
    return ResponseEnvelope(data=data, message="Profile updated")


@router.post("/me/avatar", response_model=ResponseEnvelope)
async def upload_avatar(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(UserService),
    storage: StorageService = Depends(StorageService),
) -> ResponseEnvelope:
    profile = await service.upload_avatar(session=session, user=current_user, file=file, storage=storage)
    data = PortfolioRead(
        id=profile.id,
        user_id=profile.user_id,
        name=profile.name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        resume_url=profile.resume_url,
    ).model_dump()
    return ResponseEnvelope(data=data, message="Avatar uploaded")
