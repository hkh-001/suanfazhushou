# Database Design

## Design Principles

- Use English table and column names.
- Keep PostgreSQL compatibility.
- Manage schema changes through Alembic.
- Keep SQLAlchemy models, Pydantic schemas, and migrations consistent.
- Separate seed data from schema migrations where practical.
- Store AI logs as metadata by default, not full prompts or full user code.

## Core Tables

MVP core tables:

- `users`
- `user_settings`
- `topics`
- `topic_dependencies`
- `problems`
- `problem_tags`
- `learning_records`
- `mistake_notes`
- `chat_sessions`
- `chat_messages`
- `code_reviews`
- `prompt_templates`
- `ai_call_logs`
- `recommendation_logs`

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

```text
id
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
- `is_ai_generated=true` is required for AI-generated problems.
- `is_published` controls whether the problem is visible.
- Avoid copying complete third-party statements unless the license allows it.

## problem_tags

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

```text
id
user_id
problem_id
topic_id
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

```text
id
user_id
language
code
analysis_result
created_at
```

Note: store full submitted code only where the product explicitly requires it. AI logs should not duplicate full code by default.

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
error_message
created_at
```

By default, do not store:

- full prompt
- full user code
- full model response
- API keys

## recommendation_logs

```text
id
user_id
recommendation_type
reason
payload_json
created_at
```
