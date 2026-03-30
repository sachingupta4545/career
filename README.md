# Portfolio SaaS (Multi‑tenant AI‑powered)

FastAPI backend where each user gets a chatbot that answers questions about their portfolio using RAG (Qdrant) and Groq LLM.

---

## Architecture (exact folder/file structure)

```
app/
  main.py

api/
  auth.py
  user.py
  portfolio.py
  rag.py
  chatbot.py
  deps.py

core/
  config.py
  security.py
  database.py

models/
  user.py
  portfolio.py
  project.py

schemas/
  user.py
  portfolio.py
  chatbot.py

services/
  auth_service.py
  user_service.py
  portfolio_service.py
  rag_service.py
  chatbot_service.py
  groq_service.py
  qdrant_service.py
  embedding_service.py
  storage_service.py
  pdf_service.py

utils/
  helpers.py
  chunking.py

db/
  session.py
  base.py
```

---

## Quick start

### 1) Env vars

Copy `.env.example` to `.env` and fill in:

```bash
cp .env.example .env
# Edit .env with your DATABASE_URL, JWT_SECRET_KEY, GROQ_API_KEY, QDRANT_URL
```

### 2) Install deps

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

### 3) Start services

- PostgreSQL (or another asyncpg‑compatible DB)
- Qdrant (default `http://localhost:6333`)

### 4) Run FastAPI

```bash
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for interactive API docs.

---

## APIs (summary)

### Auth
- `POST /auth/signup` – create user + blank portfolio profile
- `POST /auth/login` – JWT login (OAuth2PasswordRequestForm)

### User profile
- `GET /users/me` – current user profile (name, bio, avatar, resume)
- `PUT /users/me` – update name/bio
- `POST /users/me/avatar` – upload avatar (stored locally, S3‑ready)

### Portfolio + Projects
- `GET /portfolios/me` – profile view
- `PUT /portfolios/me` – update profile
- `POST /portfolios/me/resume` – upload resume PDF
- `GET /portfolios/me/projects` – list projects
- `POST /portfolios/me/projects` – add project
- `DELETE /portfolios/me/projects/{project_id}` – delete project

### RAG (ingestion + search)
- `POST /rag/ingest/text` – ingest plain text
- `POST /rag/ingest/qa` – ingest Q&A pairs
- `POST /rag/ingest/pdf` – ingest PDF (resume, docs)
- `POST /rag/search` – semantic search (filtered by user_id)

### Chatbot
- `POST /chatbot/chat` – intent routing + RAG fallback:
  - “projects” → DB data
  - “technologies” → tech stack
  - otherwise → RAG + Groq LLM

All APIs return `{success, data, message}`.

---

## Multi‑tenant design

- One Qdrant collection (`portfolio_rag`)
- Every vector stored with `user_id` in payload
- All searches filtered by `user_id` (strict isolation)

---

## RAG ingestion flow

Input → detect type:
- PDF → extract → clean → chunk → embed → store (source=pdf)
- Q&A → format “Q: … A: …” → embed → store (source=qa)
- Text → chunk → embed → store (source=text)

All vectors include `user_id` for tenant isolation.

---

## Chatbot intent + RAG fallback

1) Detect intent:
   - “projects” → return DB projects
   - “technologies” → return tech stack
   - otherwise → RAG

2) If RAG:
   - fetch context from Qdrant (user‑filtered)
   - build prompt with your template
   - call Groq API
   - return answer + context

---

## Storage abstraction

- `StorageService` saves avatars and resumes locally under `media/`
- Returns public URLs (`BASE_URL/media/...`)
- Designed to swap to S3 later without changing services

---

## Dependencies (key)

- `fastapi`, `uvicorn`, `sqlalchemy[asyncio]`, `asyncpg`
- `pydantic`, `pydantic-settings`, `python-jose`, `passlib`
- `qdrant-client`, `fastembed`, `pdfplumber`, `httpx`
- `aiofiles`, `python-multipart`

---

## Development notes

- All routes are thin; business logic lives in `services/`
- Async everywhere (SQLAlchemy, HTTP clients, file I/O)
- JWT auth via `api/deps.py:get_current_user`
- DB models imported in `core/database.py:init_db()` so `create_all` works
- App imports cleanly without env vars; errors only raised at runtime when needed

---

## Ready to use

- Signup → JWT → create profile → upload avatar/resume → add projects
- Ingest text/PDF/Q&A via `/rag/ingest/*`
- Ask questions via `/chatbot/chat` (intent + RAG + Groq)

Enjoy your AI‑powered portfolio SaaS!
