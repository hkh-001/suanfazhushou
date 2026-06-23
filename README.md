# AlgoMentor AI

AlgoMentor AI is a planned product-grade AI algorithm learning platform for students learning algorithms, data structures, and programming contest fundamentals.

The product is designed around a closed learning loop:

```text
knowledge map -> AI tutoring -> code diagnosis -> learning records -> dashboard feedback -> next step
```

## Current Stage

The project is currently in Post-MVP Phase 10: Minimal Isolated Judging System.

MVP v0.1 is defined as Phase 0 through Phase 4:

- Phase 0: Project Rules And Infrastructure Planning
- Phase 1: Engineering Skeleton
- Phase 2: Database And Knowledge Map
- Phase 3: AI Core Features
- Phase 4: Dashboard And Review Loop

MVP v0.1 remains complete at Phase 0 through Phase 4. Phase 4.5 focuses on stabilization, documentation sync, command verification, demo readiness, and frontend experience polish. Phase 5 and later are Post-MVP roadmap items, not required for MVP v0.1 completion.

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
- minimal auth with register, login, logout, current user, HttpOnly Cookie, and JWT
- personal problem bank with manual create, list, edit, delete, and topic association

It does not yet contain:

- mistake notebook
- OJ or code execution
- RBAC, OAuth, refresh token rotation, password reset, or production-grade permissions

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

`frontend/`, `backend/`, `judge/`, and `docker-compose.yml` now contain the Post-MVP Phase 10 isolated judging loop.

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

- Phase 5: Minimal Auth And User System
- Phase 6: Personal Problem Bank Basic
- Phase 7: Save AI-Generated Problems To Problem Bank
- Phase 8: Code Review Persistence And Mistake Notebook
- Phase 9: ZIP Problem Import With Test Cases
- Phase 10: Minimal Judging System
- Phase 11: AI Diagnosis After Failed Judgement
- Phase 12: Learning Recommendation And Weakness Analysis
- Phase 13: RAG Knowledge Retrieval
- Phase 14: Deployment, Security, Permissions, Production Hardening

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

Phase 5 auth APIs:

```text
POST http://localhost:8000/api/auth/register
POST http://localhost:8000/api/auth/login
POST http://localhost:8000/api/auth/logout
GET http://localhost:8000/api/auth/me
```

Phase 5 frontend pages:

```text
http://localhost:3000/login
http://localhost:3000/register
```

Minimal auth notes:

- Login state is stored in the backend-issued `algomentor_session` HttpOnly Cookie.
- The frontend sends API requests with credentials included and does not read or store the JWT.
- `ENABLE_DEV_USER=true` keeps the development user fallback when no Cookie is present.
- If a Cookie exists but is expired, invalid, or points to a missing user, the backend returns a safe auth error and does not fallback to the dev user.
- `SECRET_KEY=change-me-in-production-32-bytes-long!!` is for local development only. Production must use a unique strong secret of at least 32 bytes.
- Phase 5 does not implement RBAC, OAuth, refresh tokens, password reset, ZIP import, judging, OJ, or RAG.

Phase 6-9 problem bank APIs:

```text
POST http://localhost:8000/api/problems
GET http://localhost:8000/api/problems
GET http://localhost:8000/api/problems/{id}
PUT http://localhost:8000/api/problems/{id}
DELETE http://localhost:8000/api/problems/{id}
POST http://localhost:8000/api/problems/save-ai-generated
POST http://localhost:8000/api/problems/import/zip
```

Phase 6-9 problem bank frontend pages:

```text
http://localhost:3000/problems
http://localhost:3000/problems/new
http://localhost:3000/problems/{id}
http://localhost:3000/problems/import
```

Problem bank notes:

- Problems are owned by the current authenticated user.
- Problems display a per-user sequence number such as `#1`, `#2`, backed by `display_id`.
- Deleted problem numbers are not reused.
- The frontend does not send `user_id`; ownership comes from the backend session.
- `DELETE /api/problems/{id}` hard-deletes the user's own problem.
- Phase 7 supports explicit user-triggered saving from `/problems/generate` into the personal problem bank.
- Saved AI-generated problems use `is_ai_generated=true`, `source="ai_generated"`, and the same per-user `display_id` sequence as manual problems.
- Phase 9 supports explicit ZIP import into the current user's personal problem bank.
- Imported ZIP problems use `source="zip_import"`, `is_ai_generated=false`, `is_published=false`, and the same per-user `display_id` sequence.
- ZIP imports persist `.in` / `.out` files as `test_cases`, but do not execute them.
- Phase 10 consumes imported test cases through the isolated Judge service.
- Batch generation remains deferred.

Phase 8 code review and mistake notebook APIs:

```text
POST http://localhost:8000/api/code-reviews
GET http://localhost:8000/api/code-reviews
GET http://localhost:8000/api/code-reviews/{id}
DELETE http://localhost:8000/api/code-reviews/{id}

POST http://localhost:8000/api/mistakes
GET http://localhost:8000/api/mistakes
GET http://localhost:8000/api/mistakes/{id}
PUT http://localhost:8000/api/mistakes/{id}
DELETE http://localhost:8000/api/mistakes/{id}
```

Phase 8 frontend pages:

```text
http://localhost:3000/code-reviews
http://localhost:3000/code-reviews/{id}
http://localhost:3000/mistakes
http://localhost:3000/mistakes/new
http://localhost:3000/mistakes/{id}
```

Phase 8 notes:

- Code review records are saved only when the user explicitly clicks "save".
- Saved code reviews may store full code and full AI analysis as user-owned product data.
- `ai_call_logs` still store metadata only and must not store full code, prompts, or provider responses.
- Mistake notes are scoped to the current user and can optionally link to topics, personal problems, and saved code reviews.
- Phase 8 does not implement judging, submissions, test cases, ZIP import, RAG, OJ, code execution, or Dashboard recommendation analysis.

Phase 9 ZIP import notes:

- `POST /api/problems/import/zip` accepts a single `multipart/form-data` file field named `file`.
- ZIP packages must include `problem.json`, `statement.md`, and at least one `tests/{name}.in` / `tests/{name}.out` pair.
- Supported text files are `.json`, `.md`, `.in`, and `.out`; all text content must be UTF-8.
- The backend rejects path traversal, absolute paths, Windows drive paths, symbolic links, encrypted ZIP entries, duplicate logical paths, oversized archives, excessive file counts, and abnormal compression ratios.
- Phase 9 does not store the original ZIP file, run judging, create submissions, or execute uploaded content.

Phase 10 submission APIs:

```text
POST http://localhost:8000/api/submissions
GET http://localhost:8000/api/submissions/{id}
```

Phase 10 frontend pages:

```text
http://localhost:3000/problems/{id}/submit
http://localhost:3000/submissions/{id}
```

Phase 10 safety notes:

- `ENABLE_CODE_EXECUTION=false` remains the default.
- The backend never runs user code and does not mount the Docker socket.
- The separate Judge service starts one temporary, network-disabled, read-only runner container per submission.
- Runner containers receive CPU, memory, PID, output, workspace, per-case, and total-time limits.
- Only sample test-case content is returned to users; hidden inputs and expected outputs remain private.
- Full source code is stored as current-user-owned submission data and is not written to AI logs or sent to an AI provider.
- The Docker socket Judge design is for local development and controlled deployments. Production should use a separate Judge host or stronger sandbox boundary.
- Phase 10 does not implement AI diagnosis; that remains Phase 11.

To enable local judging, configure a strong shared token and explicitly enable execution before starting Compose:

```powershell
$env:JUDGE_INTERNAL_TOKEN="replace-with-a-strong-random-token"
$env:ENABLE_CODE_EXECUTION="true"
docker compose up --build
```

If the default Debian package mirror is unavailable while building the runner image, the optional `DEBIAN_MIRROR` and `DEBIAN_SECURITY_MIRROR` build variables may be set locally. They are not runtime secrets and are not hardcoded into the project.

Runtime AI settings:

- `GET /api/settings/ai` reports the current effective AI configuration source without returning the API key.
- `PUT /api/settings/ai`, `DELETE /api/settings/ai`, and `POST /api/settings/ai/test` are disabled by default.
- To enable runtime AI settings for local backend development or demos, set `ENABLE_RUNTIME_AI_SETTINGS=true` before starting FastAPI locally.
- Runtime AI settings are stored only in the current backend process memory. They are lost when the backend restarts.
- This feature is not production key management. Do not enable it on a public production deployment without authentication and a proper secret-management design.
- Docker Compose does not enable runtime AI settings; that local-demo feature remains off unless the backend is started with `ENABLE_RUNTIME_AI_SETTINGS=true`.

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

Judge unit tests:

```bash
cd judge
uv run pytest
```

Judge Docker security tests require Docker Desktop and the runner image:

```powershell
$env:DEBIAN_MIRROR="https://mirrors.tuna.tsinghua.edu.cn/debian"
$env:DEBIAN_SECURITY_MIRROR="https://mirrors.tuna.tsinghua.edu.cn/debian-security"
docker compose build judge-runner-image
cd judge
$env:RUN_JUDGE_DOCKER_TESTS="1"
uv run pytest
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

Current: Post-MVP Phase 10 Minimal Isolated Judging System.

Phase 4.5 should not add business features. It should focus on end-to-end acceptance, README and documentation checks, command verification, demo seed verification, and manual demo flow preparation.

Next: Phase 11 AI Diagnosis After Failed Judgement.

Later: AI Diagnosis, learning recommendation, RAG, and production hardening.

Phase 5 and later belong to the Post-MVP roadmap. Do not add OJ, code execution, mistake notebook, RAG, AI usage summary, or further problem-bank capabilities to MVP v0.1 without a separate phase plan.
