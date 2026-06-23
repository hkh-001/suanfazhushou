# Phase 10 Plan: Minimal Isolated Judging System

## Summary

Phase 10 adds synchronous C++17 and Python 3.11 judging through a separate Judge service. The backend never executes user code. Each submission runs in a temporary, network-disabled, resource-limited Docker container and is persisted only for the current user.

Phase 10 does not add AI diagnosis, asynchronous queues, contests, scoring, special judges, custom test input, or additional languages.

## Architecture And Security

```text
frontend -> backend /api/submissions -> judge /internal/judge -> temporary runner container
```

- Only the Judge service may access the Docker socket.
- Judge does not connect to PostgreSQL, authenticate users, or call AI providers.
- Internal requests use `X-Judge-Token`; missing or mismatched tokens return 401 and are mapped by backend to `JUDGE_UNAVAILABLE`.
- Runner containers use no network, read-only root filesystem, `cap_drop=ALL`, `no-new-privileges`, one CPU, 512 MB memory, and no host bind mounts.
- The only writable path is a 64 MB tmpfs mounted at `/workspace`.
- Container PID limit is 128 for compilation. User programs additionally receive `RLIMIT_NPROC=64`.
- Every container is labeled with `algomentor.judge=true`, submission id, and start time.
- Judge always kills and force-removes containers in shielded cleanup. Startup and periodic cleanup remove labeled containers older than five minutes.

## Timeout And Concurrency

```text
compile timeout: 10 seconds
per-case timeout: 2 seconds
test execution budget: 30 seconds
Judge request hard deadline: 50 seconds
backend HTTP timeout: 60 seconds
```

The 30-second budget excludes compilation. Normal submissions run every test case. When the budget expires, the active case becomes `time_limit_exceeded`, remaining cases become `not_run`, and the overall verdict is `time_limit_exceeded`.

Backend and Judge each allow two concurrent submissions. A third request fails immediately with `JUDGE_BUSY`; no queue is created. Backend uses asynchronous HTTP and releases its database connection while waiting.

## Memory Handling

MLE detection uses cgroup v2 `memory.events` `oom_kill` deltas and Docker `State.OOMKilled`. Exit code 137 alone is not sufficient. If reliable OOM evidence is unavailable, exit 137 is classified as `runtime_error` with a safe message indicating possible memory exhaustion.

Runtime peak memory uses GNU `time -v` maximum resident set size. Parse failures produce `memory_kb=null`; values are never invented. These behaviors are marked for validation against the target Docker/cgroup environment.

## Database

Migration: `20260619_0007_add_submissions.py`.

`submissions` stores current-user ownership, optional problem link, problem title/display-id snapshots, language, full source code, final verdict, aggregate metrics, safe compile/error output, and timestamps.

`submission_case_results` stores case index, optional test-case link, sample flag, verdict, metrics, and safe error text. Only sample cases persist input, expected output, and actual output. Hidden cases persist no content. Remaining cases after the total budget use `not_run`.

Deleting a problem or test case sets links to null without deleting submission history.

## API

```text
POST /api/submissions
GET /api/submissions/{submission_id}
```

Create request:

```json
{
  "problem_id": "uuid",
  "language": "cpp",
  "source_code": "..."
}
```

Rules:

- Language is `cpp` or `python`.
- Source length is 1-20000 characters.
- Problem must belong to the current user and contain test cases.
- Feature-disabled and missing-config requests do not create a submission.
- Other users receive `SUBMISSION_NOT_FOUND`.
- Full source code is user-owned product data and is never logged or sent to AI.

Output comparison normalizes CRLF/CR to LF, removes line-ending spaces/tabs and trailing blank lines, then compares all remaining characters strictly. Empty expected output and a single newline both normalize to an empty string and are accepted.

## Frontend

Routes:

```text
/problems/[id]/submit
/submissions/[id]
```

The submission page provides C++/Python selection, a monospace source editor, disabled/loading/error states, and a clear isolation notice. Success navigates to the result page.

The result page shows verdict, problem snapshot, source code, aggregate metrics, and case results. Sample cases show input/expected/actual content. Hidden cases show only status and metrics.

No new top navigation item is added; submission routes remain under the personal problem bank workflow.

## Configuration

```env
ENABLE_CODE_EXECUTION=false
JUDGE_BASE_URL=http://localhost:9000
JUDGE_INTERNAL_TOKEN=
JUDGE_REQUEST_TIMEOUT_SECONDS=60
SUBMISSION_MAX_IN_FLIGHT=2
JUDGE_MAX_CONCURRENT=2
JUDGE_COMPILE_TIMEOUT_SECONDS=10
JUDGE_CASE_TIMEOUT_SECONDS=2
JUDGE_TOTAL_TIMEOUT_SECONDS=30
JUDGE_MEMORY_LIMIT_MB=512
JUDGE_CPU_LIMIT=1
JUDGE_CONTAINER_PIDS_LIMIT=128
JUDGE_RUNTIME_PROCESS_LIMIT=64
JUDGE_WORKSPACE_LIMIT_MB=64
JUDGE_OUTPUT_LIMIT_BYTES=65536
JUDGE_RUNNER_IMAGE=algomentor-judge-runner:phase10
```

Docker socket access is acceptable only for local development and controlled deployments. Production should use a separate Judge host or stronger sandbox boundary.

## Testing

- Backend uses a fake Judge client and never executes code in ordinary tests.
- Judge unit tests use a fake Docker client.
- Docker integration tests cover C++/Python accepted, wrong answer, compile/syntax error, runtime error, TLE, MLE, output limit, fork bombs, network denial, read-only filesystem, workspace size, and container cleanup.
- Frontend must pass `pnpm lint` and `pnpm build`.
- Full acceptance verifies feature-disabled behavior, real isolated execution, hidden-test protection, no residual runner containers, and `/api/health` independence.

## Boundaries

- Redis is not a Judge queue in Phase 10.
- Dashboard, mistake notes, and recommendations are unchanged.
- AI providers are not called.
- Phase 11 is the first phase allowed to add AI diagnosis after stable Judge verdicts.
