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
SECRET_KEY=change-me-in-production-32-bytes-long!!
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

---

# 3. Post-MVP Pressure Tests

These checks apply to Phase 5 and later. They are not MVP v0.1 requirements.

## 3.1 Auth Pressure Test

Questions:

- Do users really need login for the current phase?
- Is the default dev user still development-only?
- Can `get_current_user` switch from dev user to real users without rewriting routers?
- Are unauthenticated users blocked from personal data?
- Are learning records, problems, mistakes, and submissions scoped to the current user?
- Does student-id login avoid exposing whether a student id exists?
- Are initial profile fields bounded, validated, and safe to use in AI context?

Pass criteria:

- Auth is introduced before personal problem bank, mistake notebook, and submissions.
- `ENABLE_DEV_USER` is safe for development and disabled for production.
- Unauthenticated users cannot access personal resources.
- Tests cover user isolation.
- Login state uses HttpOnly Cookie and JWT.
- The frontend sends credentials but does not store or read tokens.
- Dev user fallback happens only when the Cookie is missing.
- Expired, invalid, or missing-user tokens return safe auth errors and do not fallback to dev user.
- Phase 13 registration uses `student_id`, `name`, `current_level`, and `goal_track`.
- `email` and `username` remain compatibility fields and are not required user-facing fields.
- User profile context sent to AI is a short summary, not full learning history.

Risk signals:

- Dev user is accidentally available in production.
- Frontend sends `user_id` to claim ownership.
- Personal data endpoints work without authentication.
- Token is stored in localStorage or sessionStorage.
- Login failure reveals whether an email exists.
- Login failure reveals whether a student id exists.
- AI prompts receive unbounded profile text.
- Logout fails to clear the Cookie because Cookie attributes do not match.

## 3.2 Problem Bank Pressure Test

Phase 6-7 implemented baseline:

- Manual problem CRUD exists for the current authenticated user.
- Problems are scoped by `created_by_user_id`.
- Users cannot view, update, or delete other users' problems.
- `slug` is unique within one user's problem bank, not globally.
- `display_id` is unique within one user's problem bank and is not reused after hard delete.
- Topic association follows the existing visible published topics rule.
- AI-generated problem persistence is supported only through an explicit user save action.
- ZIP import, judging, and submissions remain deferred.

Questions:

- Can AI-generated problems be saved explicitly by the user?
- Are problem ids and slugs stable?
- Does every personal problem belong to the current user?
- Does the system distinguish AI-generated, ZIP-imported, manually created, and external-source problems?
- Are external sources attributed without copying licensed content blindly?

Pass criteria:

- Problem ownership is enforced.
- Problem source/type is explicit.
- AI-generated problems are marked `is_ai_generated=true`.
- Saved AI-generated problems share the same per-user `display_id` sequence as manual problems.
- AI-generated problems are not silently persisted without user action.
- Problem bank exists before ZIP import and judging.

Risk signals:

- Saved problems have no ownership.
- AI-generated content is silently persisted.
- Third-party statements are copied without license review.

Phase 16 public problem additions:

- `users.role` is limited to `user` and `admin`.
- `problems.is_public=false` remains the personal problem default.
- `problems.is_public=true` is visible to all authenticated users.
- Only admin users can create, edit, or delete public problems.
- Normal users can view and submit public problems but cannot modify them.
- Public problem API routes must be registered before dynamic `{problem_id}` routes.
- The optional dev fallback user is a normal user and must not gain admin permissions.
- Admin seeding requires `DEV_ADMIN_PASSWORD`; no default production password is hardcoded.

Phase 16 pass criteria:

- Normal users receive `PUBLIC_PROBLEM_FORBIDDEN` when trying to create public problems.
- Other users cannot access private personal problems through public routes.
- Public problem detail does not show edit/delete actions unless the backend returns `can_edit=true`.
- Submission creation accepts public problems while submission detail remains scoped to the submitting user.

## 3.2.1 Code Review And Mistake Notebook Pressure Test

Phase 8 implemented baseline:

- Code reviews are saved only when the user explicitly clicks save.
- Saved code reviews are scoped by current authenticated user.
- Saved code reviews may store full code and full AI analysis as user-owned product data.
- `ai_call_logs` remain metadata-only and do not store full code, prompts, API keys, or provider responses.
- Mistake notes are scoped by current authenticated user.
- Mistake notes can optionally link to published topics, current-user problems, and current-user saved code reviews.
- Deleting a linked problem or saved code review does not delete the mistake note.
- Dashboard weakness analysis and recommendations remain deferred to Phase 12.

Questions:

- Is every saved code review explicitly user-triggered?
- Can one user access another user's saved code review or mistake note?
- Are full code and AI analysis kept out of logs?
- Does deleting a problem or code review preserve the user's reflection record?
- Are status transitions clear for `open`, `reviewing`, and `resolved`?

Pass criteria:

- There is no auto-save path for all code reviews.
- User ownership is enforced on list, detail, update, and delete endpoints.
- `problem_id`, `topic_id`, and `code_review_id` are validated before association.
- `resolved_at` is set only for resolved mistake notes and cleared when reopened.
- No judge, submission, ZIP import, RAG, or code execution behavior is introduced.

Risk signals:

- Full user code appears in logs or AI call metadata tables.
- A mistake note can be linked to another user's problem or code review.
- `/mistakes/{id}` save redirects to a problem page instead of staying in the mistake workflow.
- Dashboard starts presenting unreviewed weakness analysis as if it were implemented.

## 3.3 ZIP Import Pressure Test

Questions:

- Is ZIP size limited?
- Is file count limited?
- Is path traversal blocked?
- Are only safe file types allowed, such as `.md`, `.json`, `.in`, and `.out`?
- Are uploaded files never executed?
- Are malformed archives rejected safely?
- Are `.in` and `.out` test case files paired and naturally sorted?
- Does import run in one transaction so partial failures roll back?
- Does imported content stay owned by the current user?

Pass criteria:

- Import validates size, count, path, extension, and metadata.
- Limits include ZIP size, file count, total uncompressed size, single file size, compression ratio, and test case count.
- Path traversal, absolute paths, Windows drive paths, backslash bypasses, symbolic links, encrypted entries, duplicate logical paths, and unsupported extensions are rejected.
- Uploaded content is stored as data only.
- Imported problems use `source="zip_import"`, `is_ai_generated=false`, and `is_published=false`.
- Imported test cases are persisted as text data and are not executed.
- Import shares the user's existing `display_id` sequence.
- No scripts, binaries, or arbitrary paths are accepted.
- Error responses are safe and user-facing.

Risk signals:

- ZIP extraction writes outside the intended directory.
- Uploaded files are executed or interpreted as code.
- Import has no size or count limits.
- A failed import leaves behind a problem without complete test cases.
- ZIP import silently bypasses current-user ownership.

## 3.4 Judge Safety Pressure Test

Phase 10 implemented baseline:

- Code execution is disabled by default.
- Backend delegates to a separate Judge service.
- Each submission uses a temporary network-disabled runner container.
- Hidden test-case content is not exposed by the API.
- Submission source is user-owned data and is not written to AI logs.

Questions:

- Is host-machine execution forbidden?
- Is a sandbox or isolated judge service used?
- Are timeout, memory, network, filesystem, and process limits enforced?
- Is `ENABLE_CODE_EXECUTION=false` still the default?
- Can malicious code be handled safely?

Pass criteria:

- Judge is isolated from the normal backend process.
- User code never runs directly on the host.
- Sandbox constraints are tested.
- Failed or malicious submissions do not compromise the service.
- Busy Judge instances fail fast instead of creating an unbounded queue.
- Runner containers are removed after success, failure, timeout, or cancellation.
- C++ and Python fork bombs are constrained by PID limits.

Risk signals:

- The backend runs user code with `subprocess` on the host.
- Network or filesystem access is unrestricted.
- Judge code is mixed into the AI code review service.

## 3.5 AI Diagnosis After Judge Pressure Test

Phase 11 implemented baseline:

- Diagnosis is triggered explicitly from a persisted submission.
- Accepted and Judge internal errors are not sent to AI.
- ContextBuilder bounds source, problem, compiler, and failed-case context.
- Hidden case names, inputs, expected outputs, and actual outputs are excluded.
- Diagnosis is temporary until the user explicitly saves a code review.

Questions:

- Does AI explain judge failures without replacing the judge verdict?
- Does AI avoid executing user code?
- Are failed test cases and code length limited before prompt construction?
- Are full code, full prompts, and sensitive data kept out of logs by default?
- Are provider failures isolated from judging correctness?

Pass criteria:

- AI diagnosis runs only after a stable judge result exists.
- Input context is bounded and sanitized.
- AI logs remain metadata-only by default.
- Provider errors return safe API errors.
- Judge verdict and persisted submission data remain unchanged after AI failure.
- Saving a diagnosis requires a separate explicit action.

Risk signals:

- AI is used as the judge.
- Failed test context is unbounded.
- Sensitive code is stored in logs without explicit policy.
- Hidden test content reaches the Prompt or frontend.
- Diagnosis is generated or persisted automatically.

## 3.6 Learning Recommendation Pressure Test

Phase 12 implemented baseline:

- Dashboard computes weak topics from current-user learning records, unresolved mistake notes, failed submissions, and personal problems.
- Recommendations are rule-based, explainable, and not persisted.
- Existing `review_queue` and `next_steps` remain compatible.
- No AI Provider, Prompt template, RAG, embedding, or `recommendation_logs` path is used.

Questions:

- Does every recommendation show a visible reason?
- Are other users' mistakes, submissions, and problems excluded?
- Are accepted submissions excluded from weakness signals?
- Are resolved mistake notes excluded from high-priority actions?
- Does the API keep all existing Dashboard fields unchanged?

Pass criteria:

- Weakness scores are capped and sorted deterministically.
- Empty user data produces empty recommendation arrays, not fake recommendations.
- Practice recommendations only include current-user problem bank items.
- The Dashboard remains usable when no weakness signals exist.
- No recommendation path calls AI Provider or queries Prompt templates.

Risk signals:

- Recommendations use cross-user data.
- AI-generated recommendations appear without a dedicated phase plan.
- RAG or vector search is introduced early.
- `recommendation_logs` is created before a clear audit/history requirement.

## 3.7 Learning Ladder Pressure Test

Phase 14-15 implemented baseline:

- Ladder templates are seeded database records.
- `GET /api/ladder` creates or returns one active path for the current user.
- Path nodes are expanded from templates and tracked through `node_user_progress`.
- Node status is computed from progress booleans.
- The first node is unlocked by default.
- Completing node N's material unlocks node N+1.
- Phase 15 stores seeded practice items in `learning_path_nodes.practice_items`.
- Phase 15 scores choice practice on the backend and sets `practice_completed` after passing.
- Coding practice is self-check only and does not execute code.
- Phase 15 does not update exam completion.

Questions:

- Can one user see or update another user's ladder nodes?
- Does concurrent first access avoid creating multiple active paths?
- Does a missing template fail safely with `LADDER_TEMPLATE_NOT_FOUND`?
- Does completing a locked node return `NODE_LOCKED`?
- Is material completion idempotent?
- Does node detail hide `correct_option_id` from practice items?
- Does practice submission require material completion?
- Does locked-node practice return `NODE_LOCKED`?
- Does low-score practice avoid setting `practice_completed`?
- Does coding self-check remain a confirmation only, without Judge or submissions?
- Are repeated practice item IDs rejected safely?
- Are external resource links displayed without crawling or copying content?
- Does `/ladder` remain useful without adding AI exams or Judge scoring early?

Pass criteria:

- Each user has at most one active learning path.
- Current-user ownership is enforced for list, detail, and completion endpoints.
- First node starts unlocked and second node starts locked.
- Completing the first node material unlocks the second node immediately.
- `practice_completed` is changed only by Phase 15 practice submission.
- `exam_passed` remains unchanged until Phase 17.
- `scripts/seed_ladder_templates.py` is idempotent.
- Choice answers below 80 points do not complete practice.
- Coding self-check is required for practice completion when coding items exist.
- No AI Provider, Judge, submission creation, RAG, embedding, or recommendation service is called by ladder practice APIs.

Risk signals:

- Ladder paths are shared across users.
- Nodes can be skipped while locked.
- Template seed content copies third-party material without license review.
- API responses leak `correct_option_id`.
- Practice can be submitted before material completion.
- Phase 15 starts implementing exams, Judge integration, submissions, RAG, or complex adaptive curriculum.

## 3.8 RAG Pressure Test

Questions:

- Is there enough content scale to justify RAG?
- Does ContextBuilder already provide the extension point?
- Is pgvector or embedding actually needed?
- Can retrieval quality be evaluated?
- Are sensitive user-generated contents excluded or governed by policy?

Pass criteria:

- RAG extends ContextBuilder through RetrievalService.
- AIService and provider contracts remain stable.
- Retrieval is justified by content volume and measurable quality needs.
- Sensitive content boundaries are explicit.

Risk signals:

- RAG is added before enough data exists.
- AI service is rewritten instead of extended.
- Vector storage is introduced without evaluation criteria.
