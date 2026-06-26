import json
from uuid import UUID, uuid4

from sqlalchemy import select

from app.core.deps import get_ai_provider
from app.main import app
from app.models.ai_call_log import AICallLog
from app.models.ladder import LadderTemplate, NodeUserProgress
from app.models.ladder_exam import LadderExamAttempt
from app.models.prompt_template import PromptTemplate
from app.models.submission import Submission
from app.providers.ai.base import AIProvider, AIProviderResult, AIProviderUsage


class FakeExamProvider(AIProvider):
    provider_name = "fake"

    def __init__(self, content: str | None = None) -> None:
        self.content = content or json.dumps(_exam_payload())
        self.calls = 0

    def complete(self, *, prompt: str, prompt_type: str) -> AIProviderResult:
        self.calls += 1
        return AIProviderResult(
            content=self.content,
            model="fake-exam-model",
            usage=AIProviderUsage(input_tokens=30, output_tokens=60),
        )


def _override_provider(provider: AIProvider) -> None:
    app.dependency_overrides[get_ai_provider] = lambda: provider


def _register(client, *, student_id: str | None = None):
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/auth/register",
        json={
            "student_id": student_id or f"exam_{suffix}",
            "password": "password123",
            "name": "Exam Student",
            "current_level": "beginner",
            "goal_track": "self_study",
            "goal_description": "Prepare a steady algorithm path.",
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


def _practice_items() -> list[dict]:
    return [
        {
            "id": "choice-1",
            "type": "choice",
            "prompt": "Which complexity grows faster?",
            "options": [{"id": "a", "text": "O(n)"}, {"id": "b", "text": "O(n log n)"}],
            "correct_option_id": "b",
            "explanation": "O(n log n) grows faster.",
        },
        {
            "id": "choice-2",
            "type": "choice",
            "prompt": "What should you do for boundary bugs?",
            "options": [{"id": "a", "text": "Trace cases"}, {"id": "b", "text": "Ignore them"}],
            "correct_option_id": "a",
            "explanation": "Small traces expose boundaries.",
        },
        {
            "id": "coding-1",
            "type": "coding",
            "prompt": "Write a small loop.",
            "self_check": "Check empty and single-element inputs.",
        },
    ]


def _template_data() -> dict:
    return {
        "phases": [
            {
                "title": "Foundation",
                "description": "Start here.",
                "nodes": [
                    {
                        "algorithm_key": "complexity",
                        "title": "Complexity",
                        "summary": "Learn growth rates.",
                        "material_markdown": "# Complexity\n\nRead the material.",
                        "resource_links": [],
                        "practice_items": _practice_items(),
                    }
                ],
            },
            {
                "title": "Patterns",
                "description": "Then continue.",
                "nodes": [
                    {
                        "algorithm_key": "sorting",
                        "title": "Sorting",
                        "summary": "Learn ordering.",
                        "material_markdown": "# Sorting\n\nRead the material.",
                        "resource_links": [],
                        "practice_items": _practice_items(),
                    }
                ],
            },
        ]
    }


def _add_template(db_session) -> LadderTemplate:
    template = LadderTemplate(
        goal_track="self_study",
        current_level="beginner",
        name="Exam Path",
        description="Template for exam tests",
        template_data=_template_data(),
        version=1,
        is_default=True,
    )
    db_session.add(template)
    db_session.commit()
    return template


def _add_prompt_template(db_session) -> None:
    template = PromptTemplate(
        name="Ladder Exam Generation",
        type="ladder_exam_generation",
        version=1,
        template_key="ladder_exam_generation",
        file_path="app/prompts/templates/ladder_exam_generation.md",
        content=(
            "{{user_profile}}\n"
            "Node: {{node_title}}\n"
            "Summary: {{node_summary}}\n"
            "Material: {{material_excerpt}}\n"
            "Practice: {{practice_summary}}\n"
            "Difficulty: {{difficulty_level}}"
        ),
        enabled=True,
    )
    db_session.add(template)
    db_session.commit()


def _nodes(body: dict) -> list[dict]:
    return [node for phase in body["data"]["phases"] for node in phase["nodes"]]


def _exam_payload() -> dict:
    questions: list[dict] = []
    for index in range(1, 11):
        questions.append(
            {
                "id": f"single-{index}",
                "type": "single_choice",
                "prompt": f"Single choice question {index}?",
                "options": [
                    {"id": "a", "text": "Option A"},
                    {"id": "b", "text": "Option B"},
                    {"id": "c", "text": "Option C"},
                    {"id": "d", "text": "Option D"},
                ],
                "correct_option_id": "a",
                "explanation": f"Single explanation {index}.",
            }
        )
    for index in range(1, 3):
        questions.append(
            {
                "id": f"code-{index}",
                "type": "code_reading",
                "prompt": f"Code reading question {index}?",
                "options": [
                    {"id": "a", "text": "Option A"},
                    {"id": "b", "text": "Option B"},
                    {"id": "c", "text": "Option C"},
                    {"id": "d", "text": "Option D"},
                ],
                "correct_option_id": "b",
                "explanation": f"Code explanation {index}.",
            }
        )
    return {"questions": questions}


def _prepare_node(client, db_session, *, provider: FakeExamProvider | None = None) -> tuple[str, str]:
    _add_template(db_session)
    _add_prompt_template(db_session)
    _register(client)
    if provider is not None:
        _override_provider(provider)
    summary = client.get("/api/ladder")
    assert summary.status_code == 200
    node_ids = [node["id"] for node in _nodes(summary.json())]
    first_node_id = node_ids[0]
    second_node_id = node_ids[1]
    material = client.post(f"/api/ladder/nodes/{first_node_id}/material-complete")
    assert material.status_code == 200
    practice = client.post(
        f"/api/ladder/nodes/{first_node_id}/practice-submit",
        json={
            "choice_answers": [
                {"item_id": "choice-1", "option_id": "b"},
                {"item_id": "choice-2", "option_id": "a"},
            ],
            "completed_coding_item_ids": ["coding-1"],
        },
    )
    assert practice.status_code == 200
    assert practice.json()["data"]["passed"] is True
    return first_node_id, second_node_id


def _correct_answers() -> list[dict]:
    return [{"question_id": f"single-{index}", "option_id": "a"} for index in range(1, 11)] + [
        {"question_id": "code-1", "option_id": "b"},
        {"question_id": "code-2", "option_id": "b"},
    ]


def _wrong_answers() -> list[dict]:
    return [{"question_id": f"single-{index}", "option_id": "b"} for index in range(1, 11)] + [
        {"question_id": "code-1", "option_id": "a"},
        {"question_id": "code-2", "option_id": "a"},
    ]


def test_exam_generate_requires_unlocked_material_and_practice(client, db_session) -> None:
    _add_template(db_session)
    _add_prompt_template(db_session)
    _register(client)
    summary = client.get("/api/ladder")
    node_ids = [node["id"] for node in _nodes(summary.json())]

    locked = client.post(f"/api/ladder/nodes/{node_ids[1]}/exam-generate")
    material_required = client.post(f"/api/ladder/nodes/{node_ids[0]}/exam-generate")
    client.post(f"/api/ladder/nodes/{node_ids[0]}/material-complete")
    practice_required = client.post(f"/api/ladder/nodes/{node_ids[0]}/exam-generate")

    assert locked.status_code == 409
    assert locked.json()["error"]["code"] == "NODE_LOCKED"
    assert material_required.status_code == 409
    assert material_required.json()["error"]["code"] == "LADDER_EXAM_REQUIRE_MATERIAL"
    assert practice_required.status_code == 409
    assert practice_required.json()["error"]["code"] == "LADDER_EXAM_REQUIRE_PRACTICE"


def test_exam_generate_reuses_generated_attempt_and_hides_answers(client, db_session) -> None:
    provider = FakeExamProvider()
    first_node_id, _ = _prepare_node(client, db_session, provider=provider)

    first = client.post(f"/api/ladder/nodes/{first_node_id}/exam-generate")
    second = client.post(f"/api/ladder/nodes/{first_node_id}/exam-generate")

    assert first.status_code == 200
    assert second.status_code == 200
    assert provider.calls == 1
    assert first.json()["data"]["attempt"]["id"] == second.json()["data"]["attempt"]["id"]
    question = first.json()["data"]["attempt"]["questions"][0]
    assert "correct_option_id" not in question or question["correct_option_id"] is None
    assert "explanation" not in question or question["explanation"] is None
    assert len(db_session.scalars(select(LadderExamAttempt)).all()) == 1


def test_exam_generate_accepts_markdown_json_fence(client, db_session) -> None:
    provider = FakeExamProvider(f"```json\n{json.dumps(_exam_payload())}\n```")
    first_node_id, _ = _prepare_node(client, db_session, provider=provider)

    response = client.post(f"/api/ladder/nodes/{first_node_id}/exam-generate")

    assert response.status_code == 200
    assert response.json()["data"]["attempt"]["status"] == "generated"


def test_exam_generate_invalid_json_does_not_save_attempt(client, db_session) -> None:
    provider = FakeExamProvider("not json")
    first_node_id, _ = _prepare_node(client, db_session, provider=provider)

    response = client.post(f"/api/ladder/nodes/{first_node_id}/exam-generate")

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "LADDER_EXAM_GENERATION_FAILED"
    assert db_session.scalars(select(LadderExamAttempt)).all() == []
    log = db_session.scalar(select(AICallLog).where(AICallLog.prompt_type == "ladder_exam_generation"))
    assert log is not None
    assert log.success is False
    assert "not json" not in (log.error_message or "")


def test_get_exam_and_submit_are_user_scoped(client, db_session) -> None:
    provider = FakeExamProvider()
    first_node_id, _ = _prepare_node(client, db_session, provider=provider)
    generated = client.post(f"/api/ladder/nodes/{first_node_id}/exam-generate")
    attempt_id = generated.json()["data"]["attempt"]["id"]
    client.cookies.clear()
    _register(client, student_id="exam_other_user")

    get_response = client.get(f"/api/ladder/exams/{attempt_id}")
    submit_response = client.post(f"/api/ladder/exams/{attempt_id}/submit", json={"answers": _correct_answers()})

    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "LADDER_EXAM_NOT_FOUND"
    assert submit_response.status_code == 404
    assert submit_response.json()["error"]["code"] == "LADDER_EXAM_NOT_FOUND"


def test_exam_submit_scores_deterministically_and_unlocks_next_node(client, db_session) -> None:
    provider = FakeExamProvider()
    first_node_id, second_node_id = _prepare_node(client, db_session, provider=provider)
    generated = client.post(f"/api/ladder/nodes/{first_node_id}/exam-generate")
    attempt_id = generated.json()["data"]["attempt"]["id"]

    response = client.post(f"/api/ladder/exams/{attempt_id}/submit", json={"answers": _correct_answers()})

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["score"] == 100
    assert body["passed"] is True
    assert body["attempt"]["status"] == "submitted"
    assert body["attempt"]["questions"][0]["correct_option_id"] == "a"
    assert body["attempt"]["questions"][0]["explanation"] == "Single explanation 1."
    nodes = [node for phase in body["ladder"]["phases"] for node in phase["nodes"]]
    assert nodes[0]["status"] == "passed"
    assert nodes[1]["id"] == second_node_id
    assert nodes[1]["status"] == "unlocked"
    progress = db_session.scalar(select(NodeUserProgress).where(NodeUserProgress.node_id == UUID(first_node_id)))
    assert progress is not None
    assert progress.exam_passed is True


def test_exam_submit_below_80_does_not_pass_and_allows_new_attempt(client, db_session) -> None:
    provider = FakeExamProvider()
    first_node_id, _ = _prepare_node(client, db_session, provider=provider)
    generated = client.post(f"/api/ladder/nodes/{first_node_id}/exam-generate")
    attempt_id = generated.json()["data"]["attempt"]["id"]
    low_score_answers = [{"question_id": f"single-{index}", "option_id": "a"} for index in range(1, 10)] + [
        {"question_id": "single-10", "option_id": "b"},
        {"question_id": "code-1", "option_id": "a"},
        {"question_id": "code-2", "option_id": "a"},
    ]

    submitted = client.post(f"/api/ladder/exams/{attempt_id}/submit", json={"answers": low_score_answers})
    regenerated = client.post(f"/api/ladder/nodes/{first_node_id}/exam-generate")

    assert submitted.status_code == 200
    assert submitted.json()["data"]["score"] == 54
    assert submitted.json()["data"]["passed"] is False
    assert regenerated.status_code == 200
    assert regenerated.json()["data"]["attempt"]["id"] != attempt_id
    assert provider.calls == 2


def test_exam_submit_requires_all_12_answers(client, db_session) -> None:
    provider = FakeExamProvider()
    first_node_id, _ = _prepare_node(client, db_session, provider=provider)
    generated = client.post(f"/api/ladder/nodes/{first_node_id}/exam-generate")
    attempt_id = generated.json()["data"]["attempt"]["id"]

    response = client.post(
        f"/api/ladder/exams/{attempt_id}/submit",
        json={"answers": [{"question_id": "single-1", "option_id": "a"}]},
    )

    assert response.status_code == 422


def test_exam_submit_80_points_passes_and_repeat_is_idempotent(client, db_session) -> None:
    provider = FakeExamProvider()
    first_node_id, _ = _prepare_node(client, db_session, provider=provider)
    generated = client.post(f"/api/ladder/nodes/{first_node_id}/exam-generate")
    attempt_id = generated.json()["data"]["attempt"]["id"]
    exact_80_answers = [{"question_id": f"single-{index}", "option_id": "a"} for index in range(1, 11)] + [
        {"question_id": "code-1", "option_id": "b"},
        {"question_id": "code-2", "option_id": "a"},
    ]

    first = client.post(f"/api/ladder/exams/{attempt_id}/submit", json={"answers": exact_80_answers})
    repeat = client.post(f"/api/ladder/exams/{attempt_id}/submit", json={"answers": _wrong_answers()})

    assert first.status_code == 200
    assert first.json()["data"]["score"] == 80
    assert first.json()["data"]["passed"] is True
    assert repeat.status_code == 200
    assert repeat.json()["data"]["score"] == 80
    assert repeat.json()["data"]["passed"] is True


def test_passed_node_cannot_generate_new_exam_and_no_judge_or_submission_created(client, db_session) -> None:
    provider = FakeExamProvider()
    first_node_id, _ = _prepare_node(client, db_session, provider=provider)
    generated = client.post(f"/api/ladder/nodes/{first_node_id}/exam-generate")
    attempt_id = generated.json()["data"]["attempt"]["id"]
    submission_count_before = len(db_session.scalars(select(Submission)).all())
    client.post(f"/api/ladder/exams/{attempt_id}/submit", json={"answers": _correct_answers()})

    response = client.post(f"/api/ladder/nodes/{first_node_id}/exam-generate")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "LADDER_EXAM_ALREADY_PASSED"
    assert len(db_session.scalars(select(Submission)).all()) == submission_count_before
    log = db_session.scalar(select(AICallLog).where(AICallLog.prompt_type == "ladder_exam_generation"))
    assert log is not None
    assert log.success is True
    assert log.error_message is None
