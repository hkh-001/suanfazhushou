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

## MVP API List

Health:

- `GET /api/health`

Topics:

- `GET /api/topics`
- `GET /api/topics/{id}`

Learning:

- `POST /api/learning/records`
- `GET /api/dashboard/summary`

AI:

- `POST /api/ai/chat`
- `POST /api/ai/code-review`
- `POST /api/ai/generate-problem`

Future APIs:

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

## API Versioning

MVP can use `/api` without explicit versioning.

Future production APIs may use:

```text
/api/v1
```
