from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.auth import router as auth_router
from api.chatbot import router as chatbot_router
from api.portfolio import router as portfolio_router
from api.rag import router as rag_router
from api.user import router as user_router
from core.config import get_settings
from core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(portfolio_router)
    app.include_router(rag_router)
    app.include_router(chatbot_router)

    os.makedirs(settings.media_dir, exist_ok=True)
    app.mount(f"/{settings.media_dir.strip('/')}", StaticFiles(directory=settings.media_dir), name="media")

    return app


app = create_app()
