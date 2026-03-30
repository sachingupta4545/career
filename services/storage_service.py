import os
import uuid

import aiofiles
from fastapi import UploadFile

from core.config import get_settings


class StorageService:
    async def save_avatar(self, user_id: str, file: UploadFile) -> str:
        settings = get_settings()

        media_root = settings.media_dir
        avatars_dir = os.path.join(media_root, "avatars", user_id)
        os.makedirs(avatars_dir, exist_ok=True)

        _, ext = os.path.splitext(file.filename or "")
        ext = (ext or ".bin").lower()
        filename = f"{uuid.uuid4().hex}{ext}"
        path = os.path.join(avatars_dir, filename)

        async with aiofiles.open(path, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                await out.write(chunk)

        base_url = settings.base_url.rstrip("/")
        url_path = f"/{media_root.strip('/')}/avatars/{user_id}/{filename}"
        return f"{base_url}{url_path}"

    async def save_resume(self, user_id: str, file: UploadFile) -> str:
        settings = get_settings()

        media_root = settings.media_dir
        resumes_dir = os.path.join(media_root, "resumes", user_id)
        os.makedirs(resumes_dir, exist_ok=True)

        _, ext = os.path.splitext(file.filename or "")
        ext = (ext or ".pdf").lower()
        filename = f"{uuid.uuid4().hex}{ext}"
        path = os.path.join(resumes_dir, filename)

        async with aiofiles.open(path, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                await out.write(chunk)

        base_url = settings.base_url.rstrip("/")
        url_path = f"/{media_root.strip('/')}/resumes/{user_id}/{filename}"
        return f"{base_url}{url_path}"
