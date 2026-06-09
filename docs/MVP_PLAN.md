# MVP Plan

## MVP Goal

The first MVP should run through the core learning loop without building heavy systems too early.

Core loop:

```text
Topic -> AI explanation -> code diagnosis -> learning record -> dashboard -> next step
```

## MVP Scope

The MVP prioritizes:

- knowledge map
- AI Q&A
- code diagnosis
- AI problem generation
- learning status records
- Dashboard basic statistics

The MVP may use:

- single-user mode
- default development user
- simplified auth placeholder

## Explicitly Out Of Scope

The MVP should not include:

- full registration and login
- email verification
- complete RBAC permissions
- complete OJ judging
- Docker sandbox execution
- full admin console
- payment
- class or teacher system
- complex recommendation algorithm

## Phase 0: Project Rules And Infrastructure Planning

### Goal

Create project rules and documentation before initializing frontend or backend code.

### Expected Files

- `AGENTS.md`
- `README.md`
- `.env.example`
- `.gitignore`
- `docs/PRODUCT_BRIEF.md`
- `docs/ARCHITECTURE.md`
- `docs/MVP_PLAN.md`
- `docs/DATABASE_DESIGN.md`
- `docs/API_DESIGN.md`
- `docs/AI_PROMPTS.md`
- `docs/PRESSURE_TEST.md`

### Expected Commands

No application startup command is required in this phase.

### Completion Criteria

- Project development rules are documented.
- MVP scope is clear.
- Technical architecture is documented.
- Database and API design are drafted.
- No frontend or backend framework has been initialized.
- No business code exists.

### Not Included

- Next.js initialization
- FastAPI initialization
- Docker Compose file
- database migrations
- business APIs
- UI pages

## Phase 1: Engineering Skeleton

### Goal

Initialize frontend, backend, and infrastructure skeleton according to the documented rules.

### Expected Files

- `frontend/`
- `backend/`
- `docker-compose.yml`
- backend health check
- frontend placeholder app shell

### Expected Commands

Planned commands after implementation:

```bash
cd frontend
pnpm install

cd backend
uv sync
```

### Expected Access

- frontend: `http://localhost:3000`
- backend health: `http://localhost:8000/api/health`

### Completion Criteria

- frontend app can start
- backend app can start
- health check returns 200
- package managers follow rules: pnpm and uv only
- no business feature is overbuilt

### Not Included

- full auth
- AI provider calls
- real knowledge content
- database business tables beyond skeleton if not needed

## Phase 2: Database And Knowledge Map

### Goal

Implement core database schema and knowledge map APIs/pages.

### Expected Files

- SQLAlchemy models
- Pydantic schemas
- Alembic migrations
- topic seed data
- topics API routes
- topics frontend pages

### Expected APIs

- `GET /api/topics`
- `GET /api/topics/{id}`
- `GET /api/dashboard/summary`
- `POST /api/learning/records`

### Completion Criteria

- migrations run on clean PostgreSQL
- topics table contains seed data
- frontend lists topics
- topic detail page displays content
- learning records can be updated for default dev user
- Phase 2 only creates `users`, `topics`, `topic_dependencies`, and `learning_records`
- `/api/topics` returns only published topics with current user learning status
- `POST /api/learning/records` upserts by `(user_id, topic_id)`

### Not Included

- full registration/login
- OJ judging
- code execution
- complex recommendation
- AI Provider
- problem system
- mistake notebook
- Dashboard frontend page

## Phase 3: AI Core Features

### Goal

Implement AI service/provider abstraction and MVP AI capabilities.

### Expected Features

- AI Q&A
- code diagnosis
- AI problem generation
- prompt template loading
- AI call metadata logging
- ContextBuilder topic context injection

### Expected APIs

- `POST /api/ai/chat`
- `POST /api/ai/code-review`
- `POST /api/ai/generate-problem`

### Completion Criteria

- frontend never calls AI provider directly
- backend AI service handles timeout and failure safely
- prompt templates are not scattered in business logic
- AI logs store metadata only by default
- runtime prompt templates are read from `prompt_templates`, not file fallback
- generated problems are parsed as JSON and marked `is_ai_generated=true`

### Not Included

- streaming SSE
- multi-provider management UI
- complete prompt admin
- storing full user code in AI logs by default
- RAG, embeddings, pgvector, or knowledge chunks
- persistent problem storage
- chat history persistence

## Phase 4: Dashboard And Review Loop

### Goal

Make the learning loop visible through dashboard statistics and review records.

### Expected Features

- learning progress summary
- topic completion statistics
- basic weak-point or mistake summary
- recent learning activity

### Expected APIs

- `GET /api/dashboard/summary`
- mistake note APIs if included in this phase

### Completion Criteria

- Dashboard reflects learning records
- user can see progress after updating topic status
- review and next-step placeholders are visible

### Not Included

- complex recommendation engine
- full spaced repetition algorithm
- teacher/admin analytics

## Phase Acceptance Rule

Each phase must end with:

- changed files summary
- implemented behavior summary
- run instructions
- test or verification instructions
- known limitations
- next recommended step
