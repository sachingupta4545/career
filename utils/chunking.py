import re


SECTION_KEYWORDS: dict[str, list[str]] = {
    "summary": ["summary", "professional summary", "profile", "about me", "objective"],
    "experience": ["experience", "work experience", "employment", "professional experience", "work history"],
    "education": ["education", "academic background", "degrees", "qualifications"],
    "skills": ["skills", "technical skills", "core competencies", "technologies", "expertise"],
    "projects": ["projects", "personal projects", "key projects", "portfolio"],
    "certifications": ["certifications", "certificates", "licenses"],
    "achievements": ["achievements", "awards", "accomplishments"],
    "contact": ["contact", "contact details"],
}


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(0, end - overlap)
    return [chunk for chunk in chunks if chunk]


def _normalize_lines(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"\n[ \t]+", "\n", normalized)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return [line.strip() for line in normalized.split("\n") if line.strip()]


def _detect_section_header(line: str) -> str | None:
    line_lower = line.lower().strip(":- ")
    for section, keywords in SECTION_KEYWORDS.items():
        if any(keyword == line_lower or keyword in line_lower for keyword in keywords):
            return section

    compact = re.sub(r"[^A-Za-z ]", "", line).strip()
    if compact and compact.isupper() and len(compact) <= 40:
        return compact.lower().replace(" ", "_")

    return None


def semantic_chunk_text(
    text: str,
    *,
    min_section_length: int = 50,
    fallback_chunk_size: int = 800,
    fallback_overlap: int = 100,
) -> list[dict]:
    lines = _normalize_lines(text)
    if not lines:
        return []

    chunks: list[dict] = []
    current_section = "header"
    current_lines: list[str] = []

    for line in lines:
        section = _detect_section_header(line)
        if section and current_lines:
            content = "\n".join(current_lines).strip()
            if len(content) >= min_section_length:
                chunks.append({"section": current_section, "content": content})
            current_section = section
            current_lines = [line]
            continue

        if section and not current_lines:
            current_section = section

        current_lines.append(line)

    if current_lines:
        content = "\n".join(current_lines).strip()
        if len(content) >= min_section_length:
            chunks.append({"section": current_section, "content": content})

    if chunks:
        return chunks

    return [
        {"section": f"chunk_{index}", "content": chunk}
        for index, chunk in enumerate(chunk_text(text, chunk_size=fallback_chunk_size, overlap=fallback_overlap))
        if len(chunk) >= min_section_length
    ]
