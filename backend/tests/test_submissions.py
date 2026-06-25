from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import delete

from app.core.config import settings
from app.main import app
from app.core.security import SESSION_COOKIE_NAME, create_access_token
from app.models.problem import Problem
from app.models.test_case import TestCase as ProblemTestCase
from app.schemas.judge import JudgeCaseResult, JudgeResponse
from app.services.judge.client import get_judge_client


class FakeJudgeClient:
    def __init__(self, verdict: str = "accepted") -> None:
        self.verdict = verdict
        self.calls = 0

    async def judge(self, payload):
        self.calls += 1
        results = []
        for case in payload.test_cases:
            case_verdict = "accepted" if self.verdict == "accepted" else "wrong_answer"
            results.append(
                JudgeCaseResult(
                    test_case_id=case.id,
                    case_index=case.case_index,
                    name=case.name,
                    is_sample=case.is_sample,
                    verdict=case_verdict,
                    execution_time_ms=4,
                    memory_kb=1024,
                    actual_output="42\n",
                )
            )
        return JudgeResponse(
            verdict=self.verdict,
            passed_case_count=len(results) if self.verdict == "accepted" else 0,
            total_case_count=len(results),
            execution_time_ms=8,
            memory_kb=1024,
            case_results=results,
        )


class ErrorJudgeClient:
    def __init__(self) -> None:
        self.calls = 0

    async def judge(self, payload):
        self.calls += 1
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "JUDGE_UNAVAILABLE", "message": "Judge service is unavailable"},
        )


class InvalidJudgeClient:
    async def judge(self, payload):
        case = payload.test_cases[0]
        return JudgeResponse(
            verdict="accepted",
            passed_case_count=1,
            total_case_count=len(payload.test_cases),
            case_results=[
                JudgeCaseResult(
                    test_case_id=case.id,
                    case_index=case.case_index + 1,
                    name=case.name,
                    is_sample=case.is_sample,
                    verdict="accepted",
                )
            ],
        )


class InvalidPassedCountJudgeClient(FakeJudgeClient):
    async def judge(self, payload):
        response = await super().judge(payload)
        return response.model_copy(update={"passed_case_count": 0})


class TransactionInspectingJudgeClient(FakeJudgeClient):
    def __init__(self, db_session) -> None:
        super().__init__()
        self.db_session = db_session
        self.connection_released = False

    async def judge(self, payload):
        self.connection_released = not self.db_session.in_transaction()
        return await super().judge(payload)


def _register(client, prefix: str = "submission") -> dict:
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/auth/register",
        json={
            "student_id": f"{prefix}_{suffix}",
            "password": "password123",
            "name": "提交用户",
            "current_level": "elementary",
            "goal_track": "self_study",
            "goal_description": None,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


def _login_as(client, user) -> None:
    client.cookies.set(SESSION_COOKIE_NAME, create_access_token(user.id))


def _create_problem_with_cases(client, db_session) -> dict:
    response = client.post(
        "/api/problems",
        json={
            "title": f"Judge Problem {uuid4().hex[:6]}",
            "difficulty": "basic",
            "description_markdown": "Print 42.",
            "topic_ids": [],
        },
    )
    assert response.status_code == 200
    problem = response.json()["data"]
    db_session.add_all(
        [
            ProblemTestCase(
                problem_id=problem["id"],
                case_index=1,
                name="sample",
                input_text="",
                expected_output_text="42\n",
                is_sample=True,
                is_hidden=False,
            ),
            ProblemTestCase(
                problem_id=problem["id"],
                case_index=2,
                name="hidden",
                input_text="secret input",
                expected_output_text="42\n",
                is_sample=False,
                is_hidden=True,
            ),
        ]
    )
    db_session.commit()
    return problem


def _create_public_problem_with_cases(client, db_session, admin_user) -> dict:
    _login_as(client, admin_user)
    response = client.post(
        "/api/problems",
        json={
            "title": f"Public Judge Problem {uuid4().hex[:6]}",
            "difficulty": "basic",
            "description_markdown": "Print 42.",
            "topic_ids": [],
            "is_public": True,
        },
    )
    assert response.status_code == 200
    problem = response.json()["data"]
    db_session.add(
        ProblemTestCase(
            problem_id=problem["id"],
            case_index=1,
            name="sample",
            input_text="",
            expected_output_text="42\n",
            is_sample=True,
            is_hidden=False,
        )
    )
    db_session.commit()
    return problem


def _enable_judge(monkeypatch, fake) -> None:
    monkeypatch.setattr(settings, "enable_code_execution", True)
    monkeypatch.setattr(settings, "judge_base_url", "http://judge:9000")
    monkeypatch.setattr(settings, "judge_internal_token", "test-token")
    app.dependency_overrides[get_judge_client] = lambda: fake


def test_submission_feature_disabled(client, db_session, monkeypatch) -> None:
    _register(client)
    problem = _create_problem_with_cases(client, db_session)
    monkeypatch.setattr(settings, "enable_code_execution", False)

    response = client.post(
        "/api/submissions",
        json={"problem_id": problem["id"], "language": "cpp", "source_code": "int main(){}"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CODE_EXECUTION_DISABLED"


def test_submission_requires_judge_config(client, db_session, monkeypatch) -> None:
    _register(client)
    problem = _create_problem_with_cases(client, db_session)
    monkeypatch.setattr(settings, "enable_code_execution", True)
    monkeypatch.setattr(settings, "judge_internal_token", "")

    response = client.post(
        "/api/submissions",
        json={"problem_id": problem["id"], "language": "python", "source_code": "print(42)"},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "JUDGE_CONFIG_MISSING"


def test_submission_success_and_hidden_case_protection(client, db_session, monkeypatch) -> None:
    user = _register(client)
    problem = _create_problem_with_cases(client, db_session)
    fake = FakeJudgeClient()
    _enable_judge(monkeypatch, fake)

    response = client.post(
        "/api/submissions",
        json={"problem_id": problem["id"], "language": "python", "source_code": "print(42)"},
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["verdict"] == "accepted"
    assert data["problem"]["display_id"] == problem["display_id"]
    assert data["source_code"] == "print(42)"
    assert data["case_results"][0]["input_text"] == ""
    assert data["case_results"][0]["expected_output_text"] == "42\n"
    assert data["case_results"][0]["actual_output"] == "42\n"
    assert data["case_results"][1]["input_text"] is None
    assert data["case_results"][1]["expected_output_text"] is None
    assert data["case_results"][1]["actual_output"] is None
    assert fake.calls == 1

    detail = client.get(f"/api/submissions/{data['id']}")
    assert detail.status_code == 200
    assert detail.json()["data"]["problem"]["id"] == problem["id"]
    assert detail.json()["data"]["source_code"] == "print(42)"
    assert detail.json()["data"]["problem"]["title"] == problem["title"]
    assert detail.json()["data"]["id"] == data["id"]
    assert user["id"]


def test_submission_allows_public_problem(client, db_session, monkeypatch, admin_user) -> None:
    problem = _create_public_problem_with_cases(client, db_session, admin_user)
    _register(client, "public-submitter")
    fake = FakeJudgeClient()
    _enable_judge(monkeypatch, fake)

    response = client.post(
        "/api/submissions",
        json={"problem_id": problem["id"], "language": "cpp", "source_code": "int main(){return 0;}"},
    )

    assert response.status_code == 201
    assert response.json()["data"]["problem"]["id"] == problem["id"]
    assert fake.calls == 1


def test_submission_rejects_other_user_problem(client, db_session, monkeypatch) -> None:
    _register(client, "owner")
    problem = _create_problem_with_cases(client, db_session)
    client.post("/api/auth/logout")
    _register(client, "other")
    fake = FakeJudgeClient()
    _enable_judge(monkeypatch, fake)

    response = client.post(
        "/api/submissions",
        json={"problem_id": problem["id"], "language": "cpp", "source_code": "int main(){}"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROBLEM_NOT_FOUND"
    assert fake.calls == 0


def test_submission_requires_test_cases(client, monkeypatch) -> None:
    _register(client)
    response = client.post(
        "/api/problems",
        json={
            "title": "No Test Cases",
            "difficulty": "beginner",
            "description_markdown": "No cases.",
            "topic_ids": [],
        },
    )
    problem = response.json()["data"]
    fake = FakeJudgeClient()
    _enable_judge(monkeypatch, fake)

    submission = client.post(
        "/api/submissions",
        json={"problem_id": problem["id"], "language": "python", "source_code": "print(1)"},
    )

    assert submission.status_code == 409
    assert submission.json()["error"]["code"] == "PROBLEM_TEST_CASES_REQUIRED"


def test_submission_validation(client) -> None:
    _register(client)
    response = client.post(
        "/api/submissions",
        json={"problem_id": str(uuid4()), "language": "java", "source_code": ""},
    )
    assert response.status_code == 422


def test_submission_judge_error_is_not_retried(client, db_session, monkeypatch) -> None:
    _register(client)
    problem = _create_problem_with_cases(client, db_session)
    fake = ErrorJudgeClient()
    _enable_judge(monkeypatch, fake)

    response = client.post(
        "/api/submissions",
        json={"problem_id": problem["id"], "language": "python", "source_code": "print(42)"},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "JUDGE_UNAVAILABLE"
    assert fake.calls == 1


def test_submission_rejects_invalid_judge_response(client, db_session, monkeypatch) -> None:
    _register(client)
    problem = _create_problem_with_cases(client, db_session)
    _enable_judge(monkeypatch, InvalidJudgeClient())

    response = client.post(
        "/api/submissions",
        json={"problem_id": problem["id"], "language": "python", "source_code": "print(42)"},
    )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "JUDGE_INVALID_RESPONSE"


def test_submission_rejects_inconsistent_passed_case_count(
    client,
    db_session,
    monkeypatch,
) -> None:
    _register(client)
    problem = _create_problem_with_cases(client, db_session)
    _enable_judge(monkeypatch, InvalidPassedCountJudgeClient())

    response = client.post(
        "/api/submissions",
        json={"problem_id": problem["id"], "language": "python", "source_code": "print(42)"},
    )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "JUDGE_INVALID_RESPONSE"


def test_submission_releases_database_transaction_while_waiting(
    client,
    db_session,
    monkeypatch,
) -> None:
    _register(client)
    problem = _create_problem_with_cases(client, db_session)
    fake = TransactionInspectingJudgeClient(db_session)
    _enable_judge(monkeypatch, fake)

    response = client.post(
        "/api/submissions",
        json={"problem_id": problem["id"], "language": "python", "source_code": "print(42)"},
    )

    assert response.status_code == 201
    assert fake.connection_released is True


def test_submission_is_user_scoped_and_survives_problem_delete(client, db_session, monkeypatch) -> None:
    first_user = _register(client, "first")
    problem = _create_problem_with_cases(client, db_session)
    fake = FakeJudgeClient("wrong_answer")
    _enable_judge(monkeypatch, fake)
    created = client.post(
        "/api/submissions",
        json={"problem_id": problem["id"], "language": "cpp", "source_code": "int main(){}"},
    ).json()["data"]

    delete_response = client.delete(f"/api/problems/{problem['id']}")
    assert delete_response.status_code == 200
    detail = client.get(f"/api/submissions/{created['id']}")
    assert detail.status_code == 200
    assert detail.json()["data"]["problem"]["id"] is None
    assert detail.json()["data"]["problem"]["title"] == problem["title"]

    client.post("/api/auth/logout")
    second_user = _register(client, "second")
    forbidden = client.get(f"/api/submissions/{created['id']}")
    assert forbidden.status_code == 404
    assert forbidden.json()["error"]["code"] == "SUBMISSION_NOT_FOUND"
    assert first_user["id"] != second_user["id"]
