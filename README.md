# AlgoMentor AI

AlgoMentor AI is a planned product-grade AI algorithm learning platform for students learning algorithms, data structures, and programming contest fundamentals.

The product is designed around a closed learning loop:

```text
knowledge map -> AI tutoring -> code diagnosis -> learning records -> dashboard feedback -> next step
```

## Current Stage

The project is currently in Phase 1: engineering skeleton initialization.

This repository currently contains:

- project development rules
- product planning documents
- architecture documents
- database and API design drafts
- environment template
- frontend engineering skeleton
- backend engineering skeleton
- Docker Compose service definitions

It does not yet contain:

- business APIs
- business pages
- database migrations
- database business tables
- AI Provider implementation
- authentication implementation
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

`frontend/`, `backend/`, and `docker-compose.yml` now contain only Phase 1 engineering skeletons.

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

Current local versions used for Phase 1:

- Node.js: `v24.14.0`
- pnpm: `10.33.0`
- Python: `3.11.9`
- uv: `0.11.2`

Version hint files:

- `.nvmrc`: Node major version
- `.python-version`: Python version

## Local Development

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

## Testing

Backend:

```bash
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

Docker Compose services use internal service names as hosts:

- `postgres`
- `redis`

When connecting from the local host machine, use:

- `localhost:5432` for PostgreSQL
- `localhost:6379` for Redis

Do not commit a real `.env` file. Use `.env.example` as the template.

## Next Step

The next product implementation step is Phase 2: database and knowledge map planning and implementation. Before creating database schema or business APIs, confirm the exact scope according to `AGENTS.md`.
