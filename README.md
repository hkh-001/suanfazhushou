# AlgoMentor AI

AlgoMentor AI is a planned product-grade AI algorithm learning platform for students learning algorithms, data structures, and programming contest fundamentals.

The product is designed around a closed learning loop:

```text
knowledge map -> AI tutoring -> code diagnosis -> learning records -> dashboard feedback -> next step
```

## Current Stage

The project is currently in Phase 4: Dashboard and review loop.

MVP v0.1 is defined as Phase 0 through Phase 4:

- Phase 0: Project Rules And Infrastructure Planning
- Phase 1: Engineering Skeleton
- Phase 2: Database And Knowledge Map
- Phase 3: AI Core Features
- Phase 4: Dashboard And Review Loop

The next step is Phase 4.5: MVP Stabilization. Phase 5 and later are Post-MVP roadmap items, not required for MVP v0.1 completion.

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
- local-only runtime AI settings page and API guarded by `ENABLE_RUNTIME_AI_SETTINGS`

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

## MVP v0.1 Focus

MVP v0.1 prioritizes:

- knowledge map
- AI Q&A
- code diagnosis
- AI problem generation
- learning status records
- Dashboard basic statistics

MVP v0.1 is complete when this loop can be demonstrated:

```text
Topic -> AI explanation -> code diagnosis -> learning record -> dashboard -> next step
```

MVP v0.1 should not prioritize:

- full registration and login
- complete OJ judging
- Docker sandbox execution
- full admin console
- complex recommendation algorithm

Post-MVP roadmap:

- Phase 5: Code Review Persistence And Mistake Notebook
- Phase 6: Problem System And Practice Flow
- Phase 7: RAG Knowledge Retrieval
- Phase 8: Code Execution / OJ Sandbox

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

Phase 4.5 settings page:

```text
http://localhost:3000/settings
```

Runtime AI settings:

- `GET /api/settings/ai` reports the current effective AI configuration source without returning the API key.
- `PUT /api/settings/ai`, `DELETE /api/settings/ai`, and `POST /api/settings/ai/test` are disabled by default.
- To enable runtime AI settings for local backend development or demos, set `ENABLE_RUNTIME_AI_SETTINGS=true` before starting FastAPI locally.
- Runtime AI settings are stored only in the current backend process memory. They are lost when the backend restarts.
- This feature is not production key management. Do not enable it on a public production deployment without authentication and a proper secret-management design.
- This phase does not modify `docker-compose.yml`; Docker Compose backend environment values remain explicit, so runtime AI settings are mainly documented for local backend startup mode.

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

AI secrets must stay backend-only. Do not put real AI keys in frontend code, browser storage, committed files, logs, or screenshots.

## Next Step

The next product implementation step is Phase 4.5: MVP Stabilization.

Phase 4.5 should not add business features. It should focus on end-to-end acceptance, README and documentation checks, command verification, demo seed verification, and manual demo flow preparation.

Phase 5 and later belong to the Post-MVP roadmap. Do not add auth, OJ, code execution, persistent problem storage, mistake notebook, RAG, or AI usage summary to MVP v0.1 without a separate phase plan.
