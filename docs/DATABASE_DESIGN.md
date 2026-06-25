# Database Design

## Design Principles

- Use English table and column names.
- Keep PostgreSQL compatibility.
- Manage schema changes through Alembic.
- Keep SQLAlchemy models, Pydantic schemas, and migrations consistent.
- Separate seed data from schema migrations where practical.
- Store AI logs as metadata by default, not full prompts or full user code.

## Table Roadmap

Long-term product tables:

- `users`
- `user_settings`
- `topics`
- `topic_dependencies`
- `problems`
- `problem_tags`
- `test_cases`
- `learning_records`
- `mistake_notes`
- `chat_sessions`
- `chat_messages`
- `code_reviews`
- `submissions`
- `prompt_templates`
- `ai_call_logs`
- `ladder_templates`
- `learning_paths`
- `learning_path_nodes`
- `node_user_progress`
- `recommendation_logs`
- `knowledge_chunks`
- `retrieval_logs`

MVP v0.1 implemented tables:

- `users`
- `topics`
- `topic_dependencies`
- `learning_records`
- `prompt_templates`
- `ai_call_logs`

Phase 2 creates `users`, `topics`, `topic_dependencies`, and `learning_records`.

Phase 3 adds `prompt_templates` and `ai_call_logs`.

Phase 3 still does not create `problems`, `chat_sessions`, `chat_messages`, `code_reviews`, or `mistake_notes`.

Phase 4 adds no database tables and no schema migration. It reuses:

- `topics`
- `learning_records`
- `users`

Phase 4 Dashboard data is computed from published topics and the current user's learning records. `mistake_notes`, `recommendation_logs`, `problems`, `code_reviews`, `chat_sessions`, and `chat_messages` remain deferred.

Phase 5 and later are Post-MVP roadmap work. They are not required for MVP v0.1 completion.

Current database reality includes MVP v0.1 tables plus implemented Post-MVP Phase 5-14 tables. Tables marked deferred below remain planning notes only until their Post-MVP phase creates an Alembic migration.

## Post-MVP Table Status

| Table | Planned Phase | Purpose | Boundary |
| --- | --- | --- | --- |
| `problems` | Phase 6 | Personal problem bank records | Implemented in Post-MVP Phase 6 |
| `problem_tags` | Phase 6 | Connect problems to topics | Implemented in Post-MVP Phase 6 |
| `test_cases` | Phase 9 | Imported problem test cases | Implemented in Post-MVP Phase 9 |
| `submissions` | Phase 10 | User-owned source and judge verdict snapshots | Implemented in Post-MVP Phase 10 |
| `submission_case_results` | Phase 10 | Per-test-case judge results | Implemented in Post-MVP Phase 10 |
| `code_reviews` | Phase 8 | Explicitly saved AI code review results | Implemented in Post-MVP Phase 8 |
| `mistake_notes` | Phase 8 | User-owned mistake notebook entries | Implemented in Post-MVP Phase 8 |
| `ladder_templates` | Phase 14 | Seeded learning ladder templates | Implemented in Post-MVP Phase 14 |
| `learning_paths` | Phase 14 | Current-user active ladder paths | Implemented in Post-MVP Phase 14 |
| `learning_path_nodes` | Phase 14 | Expanded per-path algorithm nodes | Implemented in Post-MVP Phase 14 |
| `node_user_progress` | Phase 14 | Per-user node completion booleans | Implemented in Post-MVP Phase 14 |
| `recommendation_logs` | Deferred after Phase 12 | Recommendation events and explanations | Phase 12 uses real-time rules and does not persist recommendation logs |
| `knowledge_chunks` | Phase 13 | Retrieval units for RAG | Wait for content scale and retrieval design |
| `retrieval_logs` | Phase 13 | Retrieval evaluation and trace metadata | Must avoid sensitive content leakage |

Phase 10 adds `submissions` and `submission_case_results` after defining the separate Judge service and isolated runner-container boundary. `test_cases` remains stored input/output data and is never executed by the backend itself.

## users

```text
id
email
username
student_id
name
hashed_password
current_level
goal_track
goal_description
onboarding_completed_at
learning_stage
target_track
created_at
updated_at
```

Notes:

- Phase 13 adds `student_id`, `name`, `current_level`, `goal_track`, `goal_description`, and `onboarding_completed_at`.
- New frontend registration and login use `student_id`, not email.
- `onboarding_completed_at` is set when the initial profile is collected during registration; migration also backfills it for legacy users.
- `email`, `username`, `learning_stage`, and `target_track` remain compatibility fields and are not removed in Phase 13.
- `current_level` is one of `beginner`, `elementary`, `popularization`, or `improvement`.
- `goal_track` is one of `course`, `lanqiao`, `icpc`, or `self_study`.
- User profile fields may be injected into AI context as a short summary, not as full learning history.

## user_settings

```text
id
user_id
preferred_language
ai_model
answer_style
created_at
updated_at
```

## topics

```text
id
parent_id
title
slug
category
level
difficulty_score
summary
content_markdown
template_code_cpp
template_code_python
complexity_note
common_pitfalls
estimated_minutes
status
published_at
order_index
created_at
updated_at
```

Notes:

- `parent_id` supports hierarchical knowledge maps.
- `difficulty_score` supports sorting, recommendation, and progress analysis.
- `status` can be `draft`, `published`, or `archived`.
- `estimated_minutes` supports learning planning and dashboard statistics.

## topic_dependencies

```text
id
topic_id
depends_on_topic_id
created_at
```

## problems

Implemented in Post-MVP Phase 6. Phase 7 reuses this table to store explicitly saved AI-generated problems. Phase 9 reuses it for ZIP-imported problems. Not part of MVP v0.1.

```text
id
display_id
title
slug
source
source_url
difficulty
estimated_minutes
description_markdown
input_format
output_format
constraints
sample_input
sample_output
hint
solution_markdown
solution_code_cpp
solution_code_python
is_ai_generated
is_published
created_by_user_id
published_at
created_at
updated_at
```

Notes:

- `source_url` stores external attribution.
- `is_ai_generated=true` is required for AI-generated problems saved in Phase 7.
- Phase 7 saved generated problems force `source="ai_generated"` and do not accept ownership or publication flags from the frontend.
- Phase 9 ZIP imports force `source="zip_import"`, `is_ai_generated=false`, and `is_published=false`.
- `is_published` is reserved for future publishing; Phase 6 problem bank shows only the current user's own problems.
- `created_by_user_id` owns the problem and must come from backend auth, not frontend input.
- `(created_by_user_id, slug)` is unique; slug is not globally unique.
- `(created_by_user_id, display_id)` is unique and provides a per-user visible sequence such as `#1`.
- Deleted `display_id` values are not reused.
- Avoid copying complete third-party statements unless the license allows it.
- Phase 9 creates `test_cases` as stored input/output text only. It does not create submissions, judging records, or code execution behavior.

## user_problem_counters

Implemented in Post-MVP Phase 6 follow-up. Not part of MVP v0.1.

```text
user_id
next_display_id
updated_at
```

Notes:

- Used only to allocate per-user problem `display_id` values.
- `next_display_id` increments when a manual, AI-generated, or ZIP-imported problem is created.
- Hard delete does not decrement the counter, so display ids are not reused.

## problem_tags

Implemented in Post-MVP Phase 6. Not part of MVP v0.1.

```text
id
problem_id
topic_id
created_at
```

## test_cases

Implemented in Post-MVP Phase 9. Not part of MVP v0.1.

```text
id
problem_id
case_index
name
input_text
expected_output_text
is_sample
is_hidden
created_at
updated_at
```

Notes:

- `problem_id` references `problems.id` with `on delete cascade`.
- `(problem_id, case_index)` is unique.
- `case_index` is positive and assigned from natural-sorted ZIP test-case names.
- `is_sample` marks sample cases used to populate `problems.sample_input` and `problems.sample_output`.
- `is_hidden` is reserved for Phase 10 judging and defaults to `false` in Phase 9.
- Test cases are stored as UTF-8 text data and are never executed in Phase 9.

## learning_records

```text
id
user_id
topic_id
status
progress_percent
mastery_level
review_count
last_studied_at
next_review_at
note
created_at
updated_at
```

Notes:

- `status` can be `not_started`, `learning`, `completed`, or `reviewing`.
- `progress_percent` ranges from 0 to 100.
- `mastery_level` can use a 0 to 5 scale.
- `next_review_at` supports future spaced repetition.

## ladder_templates

Implemented in Post-MVP Phase 14. Not part of MVP v0.1.

```text
id UUID primary key
goal_track varchar(40) not null
current_level varchar(40) not null
name varchar(120) not null
description text nullable
template_data jsonb not null
version integer not null default 1
is_default boolean not null default false
created_at timestamptz not null
updated_at timestamptz not null
```

Notes:

- `goal_track` and `current_level` follow the Phase 13 user profile enums.
- `(goal_track, current_level, version)` is unique.
- A partial unique index allows only one default template per `(goal_track, current_level)`.
- `template_data` stores phases and nodes seeded by `scripts/seed_ladder_templates.py`.
- Template material must be project-owned or otherwise license-safe.

## learning_paths

Implemented in Post-MVP Phase 14. Not part of MVP v0.1.

```text
id UUID primary key
user_id UUID references users(id) on delete cascade
template_id UUID references ladder_templates(id) on delete set null
goal_track varchar(40) not null
current_level varchar(40) not null
status varchar(30) not null default active
created_at timestamptz not null
updated_at timestamptz not null
```

Notes:

- A partial unique index enforces at most one active path per user.
- `goal_track` and `current_level` snapshot the selected template profile.
- Phase 14 only creates active paths; archive behavior is reserved for future path regeneration.

## learning_path_nodes

Implemented in Post-MVP Phase 14. Not part of MVP v0.1.

```text
id UUID primary key
path_id UUID references learning_paths(id) on delete cascade
topic_id UUID references topics(id) on delete set null
phase_index integer not null
node_index integer not null
algorithm_key varchar(120) not null
title varchar(120) not null
summary text not null
material_markdown text not null
resource_links jsonb not null default []
unlock_rule jsonb not null default {}
created_at timestamptz not null
updated_at timestamptz not null
```

Notes:

- `(path_id, phase_index, node_index)` is unique.
- `algorithm_key` is not unique within a path, because the same algorithm may appear in multiple phases.
- `topic_id` is optional and only binds published topics when a seed template `topic_slug` exists.
- `resource_links` are shown as references only; the backend does not fetch or copy external content.

## node_user_progress

Implemented in Post-MVP Phase 14. Not part of MVP v0.1.

```text
id UUID primary key
user_id UUID references users(id) on delete cascade
node_id UUID references learning_path_nodes(id) on delete cascade
material_completed boolean not null default false
practice_completed boolean not null default false
exam_passed boolean not null default false
material_completed_at timestamptz nullable
practice_completed_at timestamptz nullable
exam_passed_at timestamptz nullable
created_at timestamptz not null
updated_at timestamptz not null
```

Notes:

- `(user_id, node_id)` is unique.
- Phase 14 updates only `material_completed`.
- `practice_completed` is reserved for Phase 15.
- `exam_passed` is reserved for Phase 16.
- Node status is computed by the API and not stored as a denormalized string.
- Completing node N's material unlocks node N+1.

## submissions

Implemented in Post-MVP Phase 10.

```text
id
user_id
problem_id
problem_title
problem_display_id
language
source_code
verdict
passed_case_count
total_case_count
execution_time_ms
memory_kb
compile_output
error_message
created_at
finished_at
```

Notes:

- Full source code is current-user-owned product data, not log data.
- Problem title and display-id snapshots survive hard deletion.
- `problem_id` uses `on delete set null`.
- Phase 10 supports `cpp` and `python` only.

## submission_case_results

Implemented in Post-MVP Phase 10.

```text
id
submission_id
test_case_id
case_index
name
is_sample
verdict
execution_time_ms
memory_kb
input_text
expected_output_text
actual_output
error_message
created_at
```

Notes:

- Sample cases may store input, expected output, and actual output.
- Hidden cases keep those content fields null.
- `not_run` marks cases skipped after the total execution budget.
- `test_case_id` uses `on delete set null`.

## mistake_notes

Implemented in Post-MVP Phase 8. Not part of MVP v0.1.

```text
id
user_id
problem_id
topic_id
code_review_id
title
error_type
root_cause
wrong_code
fixed_code
fix_suggestion
ai_summary
user_reflection
review_status
resolved_at
created_at
updated_at
```

Notes:

- `root_cause` records the underlying reason.
- `fix_suggestion` records concrete repair guidance.
- `review_status` can be `open`, `reviewing`, or `resolved`.
- `problem_id`, `topic_id`, and `code_review_id` are optional links and use `on delete set null`.
- Mistake notes are user-owned and must be queried by current backend user.
- Phase 8 does not use mistake notes for Dashboard recommendation or RAG.

## chat_sessions

```text
id
user_id
title
mode
created_at
updated_at
```

## chat_messages

```text
id
session_id
role
content
model
created_at
```

## code_reviews

Implemented in Post-MVP Phase 8. Not part of MVP v0.1.

```text
id
user_id
topic_id
problem_id
language
question
code
analysis_result
model
prompt_type
input_tokens
output_tokens
created_at
updated_at
```

Notes:

- Code reviews are saved only when the user explicitly clicks save.
- Storing full code and full AI analysis is allowed here because this is user-owned product data.
- `ai_call_logs` must not duplicate full code, full prompts, API keys, or provider responses.
- `problem_id` and `topic_id` are optional links and use `on delete set null`.
- Phase 8 does not run code or judge submissions.

## prompt_templates

```text
id
name
type
version
template_key
file_path
content
input_schema_json
output_schema_json
enabled
created_at
updated_at
```

File template relationship:

- files provide default seed templates
- database rows provide active runtime templates
- `template_key` connects file and database versions
- `file_path` records the template source

## ai_call_logs

```text
id
user_id
provider
model
prompt_type
input_tokens
output_tokens
latency_ms
success
error_code
error_message
created_at
```

By default, do not store:

- full prompt
- full user code
- full model response
- API keys

## recommendation_logs

Deferred after Post-MVP Phase 12. Not implemented in MVP v0.1 and not implemented by Phase 12.

Phase 12 recommendation and weakness analysis is computed in real time from existing user-owned records:

- `learning_records`
- `mistake_notes`
- `submissions`
- `problems`
- `problem_tags`

No migration is created for recommendation logging in Phase 12.

```text
id
user_id
recommendation_type
reason
payload_json
created_at
```
