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
