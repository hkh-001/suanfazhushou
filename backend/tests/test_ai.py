from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.deps import get_ai_provider
from app.main import app
from app.models.ai_call_log import AICallLog
from app.models.ladder import LadderTemplate, LearningPath, LearningPathNode, NodeUserProgress
from app.models.ladder_exam import LadderExamAttempt
from app.models.prompt_template import PromptTemplate
from app.providers.ai.base import AIProvider, AIProviderError, AIProviderResult, AIProviderUsage
from app.services.ai.context_builder import ContextBuilder


class FakeAIProvider(AIProvider):
    provider_name = "fake"

    def __init__(self, content: str = "Helpful AI response") -> None:
        self.content = content

    def complete(self, *, prompt: str, prompt_type: str) -> AIProviderResult:
        return AIProviderResult(
            content=self.content,
            model="fake-model",
            usage=AIProviderUsage(input_tokens=10, output_tokens=20),
        )


class CapturingAIProvider(FakeAIProvider):
    def __init__(self, content: str = "Helpful AI response") -> None:
        super().__init__(content)
        self.prompts: list[str] = []

    def complete(self, *, prompt: str, prompt_type: str) -> AIProviderResult:
        self.prompts.append(prompt)
        return super().complete(prompt=prompt, prompt_type=prompt_type)


class TimeoutAIProvider(AIProvider):
    provider_name = "fake"

    def complete(self, *, prompt: str, prompt_type: str) -> AIProviderResult:
        raise AIProviderError("AI_PROVIDER_TIMEOUT", "AI provider request timed out", status_code=503)


def add_template(db_session, *, template_key: str, version: int = 1, content: str | None = None) -> PromptTemplate:
    template = PromptTemplate(
        name=template_key,
        type=template_key,
        version=version,
        template_key=template_key,
        file_path=f"app/prompts/templates/{template_key}.md",
        content=content or "Context: {{topic_context}}\nInput: {{question}}{{code}}{{requirements}}",
        enabled=True,
    )
    db_session.add(template)
    db_session.commit()
    return template


def override_provider(provider: AIProvider) -> None:
    app.dependency_overrides[get_ai_provider] = lambda: provider


def test_chat_returns_fake_provider_result(client: TestClient, db_session, dev_user) -> None:
    add_template(db_session, template_key="concept_explanation")
    override_provider(FakeAIProvider("Step-by-step explanation"))

    response = client.post(
        "/api/ai/chat",
        json={"question": "How do prefix sums work?", "mode": "beginner"},
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["result"] == "Step-by-step explanation"
    assert body["prompt_type"] == "concept_explanation"
    assert body["model"] == "fake-model"
    assert body["usage"] == {"input_tokens": 10, "output_tokens": 20}


def test_code_review_does_not_log_full_code(client: TestClient, db_session, dev_user) -> None:
    add_template(db_session, template_key="code_review")
    override_provider(FakeAIProvider("Bug cause before fix"))
    code = "int main(){return 0;}"

    response = client.post(
        "/api/ai/code-review",
        json={"language": "cpp", "code": code, "question": "Why wrong?"},
    )

    assert response.status_code == 200
    log = db_session.scalar(select(AICallLog).where(AICallLog.prompt_type == "code_review"))
    assert log is not None
    assert log.success is True
    assert log.input_tokens == 10
    assert code not in (log.error_message or "")


def test_ai_prompt_includes_short_user_profile_context(client: TestClient, db_session, dev_user) -> None:
    dev_user.current_level = "popularization"
    dev_user.goal_track = "lanqiao"
    dev_user.goal_description = "\u5e0c\u671b\u51c6\u5907\u7701\u8d5b\u3002"
    db_session.commit()
    add_template(db_session, template_key="concept_explanation")
    provider = CapturingAIProvider("Profile-aware response")
    override_provider(provider)

    response = client.post(
        "/api/ai/chat",
        json={"question": "How should I practice sorting?", "mode": "beginner"},
    )

    assert response.status_code == 200
    prompt = provider.prompts[0]
    assert "用户学习背景 - 仅作为个性化教学参考" in prompt
    assert "\u5f53\u524d\u6c34\u5e73\uff1a" in prompt
    assert "\u5b66\u4e60\u76ee\u6807\uff1a" in prompt
    assert "\u5e0c\u671b\u51c6\u5907\u7701\u8d5b\u3002" in prompt
    assert "用户学习背景结束" in prompt
    log = db_session.scalar(select(AICallLog).where(AICallLog.prompt_type == "concept_explanation"))
    assert log is not None


def test_user_profile_context_uses_defaults_for_missing_profile_fields(db_session, dev_user) -> None:
    dev_user.current_level = None
    dev_user.goal_track = ""

    context = ContextBuilder(db_session).build_user_profile_context(dev_user)

    assert "\u5f53\u524d\u6c34\u5e73\uff1a" in context
    assert "\u5b66\u4e60\u76ee\u6807\uff1a" in context
    assert "None" not in context


def test_user_profile_context_includes_ladder_summary_without_exam_payload(db_session, dev_user) -> None:
    template = LadderTemplate(
        goal_track="self_study",
        current_level="beginner",
        name="测试天梯路径",
        description="Context test path",
        template_data={"phases": []},
        version=1,
        is_default=False,
    )
    db_session.add(template)
    db_session.flush()
    path = LearningPath(
        user_id=dev_user.id,
        template_id=template.id,
        goal_track="self_study",
        current_level="beginner",
        status="active",
    )
    db_session.add(path)
    db_session.flush()
    node = LearningPathNode(
        path_id=path.id,
        phase_index=1,
        node_index=1,
        algorithm_key="binary-search",
        title="二分查找",
        summary="学习二分边界。",
        material_markdown="# 二分查找\n\n很长的资料不应完整进入画像上下文。",
        resource_links=[],
        practice_items=[
            {
                "id": "choice-1",
                "type": "choice",
                "prompt": "二分查找的关键是什么？",
                "options": [{"id": "a", "text": "边界"}],
                "correct_option_id": "a",
                "explanation": "检查边界。",
            }
        ],
        unlock_rule={},
    )
    db_session.add(node)
    db_session.flush()
    db_session.add(
        NodeUserProgress(
            user_id=dev_user.id,
            node_id=node.id,
            material_completed=True,
            practice_completed=True,
            exam_passed=False,
        )
    )
    db_session.add(
        LadderExamAttempt(
            user_id=dev_user.id,
            path_id=path.id,
            node_id=node.id,
            status="submitted",
            exam_payload={"questions": [{"correct_option_id": "a", "secret": "full exam payload"}]},
            submitted_answers={"answers": []},
            result_payload={"results": []},
            score=72,
            passed=False,
        )
    )
    db_session.commit()

    context = ContextBuilder(db_session).build_user_profile_context(dev_user)

    assert "天梯路径：测试天梯路径" in context
    assert "当前节点：二分查找" in context
    assert "已完成练习 1 个" in context
    assert "最近考试：二分查找 考试未通过，得分 72" in context
    assert "correct_option_id" not in context
    assert "full exam payload" not in context


def test_generate_problem_parses_json(client: TestClient, db_session, dev_user) -> None:
    add_template(db_session, template_key="problem_generation")
    override_provider(
        FakeAIProvider(
            """
{
  "title": "Prefix Sum Warmup",
  "statement": "Given an array, answer range sum queries.",
  "input_format": "n q followed by array and queries",
  "output_format": "One sum per line",
  "constraints": "1 <= n, q <= 1000",
  "sample_input": "3 1\\n1 2 3\\n1 3",
  "sample_output": "6",
  "test_cases": [
    {
      "name": "01",
      "input": "3 1\\n1 2 3\\n1 3",
      "expected_output": "6",
      "is_sample": true
    },
    {
      "name": "02",
      "input": "5 2\\n1 2 3 4 5\\n2 4\\n1 5",
      "expected_output": "9\\n15",
      "is_sample": false
    }
  ],
  "hints": ["Build prefix sums"],
  "solution_idea": "先预处理前缀和数组，每次询问用右端前缀和减去左端前一个位置的前缀和，单次询问复杂度为 O(1)。",
  "solution_code_cpp": "#include <bits/stdc++.h>\\nusing namespace std;\\nint main(){return 0;}",
  "solution_code_python": "import sys\\nprint('ok')",
  "is_ai_generated": true
}
""".strip()
        )
    )

    response = client.post(
        "/api/ai/generate-problem",
        json={"difficulty": "beginner", "requirements": "range sum"},
    )

    assert response.status_code == 200
    assert '"is_ai_generated": true' in response.json()["data"]["result"]
    assert '"test_cases": [' in response.json()["data"]["result"]
    assert '"solution_code_cpp":' in response.json()["data"]["result"]
    assert '"solution_code_python":' in response.json()["data"]["result"]


def test_generate_problem_parse_error_is_safe(client: TestClient, db_session, dev_user) -> None:
    add_template(db_session, template_key="problem_generation")
    override_provider(FakeAIProvider("not json"))

    response = client.post(
        "/api/ai/generate-problem",
        json={"difficulty": "beginner", "requirements": "range sum"},
    )

    assert response.status_code == 502
    assert response.json() == {
        "error": {
            "code": "AI_OUTPUT_PARSE_ERROR",
            "message": "AI generated output could not be parsed",
        }
    }
    log = db_session.scalar(select(AICallLog).where(AICallLog.prompt_type == "problem_generation"))
    assert log is not None
    assert log.success is False
    assert log.error_code == "AI_OUTPUT_PARSE_ERROR"


def test_missing_prompt_template_returns_safe_error(client: TestClient, db_session, dev_user) -> None:
    for template in db_session.scalars(
        select(PromptTemplate).where(PromptTemplate.template_key == "concept_explanation")
    ):
        template.enabled = False
    db_session.commit()
    override_provider(FakeAIProvider())

    response = client.post("/api/ai/chat", json={"question": "Explain arrays", "mode": "beginner"})

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "PROMPT_TEMPLATE_NOT_FOUND"


def test_ai_config_missing_returns_safe_error(client: TestClient, db_session, dev_user) -> None:
    add_template(db_session, template_key="concept_explanation")
    app.dependency_overrides.pop(get_ai_provider, None)

    response = client.post("/api/ai/chat", json={"question": "Explain arrays", "mode": "beginner"})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AI_CONFIG_MISSING"


def test_provider_timeout_returns_safe_error(client: TestClient, db_session, dev_user) -> None:
    add_template(db_session, template_key="concept_explanation")
    override_provider(TimeoutAIProvider())

    response = client.post("/api/ai/chat", json={"question": "Explain arrays", "mode": "beginner"})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AI_PROVIDER_TIMEOUT"


def test_template_version_desc_is_used(client: TestClient, db_session, dev_user) -> None:
    add_template(db_session, template_key="concept_explanation", version=1, content="old {{question}}")
    add_template(db_session, template_key="concept_explanation", version=2, content="new {{question}}")
    override_provider(FakeAIProvider("latest template used"))

    response = client.post("/api/ai/chat", json={"question": "Explain arrays", "mode": "beginner"})

    assert response.status_code == 200
    templates = db_session.scalars(
        select(PromptTemplate)
        .where(PromptTemplate.template_key == "concept_explanation")
        .order_by(PromptTemplate.version.desc())
    ).all()
    assert templates[0].version == 2


def test_ai_input_validation(client: TestClient, dev_user) -> None:
    response = client.post(
        "/api/ai/code-review",
        json={"language": "java", "code": "x", "question": ""},
    )

    assert response.status_code == 422


def test_missing_topic_uses_safe_404(client: TestClient, db_session, dev_user) -> None:
    add_template(db_session, template_key="concept_explanation")
    override_provider(FakeAIProvider())

    response = client.post(
        "/api/ai/chat",
        json={"topic_id": str(uuid4()), "question": "Explain topic", "mode": "beginner"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TOPIC_NOT_FOUND"
