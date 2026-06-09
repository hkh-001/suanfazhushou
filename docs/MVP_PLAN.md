# MVP Plan

## MVP Goal

The first MVP should run through the core learning loop without building heavy systems too early.

Core loop:

```text
Topic -> AI explanation -> code diagnosis -> learning record -> dashboard -> next step
```

## MVP v0.1 Scope

MVP v0.1 prioritizes:

- knowledge map
- AI Q&A
- code diagnosis
- AI problem generation
- learning status records
- Dashboard basic statistics

MVP v0.1 may use:

- single-user mode
- default development user
- simplified auth placeholder

MVP v0.1 includes only:

- Phase 0: Project Rules And Infrastructure Planning
- Phase 1: Engineering Skeleton
- Phase 2: Database And Knowledge Map
- Phase 3: AI Core Features
- Phase 4: Dashboard And Review Loop

Phase 5 and later are Post-MVP roadmap items. They are not required for MVP v0.1 completion.

## MVP v0.1 Completion Criteria

MVP v0.1 is complete when the main learning loop can be demonstrated end to end:

```text
Topic -> AI explanation -> code diagnosis -> learning record -> dashboard -> next step
```

Required demonstration:

- user can browse published topics
- user can open a topic detail page
- user can ask AI for topic-aware explanation
- user can submit code for AI diagnosis
- user can update a topic learning record
- Dashboard reflects learning progress
- Dashboard shows rule-based next steps

MVP v0.1 does not require:

- OJ or code execution
- complete mistake notebook
- real registration/login or JWT auth
- RAG, embeddings, pgvector, or knowledge chunks
- complex recommendation engine
- persistent problem storage

## Explicitly Out Of Scope

MVP v0.1 should not include:

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

Make the learning loop visible through a Dashboard-first review loop.

### Expected Features

- learning progress summary
- topic completion statistics
- recent learning activity
- review queue based on existing learning records
- rule-based next steps

### Expected APIs

- `GET /api/dashboard/summary`

### Completion Criteria

- Dashboard reflects learning records
- user can see progress after updating topic status
- `/dashboard` page displays progress, category progress, recent activity, review queue, and next steps
- `GET /api/dashboard/summary` keeps Phase 2 fields and only appends Phase 4 fields
- next steps are rule-based and do not call AI Provider
- Phase 4 does not add database tables or migrations

### Not Included

- mistake notebook or `mistake_notes`
- recommendation logs
- complex recommendation engine
- full spaced repetition algorithm
- teacher/admin analytics
- AI usage summary

## Phase 4.5: MVP Stabilization

### Goal

Stabilize MVP v0.1 without adding business features.

### Expected Work

- end-to-end acceptance testing
- README startup and verification command review
- documentation synchronization
- `.env.example` consistency check
- Docker Compose configuration verification
- backend test suite verification
- frontend lint and build verification
- demo seed data verification
- manual demo flow documentation
- known limitations list

### Expected Commands

```bash
docker compose config
docker compose up -d postgres redis

cd backend
uv run alembic upgrade head
uv run python scripts/seed_topics.py
uv run python scripts/seed_prompt_templates.py
uv run pytest

cd frontend
pnpm lint
pnpm build
```

### Manual Demo Flow

```text
open /topics
-> open topic detail
-> update learning status
-> ask AI tutor from /chat
-> submit code to /code-review
-> generate practice prompt from /problems/generate
-> open /dashboard
-> verify progress and next steps
```

### Completion Criteria

- MVP v0.1 main loop can be demonstrated from UI.
- Required backend tests pass.
- Frontend lint and build pass.
- Docker Compose config is valid.
- README and docs match the implemented behavior.
- No secrets, caches, dependency folders, or build artifacts are tracked.

### Not Included

- new business APIs
- new frontend feature pages
- database schema changes
- Alembic migrations
- AI Provider behavior changes
- auth, OJ, RAG, mistake notebook, or problem persistence

## Phase Acceptance Rule

Each phase must end with:

- changed files summary
- implemented behavior summary
- run instructions
- test or verification instructions
- known limitations
- next recommended step

## Post-MVP Roadmap

The following phases are Post-MVP work. They are not required for MVP v0.1 completion.

### Phase 5: Code Review Persistence And Mistake Notebook

Planned direction:

- persist selected code review results only when explicitly saved by the user
- introduce mistake note workflows
- support root cause, fix suggestion, reflection, and review status
- connect mistake review back to Dashboard and review loop

Boundary:

- do not automatically store full user code without explicit product decision
- keep AI logs metadata-only by default

### Phase 6: Problem System And Practice Flow

Planned direction:

- introduce persisted `problems`
- connect problems to topics
- support AI-generated original problems as saved practice items
- add practice list/detail pages

Boundary:

- avoid copying third-party problem statements unless license allows
- keep external source metadata and attribution

### Phase 7: RAG Knowledge Retrieval

Planned direction:

- add retrieval-ready knowledge chunks
- improve AI context beyond single `topic_id`
- evaluate embeddings or PostgreSQL-compatible vector retrieval

Boundary:

- do not introduce RAG into MVP v0.1
- keep ContextBuilder extensible

### Phase 8: Code Execution / OJ Sandbox

Planned direction:

- add sandboxed code execution
- support timeout, memory limits, network restrictions, and filesystem isolation
- evaluate submission and judging workflow

Boundary:

- never execute untrusted user code on the host machine
- keep `ENABLE_CODE_EXECUTION=false` until sandboxing is explicitly implemented
