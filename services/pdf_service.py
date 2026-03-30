import re

import anyio
import pdfplumber
from fastapi import UploadFile


class PdfService:
    async def extract_text(self, file: UploadFile) -> str:
        data = await file.read()

        def _extract() -> str:
            text_parts: list[str] = []
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text_parts.append(page_text)
            return "\n".join(text_parts)

        import io

        return await anyio.to_thread.run_sync(_extract)

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.replace("\x00", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()
