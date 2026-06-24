# Post-MVP Roadmap

MVP v0.1 ends at Phase 4, with Phase 4.5 reserved for stabilization and frontend experience polish. Phase 5 and later are Post-MVP work. They are not required for MVP v0.1 completion.

Post-MVP work must be planned, implemented, tested, and committed phase by phase. Do not merge multiple roadmap phases into one unreviewed implementation.

## Dependency Principles

```text
Auth -> Personal Data Ownership
Problem Bank -> ZIP Import -> Test Cases -> Judging
Judging -> Failed Submission -> AI Diagnosis
Mistake Notebook -> Weakness Analysis -> Recommendation
Content Scale -> RAG
```

Key ordering rules:

- Minimal auth should happen before personal problem banks, mistake notebooks, and submission history.
- Personal problem bank should happen before ZIP import and judging.
- ZIP import should happen before complete judging, because test cases need a safe import and validation model.
- Judging must be planned as its own safety-critical system.
- AI diagnosis after failed judgement should be added only after judging is stable.
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

## Phase 13: RAG Knowledge Retrieval

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

## Phase 14: Deployment, Security, Permissions, Production Hardening

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
