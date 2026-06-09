# AlgoMentor AI

AlgoMentor AI is a planned product-grade AI algorithm learning platform for students learning algorithms, data structures, and programming contest fundamentals.

The product is designed around a closed learning loop:

```text
knowledge map -> AI tutoring -> code diagnosis -> learning records -> dashboard feedback -> next step
```

## Current Stage

The project is currently in Phase 4: Dashboard and review loop.

This repository currently contains:

- project development rules
- product planning documents
- architecture documents
- database and API design drafts
- environment template
- frontend engineering skeleton
- backend engineering skeleton
- Docker Compose service definitions
- PostgreSQL schema for users, topics, topic dependencies, and learning records
- knowledge map APIs and pages
- AI tutoring, code diagnosis, and AI-generated practice prompt APIs and pages
- prompt template runtime loading and AI call metadata logs
- Dashboard page with learning progress, review queue, and rule-based next steps

It does not yet contain:

- authentication implementation
- persisted problem system
- mistake notebook
- OJ or code execution

## Planned Directory Structure

Planned future structure:

```text
.
├─ AGENTS.md
├─ README.md
├─ .env.example
├─ .gitignore
├─ docs/
│  ├─ PRODUCT_BRIEF.md
│  ├─ ARCHITECTURE.md
│  ├─ MVP_PLAN.md
│  ├─ DATABASE_DESIGN.md
│  ├─ API_DESIGN.md
│  ├─ AI_PROMPTS.md
│  └─ PRESSURE_TEST.md
├─ frontend/
├─ backend/
└─ docker-compose.yml
```

`frontend/`, `backend/`, and `docker-compose.yml` now contain the Phase 4 learning dashboard loop.

## MVP Focus

The first MVP should prioritize:

- knowledge map
- AI Q&A
- code diagnosis
- AI problem generation
- learning status records
- Dashboard basic statistics

The first MVP should not prioritize:

- full registration and login
- complete OJ judging
- Docker sandbox execution
- full admin console
- complex recommendation algorithm

## Planned Engineering Standards

Frontend:

- Next.js 15
- TypeScript
- Tailwind CSS
- shadcn/ui
- pnpm only

Backend:

- FastAPI
- Python 3.11+
- SQLAlchemy 2.x
- Alembic
- Pydantic
- uv only

Infrastructure:

- PostgreSQL
- Redis
- Docker Compose

AI:

- backend-only AI provider calls
- OpenAI-compatible provider first
- prompt templates managed independently
- metadata-only AI call logs by default

## Runtime Versions

Current local versions used for development:

- Node.js: `v24.14.0`
- pnpm: `10.33.0`
- Python: `3.11.9`
- uv: `0.11.2`

Version hint files:

- `.nvmrc`: Node major version
- `.python-version`: Python version

## Local Development

Database:

```bash
docker compose up -d postgres redis
```

Docker Compose services use internal service names as hosts:

- `postgres`
- `redis`

When running Alembic or FastAPI directly from the host machine, use `localhost` for PostgreSQL. The default backend settings already use:

```text
postgresql+psycopg://algomentor:algomentor_password@localhost:5432/algomentor?connect_timeout=5
```

When running inside Docker Compose, `docker-compose.yml` injects:

```text
postgresql+psycopg://algomentor:algomentor_password@postgres:5432/algomentor?connect_timeout=5
```

Migrations and seed:

```bash
cd backend
uv run alembic upgrade head
uv run python scripts/seed_topics.py
uv run python scripts/seed_prompt_templates.py
```

Frontend:

```bash
cd frontend
pnpm install
pnpm dev
```

Frontend URL:

```text
http://localhost:3000
```

Backend:

```bash
cd backend
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend health check:

```text
http://localhost:8000/api/health
```

Phase 2 APIs:

```text
GET http://localhost:8000/api/topics
GET http://localhost:8000/api/topics/{id}
POST http://localhost:8000/api/learning/records
GET http://localhost:8000/api/dashboard/summary
```

Phase 4 expands `GET /api/dashboard/summary` while keeping the Phase 2 top-level fields compatible. It now returns learning progress counts, estimated minutes, category progress, recent activity, review queue, and rule-based next steps. Recommendations do not call the AI provider.

Phase 3 APIs:

```text
POST http://localhost:8000/api/ai/chat
POST http://localhost:8000/api/ai/code-review
POST http://localhost:8000/api/ai/generate-problem
```

Phase 2 frontend pages:

```text
http://localhost:3000
http://localhost:3000/topics
http://localhost:3000/topics/{id}
```

Phase 3 frontend pages:

```text
http://localhost:3000/chat
http://localhost:3000/code-review
http://localhost:3000/problems/generate
```

Phase 4 frontend page:

```text
http://localhost:3000/dashboard
```

## Testing

Backend:

```bash
docker compose up -d postgres
cd backend
uv run pytest
```

Frontend:

```bash
cd frontend
pnpm lint
pnpm build
```

Docker Compose config check:

```bash
docker compose config
```

Docker Compose startup:

```bash
docker compose up --build
```

## Environment Notes

Do not commit a real `.env` file. Use `.env.example` as the template.

## Next Step

The next product implementation step is Phase 5 planning. Do not add auth, OJ, code execution, persistent problem storage, mistake notebook, or AI usage summary without a separate phase plan.
