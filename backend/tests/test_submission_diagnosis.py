from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from app.core.deps import get_ai_provider
from app.main import app
from app.models.ai_call_log import AICallLog
from app.models.code_review import CodeReview
from app.models.mistake_note import MistakeNote
from app.models.problem import Problem
from app.models.prompt_template import PromptTemplate
from app.models.submission import Submission, SubmissionCaseResult
from app.providers.ai.base import AIProvider, AIProviderError, AIProviderResult, AIProviderUsage
from scripts import seed_prompt_templates


class CapturingAIProvider(AIProvider):
    provider_name = "fake"

    def __init__(self, content: str = "## 诊断\n请先检查边界条件。") -> None:
        self.content = content
        self.prompts: list[str] = []

    def complete(self, *, prompt: str, prompt_type: str) -> AIProviderResult:
        self.prompts.append(prompt)
        return AIProviderResult(
            content=self.content,
            model="fake-model",
            usage=AIProviderUsage(input_tokens=12, output_tokens=24),
        )


class ErrorAIProvider(AIProvider):
    provider_name = "fake"

    def complete(self, *, prompt: str, prompt_type: str) -> AIProviderResult:
        raise AIProviderError(
            "AI_PROVIDER_TIMEOUT",
            "AI provider request timed out",
            status_code=503,
        )


def _register(client, prefix: str = "diagnosis") -> dict:
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"{prefix}-{suffix}@example.com",
            "username": f"{prefix}_{suffix}",
            "password": "password123",
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


def _add_template(db_session) -> None:
    db_session.add(
        PromptTemplate(
            name="Submission Diagnosis",
            type="submission_diagnosis",
            version=1,
            template_key="submission_diagnosis",
            file_path="submission_diagnosis.md",
            content=(
                "Verdict={{verdict}}\nLanguage={{language}}\n"
                "Problem={{problem_context}}\nCode={{source_code}}\n"
                "Compile={{compile_output}}\nError={{error_message}}\n"
                "Cases={{case_context}}"
            ),
            enabled=True,
        )
    )
    db_session.commit()


def _create_problem(client) -> dict:
    response = client.post(
        "/api/problems",
        json={
            "title": "Diagnosis Problem",
            "difficulty": "basic",
            "description_markdown": "Find the correct range sum.",
            "input_format": "An array and query.",
            "output_format": "The range sum.",
            "constraints": "1 <= n <= 100000",
            "hint": "This must not be sent.",
            "solution_markdown": "Secret solution must not be sent.",
            "solution_code_cpp": "int secret_solution;",
            "topic_ids": [],
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


def _create_submission(
    db_session,
    *,
    user_id: UUID,
    problem: dict,
    verdict: str = "wrong_answer",
    source_code: str = "print(0)",
    case_results: list[SubmissionCaseResult] | None = None,
) -> Submission:
    submission = Submission(
        user_id=user_id,
        problem_id=UUID(problem["id"]),
        problem_title=problem["title"],
        problem_display_id=problem["display_id"],
        language="python",
        source_code=source_code,
        verdict=verdict,
        passed_case_count=0,
        total_case_count=max(1, len(case_results or [])),
        execution_time_ms=10,
        memory_kb=1024,
        compile_output="compiler output",
        error_message="submission error",
        finished_at=datetime.now(timezone.utc),
    )
    submission.case_results = case_results or [
        SubmissionCaseResult(
            case_index=1,
            name="sample",
            is_sample=True,
            verdict="wrong_answer",
            execution_time_ms=10,
            memory_kb=1024,
            input_text="1 2",
            expected_output_text="3",
            actual_output="0",
        )
    ]
    db_session.add(submission)
    db_session.commit()
    db_session.refresh(submission)
    return submission


def _override_provider(provider: AIProvider) -> None:
    app.dependency_overrides[get_ai_provider] = lambda: provider


def test_failed_submission_diagnosis_uses_safe_context(client, db_session) -> None:
    user = _register(client)
    problem = _create_problem(client)
    source_code = "A" * 10000 + "MIDDLE_SECRET" + "B" * 10000
    cases = [
        SubmissionCaseResult(
            case_index=1,
            name="visible-sample",
            is_sample=True,
            verdict="wrong_answer",
            input_text="sample input",
            expected_output_text="sample expected",
            actual_output="sample actual",
        ),
        SubmissionCaseResult(
            case_index=2,
            name="HIDDEN_CASE_NAME",
            is_sample=False,
            verdict="runtime_error",
            input_text="HIDDEN_INPUT",
            expected_output_text="HIDDEN_EXPECTED",
            actual_output="HIDDEN_ACTUAL",
            error_message="safe runtime summary",
        ),
    ]
    submission = _create_submission(
        db_session,
        user_id=UUID(user["id"]),
        problem=problem,
        source_code=source_code,
        case_results=cases,
    )
    _add_template(db_session)
    provider = CapturingAIProvider()
    _override_provider(provider)

    response = client.post(f"/api/submissions/{submission.id}/ai-diagnose")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["submission_id"] == str(submission.id)
    assert data["verdict"] == "wrong_answer"
    assert data["prompt_type"] == "submission_diagnosis"
    assert data["context_info"] == {
        "code_truncated": True,
        "problem_context_included": True,
        "failed_case_count_included": 2,
    }
    prompt = provider.prompts[0]
    assert "[... source code truncated ...]" in prompt
    assert "MIDDLE_SECRET" not in prompt
    assert "sample input" in prompt
    assert "sample expected" in prompt
    assert "sample actual" in prompt
    assert "HIDDEN_CASE_NAME" not in prompt
    assert "HIDDEN_INPUT" not in prompt
    assert "HIDDEN_EXPECTED" not in prompt
    assert "HIDDEN_ACTUAL" not in prompt
    assert "Secret solution must not be sent." not in prompt
    assert "int secret_solution;" not in prompt
    assert db_session.scalar(select(func.count()).select_from(CodeReview)) == 0
    assert db_session.scalar(select(func.count()).select_from(MistakeNote)) == 0
    log = db_session.scalar(
        select(AICallLog).where(AICallLog.prompt_type == "submission_diagnosis")
    )
    assert log is not None
    assert log.success is True
    assert not hasattr(log, "prompt")
    assert source_code not in (log.error_message or "")


@pytest.mark.parametrize(
    "verdict",
    [
        "compile_error",
        "wrong_answer",
        "runtime_error",
        "time_limit_exceeded",
        "memory_limit_exceeded",
        "output_limit_exceeded",
    ],
)
def test_all_explainable_verdicts_are_supported(
    client,
    db_session,
    verdict: str,
) -> None:
    user = _register(client, verdict)
    problem = _create_problem(client)
    submission = _create_submission(
        db_session,
        user_id=UUID(user["id"]),
        problem=problem,
        verdict=verdict,
    )
    _add_template(db_session)
    provider = CapturingAIProvider()
    _override_provider(provider)

    response = client.post(f"/api/submissions/{submission.id}/ai-diagnose")

    assert response.status_code == 200
    assert response.json()["data"]["verdict"] == verdict
    assert len(provider.prompts) == 1


@pytest.mark.parametrize("verdict", ["accepted", "internal_error"])
def test_non_diagnosable_verdict_does_not_call_provider(
    client,
    db_session,
    verdict: str,
) -> None:
    user = _register(client, verdict)
    problem = _create_problem(client)
    submission = _create_submission(
        db_session,
        user_id=UUID(user["id"]),
        problem=problem,
        verdict=verdict,
    )
    provider = CapturingAIProvider()
    _override_provider(provider)

    response = client.post(f"/api/submissions/{submission.id}/ai-diagnose")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SUBMISSION_DIAGNOSIS_NOT_AVAILABLE"
    assert provider.prompts == []


def test_submission_diagnosis_is_user_scoped(client, db_session) -> None:
    owner = _register(client, "owner")
    problem = _create_problem(client)
    submission = _create_submission(
        db_session,
        user_id=UUID(owner["id"]),
        problem=problem,
    )
    client.post("/api/auth/logout")
    _register(client, "other")
    _add_template(db_session)
    provider = CapturingAIProvider()
    _override_provider(provider)

    response = client.post(f"/api/submissions/{submission.id}/ai-diagnose")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SUBMISSION_NOT_FOUND"
    assert provider.prompts == []


def test_deleted_problem_uses_submission_snapshot(client, db_session) -> None:
    user = _register(client)
    problem = _create_problem(client)
    submission = _create_submission(
        db_session,
        user_id=UUID(user["id"]),
        problem=problem,
    )
    db_session.delete(db_session.get(Problem, UUID(problem["id"])))
    db_session.commit()
    _add_template(db_session)
    provider = CapturingAIProvider()
    _override_provider(provider)

    response = client.post(f"/api/submissions/{submission.id}/ai-diagnose")

    assert response.status_code == 200
    assert response.json()["data"]["context_info"]["problem_context_included"] is False
    assert "original problem record is no longer available" in provider.prompts[0]
    assert problem["title"] in provider.prompts[0]


def test_diagnosis_limits_failed_cases_to_five(client, db_session) -> None:
    user = _register(client)
    problem = _create_problem(client)
    cases = [
        SubmissionCaseResult(
            case_index=index,
            name=f"case-{index}",
            is_sample=index == 1,
            verdict="wrong_answer",
            input_text="i" * 3000,
            expected_output_text="e" * 3000,
            actual_output="a" * 3000,
        )
        for index in range(1, 8)
    ]
    submission = _create_submission(
        db_session,
        user_id=UUID(user["id"]),
        problem=problem,
        case_results=cases,
    )
    _add_template(db_session)
    provider = CapturingAIProvider()
    _override_provider(provider)

    response = client.post(f"/api/submissions/{submission.id}/ai-diagnose")

    assert response.status_code == 200
    assert response.json()["data"]["context_info"]["failed_case_count_included"] == 5
    prompt = provider.prompts[0]
    assert "Case #5" in prompt
    assert "Case #6" not in prompt


def test_provider_failure_does_not_change_submission_verdict(client, db_session) -> None:
    user = _register(client)
    problem = _create_problem(client)
    submission = _create_submission(
        db_session,
        user_id=UUID(user["id"]),
        problem=problem,
    )
    _add_template(db_session)
    _override_provider(ErrorAIProvider())

    response = client.post(f"/api/submissions/{submission.id}/ai-diagnose")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AI_PROVIDER_TIMEOUT"
    db_session.expire_all()
    assert db_session.get(Submission, submission.id).verdict == "wrong_answer"


def test_missing_submission_diagnosis_template_is_safe(client, db_session) -> None:
    user = _register(client)
    problem = _create_problem(client)
    submission = _create_submission(
        db_session,
        user_id=UUID(user["id"]),
        problem=problem,
    )
    for template in db_session.scalars(
        select(PromptTemplate).where(
            PromptTemplate.template_key == "submission_diagnosis"
        )
    ):
        template.enabled = False
    db_session.commit()
    provider = CapturingAIProvider()
    _override_provider(provider)

    response = client.post(f"/api/submissions/{submission.id}/ai-diagnose")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "PROMPT_TEMPLATE_NOT_FOUND"
    assert provider.prompts == []


def test_saved_diagnosis_accepts_full_submission_source(client, db_session) -> None:
    user = _register(client)
    problem = _create_problem(client)
    source_code = "x" * 20000
    submission = _create_submission(
        db_session,
        user_id=UUID(user["id"]),
        problem=problem,
        source_code=source_code,
    )

    response = client.post(
        "/api/code-reviews",
        json={
            "problem_id": problem["id"],
            "language": "python",
            "question": (
                f"判题提交 {submission.id} 的 AI 失败诊断，原始 verdict：wrong_answer"
            ),
            "code": source_code,
            "analysis_result": "诊断结果",
            "model": "fake-model",
            "prompt_type": "submission_diagnosis",
            "input_tokens": 12,
            "output_tokens": 24,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["code"] == source_code


def test_submission_diagnosis_prompt_seed_is_idempotent(db_session, monkeypatch) -> None:
    class SessionContext:
        def __enter__(self):
            return db_session

        def __exit__(self, exc_type, exc, traceback):
            return False

    monkeypatch.setattr(
        seed_prompt_templates,
        "SessionLocal",
        lambda: SessionContext(),
    )

    seed_prompt_templates.seed_prompt_templates()
    seed_prompt_templates.seed_prompt_templates()

    count = db_session.scalar(
        select(func.count())
        .select_from(PromptTemplate)
        .where(
            PromptTemplate.template_key == "submission_diagnosis",
            PromptTemplate.version == 1,
        )
    )
    assert count == 1
