# Architecture

## System Overview

AlgoMentor AI uses a separated frontend/backend architecture.

Main components:

- frontend web app
- backend API service
- PostgreSQL database
- Redis service
- AI provider layer

## Technology Stack

Frontend:

- Next.js 15
- TypeScript
- Tailwind CSS
- shadcn/ui
- Recharts or ECharts
- pnpm

Backend:

- FastAPI
- Python 3.11+
- SQLAlchemy 2.x
- Alembic
- Pydantic
- uv

Data:

- PostgreSQL
- Redis

Deployment:

- Docker Compose

## Frontend Layers

Recommended frontend structure:

```text
app routes
-> feature modules
-> shared components
-> API client
-> shared types
```

Frontend rules:

- Call backend through an API client layer.
- Do not call AI providers directly.
- Keep pages readable and product-grade.
- Handle loading, empty, and error states.

## Backend Layers

Recommended backend structure:

```text
router
-> schema
-> service
-> repository
-> model
-> database
```

Backend rules:

- Use `/api` prefix.
- Use Pydantic for request and response models.
- Use SQLAlchemy models for database mapping.
- Use Alembic for schema migrations.
- Keep business logic out of routers where practical.

## Minimal Auth Architecture

Post-MVP Phase 5 adds minimal auth without adding new database tables.

Auth components:

```text
Auth Router
-> Auth Schemas
-> Auth Service
-> User Repository
-> User Model
```

Session model:

- Backend issues an HttpOnly `algomentor_session` Cookie.
- Cookie value is a JWT access token.
- Frontend sends requests with `credentials: include`.
- Frontend must not read, store, or log the token.
- `get_current_user` reads the Cookie and returns a real `User` ORM object.
- Dev user fallback is allowed only when the Cookie is missing and `ENABLE_DEV_USER=true`.
- Expired, invalid, or missing-user tokens return auth errors and do not fallback to the dev user.

Phase 5 auth boundaries:

- no RBAC
- no OAuth
- no refresh token rotation
- no sessions table
- no password reset

Phase 13 student profile extension:

- Auth keeps the same HttpOnly Cookie and JWT session mechanism.
- Registration and login use `student_id` as the user-facing account.
- `email` and `username` remain compatibility fields, not primary login fields.
- `current_level`, `goal_track`, and optional `goal_description` live on `users` for the first profile version.
- AI ContextBuilder may add a short profile summary to prompts, but must not inject full learning history or store full prompts in logs.
- no production-grade permission system

Phase 18 profile-aware context extension:

- ContextBuilder combines the student profile with a concise active-ladder progress summary.
- The summary is used only as learning background and is character-truncated.
- It must not include full ladder material, practice answer keys, exam answer keys, full exam payloads, or full learning history.
- AI call logs continue to store metadata only.

Phase 16 minimal role extension:

- `users.role` is limited to `user` and `admin`.
- Registered students and the optional dev fallback user are `user` by default.
- The seeded `admin` account is created by `scripts/seed_admin.py` only when `DEV_ADMIN_PASSWORD` is configured.
- Role checks are enforced in backend services; frontend role checks are only presentation hints.
- This is not a classroom, teacher, or full RBAC system.

## Personal Problem Bank Architecture

Post-MVP Phase 6 adds a user-owned problem bank using the existing backend layering pattern:

```text
router -> schema -> service -> repository -> model
```

Rules:

- Problem ownership is enforced with `created_by_user_id` from `get_current_user`.
- The frontend never sends `user_id` to choose ownership.
- Problem bank CRUD is independent from judging, submissions, ZIP import, and AI generation persistence.
- `problem_tags` links personal problems to currently visible published topics.
- Future AI-generated problem saving should reuse the problem service instead of bypassing ownership checks.
- Future judging must remain a separate sandbox/judge service and must not be mixed into ordinary problem CRUD.

Phase 16 public problem extension:

- `problems.is_public=false` remains the personal problem-bank default.
- `problems.is_public=true` marks admin-maintained public problems visible to all authenticated users.
- Normal users may view and submit public problems but cannot create, edit, or delete them.
- Admin users may create, edit, and delete public problems.
- Problem detail responses include backend-computed `can_edit` and `can_delete`; the frontend should not infer these permissions itself.

## AI Provider Abstraction

All AI calls must go through backend services.

Recommended structure:

```text
AIService
├─ ChatService
├─ CodeReviewService
├─ ProblemGenerationService
├─ PromptTemplateService
└─ Provider Adapter
   ├─ OpenAICompatibleProvider
   ├─ DeepSeekProvider
   ├─ QwenProvider
   └─ KimiProvider
```

MVP should implement OpenAI-compatible provider behavior first.

AI provider requirements:

- configurable base URL
- configurable model
- configurable timeout
- bounded retries
- metadata logging
- safe error handling

Frontend must never call model providers directly. New AI features, including Post-MVP judging diagnosis and RAG-enhanced tutoring, must continue to use the backend service/provider layer.

## Prompt Template Architecture

Prompt templates should be stored as files for seed/default versions and in the database for active runtime versions.

Recommended file location:

```text
backend/app/prompts/templates/
```

The database table `prompt_templates` should reference:

- `template_key`
- `file_path`
- `version`
- `enabled`

## Post-MVP Dependency Architecture

Post-MVP work should follow these dependency paths:

```text
Auth -> Personal Data Ownership
Student Profile -> Profile-Aware AI Context
Problem Bank -> ZIP Import -> Test Cases -> Judging
Judging -> Failed Submission -> AI Diagnosis
Mistake Notebook -> Weakness Analysis -> Recommendation
Student Profile -> Ladder Templates -> Ladder Progress -> Ladder Exams
Profile + Ladder Progress -> OpenMAIC Interactive Classroom POC
OpenMAIC POC -> Topic/Ladder Interactive Lessons
Content Scale -> RAG
```

Architecture boundaries:

- Auth should be introduced before personal problem banks, mistake notebooks, and submission history.
- Student profile should be introduced before ladder paths and profile-aware AI generation.
- Problem bank should exist before ZIP import and judging.
- ZIP import should validate problem packages and test cases before judging consumes them.
- Judging should be isolated as a sandbox or judge service. It must not be mixed into the normal AI code review service.
- AI diagnosis after failed judgement should consume judge results and limited failure context. It must not replace judge verdicts.
- Recommendation should build from owned user data such as learning records, mistakes, problems, and submissions.
- OpenMAIC integration should use an adapter and optional external service boundary. It should not replace AIService, PromptRenderer, user auth, ladder progress rules, or backend-owned permission checks.
- RAG should extend the existing ContextBuilder path through a RetrievalService. It should not rewrite AIService or bypass prompt template rules.

## Phase 10 Isolated Judge Architecture

```text
Frontend
-> Backend Submission API
-> Internal Judge HTTP API
-> Temporary Runner Container
-> Submission Persistence
```

- Backend validates auth, problem ownership, feature flags, and response schemas.
- Judge owns Docker lifecycle and never connects to PostgreSQL or AI providers.
- Backend and frontend never mount the Docker socket.
- Runner containers have no network, a read-only root filesystem, bounded tmpfs workspace, and CPU/memory/PID/output/time limits.
- `ENABLE_CODE_EXECUTION=false` is the default and `/api/health` does not depend on Judge.
- The Docker socket approach is limited to local development and controlled deployments; production should isolate Judge on a separate host or stronger sandbox platform.

## Phase 11 Failed Submission Diagnosis

```text
Submission Detail
-> Submission ownership and verdict validation
-> ContextBuilder bounded diagnosis context
-> PromptRenderer database template
-> AI Provider
-> Temporary frontend result
-> Optional explicit code_review save
```

- Phase 11 consumes only persisted verdicts and never calls Judge or executes code.
- Judge truth remains authoritative; accepted and internal-error results are not diagnosed.
- ContextBuilder excludes hidden case names and content before Prompt rendering.
- Problem solutions, standard code, and hints are not included in diagnosis context.
- AI results are temporary by default and reuse the Phase 8 explicit code-review save path.
- No diagnosis table, submission-to-code-review foreign key, RAG, or automatic mistake-note creation is introduced.

## Phase 12 Rule-Based Recommendation Architecture

```text
Dashboard API
-> Learning records
-> Mistake notes
-> Failed submissions
-> Personal problem bank
-> Rule-based weakness scoring
-> Dashboard recommendation sections
```

- Phase 12 recommendations are computed synchronously in the Dashboard service.
- No `recommendation_logs` table is created in Phase 12.
- No AI Provider, Prompt template, RetrievalService, embedding, pgvector, or RAG path is used.
- Recommendations are scoped to the current user and remain explainable through visible signals.
- Existing `review_queue` and `next_steps` remain learning-record/path recommendations; Phase 12 `recommendation_actions` add mistake/submission-driven actions.
- Phase 18 adds active-ladder progress to the Dashboard summary and may add ladder-node recommendation actions.
- Ladder recommendation actions are computed from current-user ladder progress and submitted exam attempts; they do not call AI or prompt templates.

## Phase 14-17 Learning Ladder Architecture

```text
Student profile
-> Ladder template selection
-> Active learning path
-> Expanded path nodes
-> Seeded practice items copied into nodes
-> AI-generated exam attempt
-> Deterministic backend scoring
-> Node progress booleans
-> /ladder page
```

- Phase 14 stores templates in `ladder_templates` and seeds them through `scripts/seed_ladder_templates.py`.
- Each user can have one active `learning_paths` row.
- A path expands template nodes into `learning_path_nodes` and creates `node_user_progress` rows for that user.
- Phase 15 copies seeded `practice_items` into `learning_path_nodes` during path creation; existing paths do not automatically update when templates change.
- Node status is computed in the ladder service instead of stored as a `status` column.
- The first node is unlocked by default.
- Phase 17 changes the unlock rule: node N+1 unlocks only after node N has `exam_passed=true`.
- Phase 14 updates `material_completed`; Phase 15 updates `practice_completed`.
- `material_completed` and `practice_completed` are prerequisites for generating the Phase 17 node exam.
- Choice practice is scored synchronously by the ladder service.
- Coding practice is self-check only and never reaches the Judge, submission service, AI Provider, or code execution path.
- No practice attempt history is stored in Phase 15.
- Phase 17 stores AI-generated exams in `ladder_exam_attempts`; unsubmitted attempts are reused.
- AI only generates exam questions. The backend validates the JSON payload and scores submitted answers from the stored answer key.
- Phase 17 code questions are code reading or code completion multiple-choice questions, not executable programs.
- Passing an exam at 80 or above sets `exam_passed=true` and unlocks the next node.
- Ladder exams do not call Judge, create submissions, run user code, use RetrievalService/RAG, or call recommendation services.
- External resource links are displayed only and are not fetched or copied by the backend.
- Phase 18 allows Dashboard links to target `/ladder?node_id=...`; the ladder page validates the node against the current user's summary and falls back safely.

Future OpenMAIC shape:

```text
Frontend topic/ladder action
-> Backend interactive lesson API
-> OpenMAIC Adapter
-> External OpenMAIC service
-> Stored lesson job/status/url metadata
```

OpenMAIC integration boundaries:

- OpenMAIC starts as an optional feature-flagged external service, not copied into the main frontend.
- The frontend should call AlgoMentor backend APIs, not OpenMAIC directly.
- The backend must not send student ids, full source code, hidden tests, exam answer keys, full exam payloads, or full learning history to OpenMAIC.
- OpenMAIC provider keys, access codes, and service URLs stay backend-side or in the OpenMAIC service environment.
- Topic and ladder lesson generation must be explicit user actions and should tolerate OpenMAIC timeouts/failures without affecting core learning flows.

Future RAG shape:

```text
AIService
-> ContextBuilder
-> RetrievalService
-> PromptRenderer
-> Provider Adapter
```

Future judging shape:

```text
Backend API
-> Submission Service
-> Judge/Sandbox Service
-> Result Persistence
-> Optional AI Diagnosis Service
```

## Docker Services

Current Docker Compose services:

- `frontend`
- `backend`
- `postgres`
- `redis`
- `judge`
- `judge-runner-image`

Ports:

- frontend: `3000`
- backend: `8000`
- postgres: `5432`
- redis: `6379`
- Judge health/internal API: `127.0.0.1:9000`

Only `judge` mounts the Docker socket. `backend` reaches Judge through the internal network and never receives Docker control access.

## Security Architecture

Security requirements:

- secrets loaded from environment variables
- AI API keys kept backend-only
- code execution disabled by default
- user input validated by backend schemas
- internal stack traces not exposed to frontend
- AI logs store metadata only by default
- untrusted user code must never run on the host machine
- code execution remains disabled by default and may be enabled only when the isolated Judge service and shared internal token are configured
