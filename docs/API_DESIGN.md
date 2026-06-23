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

Auth:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

Phase 5 auth rules:

- Auth uses an HttpOnly `algomentor_session` Cookie with JWT access token.
- Auth responses return user data only; they do not return JWTs or `hashed_password`.
- Register accepts `email`, `username`, and `password`; `learning_stage` and `target_track` default to `beginner` and `algorithm_basics`.
- Register duplicate email returns `EMAIL_ALREADY_REGISTERED`.
- Register duplicate username returns `USERNAME_ALREADY_TAKEN`.
- Login invalid email or password returns `INVALID_CREDENTIALS` without revealing whether the user exists.
- Logout clears the Cookie only; it does not disable development-user fallback.
- `GET /api/auth/me` returns the real Cookie user first.
- `GET /api/auth/me` may fallback to dev user only when the Cookie is missing and `ENABLE_DEV_USER=true`.
- If a Cookie exists but is expired, invalid, or references a missing user, the backend returns `TOKEN_EXPIRED`, `TOKEN_INVALID`, or `INVALID_SESSION` and does not fallback to dev user.
- Phase 5 does not include RBAC, OAuth, refresh tokens, password reset, sessions table, or production permission management.

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

## Phase 6 Problem Bank APIs

Implemented across Post-MVP Phase 6-9. These APIs are not part of MVP v0.1, but are current Post-MVP contracts.

- `POST /api/problems`
- `GET /api/problems?page=1&page_size=20`
- `GET /api/problems/{id}`
- `PUT /api/problems/{id}`
- `DELETE /api/problems/{id}`
- `POST /api/problems/save-ai-generated`
- `POST /api/problems/import/zip`

Rules:

- All problem APIs require `get_current_user`.
- Ownership comes from the backend session; the frontend must not send `user_id`.
- List and detail endpoints only return problems owned by the current user.
- List and detail responses include `display_id`, a per-user visible sequence number.
- Other users' problems return `PROBLEM_NOT_FOUND`.
- `GET /api/problems` returns `PaginatedResponse` and sorts by `created_at DESC, id DESC`.
- `slug` is unique per user through `(created_by_user_id, slug)`.
- `display_id` is unique per user through `(created_by_user_id, display_id)`.
- `DELETE /api/problems/{id}` hard-deletes the current user's problem.
- Hard delete does not reuse `display_id`; future submissions, mistake notes, or judge records may require a soft-delete strategy.
- `topic_ids` can associate problems with currently visible published topics.
- `/api/problems` returns the current user's own problems and does not filter by `is_published`.
- Phase 7 persists AI-generated problems only when the user explicitly clicks save.
- `POST /api/problems/save-ai-generated` must be registered before `/api/problems/{id}` so `save-ai-generated` is not parsed as a problem id.
- Saved generated problems force `is_ai_generated=true`, `source="ai_generated"`, `is_published=false`, and current-user ownership on the backend.
- Saved generated problems share the same per-user `display_id` sequence as manually created problems.
- Phase 9 imports ZIP problem packages only through explicit user upload.
- ZIP imports force `source="zip_import"`, `is_ai_generated=false`, `is_published=false`, and current-user ownership on the backend.
- ZIP imports persist `.in` / `.out` files as `test_cases`; Phase 9 does not execute those files.
- Problem bank APIs still do not create submissions or judge code.

ZIP import contract:

- Request: `multipart/form-data`, field name `file`.
- Response: `DataResponse[{ problem, test_cases_count }]`.
- `problem` uses the same `ProblemDetail` shape as manual and AI-saved problem APIs.
- The endpoint must be registered before `/api/problems/{id}` so `import/zip` is not parsed as a problem id.
- Accepted package files: `problem.json`, `statement.md`, optional `.md` support files, and paired `tests/{name}.in` / `tests/{name}.out`.
- The backend rejects invalid ZIP archives, path traversal, unsafe paths, symbolic links, encrypted entries, duplicate logical paths, unsupported extensions, unsafe compression ratios, oversized files, invalid JSON, invalid UTF-8, missing statement, and unmatched test-case pairs.

Problem errors:

- `PROBLEM_NOT_FOUND`
- `PROBLEM_SLUG_ALREADY_EXISTS`
- `TOPIC_NOT_FOUND`
- ZIP import errors such as `ZIP_INVALID_ARCHIVE`, `ZIP_ARCHIVE_EMPTY`, `ZIP_PATH_NOT_ALLOWED`, `ZIP_FILE_TYPE_NOT_ALLOWED`, `ZIP_TEST_CASE_PAIR_MISMATCH`, and `ZIP_PROBLEM_METADATA_INVALID`
- inherited auth errors such as `AUTH_REQUIRED`, `TOKEN_EXPIRED`, `TOKEN_INVALID`, `INVALID_SESSION`

## Phase 8 Code Review And Mistake Notebook APIs

Implemented in Post-MVP Phase 8. These APIs are not part of MVP v0.1, but are current Post-MVP contracts.

Code review persistence:

- `POST /api/code-reviews`
- `GET /api/code-reviews?page=1&page_size=20`
- `GET /api/code-reviews/{id}`
- `DELETE /api/code-reviews/{id}`

Mistake notebook:

- `POST /api/mistakes`
- `GET /api/mistakes?page=1&page_size=20&status=open`
- `GET /api/mistakes/{id}`
- `PUT /api/mistakes/{id}`
- `DELETE /api/mistakes/{id}`

Rules:

- All endpoints require `get_current_user`.
- Ownership comes from the backend session; the frontend must not send `user_id`.
- Code reviews are saved only when users explicitly click save.
- Saved code reviews may store full code and full AI analysis as user-owned product data.
- `ai_call_logs` remain metadata-only and must not store full code, prompts, API keys, or provider responses.
- `problem_id`, when present, must belong to the current user.
- `code_review_id`, when present on mistake notes, must belong to the current user.
- `topic_id`, when present, must point to a published topic.
- Mistake note status can be `open`, `reviewing`, or `resolved`.
- Updating a mistake note to `resolved` sets `resolved_at`; moving it back to `open` or `reviewing` clears `resolved_at`.
- Phase 8 does not implement judging, submissions, test cases, ZIP import, RAG, code execution, or Dashboard recommendation analysis.

Phase 8 errors:

- `CODE_REVIEW_NOT_FOUND`
- `MISTAKE_NOTE_NOT_FOUND`
- `PROBLEM_NOT_FOUND`
- `TOPIC_NOT_FOUND`
- inherited auth errors such as `AUTH_REQUIRED`, `TOKEN_EXPIRED`, `TOKEN_INVALID`, `INVALID_SESSION`

## Phase 10 Submission APIs

Implemented in Post-MVP Phase 10:

- `POST /api/submissions`
- `GET /api/submissions/{id}`

Rules:

- All submission APIs require `get_current_user`.
- `POST` accepts `problem_id`, `language=cpp|python`, and `source_code` up to 20000 characters.
- The problem must belong to the current user and contain test cases.
- `ENABLE_CODE_EXECUTION=false` returns `CODE_EXECUTION_DISABLED` without creating a submission.
- Backend calls the separate Judge service asynchronously and never executes code directly.
- Judge requests are not retried.
- Full source code is returned only to the owning user.
- Sample case details may be returned; hidden case input, expected output, and actual output are always null.
- Deleted problems retain title and display-id snapshots in submission history.

Errors:

- `CODE_EXECUTION_DISABLED`
- `JUDGE_CONFIG_MISSING`
- `JUDGE_UNAVAILABLE`
- `JUDGE_TIMEOUT`
- `JUDGE_BUSY`
- `JUDGE_INVALID_RESPONSE`
- `PROBLEM_TEST_CASES_REQUIRED`
- `SUBMISSION_NOT_FOUND`

## Post-MVP Planned APIs

The APIs below remain deferred.

AI diagnosis after failed judgement, planned for Phase 11:

- `POST /api/submissions/{id}/ai-diagnose`

Planning boundaries:

- Further judge capabilities must preserve the approved isolated service and sandbox boundary.
- Upload APIs must include file size, file count, file type, and path traversal controls.
- Post-MVP APIs must preserve `/api` prefix and the existing success/error response structure.
- Current MVP v0.1 APIs must not be changed to accommodate planned APIs prematurely.

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
