import re

import anyio
import pdfplumber
from fastapi import HTTPException, UploadFile, status


class PdfService:
    def validate_upload(self, file: UploadFile) -> None:
        filename = (file.filename or "").lower()
        content_type = (file.content_type or "").lower()
        if not filename.endswith(".pdf") and content_type not in {"application/pdf", "application/x-pdf"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported.",
            )

    async def extract_text(self, file: UploadFile) -> str:
        data = await file.read()

        def _extract() -> str:
            import io

            text_parts: list[str] = []
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text_parts.append(page_text)
            return "\n\n".join(text_parts)

        return await anyio.to_thread.run_sync(_extract)

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.replace("\x00", " ")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n[ \t]+", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"-\n", "", text)
        text = re.sub(r"(\w)\n(\w)", r"\1 \2", text)
        return text.strip()
