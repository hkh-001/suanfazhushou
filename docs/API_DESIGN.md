# API Design

## API Principles

- All backend APIs use the `/api` prefix.
- Request and response models must use Pydantic.
- Use reasonable HTTP status codes.
- Use consistent response structures.
- Validate user input.
- Do not expose internal stack traces to frontend clients.
- List endpoints should reserve pagination.

## Response Structure

Default success response for object endpoints:

```json
{
  "data": {}
}
```

Default success response for list endpoints:

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 0
  }
}
```

Default error response:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "User-facing error message"
  }
}
```

## HTTP Status Codes

Recommended usage:

- `200 OK`: successful read or update
- `201 Created`: successful creation
- `204 No Content`: successful deletion with no body
- `400 Bad Request`: invalid request
- `401 Unauthorized`: authentication required
- `403 Forbidden`: permission denied
- `404 Not Found`: resource not found
- `409 Conflict`: conflicting state
- `422 Unprocessable Entity`: validation failure
- `500 Internal Server Error`: safe internal error message

## Pagination

List endpoints should reserve pagination parameters:

```text
page
page_size
limit
offset
```

MVP can implement `page` and `page_size` first.

## MVP v0.1 API List

Health:

- `GET /api/health`

Topics:

- `GET /api/topics`
- `GET /api/topics/{id}`

Phase 2 topic rules:

- `GET /api/topics` supports `page` and `page_size`.
- Topic list responses include current user learning status.
- Only `published` topics are returned.
- `GET /api/topics/{id}` uses UUID `id`, not slug.
- Missing topics return a safe `TOPIC_NOT_FOUND` error.

Learning:

- `POST /api/learning/records`
- `GET /api/dashboard/summary`

Phase 2 learning rules:

- `POST /api/learning/records` uses backend `get_current_user`.
- The frontend must not send `user_id`.
- Learning records are upserted by `(user_id, topic_id)`.
- Allowed statuses are `not_started`, `learning`, and `mastered`.

Phase 4 dashboard rules:

- `GET /api/dashboard/summary` keeps the Phase 2 top-level fields:
  - `total_topics`
  - `started_topics`
  - `learning_topics`
  - `mastered_topics`
  - `progress_percent`
- Phase 4 only appends structured fields:
  - `not_started_topics`
  - `total_estimated_minutes`
  - `completed_estimated_minutes`
  - `status_counts`
  - `category_progress`
  - `recent_activity`
  - `review_queue`
  - `next_steps`
- Dashboard data is scoped to the current backend user.
- Dashboard statistics only include `published` topics.
- `review_queue` is derived from existing `learning_records`; no `mistake_notes` table is required in Phase 4.
- `next_steps` are rule-based:
  - recommend published topics without a current user learning record first
  - if all topics are started, recommend non-mastered topics
  - if all topics are mastered, return an empty list
- Dashboard recommendations do not call the AI Provider and do not query `prompt_templates`.

AI:

- `POST /api/ai/chat`
- `POST /api/ai/code-review`
- `POST /api/ai/generate-problem`

Phase 3 AI rules:

- All AI responses use `{ "data": { "result": "...", "prompt_type": "...", "model": "...", "usage": { "input_tokens": null, "output_tokens": null } } }`.
- `POST /api/ai/chat` accepts `topic_id`, `question`, and `mode`.
- `POST /api/ai/code-review` accepts `topic_id`, `language`, `code`, and optional `question`.
- `POST /api/ai/generate-problem` accepts `topic_id`, `difficulty`, and optional `requirements`.
- AI configuration errors return `AI_CONFIG_MISSING`.
- Provider timeout returns `AI_PROVIDER_TIMEOUT`.
- Provider non-2xx or invalid provider responses return `AI_PROVIDER_ERROR`.
- Generated problem parse failures return `AI_OUTPUT_PARSE_ERROR`.
- Missing runtime prompt templates return `PROMPT_TEMPLATE_NOT_FOUND`.
- The backend must not expose provider stack traces or full provider responses.

Settings:

- `GET /api/settings/ai`
- `PUT /api/settings/ai`
- `DELETE /api/settings/ai`
- `POST /api/settings/ai/test`

Phase 4.5 AI settings rules:

- `GET /api/settings/ai` returns the current effective AI configuration status and never returns an API key.
- Settings response includes:
  - `configured`
  - `source`: `runtime`, `env`, or `none`
  - `provider`
  - `base_url`
  - `model`
  - `api_key_set`
  - `runtime_settings_enabled`
- `base_url` must be displayed without query string or fragment.
- `PUT`, `DELETE`, and `POST /api/settings/ai/test` require `ENABLE_RUNTIME_AI_SETTINGS=true`.
- If runtime settings are disabled, mutating/test endpoints return `403` with `FEATURE_DISABLED`.
- `PUT /api/settings/ai` stores configuration only in backend process memory.
- Runtime settings are for local development and demos, not production secret management.
- `POST /api/settings/ai/test` sends a minimal provider request and must not log API keys, full prompts, or full provider responses.

Post-MVP future APIs:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/users/me`
- `GET /api/problems`
- `GET /api/problems/{id}`
- `GET /api/mistakes`
- `POST /api/mistakes`
- `PUT /api/mistakes/{id}`
- `DELETE /api/mistakes/{id}`

## Error Handling

Rules:

- Return clear user-facing messages.
- Log detailed errors on the backend.
- Never expose stack traces to frontend users.
- AI provider errors should return safe API errors.
- Validation errors should identify invalid fields where practical.
- Disabled runtime AI settings should return `FEATURE_DISABLED`.

## API Versioning

MVP can use `/api` without explicit versioning.

Future production APIs may use:

```text
/api/v1
```
