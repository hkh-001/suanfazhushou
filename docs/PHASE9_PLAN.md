# Phase 9 Plan: ZIP Problem Import With Test Cases

## 1. Scope And Boundaries

Phase 9 adds safe ZIP import for one user-owned problem package at a time.

Included:

- Upload one ZIP package through `POST /api/problems/import/zip`.
- Parse problem metadata, statement text, optional support files, and `.in` / `.out` test cases.
- Create one current-user-owned `problems` row and related `test_cases` rows in one transaction.
- Reuse Phase 6-7 problem ownership, slug, topic visibility, and `display_id` rules.
- Store imported test cases as UTF-8 text data.

Not included:

- Running uploaded files.
- Code execution, judge, sandbox, OJ, submissions, or verdicts.
- Saving original ZIP archives.
- Batch import of multiple problems.
- Public publishing workflow.

Phase 10 interface reserve:

- `test_cases` stores input/output text and sample flags for a future judge.
- `is_hidden` is reserved for Phase 10 and defaults to `false` in Phase 9.
- Judge/sandbox design must remain separate from ZIP parsing.

## 2. Data Model Design

Implemented table: `test_cases`.

```text
id UUID primary key
problem_id UUID not null references problems(id) on delete cascade
case_index integer not null
name varchar(120) nullable
input_text text not null
expected_output_text text not null
is_sample boolean not null default false
is_hidden boolean not null default false
created_at timestamptz not null default now()
updated_at timestamptz not null default now()
```

Constraints and indexes:

- `UNIQUE(problem_id, case_index)`
- `CHECK(case_index > 0)`
- index on `problem_id`
- index on `(problem_id, case_index)`

`problems` table changes:

- No new `problems` columns in Phase 9.
- Imported problems use existing fields:
  - `source="zip_import"`
  - `source_url` from `problem.json`, optional
  - `is_ai_generated=false`
  - `is_published=false`
  - `sample_input` / `sample_output` from the selected sample test case

Alembic migration:

- `20260613_0006_add_test_cases.py`
- Downgrade drops indexes before dropping `test_cases`.

## 3. ZIP Package Format

Supported root layout:

```text
problem.json
statement.md
solution.md
input_format.md
output_format.md
constraints.md
tests/01.in
tests/01.out
tests/02.in
tests/02.out
```

Supported single-top-level layout:

```text
problem-package/problem.json
problem-package/statement.md
problem-package/tests/01.in
problem-package/tests/01.out
```

Rules:

- Either all files are in ZIP root, or all files are under one top-level directory.
- Multiple top-level directories are rejected.
- Mixing root files and top-level directories is rejected.
- Nested directories outside `tests/` are rejected.
- `tests/` may contain only direct `{name}.in` and `{name}.out` files.
- All text files must be UTF-8.

Required files:

- `problem.json`
- `statement.md`
- at least one paired `tests/{name}.in` and `tests/{name}.out`

Optional files:

- `solution.md`
- `input_format.md`
- `output_format.md`
- `constraints.md`

`problem.json` fields:

```json
{
  "title": "Range Sum Query",
  "slug": "range-sum-query",
  "difficulty": "basic",
  "estimated_minutes": 30,
  "source_url": "https://example.com/source",
  "topic_ids": ["00000000-0000-0000-0000-000000000000"],
  "sample_case_names": ["01"]
}
```

Field rules:

- `title`: required, 1-160 chars
- `slug`: optional, normalized by backend; unique only within current user
- `difficulty`: `beginner | basic | intermediate | advanced`
- `estimated_minutes`: optional positive integer
- `source_url`: optional, max 500 chars
- `topic_ids`: optional list of published topic UUIDs
- `sample_case_names`: optional list of case names without `.in` / `.out`

Sample behavior:

- If `sample_case_names` is present, matching cases are marked `is_sample=true`.
- If absent, the first naturally sorted test case is the sample.
- `problems.sample_input` and `problems.sample_output` come from the first sample case.

Natural sorting:

- Numeric path fragments sort numerically, so `2` comes before `10`.

## 4. Security Strategy

Default limits:

```text
ZIP_MAX_BYTES = 10 MB
ZIP_MAX_FILES = 50
ZIP_MAX_UNCOMPRESSED_BYTES = 2 MB
ZIP_MAX_SINGLE_FILE_BYTES = 512 KB
ZIP_MAX_COMPRESSION_RATIO = 20
TEST_CASE_MAX_COUNT = 100
TEST_CASE_MAX_INPUT_BYTES = 256 KB
TEST_CASE_MAX_OUTPUT_BYTES = 256 KB
```

Rejected inputs:

- `../`
- absolute paths
- Windows drive paths
- backslash path bypasses
- symbolic link entries
- encrypted entries
- duplicate logical paths
- unsupported extensions
- oversized files
- excessive uncompressed content
- abnormal compression ratios
- invalid UTF-8
- invalid JSON
- unpaired `.in` / `.out` files

Allowed extensions:

```text
.json
.md
.in
.out
```

Phase 9 never executes uploaded files. Uploaded content is parsed only as bounded text data.

## 5. API Design

Endpoint:

```text
POST /api/problems/import/zip
```

Request:

```text
multipart/form-data
file=<problem.zip>
```

Success response:

```json
{
  "data": {
    "problem": {
      "id": "...",
      "display_id": 1,
      "source": "zip_import"
    },
    "test_cases_count": 2
  }
}
```

Representative error codes:

- `ZIP_FILE_REQUIRED`
- `ZIP_INVALID_ARCHIVE`
- `ZIP_FILE_TOO_LARGE`
- `ZIP_FILE_COUNT_EXCEEDED`
- `ZIP_UNCOMPRESSED_SIZE_EXCEEDED`
- `ZIP_COMPRESSION_RATIO_EXCEEDED`
- `ZIP_PATH_NOT_ALLOWED`
- `ZIP_FILE_TYPE_NOT_ALLOWED`
- `ZIP_DUPLICATE_PATH`
- `ZIP_INVALID_ENCODING`
- `ZIP_INVALID_JSON`
- `ZIP_PROBLEM_METADATA_INVALID`
- `ZIP_STATEMENT_REQUIRED`
- `ZIP_TEST_CASE_REQUIRED`
- `ZIP_TEST_CASE_PAIR_MISMATCH`
- `ZIP_TEST_CASE_LIMIT_EXCEEDED`
- `PROBLEM_SLUG_ALREADY_EXISTS`
- `TOPIC_NOT_FOUND`
- inherited auth errors

Processing is synchronous in Phase 9.

## 6. Backend Implementation Plan

Implementation uses standard library `zipfile` and `io.BytesIO`.

Parsing flow:

1. Read upload bytes with a hard max.
2. Open with `zipfile.ZipFile`.
3. Validate entry count, path safety, extension allowlist, sizes, compression ratio, encryption, and symlink status.
4. Normalize root or single-top-level layout into logical paths.
5. Decode UTF-8 text content.
6. Parse and validate `problem.json`.
7. Pair and naturally sort test cases.
8. Resolve published topics.
9. Allocate current-user `display_id`.
10. Create problem and test cases in one database transaction.

Transaction strategy:

- Problem and test cases commit together.
- Any parse, validation, topic, or database error rolls back the import.

## 7. Frontend Implementation Plan

Page:

```text
/problems/import
```

UI:

- `AppShell + PageHeader`
- ZIP file input
- format and security instructions
- error state with safe translated messages
- success state before navigating to `/problems/{id}`

Existing `/problems` adds a `导入 ZIP` entry.

`apiFetch` must not set JSON `Content-Type` when `body` is `FormData`; the browser must set the multipart boundary.

## 8. Testing Strategy

Backend tests:

- normal ZIP import
- current-user ownership
- `display_id` sequence integration
- `source="zip_import"`
- test cases persisted
- default and declared samples
- invalid ZIP
- empty ZIP
- path traversal
- multiple top-level directories
- root/top-level mixing
- symlink entries
- unsupported extensions
- file count and compression limits
- invalid JSON
- missing metadata or statement
- `.in` / `.out` mismatch
- test-case count boundary
- invalid UTF-8
- unpublished topic rejection
- slug conflict
- rollback on failure
- auth required when dev fallback is disabled

Frontend tests:

- `pnpm lint`
- `pnpm build`
- `/problems/import` builds
- `/problems/generate` remains available
- FormData upload avoids JSON content type

## 9. Risks And Dependencies

Dependencies:

- `python-multipart` is required for FastAPI multipart upload parsing.

Risks:

- Large uploads can pressure memory because Phase 9 reads ZIP bytes in memory.
- Test cases stored in PostgreSQL should remain bounded by strict limits.
- ZIP import must not be mistaken for judge readiness.
- Copyright risk remains with user-provided problem statements; users must import only content they have rights to use.

Sandbox:

- Phase 9 does not need Docker sandbox.
- Phase 10 must define sandbox/judge service separately before running user code.

## 10. Task Breakdown

1. Add `test_cases` schema, model, and migration.
2. Add `python-multipart` and FormData-safe `apiFetch`.
3. Add ZIP parser and security validation service.
4. Add `POST /api/problems/import/zip`.
5. Add `/problems/import` page and `/problems` entry.
6. Add tests and synchronize docs.
