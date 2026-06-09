# Pressure Test

This document is used to challenge the product and technical plan before implementation expands too far.

It is split into:

1. Product Pressure Test
2. Technical Pressure Test

---

# 1. Product Pressure Test

## 1.1 Core User Value

Questions:

- Does this help students learn algorithms more systematically?
- Does it reduce confusion around learning order?
- Does it help users understand mistakes instead of only receiving answers?
- Does it make review and weak-point tracking easier?

Pass criteria:

- The MVP supports a visible learning loop.
- Users can move from topic learning to AI help to code diagnosis to learning record.
- Dashboard shows at least basic learning progress.

Risk signals:

- The product becomes only a generic chat UI.
- The product gives final answers too quickly.
- Users cannot see what to learn next.

## 1.2 Differentiation From Directly Asking ChatGPT

Questions:

- Why would a student use this instead of ChatGPT directly?
- Does the platform remember learning state?
- Does the platform organize algorithm knowledge?
- Does it connect AI answers with topics, mistakes, and progress?

Pass criteria:

- Knowledge map exists.
- AI interactions can be associated with topic/problem context.
- Learning records and Dashboard exist.
- Code diagnosis follows educational structure.

Risk signals:

- AI features are isolated and stateless.
- No learning history is captured.
- No topic or progress context is used.

## 1.3 MVP Scope Pressure

Questions:

- Is MVP v0.1 too large?
- Are we trying to build auth, OJ, admin, recommendation, and AI all at once?
- Can MVP v0.1 be completed in small, verifiable phases?

Pass criteria:

- MVP v0.1 is limited to Phase 0 through Phase 4.
- Phase 4.5 is stabilization only and does not add business features.
- Phase 5 and later are clearly treated as Post-MVP roadmap work.
- Full auth is not core MVP v0.1.
- OJ and code sandbox are deferred.
- Admin console is deferred.
- Recommendation engine starts as simple rules or placeholder.
- Each phase has clear acceptance criteria.

Risk signals:

- MVP v0.1 includes complete OJ.
- MVP v0.1 includes full admin UI.
- MVP v0.1 includes complex multi-user permissions.
- MVP v0.1 treats Phase 5+ as required completion work.
- MVP v0.1 cannot be manually verified after each phase.

## 1.4 Learning Loop Pressure

Target loop:

```text
Topic -> AI explanation -> code diagnosis -> learning record -> dashboard -> next step
```

Questions:

- Can a user complete this loop in MVP?
- Is each step visible in the UI?
- Is there a stored record after the user learns or reviews?
- Does Dashboard reflect user actions?

Pass criteria:

- Topic page exists.
- AI Q&A exists.
- Code review exists.
- Learning status update exists.
- Dashboard summary reflects learning data.

Risk signals:

- Dashboard is purely static for too long.
- Learning records are not connected to topics.
- AI responses are not connected to learning context.

## 1.7 Phase 4 Dashboard Loop Pressure

Questions:

- Does the Dashboard change after a topic learning status is updated?
- Can the user see overall progress, recent activity, review queue, and next steps?
- Are next steps deterministic and understandable?
- Is the Dashboard useful without becoming a flashy analytics screen?

Pass criteria:

- `/dashboard` reads real `GET /api/dashboard/summary` data.
- Status counts and category progress reflect current user learning records.
- Review queue uses existing learning records only.
- Next steps are rule-based and link back to topic detail pages.

Risk signals:

- Dashboard displays static placeholder numbers.
- Dashboard recommendations call AI Provider in Phase 4.
- Phase 4 creates new tables or migrations for review features.
- Empty states do not guide users back to the knowledge map.

## 1.8 Phase 4.5 MVP Stabilization Pressure

Questions:

- Can the MVP v0.1 loop be demonstrated end to end without adding new features?
- Are README, docs, environment notes, and manual demo steps aligned?
- Do the required commands pass in a clean local setup?
- Is demo seed data sufficient for the main loop?

Pass criteria:

- Phase 4.5 changes documentation, validation steps, and demo readiness only.
- No business API, schema, AI Provider behavior, auth, OJ, RAG, or problem persistence is added.
- The manual demo flow covers topic learning, AI help, code diagnosis, learning record update, Dashboard, and next step.
- Known limitations are documented clearly.

Risk signals:

- Phase 4.5 expands into Phase 5 features.
- Stabilization creates new tables or migrations.
- README commands do not match the implemented project.
- Demo flow requires undocumented manual setup.

## 1.5 Content Quality And Copyright

Questions:

- Are seed topics original or license-safe?
- Are external problems attributed?
- Are third-party statements avoided unless license allows?
- Are AI-generated problems clearly marked?

Pass criteria:

- MVP content is original or AI generated.
- AI-generated problems use `is_ai_generated=true`.
- External problems store metadata and `source_url`, not full copied statements by default.

Risk signals:

- Full third-party problem statements copied without license.
- No source attribution.
- Generated and external content are indistinguishable.

## 1.6 Teaching Quality

Questions:

- Does AI teach step by step?
- Does it avoid giving full solutions too early?
- Does it adapt to beginner and advanced modes?
- Does code diagnosis explain causes before fixes?

Pass criteria:

- Prompt templates enforce educational structure.
- Code review output includes bug cause and fix suggestion.
- Problem help gives hints before final code.

Risk signals:

- AI immediately outputs full accepted code.
- Explanations use unexplained jargon in beginner mode.
- Code review only rewrites code without diagnosis.

---

# 2. Technical Pressure Test

## 2.1 Health Check

Checks:

- Backend exposes `GET /api/health`.
- Health response includes service status.
- Optional checks for database and Redis can be added later.

MVP pass criteria:

- `GET /api/health` returns 200.
- Backend can start without AI provider configured.
- Failed AI configuration does not break health check.

## 2.2 Database Migration

Checks:

- Alembic migration can run on clean PostgreSQL.
- Models, schemas, and migrations are consistent.
- Seed data is separated from schema migration where practical.

Command planned for implementation phases:

```bash
cd backend
uv run alembic upgrade head
```

MVP pass criteria:

- Clean database migrates successfully.
- Required MVP tables exist.
- Old migrations are not edited casually.

## 2.3 Docker Compose

Expected services:

- frontend
- backend
- postgres
- redis

Expected ports:

- frontend: 3000
- backend: 8000
- postgres: 5432
- redis: 6379

Checks planned for implementation phases:

```bash
docker compose config
docker compose up -d postgres redis
```

MVP pass criteria:

- Compose config is valid.
- PostgreSQL starts.
- Redis starts.
- Backend can connect to PostgreSQL and Redis through Compose network.

## 2.4 Environment Configuration

Required fields include:

```env
APP_ENV=development
APP_NAME=AlgoMentor AI
LOG_LEVEL=INFO
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:3000
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=algomentor
POSTGRES_USER=algomentor
POSTGRES_PASSWORD=algomentor_password
DATABASE_URL=postgresql+psycopg://algomentor:algomentor_password@postgres:5432/algomentor
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0
ENABLE_DEV_USER=true
DEV_USER_ID=00000000-0000-0000-0000-000000000001
ENABLE_CODE_EXECUTION=false
AI_PROVIDER=openai_compatible
AI_BASE_URL=
AI_API_KEY=
AI_MODEL=
AI_TIMEOUT_SECONDS=60
AI_MAX_RETRIES=1
SECRET_KEY=change_me_in_production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

Pass criteria:

- No required runtime config is hardcoded.
- Frontend only receives public config.
- AI secrets are backend-only.

## 2.5 API Response

Checks:

- All backend APIs use `/api` prefix.
- Pydantic request and response schemas exist.
- List endpoints reserve pagination.
- Errors do not expose stack traces.

MVP APIs:

- `GET /api/health`
- `GET /api/topics`
- `GET /api/topics/{id}`
- `POST /api/learning/records`
- `GET /api/dashboard/summary`
- `POST /api/ai/chat`
- `POST /api/ai/code-review`
- `POST /api/ai/generate-problem`

Pass criteria:

- Main MVP endpoints respond with documented status codes.
- Invalid input returns reasonable 4xx response.
- Internal failure returns safe error message.

## 2.6 AI Timeout And Retry

Checks:

- AI calls use `AI_TIMEOUT_SECONDS`.
- AI calls use `AI_MAX_RETRIES`.
- Provider failure does not crash backend.
- AI logs store metadata only.

Pass criteria:

- Timeout is configurable.
- Retry is bounded.
- AI error is returned as safe API response.
- Full prompt, full code, and API keys are not saved in `ai_call_logs` by default.

## 2.6.1 Runtime AI Settings Safety

Checks:

- Runtime AI settings are disabled by default with `ENABLE_RUNTIME_AI_SETTINGS=false`.
- `PUT /api/settings/ai`, `DELETE /api/settings/ai`, and `POST /api/settings/ai/test` return `FEATURE_DISABLED` unless explicitly enabled.
- Runtime settings are stored only in backend process memory.
- API keys are not returned to the frontend, stored in the database, written to files, logged, or stored in browser storage.
- `base_url` accepts only `http` and `https`, and query string / fragment are removed.
- Docker Compose is not expanded in Phase 4.5; runtime settings are primarily for local backend startup mode.

Pass criteria:

- `/settings` clearly shows whether runtime editing is enabled.
- `/settings` distinguishes runtime, env, and missing configuration sources.
- Provider calls pick up runtime config changes without restarting the app.
- Settings tests clear runtime config after execution.

Risk signals:

- Runtime settings become a production secret-management system.
- API keys appear in responses, logs, browser storage, or committed files.
- Runtime settings require database tables or migrations.

## 2.7 Redis Readiness

MVP Redis usage may be light.

Checks:

- Redis starts in Docker Compose.
- Backend can connect to Redis if Redis integration is enabled.
- App does not fail catastrophically if optional Redis-dependent feature is unused.

Future use:

- rate limiting
- caching
- AI request state
- task queue
- session support

## 2.8 Frontend Quality

Checks:

- Pages handle loading state.
- Pages handle empty state.
- Pages handle error state.
- Code blocks are readable.
- Layout works on desktop and is usable on mobile.

MVP pages:

- `/dashboard`
- `/roadmap`
- `/topics`
- `/topics/[id]`
- `/chat`
- `/code-review`
- `/problems/generate`

Pass criteria:

- No page is a blank shell.
- User can understand the next action.
- UI is not a flashy dashboard without learning utility.

Phase 4 Dashboard checks:

- `/dashboard` handles loading, empty, error, and normal states.
- Overview stats include total, started, learning, mastered, not started, progress percent, and estimated minutes.
- Progress distribution and category progress use CSS progress bars, not a chart dependency.
- Recent activity, review queue, and next steps link to topic detail pages.
- The homepage links to `/dashboard` without adding auth, OJ, or admin entry points.

## 2.9 Future Concurrency And Rate Limiting

Not required in early MVP, but design must leave room for:

- concurrent AI requests
- per-user rate limiting
- per-IP rate limiting
- AI provider quota protection
- request queueing for code execution
- dashboard query optimization

Future pressure tests:

```text
10 concurrent AI chat requests
50 concurrent topic list requests
1000 learning_records rows dashboard query
Redis-backed rate limiting
AI timeout under provider delay
```

## 2.10 Code Execution Safety

MVP setting:

```env
ENABLE_CODE_EXECUTION=false
```

MVP pass criteria:

- No user code is executed on host machine.
- Code review uses AI analysis only.
- Any code execution endpoint is disabled, mocked, or absent.

Future requirements:

- Docker sandbox
- timeout
- memory limit
- network disabled
- filesystem restrictions
- language-specific runners
