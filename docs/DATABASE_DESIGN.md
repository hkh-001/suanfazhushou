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

Current database reality is the Phase 0-4 implemented schema. Deferred tables below are planning notes only. They must not be treated as existing tables until their Post-MVP phase creates an Alembic migration.

## Deferred Post-MVP Tables

| Table | Planned Phase | Purpose | Boundary |
| --- | --- | --- | --- |
| `problems` | Phase 6 | Personal problem bank records | Implemented in Post-MVP Phase 6 |
| `problem_tags` | Phase 6 | Connect problems to topics | Implemented in Post-MVP Phase 6 |
| `test_cases` | Phase 9 | Imported or authored problem test cases | Wait for ZIP/test-case validation policy |
| `submissions` | Phase 10 | Judge submissions and verdicts | Wait for sandbox/judge design |
| `code_reviews` | Phase 8 | Explicitly saved AI code review results | Implemented in Post-MVP Phase 8 |
| `mistake_notes` | Phase 8 | User-owned mistake notebook entries | Implemented in Post-MVP Phase 8 |
| `recommendation_logs` | Phase 12 | Recommendation events and explanations | Wait for weakness analysis model |
| `knowledge_chunks` | Phase 13 | Retrieval units for RAG | Wait for content scale and retrieval design |
| `retrieval_logs` | Phase 13 | Retrieval evaluation and trace metadata | Must avoid sensitive content leakage |

Judging-related tables such as `test_cases` and `submissions` must wait until the sandbox approach is defined. Do not add these tables only to satisfy UI placeholders.

## users

```text
id
email
username
hashed_password
learning_stage
target_track
created_at
updated_at
```

MVP may use a default development user instead of full registration and login.

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

Implemented in Post-MVP Phase 6. Phase 7 reuses this table to store explicitly saved AI-generated problems. Not part of MVP v0.1.

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
- `is_published` is reserved for future publishing; Phase 6 problem bank shows only the current user's own problems.
- `created_by_user_id` owns the problem and must come from backend auth, not frontend input.
- `(created_by_user_id, slug)` is unique; slug is not globally unique.
- `(created_by_user_id, display_id)` is unique and provides a per-user visible sequence such as `#1`.
- Deleted `display_id` values are not reused.
- Avoid copying complete third-party statements unless the license allows it.
- Phase 6 and Phase 7 do not create submissions, test cases, judging records, or mistake notes.

## user_problem_counters

Implemented in Post-MVP Phase 6 follow-up. Not part of MVP v0.1.

```text
user_id
next_display_id
updated_at
```

Notes:

- Used only to allocate per-user problem `display_id` values.
- `next_display_id` increments when a manual or AI-generated problem is created.
- Hard delete does not decrement the counter, so display ids are not reused.

## problem_tags

Implemented in Post-MVP Phase 6. Not part of MVP v0.1.

```text
id
problem_id
topic_id
created_at
```

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

Planned for Post-MVP Phase 12. Not implemented in MVP v0.1.

```text
id
user_id
recommendation_type
reason
payload_json
created_at
```
