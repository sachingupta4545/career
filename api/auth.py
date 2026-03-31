from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db_session
from schemas.user import ResponseEnvelope, Token, UserCreate, UserRead
from services.auth_service import AuthService


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


router = APIRouter(prefix="/auth", tags=["auth"])


def _raise_400(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


@router.post("/signup", response_model=ResponseEnvelope)
async def signup(
    payload: UserCreate,
    session: AsyncSession = Depends(get_db_session),
    service: AuthService = Depends(AuthService),
) -> ResponseEnvelope:
    try:
        user = await service.signup(session=session, payload=payload)
    except ValueError as exc:
        _raise_400(str(exc))

    return ResponseEnvelope(data=UserRead(id=user.id, email=user.email).model_dump(), message="Signup successful")


@router.post("/login", response_model=ResponseEnvelope)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
    service: AuthService = Depends(AuthService),
) -> ResponseEnvelope:
    try:
        user = await service.authenticate(session=session, email=payload.email, password=payload.password)
        token = await service.issue_token(user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return ResponseEnvelope(data=Token(access_token=token).model_dump(), message="Login successful")
