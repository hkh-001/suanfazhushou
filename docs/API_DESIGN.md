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

Phase 12 dashboard recommendation additions:

- `GET /api/dashboard/summary` additionally returns:
  - `weak_topics`
  - `recommendation_actions`
  - `practice_recommendations`
- These fields are computed from the current user's learning records, unresolved mistake notes, failed submissions, and personal problem bank.
- `weak_topics` include only published topics with a concrete current-user signal.
- `recommendation_actions` complement `review_queue` and `next_steps`; they do not replace the Phase 4 learning-record flow.
- Recommendations are rule-based and do not call AI Provider, Prompt templates, RAG, or `recommendation_logs`.

Phase 18 dashboard ladder recommendation additions:

- `GET /api/dashboard/summary` additionally returns `ladder_progress`, or `null` when the current user has no active ladder path.
- `ladder_progress` summarizes the current user's active path, current node, material/practice/exam counts, and next action.
- `recommendation_actions` may include ladder actions:
  - `read_ladder_material`
  - `complete_ladder_practice`
  - `take_ladder_exam`
  - `retry_ladder_exam`
- Ladder actions use `target_type="ladder_node"` and link to `/ladder?node_id={id}` on the frontend.
- These recommendations are still rule-based and do not call AI Provider, Prompt templates, RAG, or `recommendation_logs`.

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

Phase 18 AI context notes:

- AI tutoring, problem generation, code review, submission diagnosis, and ladder exam generation receive a short learning-background block.
- The block contains profile fields and a concise active-ladder summary only.
- Context truncation is character-based in Phase 18; no tokenizer is introduced.
- Full ladder material, practice answer keys, exam answer keys, full exam payloads, and full learning history are not sent to the AI provider.

Auth:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

Phase 5 auth rules:

- Auth uses an HttpOnly `algomentor_session` Cookie with JWT access token.
- Auth responses return user data only; they do not return JWTs or `hashed_password`.
- Phase 13 upgrades auth to student accounts and initial learning profiles.
- Register accepts `student_id`, `password`, `name`, `current_level`, `goal_track`, and optional `goal_description`.
- Successful registration marks the initial learning profile as completed by setting `onboarding_completed_at`.
- Register duplicate student id returns `STUDENT_ID_ALREADY_EXISTS`.
- Login accepts `student_id` and `password`.
- Login invalid student id or password returns `INVALID_CREDENTIALS` without revealing whether the user exists.
- `GET /api/auth/me` returns `student_id`, `name`, `current_level`, `goal_track`, and `goal_description`.
- `email`, `username`, `learning_stage`, and `target_track` remain compatibility fields but are not user-facing registration fields after Phase 13; clients should not depend on `email` or `username` for display or login behavior.
- Logout clears the Cookie only; it does not disable development-user fallback.
- `GET /api/auth/me` returns the real Cookie user first.
- `GET /api/auth/me` may fallback to dev user only when the Cookie is missing and `ENABLE_DEV_USER=true`.
- If a Cookie exists but is expired, invalid, or references a missing user, the backend returns `TOKEN_EXPIRED`, `TOKEN_INVALID`, or `INVALID_SESSION` and does not fallback to dev user.
- Phase 16 adds a minimal `role=user|admin` field. It is only used for public problem maintenance and is not a full RBAC, classroom, or teacher system.
- `ENABLE_DEV_USER=false` is the default after Phase 16. If explicitly enabled, dev fallback resolves to a normal user, not admin.

Settings:

- `GET /api/settings/ai`
- `PUT /api/settings/ai`
- `DELETE /api/settings/ai`
- `POST /api/settings/ai/test`

Phase 4.5 AI settings rules:

- `GET /api/settings/ai` returns the current effective AI configuration status and never returns an API key.
- Settings response includes:
  - `configured`
  - `source`: `runtime`, `persistent`, `env`, or `none`
  - `provider`
  - `base_url`
  - `model`
  - `api_key_set`
  - `runtime_settings_enabled`
- `base_url` must be displayed without query string or fragment.
- `PUT`, `DELETE`, and `POST /api/settings/ai/test` require `ENABLE_RUNTIME_AI_SETTINGS=true`.
- If runtime settings are disabled, mutating/test endpoints return `403` with `FEATURE_DISABLED`.
- `PUT /api/settings/ai` stores configuration in backend process memory and, when `ENABLE_PERSISTENT_AI_SETTINGS=true`, writes the local ignored persistent settings file.
- Runtime AI settings are global/shared for the backend service. They are not stored per user.
- Persistent settings survive backend restarts and are reported as `source="persistent"` until replaced by an in-memory runtime update.
- `PERSISTENT_AI_SETTINGS_PATH` may be absolute or relative; relative paths are resolved from the backend project directory.
- `DELETE /api/settings/ai` clears both runtime memory and the local persistent settings file when persistent settings are enabled.
- Runtime settings are convenient local/shared configuration, not production secret management.
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
- `GET /api/problems/public?page=1&page_size=20`
- `GET /api/problems/public/{id}`

Rules:

- All problem APIs require `get_current_user`.
- Ownership comes from the backend session; the frontend must not send `user_id`.
- Personal list and detail endpoints return only non-public problems owned by the current user.
- Public list and detail endpoints return public problems to any authenticated user.
- Admin users may create, update, and delete public problems.
- Normal users may view and submit public problems, but may not create, update, or delete them.
- `ProblemListItem` and `ProblemDetail` include `is_public`, `can_edit`, and `can_delete`.
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
- Phase 16 submission creation accepts either the current user's personal problem or a public problem.

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
- `PUBLIC_PROBLEM_FORBIDDEN`
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
- The problem must either belong to the current user or be public, and it must contain test cases.
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

## Phase 11 Submission Diagnosis API

Implemented in Post-MVP Phase 11:

- `POST /api/submissions/{id}/ai-diagnose`

Rules:

- Requires the owning current user and a persisted submission.
- Accepts no request body and never accepts source code, verdict, case data, or user id from the frontend.
- Supports `compile_error`, `wrong_answer`, `runtime_error`, `time_limit_exceeded`, `memory_limit_exceeded`, and `output_limit_exceeded`.
- `accepted` and `internal_error` return `SUBMISSION_DIAGNOSIS_NOT_AVAILABLE`.
- Does not check Judge availability, rerun code, or modify the stored verdict.
- Source, problem, compiler, and failed-case context are bounded before the Prompt is rendered.
- Hidden case names and content are never included in the Prompt.
- The result is not persisted automatically; users may explicitly save it through `POST /api/code-reviews`.

Response includes:

- `submission_id`
- authoritative `verdict`
- Markdown `result`
- model and token usage metadata
- `context_info.code_truncated`
- `context_info.problem_context_included`
- `context_info.failed_case_count_included`

Errors:

- `SUBMISSION_NOT_FOUND`
- `SUBMISSION_DIAGNOSIS_NOT_AVAILABLE`
- `PROMPT_TEMPLATE_NOT_FOUND`
- existing AI configuration/provider errors
- inherited auth errors

## Phase 14-17 Learning Ladder APIs

Implemented across Post-MVP Phase 14-17:

- `GET /api/ladder`
- `GET /api/ladder/nodes/{id}`
- `POST /api/ladder/nodes/{id}/material-complete`
- `POST /api/ladder/nodes/{id}/practice-submit`
- `POST /api/ladder/nodes/{id}/exam-generate`
- `GET /api/ladder/exams/{id}`
- `POST /api/ladder/exams/{id}/submit`

Rules:

- All ladder APIs require `get_current_user`.
- `GET /api/ladder` returns the current user's active path or creates one from a default template.
- Template selection uses the user's `goal_track` and `current_level`, then falls back to the closest lower level and finally `self_study/beginner`.
- Each user may have only one active path.
- Path creation expands the selected template into `learning_path_nodes` and creates one `node_user_progress` row per node.
- Phase 15 copies seeded `practice_items` from template data into `learning_path_nodes` when the path is created; already generated paths do not automatically follow later template updates.
- Node status is computed from progress booleans and is not stored as a separate database column.
- The first node is unlocked by default.
- Phase 17 changes the unlock rule: node N+1 unlocks only after node N has `exam_passed=true`.
- `POST /api/ladder/nodes/{id}/material-complete` is idempotent for already completed unlocked nodes and returns the full updated ladder summary.
- `GET /api/ladder/nodes/{id}` returns public practice items but never returns `correct_option_id`.
- `POST /api/ladder/nodes/{id}/practice-submit` accepts choice answers and coding self-check confirmations, scores choices on the backend, and returns per-choice correctness plus the updated full ladder summary.
- `practice_completed` is set when the score is at least 80 and all coding self-check items are confirmed.
- Coding practice is self-check only; it does not execute code, create submissions, call Judge, or call AI.
- `POST /api/ladder/nodes/{id}/exam-generate` requires an unlocked node with `material_completed=true` and `practice_completed=true`.
- Exam generation is explicit. Existing unsubmitted `generated` attempts are reused instead of calling AI again.
- Generated exams contain 10 `single_choice` questions worth 6 points each and 2 `code_reading` questions worth 20 points each.
- `GET /api/ladder/exams/{id}` hides `correct_option_id` and `explanation` before submission, then returns them after submission.
- `POST /api/ladder/exams/{id}/submit` requires exactly 12 answers, scores deterministically from the stored answer key, marks `exam_passed=true` at 80 or above, and returns the updated full ladder summary.
- Phase 17 AI only generates exam questions. It does not score answers, call Judge, create submissions, run user code, use RAG, or call recommendation services.
- Code-related exam questions are code reading or code completion multiple-choice questions only.
- Locked nodes return `NODE_LOCKED`.
- Practice submission before material completion returns `NODE_MATERIAL_REQUIRED`.
- Other users' nodes return `LADDER_NODE_NOT_FOUND`.

Response shape:

```text
GET /api/ladder -> DataResponse[LadderSummary]
GET /api/ladder/nodes/{id} -> DataResponse[LadderNodeDetail]
POST /api/ladder/nodes/{id}/material-complete -> DataResponse[LadderSummary]
POST /api/ladder/nodes/{id}/practice-submit -> DataResponse[LadderPracticeSubmitResult]
POST /api/ladder/nodes/{id}/exam-generate -> DataResponse[LadderExamGenerationResult]
GET /api/ladder/exams/{id} -> DataResponse[LadderExamAttemptDetail]
POST /api/ladder/exams/{id}/submit -> DataResponse[LadderExamSubmitResult]
```

Errors:

- `LADDER_TEMPLATE_NOT_FOUND`
- `LADDER_NODE_NOT_FOUND`
- `LADDER_PATH_CREATE_FAILED`
- `LADDER_PRACTICE_NOT_FOUND`
- `LADDER_PRACTICE_VALIDATION_ERROR`
- `LADDER_EXAM_NOT_FOUND`
- `LADDER_EXAM_ALREADY_PASSED`
- `LADDER_EXAM_REQUIRE_MATERIAL`
- `LADDER_EXAM_REQUIRE_PRACTICE`
- `LADDER_EXAM_GENERATION_FAILED`
- `LADDER_EXAM_VALIDATION_ERROR`
- `NODE_LOCKED`
- `NODE_MATERIAL_REQUIRED`
- inherited AI errors: `AI_CONFIG_MISSING`, `AI_PROVIDER_TIMEOUT`, `AI_PROVIDER_ERROR`, `PROMPT_TEMPLATE_NOT_FOUND`
- inherited auth errors

## Phase 19A OpenMAIC POC APIs

Phase 19A adds admin-only backend POC endpoints for validating an external OpenMAIC service. These endpoints are not user-facing product APIs and do not persist lesson records.

```text
GET /api/openmaic/poc/status
POST /api/openmaic/poc/generate
GET /api/openmaic/poc/jobs/{job_id}
```

Rules:

- `ENABLE_OPENMAIC_INTEGRATION=false` disables all POC endpoints with `FEATURE_DISABLED`.
- Only `role=admin` can call the POC endpoints; normal users receive `ADMIN_REQUIRED`.
- The frontend must not call OpenMAIC directly.
- OpenMAIC auth values, provider keys, access codes, and raw service errors are never returned.
- Prefer `header` auth when possible. `query` auth may appear in upstream logs, and `body` auth may not work for GET job polling through some gateways.
- Generate requests send only a bounded Chinese classroom requirement, `language="zh-CN"`, and disabled TTS/image/video/web search flags.

`POST /api/openmaic/poc/generate` request:

```json
{
  "title": "双指针入门",
  "audience_level": "入门",
  "goal": "蓝桥杯基础训练",
  "summary": "讲解左右指针、快慢指针和常见边界错误。"
}
```

Response shape:

```text
GET /api/openmaic/poc/status -> DataResponse[OpenMAICPocStatus]
POST /api/openmaic/poc/generate -> DataResponse[OpenMAICJobStatus]
GET /api/openmaic/poc/jobs/{job_id} -> DataResponse[OpenMAICJobStatus]
```

Errors:

- `FEATURE_DISABLED`
- `ADMIN_REQUIRED`
- `OPENMAIC_CONFIG_MISSING`
- `OPENMAIC_TIMEOUT`
- `OPENMAIC_UNAVAILABLE`
- `OPENMAIC_INVALID_RESPONSE`
- `OPENMAIC_JOB_NOT_FOUND`
- inherited auth errors

## Phase 19B-19C Interactive Lesson APIs

Phase 19B adds user-triggered topic interactive lessons through the backend OpenMAIC adapter. Phase 19C extends the same lesson metadata flow to learning ladder nodes.

```text
POST /api/topics/{topic_id}/interactive-lessons?force=false
POST /api/ladder/nodes/{node_id}/interactive-lessons?force=false
GET /api/interactive-lessons/{lesson_id}
POST /api/interactive-lessons/{lesson_id}/refresh
```

Rules:

- All endpoints require `get_current_user`.
- `topic_id` must point to a `published` topic; missing or unpublished topics return `TOPIC_NOT_FOUND`.
- `POST /api/topics/{topic_id}/interactive-lessons` is an explicit user action and never runs automatically.
- `POST /api/ladder/nodes/{node_id}/interactive-lessons` is an explicit user action for current-user active-path nodes only.
- If the same user already has a recent `submitted`, `processing`, or `completed` lesson for the same topic, the backend returns that lesson instead of calling OpenMAIC again.
- If the same user already has a recent `submitted`, `processing`, or `completed` lesson for the same ladder node, the backend returns that lesson instead of calling OpenMAIC again.
- `force=true` skips reusable `submitted`, `processing`, or `completed` lessons and creates a new OpenMAIC generation request.
- `failed` lessons are not reused; users may retry generation.
- The frontend calls only AlgoMentor APIs and never calls OpenMAIC directly.
- The backend sends only topic title/category/level/summary/content excerpt plus current profile level and goal track.
- Ladder-node lessons send only node title, summary, phase/node index, bounded material excerpt, completion booleans, and current profile level and goal track.
- The backend does not send student id, full learning history, code, submissions, hidden tests, private notes, ladder exam payloads, or answer keys.
- Ladder-node lessons do not send `practice_items`, choice answer keys, full exam payloads, or exam answer keys.
- `refresh` performs a single OpenMAIC poll and does not long-poll.
- `OPENMAIC_MAX_POLL_MINUTES` is used as a stale guard during refresh. Stale active lessons are marked `failed` with `OPENMAIC_STALE_PENDING` after a final poll when a job id exists.
- OpenMAIC `unknown` status is returned and stored as `processing`.
- `completed` requires a classroom URL; otherwise the lesson remains `processing` or becomes `failed`.
- OpenMAIC lessons never mutate learning records, ladder `material_completed`, `practice_completed`, `exam_passed`, submissions, or AI logs.

Response:

```json
{
  "data": {
    "id": "uuid",
    "source_type": "topic",
    "topic_id": "uuid",
    "node_id": null,
    "provider": "openmaic",
    "status": "processing",
    "title": "双指针互动课堂",
    "classroom_url": null,
    "error_code": null,
    "error_message": null,
    "created_at": "2026-06-27T00:00:00Z",
    "updated_at": "2026-06-27T00:00:00Z",
    "completed_at": null
  }
}
```

Errors:

- `INTERACTIVE_LESSON_NOT_FOUND`
- `INTERACTIVE_LESSON_GENERATION_FAILED`
- `LADDER_NODE_NOT_FOUND`
- `NODE_LOCKED`
- `FEATURE_DISABLED`
- `OPENMAIC_CONFIG_MISSING`
- `OPENMAIC_TIMEOUT`
- `OPENMAIC_UNAVAILABLE`
- `OPENMAIC_INVALID_RESPONSE`
- `OPENMAIC_JOB_NOT_FOUND`
- `OPENMAIC_AUTH_FAILED`
- `OPENMAIC_STALE_PENDING`
- `TOPIC_NOT_FOUND`
- inherited auth errors

## Post-MVP Planned APIs

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
