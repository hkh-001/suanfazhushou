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
- no production-grade permission system

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
Problem Bank -> ZIP Import -> Test Cases -> Judging
Judging -> Failed Submission -> AI Diagnosis
Mistake Notebook -> Weakness Analysis -> Recommendation
Content Scale -> RAG
```

Architecture boundaries:

- Auth should be introduced before personal problem banks, mistake notebooks, and submission history.
- Problem bank should exist before ZIP import and judging.
- ZIP import should validate problem packages and test cases before judging consumes them.
- Judging should be isolated as a sandbox or judge service. It must not be mixed into the normal AI code review service.
- AI diagnosis after failed judgement should consume judge results and limited failure context. It must not replace judge verdicts.
- Recommendation should build from owned user data such as learning records, mistakes, problems, and submissions.
- RAG should extend the existing ContextBuilder path through a RetrievalService. It should not rewrite AIService or bypass prompt template rules.

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

## Docker Service Planning

Planned Docker Compose services:

- `frontend`
- `backend`
- `postgres`
- `redis`

Planned ports:

- frontend: `3000`
- backend: `8000`
- postgres: `5432`
- redis: `6379`

Docker Compose is not created in the current documentation-only phase.

## Security Architecture

Security requirements:

- secrets loaded from environment variables
- AI API keys kept backend-only
- code execution disabled by default
- user input validated by backend schemas
- internal stack traces not exposed to frontend
- AI logs store metadata only by default
- untrusted user code must never run on the host machine
- code execution remains disabled until a sandbox/judge service is explicitly designed and approved
