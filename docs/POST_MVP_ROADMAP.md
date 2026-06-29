# Post-MVP Roadmap

MVP v0.1 ends at Phase 4, with Phase 4.5 reserved for stabilization and frontend experience polish. Phase 5 and later are Post-MVP work. They are not required for MVP v0.1 completion.

Post-MVP work must be planned, implemented, tested, and committed phase by phase. Do not merge multiple roadmap phases into one unreviewed implementation.

## Dependency Principles

```text
Auth -> Personal Data Ownership
Problem Bank -> ZIP Import -> Test Cases -> Judging
Judging -> Failed Submission -> AI Diagnosis
Mistake Notebook -> Weakness Analysis -> Recommendation
Profile + Ladder Progress -> OpenMAIC Interactive Classroom POC
OpenMAIC POC -> Topic/Ladder Interactive Lessons
Content Scale -> RAG
```

Key ordering rules:

- Minimal auth should happen before personal problem banks, mistake notebooks, and submission history.
- Personal problem bank should happen before ZIP import and judging.
- ZIP import should happen before complete judging, because test cases need a safe import and validation model.
- Judging must be planned as its own safety-critical system.
- AI diagnosis after failed judgement should be added only after judging is stable.
- OpenMAIC work should start as an optional external-service integration after profile-aware ladder context is stable. It must not replace AlgoMentor's AIService, prompt templates, user system, or ladder progress rules.
- RAG should wait until knowledge, problem, mistake, and code diagnosis data are large enough to justify retrieval.

## Phase 5: Minimal Auth And User System

### Goal

Replace dev-user-only behavior with a minimal real user system.

Status: implemented as the first Post-MVP phase with HttpOnly Cookie + JWT and development-user fallback.

### Dependencies

- MVP v0.1 complete
- Existing `get_current_user` dependency
- Existing `users` table

### Expected Features

- Register, login, logout, and current user endpoint
- Password hashing
- Session or token-based authentication
- User-owned learning records
- Dev user remains available only for development when explicitly enabled
- Frontend `/login` and `/register` pages
- Top navigation login state

### Not Included

- Full RBAC
- Email verification
- OAuth/social login
- Admin console
- Organization or classroom system

### Risk Level

medium

### Completion Criteria

- Unauthenticated users cannot access personal data.
- Existing learning APIs use real authenticated users.
- `ENABLE_DEV_USER` remains a development-only escape hatch.
- Tests cover authenticated and unauthenticated access.
- The frontend does not store JWTs in browser storage.

## Phase 6: Personal Problem Bank Basic

### Goal

Introduce a user-owned problem bank for manually created and curated practice problems.

Status: implemented as Post-MVP Phase 6 with manual CRUD, per-user ownership, and topic associations.

### Dependencies

- Phase 5 auth
- Personal data ownership model

### Expected Features

- Create, list, view, update, and delete personal problems
- Link problems to topics
- Store source metadata, difficulty, tags, and estimated time
- Distinguish user-created problems from future AI-generated and imported problems

### Not Included

- ZIP import
- Judging or submissions
- AI-generated problem persistence
- Third-party problem scraping

### Risk Level

medium

### Completion Criteria

- Problems belong to the current user.
- Users cannot access other users' problems.
- External sources store metadata and attribution without copying licensed statements blindly.
- Problem list/detail pages are usable without judging.
- `problems` and `problem_tags` migrations are reproducible and rollbackable.
- Personal problems have per-user visible numbering through `display_id`.
- Frontend `/problems`, `/problems/new`, and `/problems/{id}` build successfully.

## Phase 7: Save AI-Generated Problems To Problem Bank

Status: implemented in Post-MVP Phase 7.

### Goal

Allow users to save generated practice problems into their personal problem bank.

### Dependencies

- Phase 6 problem bank
- Existing AI problem generation endpoint

### Expected Features

- Save generated problem result as a problem record
- Mark saved problems with `is_ai_generated=true`
- Preserve topic, difficulty, generation metadata, and user ownership
- Allow editing before or after save if product flow requires it

### Not Included

- Judging
- Test case generation guarantees
- Public problem publishing workflow
- Bulk generation

### Risk Level

medium

### Completion Criteria

- AI-generated problems can be saved explicitly by the user.
- Saved generated problems appear in the user's problem bank.
- Saved generated problems share the personal problem bank `display_id` sequence.
- Generated content is not silently persisted without user action.
- Logs still avoid storing API keys, full prompts, or unrelated sensitive content.

## Phase 8: Code Review Persistence And Mistake Notebook

Status: implemented in Post-MVP Phase 8.

### Goal

Persist selected code review results and support a structured mistake notebook.

### Dependencies

- Phase 5 auth
- Phase 6 problem bank is recommended when mistakes are tied to problems
- Existing AI code diagnosis flow

### Expected Features

- Save code review results only when explicitly requested
- Create mistake notes with root cause, fix suggestion, reflection, and review status
- Link mistakes to topics and optionally problems
- Show review status and revisit flow

### Not Included

- Automatic storage of every submitted code snippet
- Judging integration
- Advanced weakness recommendation
- Teacher/admin review workflow

### Risk Level

medium

### Completion Criteria

- Users explicitly choose what to save.
- Mistake notes are scoped to the current user.
- Sensitive code retention is documented and minimized.
- Dashboard can link to saved mistake review items without changing AI logs into content storage.
- Saved code reviews and mistake notes do not introduce judging, submissions, ZIP import, RAG, or code execution.

## Phase 9: ZIP Problem Import With Test Cases

Status: implemented.

### Goal

Import user-owned problem packages and test cases safely from ZIP files.

### Dependencies

- Phase 6 problem bank
- File validation policy
- Storage and ownership model

### Expected Features

- Upload ZIP with problem metadata and test case files
- Validate allowed file types such as `.md`, `.json`, `.in`, and `.out`
- Enforce ZIP size and file count limits
- Prevent path traversal
- Store imported source as user-owned problem data
- Persist imported `.in` / `.out` pairs as `test_cases`
- Keep `source="zip_import"` and current-user ownership on imported problems

### Not Included

- Executing uploaded files
- Running judge
- Creating submissions
- Sandbox or OJ behavior
- Accepting arbitrary scripts or binaries
- Public sharing or marketplace import

### Risk Level

high

### Completion Criteria

- Malicious paths are rejected.
- Oversized archives and too many files are rejected.
- Only allowed file types are accepted.
- Uploaded content is never executed.
- Imported problems share the same per-user `display_id` sequence as manual and AI-saved problems.
- Imported test cases are stored as text data and are consumed by the isolated Phase 10 Judge service.

## Phase 10: Minimal Judging System

Status: implemented with a separate Docker Judge service; production sandbox hardening remains required.

### Goal

Add a minimal, isolated judging system for submitted code.

### Dependencies

- Phase 6 problem bank
- Phase 9 test case import
- Sandbox design approval

### Expected Features

- Submit code for a problem
- Run in isolated sandbox or judge service
- Enforce timeout, memory, filesystem, process, and network limits
- Return basic statuses such as accepted, wrong answer, runtime error, compile error, and time limit exceeded

### Not Included

- Distributed judge cluster
- Advanced scoring
- Contest mode
- AI diagnosis after failure

### Risk Level

high

### Completion Criteria

- User code is never executed directly on the host.
- `ENABLE_CODE_EXECUTION=false` remains the default.
- Sandbox limits are enforced and tested.
- Judge service boundaries are separate from normal AI code review.
- C++17 and Python 3.11 submissions can be created and viewed by their owner.
- Hidden test-case content is not exposed through submission APIs.

## Phase 11: AI Diagnosis After Failed Judgement

Status: implemented.

### Goal

Use AI to explain failed submissions after the judge returns a stable result.

### Dependencies

- Phase 10 judging system
- Existing AI provider layer
- Safe truncation policy for code and failed test context

### Expected Features

- Diagnose compile, wrong-answer, runtime, time-limit, memory-limit, and output-limit failures
- Include limited failed test context
- Explain likely bug cause and next debugging steps
- Keep AI as explanation, not the source of judgement truth

### Not Included

- AI executing code
- AI replacing judge verdicts
- Persisting full sensitive code by default
- Unlimited failed test case injection into prompts

### Risk Level

high

### Completion Criteria

- AI diagnosis runs only after a judge verdict exists.
- Prompt input length is bounded.
- Logs store metadata only by default.
- Provider failures do not affect judge verdict correctness.
- Hidden test content is excluded before Prompt rendering.
- Diagnosis is temporary unless the user explicitly saves a code review.
- Accepted and Judge internal-error results are not sent to AI.

## Phase 12: Learning Recommendation And Weakness Analysis

### Goal

Use accumulated learning records, mistakes, problems, and submissions to recommend learning actions.

Status: implemented as real-time rule-based Dashboard recommendations without `recommendation_logs`.

### Dependencies

- Phase 8 mistake notebook
- Phase 10 submissions or enough learning history

### Expected Features

- Weak topic summaries
- Recommended review items
- Suggested next problems or topics
- Dashboard integration
- Rule-based recommendation actions using current-user mistake notes and failed submissions

### Not Included

- Black-box recommendation engine without explainability
- Teacher/admin analytics
- Real-time adaptive curriculum
- RAG requirement
- Recommendation history persistence

### Risk Level

medium

### Completion Criteria

- Recommendations are explainable.
- Users can see why an item is recommended.
- Other users' data does not influence personal recommendations.
- Existing rule-based next steps remain compatible.
- Dashboard keeps existing Phase 2/4 fields and appends weakness/recommendation sections.

## Phase 13: Student Account And Initial Learning Profile

Status: implemented/in progress.

### Goal

Upgrade minimal auth into a student-account system and collect an initial learning profile for AI context.

### Dependencies

- Phase 5 auth
- Existing `users` table
- Existing AI ContextBuilder

### Expected Features

- Register and login with `student_id`
- Store display name, current level, goal track, and optional goal description
- Keep legacy `email` and `username` fields for compatibility
- Add profile summary to AI tutoring, problem generation, code review, and submission diagnosis context

### Not Included

- Ladder learning path
- RBAC, classroom, teacher, or admin system
- RAG
- Complex adaptive curriculum

### Risk Level

medium

### Completion Criteria

- Student id registration and login work with HttpOnly Cookie sessions.
- Existing users are safely backfilled by migration.
- Profile fields are returned by `/api/auth/me`.
- AI prompts receive a short profile summary without logging full prompts.
- Existing personal-data isolation remains intact.

## Phase 14: Ladder Templates And Path Foundation

Status: implemented.

### Goal

Create the base learning ladder path model and first visual ladder page.

### Dependencies

- Phase 13 student profile
- Seeded ladder templates

### Expected Features

- Store ladder templates and per-user active learning paths
- Show phases and algorithm nodes as a ladder
- Track material completion and basic node unlock state
- Unlock node N+1 after node N material is completed
- Seed default templates for supported profile combinations

### Not Included

- AI exams
- Choice-question or coding-practice grading
- Judge integration
- RAG
- Teacher analytics

### Risk Level

medium

### Completion Criteria

- A user can get or create one active path.
- First node is unlocked and later nodes follow material-completion progression rules.
- Completing the first node material unlocks the second node.
- Ladder page renders phases, nodes, node material, and resource links safely.
- `practice_completed` and `exam_passed` are left unchanged by Phase 14 and reserved for Phase 15/16.

## Phase 15: Ladder Materials And Practice Progress

Status: implemented.

### Goal

Add seeded node practice and basic practice progress to ladder nodes.

### Dependencies

- Phase 14 ladder path foundation
- Existing topics/problem bank where useful

### Expected Features

- Markdown teaching content per node
- External learning links
- Basic choice and coding practice content
- Practice completion state
- Backend-scored choice practice with an 80-point threshold
- Coding self-check confirmation without executing code
- `/ladder` material and practice sections in the node detail view

### Not Included

- Judge-scored coding exercises
- AI exams
- Submissions
- Practice attempt history
- AI-generated practice content

### Risk Level

medium

### Completion Criteria

- Users can read material, complete practice, and see node progress update.
- Seeded `practice_items` are copied into path nodes when the path is generated.
- Existing paths do not automatically update when templates change.
- Choice answers are scored by the backend and answer keys are hidden from node-detail responses.
- Coding practice is not executed in Phase 15.
- `practice_completed` does not unlock the next node; material completion remains the unlock rule.

## Phase 16: Admin Role And Public Problem Bank

Status: implemented.

### Goal

Add a minimal `admin` role and a public problem bank before AI ladder exams and later content generation work.

### Dependencies

- Phase 13 student accounts
- Phase 6-10 problem bank and submissions

### Expected Features

- `users.role` with `user` and `admin`
- `problems.is_public` to distinguish personal and public problems
- Admin-only creation, editing, and deletion of public problems
- Public problem list/detail APIs and pages
- Normal users can view and submit public problems
- Development admin seeded by `scripts/seed_admin.py` using `DEV_ADMIN_PASSWORD`

### Not Included

- Full RBAC
- Teacher/classroom system
- Admin analytics console
- Public problem global numbering
- AI exams, RAG, or content marketplace workflows

### Completion Criteria

- Normal users cannot create, edit, or delete public problems.
- Admin users can maintain public problems.
- Public problem routes are registered before dynamic problem-id routes.
- Submissions accept public problems without exposing other users' submissions.
- `ENABLE_DEV_USER=false` is the default, and dev fallback is not admin.

## Phase 17: AI Ladder Exam And Unlock Flow

Status: implemented.

### Goal

Generate and grade node exams, then mark nodes as passed after successful evaluation.

### Dependencies

- Phase 15 ladder practice progress
- Phase 16 admin/public problem boundary
- Existing AI provider layer and prompt templates

### Expected Features

- Explicit AI-generated node exams
- `ladder_exam_attempts` persistence for generated/submitted attempts
- 10 normal single-choice questions and 2 code-reading/code-completion multiple-choice questions
- Backend deterministic scoring from the stored answer key
- Score out of 100 with 80 as passing threshold
- Submitted passing exam sets `exam_passed=true`
- Passed exam unlocks the next node
- Unsubmitted generated attempts are reused instead of repeatedly calling AI

### Not Included

- Running exam code through Judge
- Creating submissions
- AI-based scoring
- RAG or retrieval
- Contest mode
- Ranking
- Classroom or teacher workflows

### Risk Level

high

### Completion Criteria

- Exam generation is explicit and validated.
- Invalid AI JSON is rejected safely.
- Locked nodes cannot be skipped.
- Passing unlocks the next node.
- Exam attempts do not leak answer keys before submission.
- AI call logs store only metadata, not full exams or answer keys.

## Phase 18: Profile-Aware AI Context And Recommendation Integration

Status: implemented as concise profile + ladder context for AI calls and rule-based ladder recommendations on Dashboard.

### Goal

Use student profile and ladder progress to improve AI context and Dashboard recommendations.

### Dependencies

- Phase 13 student profile
- Phase 17 ladder exam/progress data

### Expected Features

- Profile-aware AI tutoring and problem generation
- Dashboard recommendations can reference stuck ladder nodes and failed exams
- Short context summaries only

### Not Included

- RAG
- Full learning-history prompt injection
- Black-box recommendation model

### Risk Level

medium

### Completion Criteria

- AI context includes concise profile and ladder summaries.
- Recommendations remain explainable and user-scoped.
- Dashboard exposes `ladder_progress` and ladder-node recommendation actions.

## Phase 19A: OpenMAIC External Service POC

### Goal

Validate whether OpenMAIC can run as an independent interactive-classroom service and be called safely from AlgoMentor AI.

### Dependencies

- Phase 13 student profile
- Phase 14-18 ladder path, progress, and profile-aware context
- Existing backend service/provider layering
- OpenMAIC deployment and API compatibility review

### Expected Features

- Add an optional OpenMAIC service only for local/dev POC or controlled deployments
- Add backend configuration such as `ENABLE_OPENMAIC_INTEGRATION`, `OPENMAIC_BASE_URL`, `OPENMAIC_REQUEST_TIMEOUT_SECONDS`, `OPENMAIC_MAX_POLL_MINUTES`, and optional server-side access code
- Add an OpenMAIC client/adapter layer isolated from business services
- Verify server-to-server generation of an interactive classroom from a topic or ladder-node summary
- Keep OpenMAIC model/API-key configuration separate from AlgoMentor runtime AI settings in the first version
- Feature flag allows the integration to be fully disabled

### Not Included

- Deep UI embedding
- Replacing AlgoMentor AIService
- Copying OpenMAIC code into the main frontend
- Persisting full classroom artifacts
- Sending student ids, full code, hidden tests, exam answer keys, or sensitive user content to OpenMAIC
- RAG, classroom management, teacher workflows, or production SSO

### Risk Level

high

### Completion Criteria

- OpenMAIC can start independently without breaking existing Docker services.
- AlgoMentor backend can call OpenMAIC through an adapter and handle timeout/failure safely.
- Existing AI, Judge, ladder, Dashboard, and problem bank tests continue to pass.
- The integration can be disabled entirely with a feature flag.
- Sensitive data boundaries are documented before any user-facing rollout.

## Phase 19B: Topic Interactive Lessons With OpenMAIC

Status: implemented as a user-triggered topic lesson flow backed by `interactive_lessons` job/status/url records.

### Goal

Expose a user-triggered interactive lesson flow for knowledge topics using OpenMAIC as an external classroom generator.

### Dependencies

- Phase 19A OpenMAIC POC
- Existing topic detail pages and published-topic visibility rules

### Expected Features

- Add a topic-level "generate interactive lesson" action
- Build a safe Chinese classroom requirement from topic title, summary, category, current level, and goal track
- Store lightweight lesson records, such as status, source topic, provider, external job id, and external URL, so users can track generation status and reopen classrooms
- Poll generation status through AlgoMentor backend rather than directly from the frontend to OpenMAIC
- Open generated classrooms in a new tab or controlled route after generation completes
- Store OpenMAIC `unknown` status as `processing` and persist only fixed safe error messages, not raw upstream responses

### Not Included

- iframe embedding as the default path
- Automatic generation without user action
- Classroom completion tracking
- Writing OpenMAIC output back into the knowledge base
- Passing full personal learning history or private notes to OpenMAIC

### Risk Level

high

### Completion Criteria

- Users can generate a lesson from a visible topic.
- Generation is explicit and does not block normal API workers for long periods.
- OpenMAIC failures appear as safe user-facing errors.
- No OpenMAIC secret, access code, or provider key reaches the frontend.

## Phase 19C: Ladder Node Interactive Lessons With OpenMAIC

Status: implemented as a user-triggered ladder-node lesson flow backed by the shared `interactive_lessons` metadata table.

### Goal

Extend interactive lessons to learning ladder nodes so users can open a classroom tailored to the current algorithm node.

### Dependencies

- Phase 19B topic lessons
- Phase 18 ladder-aware AI context and `/ladder?node_id=...`

### Expected Features

- Add a ladder-node lesson action inside `/ladder`
- Use current node title, summary, material excerpt, user level, goal track, and progress status as bounded context
- Link generated lessons back to the source ladder node
- Store ladder-node lessons as `source_type='ladder_node'` metadata rows without storing full classroom artifacts
- Normalize OpenMAIC `unknown` status to `processing` and store only fixed safe error messages
- Keep Dashboard recommendation links to lesson actions deferred

### Not Included

- Marking `material_completed`, `practice_completed`, or `exam_passed` from OpenMAIC activity
- Importing OpenMAIC quizzes into ladder practice or exams
- RAG-backed lesson generation
- Automatic classroom generation for every node
- Dashboard lesson recommendations

### Risk Level

high

### Completion Criteria

- A user can generate/open a classroom for an accessible ladder node.
- The backend validates node ownership before generation.
- Locked nodes cannot generate classrooms.
- Classroom generation does not mutate ladder progress.
- Ladder-node lesson downgrade is documented as lossy because the Phase 19B schema cannot represent node lessons.
- Lesson prompts do not include practice answer keys, exam payloads, hidden tests, or full user history.
- The existing ladder exam and progress rules remain unchanged.

## Phase 19D: OpenMAIC Real-Service Hardening

Status: implemented as compatibility and operational hardening for the existing OpenMAIC adapter and lesson flows.

### Goal

Make the external OpenMAIC integration reliable enough for local and demo validation against a real running OpenMAIC service.

### Expected Features

- Harden adapter status and classroom URL parsing for realistic OpenMAIC response shapes
- Map OpenMAIC authentication failures to `OPENMAIC_AUTH_FAILED`
- Use `OPENMAIC_MAX_POLL_MINUTES` as a stale lesson guard during refresh
- Allow explicit regeneration with `force=true` for topic and ladder-node lessons
- Provide `scripts/check_openmaic_integration.py` for local adapter checks without database writes

### Not Included

- Dashboard lesson recommendations
- OpenMAIC Docker Compose ownership
- iframe embedding
- Classroom completion tracking
- Writing classroom artifacts back into AlgoMentor content

### Completion Criteria

- Topic and ladder-node completed lessons can be explicitly regenerated.
- Stale `pending`, `submitted`, or `processing` lessons converge to a safe failed state.
- Adapter tests cover auth failure, status aliases, URL aliases, and nested unknown status behavior.
- Local integration script can report normalized OpenMAIC generate/poll results without printing secrets.

## Phase 19E: OpenMAIC Local Real-Service Validation

Status: implemented as local runbook and response-shape validation for the real OpenMAIC service.

### Goal

Close the gap between adapter-level support and a repeatable local OpenMAIC validation flow.

### Expected Features

- Validate the real local OpenMAIC response shape: `queued` generation jobs and `succeeded` completed jobs with `result.url`
- Make `scripts/check_openmaic_integration.py` wait for completion by default while keeping a `--no-wait` quick mode
- Document that OpenMAIC runs outside AlgoMentor Docker Compose, typically from `D:\OpenMAIC` on port `3010`
- Clarify that OpenMAIC `ACCESS_CODE` protects browser access and is not required for the local server-to-server generation API

### Not Included

- OpenMAIC Docker Compose ownership
- Dashboard lesson recommendations
- RAG retrieval
- Copying OpenMAIC code into the AlgoMentor frontend

### Completion Criteria

- Local check script can generate, poll, and print a completed classroom URL against a running OpenMAIC service.
- Adapter tests cover the real `succeeded + result.url` response shape.
- Topic and ladder classroom generation continue to work only through AlgoMentor backend APIs.

## Phase 19F: Per-user AI Provider Settings

Status: implemented as account-scoped BYOK configuration before RAG.

### Goal

Let each logged-in user save one OpenAI-compatible AI provider configuration that survives backend restarts and is used by AI calls for that user.

### Expected Features

- Store per-user `base_url`, `api_key`, and `model` in `user_ai_settings`
- Resolve AI settings in priority order: user config, global runtime/persistent fallback, environment variables, none
- Use current-user settings for AI chat, problem generation, code review, submission diagnosis, ladder exam generation, and settings test calls
- Keep API keys out of frontend responses, browser storage, logs, and AI call metadata

### Not Included

- OpenMAIC configuration changes
- Multiple provider profiles per user
- Production-grade key encryption or KMS-backed secret storage
- RAG retrieval

### Completion Criteria

- A user's saved AI configuration persists after backend restart.
- Another user cannot read or use that configuration.
- Clearing settings deletes only the current user's row.
- Existing global runtime/env settings remain available only as fallback.

## Phase 20: RAG Knowledge Retrieval

### Goal

Expand AI context beyond single `topic_id` using retrieval.

### Dependencies

- Enough content scale to justify retrieval
- ContextBuilder extension point
- Candidate knowledge/problem/mistake/code review data sources

### Expected Features

- RetrievalService behind ContextBuilder
- Knowledge chunks or equivalent retrieval units
- Retrieval logs and evaluation strategy
- Optional embedding/vector store after pressure testing

### Not Included

- Rewriting AI service
- Introducing pgvector before it is justified
- Retrieval over sensitive user content without explicit policy
- Replacing curated prompt templates

### Risk Level

high

### Completion Criteria

- ContextBuilder can switch from topic-only context to retrieval-backed context.
- Retrieval quality can be evaluated.
- Sensitive content boundaries are documented.
- AI service/provider contracts remain stable.

## Phase 21: Deployment, Security, Permissions, Production Hardening

### Goal

Prepare the platform for safer production deployment.

### Dependencies

- Auth and personal data ownership
- Finalized production feature set for the release
- Deployment target decision

### Expected Features

- Production environment configuration
- Secret management
- Rate limiting
- Permission audit
- Logging and monitoring
- Backup and migration strategy
- Security review for upload, judge, and AI paths

### Not Included

- New learning features
- New AI capabilities
- New judging languages without sandbox review
- Large UI redesign

### Risk Level

high

### Completion Criteria

- Secrets are not stored in frontend, database, or logs.
- Public endpoints have appropriate authentication and authorization.
- Judge/upload/RAG paths have documented safety controls.
- Deployment and rollback steps are documented and tested.
