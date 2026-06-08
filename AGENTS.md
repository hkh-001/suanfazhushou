# AGENTS.md

## Project Identity

Project name: AlgoMentor AI

AlgoMentor AI is a formal product-grade AI algorithm learning platform, not a throwaway demo.

The platform focuses on building a closed learning loop:

1. Knowledge map
2. AI tutoring
3. Code diagnosis
4. AI problem generation
5. Learning records
6. Dashboard statistics
7. Review and next-step recommendation

## Tech Stack

Frontend:

- Next.js 15
- TypeScript
- Tailwind CSS
- shadcn/ui
- Recharts or ECharts
- pnpm only

Backend:

- FastAPI
- Python 3.11+
- SQLAlchemy 2.x
- Alembic
- Pydantic
- PostgreSQL
- Redis
- uv only

AI:

- OpenAI-compatible API first
- Provider abstraction required
- Prompt templates must be managed independently
- AI calls must go through backend service/provider layer

Deployment:

- Docker Compose
- Separate services for frontend, backend, postgres, redis

## Naming Rules

Even if the project path contains Chinese characters, all technical identifiers must use English only:

- package names
- Docker service names
- Python modules
- environment variables
- database tables
- database columns
- migration names
- API paths
- frontend route segments
- config keys

Recommended names:

- Project display name: AlgoMentor AI
- App/package name: algomentor
- Database name: algomentor
- Docker services: frontend, backend, postgres, redis
- Python backend module: app

## Before Implementation

Before writing or changing code, Codex must:

1. Read the current project structure.
2. Confirm the current task phase and scope.
3. List the files expected to be created or modified.
4. Briefly explain the implementation plan.
5. Identify whether the task affects:
   - architecture
   - dependencies
   - database schema
   - Docker configuration
   - authentication
   - AI Provider behavior
   - API contracts

If the task affects architecture, dependencies, database schema, Docker, authentication, or AI Provider behavior, Codex must explain the impact before implementation.

## MVP Priority

MVP must prioritize:

1. Knowledge map
2. AI Q&A
3. Code diagnosis
4. AI problem generation
5. Learning status records
6. Dashboard basic statistics

MVP may use:

- single-user mode
- default development user
- simplified auth placeholder

MVP must not prioritize:

- full registration/login
- email verification
- full admin console
- full OJ judging
- Docker sandbox execution
- payment
- class/teacher system
- complex recommendation algorithm

## Forbidden Actions

Do not:

- Hardcode API keys or secrets.
- Put AI prompts directly inside business logic.
- Let frontend call AI model providers directly.
- Run untrusted user code directly on the host machine.
- Implement full OJ or sandbox execution in MVP unless explicitly approved.
- Build a complex auth system in MVP phase.
- Mix frontend and backend business logic.
- Create unrelated large files, cache files, or generated artifacts.
- Add broad refactors unrelated to the current task.
- Change existing user files without checking context.
- Expose internal stack traces to frontend users.
- Copy full third-party problem statements or solutions without license permission.

## Dependency Management

Frontend dependency rules:

- Use pnpm only.
- Do not use npm or yarn unless explicitly justified and approved.

Backend dependency rules:

- Use uv only.
- Do not use pip, pipenv, poetry, or conda unless explicitly justified and approved.

When adding a dependency, Codex must explain:

- package name
- purpose
- affected area
- whether it affects Docker images or lock files
- whether it increases runtime, build, or security risk

Dependencies should be added only when they solve a real project need.

## Architecture Rules

Backend must follow layered structure:

- router
- schema
- service
- repository
- model
- provider

Frontend should follow a feature-oriented structure:

- app routes
- shared components
- feature modules
- API client layer
- shared types

AI capabilities must be isolated behind service/provider interfaces.

Database schema changes must use Alembic migrations.

Frontend pages should call backend through a dedicated API client layer.

## Database Migration Rules

All schema changes must go through Alembic.

Rules:

- Do not modify old generated migrations casually.
- If schema changes after a migration has been committed, create a new migration.
- SQLAlchemy models, Pydantic schemas, and Alembic migrations must stay consistent.
- Seed data and schema migrations should be separated where practical.
- Migrations must be reproducible on a clean database.
- Table names and column names must be English.
- PostgreSQL compatibility is required even if local development temporarily uses another database.

## API Rules

All backend APIs must use the `/api` prefix.

API requirements:

- Use Pydantic request and response models.
- Use reasonable HTTP status codes.
- Use consistent response structures.
- Validate user input.
- List endpoints should reserve pagination parameters such as `page`, `page_size`, `limit`, or `offset`.
- Do not expose internal stack traces to frontend clients.
- Return clear user-facing error messages.
- Keep API contracts documented in `docs/API_DESIGN.md`.

MVP API examples:

- `GET /api/health`
- `GET /api/topics`
- `GET /api/topics/{id}`
- `POST /api/learning/records`
- `GET /api/dashboard/summary`
- `POST /api/ai/chat`
- `POST /api/ai/code-review`
- `POST /api/ai/generate-problem`

## AI Call And Logging Rules

All AI calls must go through backend AI service/provider layers.

Frontend must never directly call:

- OpenAI
- DeepSeek
- Qwen
- Kimi
- any other model provider

AI logs should record metadata only:

- provider
- model
- prompt_type
- latency
- success
- token usage
- error category when relevant
- created_at

By default, do not store in `ai_call_logs`:

- complete user code
- complete prompt
- complete model response
- API keys
- sensitive user content

Timeout, retry, and error strategy:

- Use `AI_TIMEOUT_SECONDS` for provider calls.
- Use `AI_MAX_RETRIES` for bounded retries.
- Default retry count should be low in MVP, for example `1`.
- Retry only transient failures where reasonable.
- Return clear errors when provider calls fail.
- Log failure metadata without leaking secrets.
- AI provider errors should not crash the backend process.

## Prompt Management Rules

Prompt templates must not be scattered in business code.

Prompt templates should be managed through:

- template files for default seed prompts
- `prompt_templates` database records for active runtime versions

Recommended file location:

```text
backend/app/prompts/templates/
```

Recommended prompt types:

- concept_explanation
- problem_hint
- code_review
- complexity_analysis
- problem_generation
- learning_path
- mistake_review

`prompt_templates` should connect database templates with file templates using:

- `template_key`
- `file_path`
- `version`
- `enabled`

## AI Teaching Behavior Rules

Default AI behavior must be educational and heuristic.

General teaching rules:

- Explain ideas before code.
- Prefer step-by-step guidance.
- For problem solving, provide hints, reasoning, and pseudocode before full code.
- For code diagnosis, explain the bug and root cause before giving corrected code.
- Avoid directly giving final answers by default.
- When giving full code, explain why it is necessary.
- Beginner mode must avoid unexplained terminology.
- Advanced mode may use concise competitive-programming style explanations.
- Complexity analysis should include both time and space complexity when relevant.
- Common pitfalls should be included for algorithm topics and code reviews.

## Content Copyright Rules

Do not copy full third-party problem statements or solutions unless the license clearly allows it.

For external problems, prefer storing:

- title
- metadata
- tags
- difficulty
- source
- source_url
- short internal note
- user progress records

MVP seed problems should preferably be:

- original
- AI generated
- license-safe

AI generated problems must be marked:

```text
is_ai_generated = true
```

External imported problems must keep source attribution through `source` and `source_url`.

## UI Quality Rules

Frontend pages should feel like a formal learning product and developer tool hybrid.

UI requirements:

- Clear layout and hierarchy.
- Strong reading experience for algorithm explanations.
- Strong reading experience for code blocks.
- Code blocks should be clear and copyable.
- Pages must handle loading, empty, and error states.
- Avoid flashy dashboard-style visuals.
- Avoid decorative UI that reduces readability.
- Prefer calm, structured, information-dense screens.
- Dashboard should communicate learning progress, not just charts.
- Mobile should be usable, but desktop is the MVP priority.

## Security Rules

Secrets must come from environment variables.

Required security rules:

- AI API keys must never be exposed to frontend.
- User inputs must be validated with Pydantic.
- Code execution must remain disabled unless sandboxing is explicitly implemented.
- Use `ENABLE_CODE_EXECUTION=false` by default.
- Use timeout and error handling for AI calls.
- Log AI calls without secrets.
- Do not store sensitive prompt/user content unless explicitly required.
- Do not expose backend stack traces to users.
- Add rate limiting design before production use.

Code execution rules:

- Do not run user-submitted code on the host machine.
- Docker sandbox execution is a future feature.
- Sandbox must include timeout, memory limits, network restrictions, and filesystem restrictions.

## Environment Configuration

Required `.env.example` fields include:

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

## Testing Requirements

For every implemented phase:

- Backend health check must pass.
- Main API endpoints must have basic tests.
- Frontend must build or pass configured lint/type checks.
- Docker Compose startup path must be verified.
- Database migrations must be reproducible.
- AI provider failures must be handled without crashing the app.

Testing should scale with risk:

- Schema changes require migration verification.
- API changes require API tests.
- UI changes require manual browser verification when practical.
- AI changes require mocked or controlled provider tests where possible.

## Task Completion Standard

A task is complete only when:

- Files are implemented according to project structure.
- Relevant commands run successfully.
- APIs or pages are manually verified.
- README or docs are updated when behavior changes.
- No secrets are committed.
- No unrelated files are changed.
- The final response explains changes clearly.

## Required Summary Format

After every code change, summarize:

### Changed Files

- `path/to/file`: what changed

### Implemented

- feature or behavior

### How To Run

- commands

### How To Test

- commands or manual verification steps

### Notes

- known limitations
- next recommended step
