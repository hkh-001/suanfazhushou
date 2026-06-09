from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.deps import get_ai_provider
from app.main import app
from app.models.ai_call_log import AICallLog
from app.models.prompt_template import PromptTemplate
from app.providers.ai.base import AIProvider, AIProviderError, AIProviderResult, AIProviderUsage


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
    assert not hasattr(log, "prompt")
    assert code not in (log.error_message or "")


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
  "hints": ["Build prefix sums"],
  "solution_idea": "Use prefix sums to answer each query in O(1).",
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
