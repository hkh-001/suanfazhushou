# AlgoMentor AI

AlgoMentor AI is a planned product-grade AI algorithm learning platform for students learning algorithms, data structures, and programming contest fundamentals.

The product is designed around a closed learning loop:

```text
knowledge map -> AI tutoring -> code diagnosis -> learning records -> dashboard feedback -> next step
```

## Current Stage

The project is currently in the planning and project rules stage.

This repository currently contains only:

- project development rules
- product planning documents
- architecture documents
- database and API design drafts
- environment template
- ignore rules

It does not yet contain:

- frontend application code
- backend application code
- Docker Compose configuration
- database migrations
- business APIs

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

`frontend/`, `backend/`, and `docker-compose.yml` are intentionally not created yet.

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

## Next Step

The next implementation step is Phase 0 initialization. Before creating code, the exact file list, commands, and impact should be confirmed according to `AGENTS.md`.
