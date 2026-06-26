import json
from time import perf_counter

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.providers.ai.base import AIProvider, AIProviderError, AIProviderResult
from app.repositories.ai_call_logs import create_ai_call_log
from app.schemas.ai import (
    AIResponseData,
    AIUsage,
    ChatRequest,
    CodeReviewRequest,
    GeneratedProblem,
    ProblemGenerationRequest,
)
from app.schemas.ladder_exam import LadderExamAIResult, LadderExamPayload
from app.models.submission import Submission
from app.schemas.submission import SubmissionDiagnosisResponse
from app.services.ai.context_builder import ContextBuilder
from app.services.ai.prompt_renderer import PromptRenderer
from app.services.settings.ai_runtime_settings import get_effective_ai_settings


_ERROR_MESSAGES = {
    "AI_PROVIDER_TIMEOUT": "AI provider request timed out",
    "AI_PROVIDER_ERROR": "AI provider returned an error",
    "AI_CONFIG_MISSING": "AI provider configuration is missing",
    "AI_OUTPUT_PARSE_ERROR": "AI output could not be parsed",
    "PROMPT_TEMPLATE_NOT_FOUND": "Prompt template not found",
}


def _safe_error_message(code: str) -> str:
    return _ERROR_MESSAGES.get(code, code.replace("_", " ").title())


def _strip_json_fence(content: str) -> str:
    stripped = content.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if len(lines) >= 3 and lines[0].strip().lower() in {"```json", "```"} and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return stripped


class AIService:
    def __init__(self, db: Session, provider: AIProvider) -> None:
        self.db = db
        self.provider = provider
        self.context_builder = ContextBuilder(db)
        self.prompt_renderer = PromptRenderer(db)

    def chat(self, *, user: User, payload: ChatRequest) -> AIResponseData:
        context = self.context_builder.build_topic_context(payload.topic_id)
        user_profile = self.context_builder.build_user_profile_context(user)
        prompt = self.prompt_renderer.render(
            template_key="concept_explanation",
            values={
                "topic_context": "\n\n".join(part for part in [user_profile, context] if part),
                "mode": payload.mode,
                "question": payload.question,
            },
        )
        return self._complete(user=user, prompt=prompt, prompt_type="concept_explanation")

    def code_review(self, *, user: User, payload: CodeReviewRequest) -> AIResponseData:
        context = self.context_builder.build_topic_context(payload.topic_id)
        user_profile = self.context_builder.build_user_profile_context(user)
        prompt = self.prompt_renderer.render(
            template_key="code_review",
            values={
                "topic_context": "\n\n".join(part for part in [user_profile, context] if part),
                "language": payload.language,
                "code": payload.code,
                "question": payload.question or "",
            },
        )
        return self._complete(user=user, prompt=prompt, prompt_type="code_review")

    def generate_problem(self, *, user: User, payload: ProblemGenerationRequest) -> AIResponseData:
        context = self.context_builder.build_topic_context(payload.topic_id)
        user_profile = self.context_builder.build_user_profile_context(user)
        prompt = self.prompt_renderer.render(
            template_key="problem_generation",
            values={
                "topic_context": "\n\n".join(part for part in [user_profile, context] if part),
                "difficulty": payload.difficulty,
                "requirements": payload.requirements or "",
            },
        )
        started = perf_counter()
        provider_result = self._call_provider(prompt=prompt, prompt_type="problem_generation", started=started, user=user)
        try:
            parsed = GeneratedProblem.model_validate(json.loads(provider_result.content))
        except (json.JSONDecodeError, ValidationError) as exc:
            self._log_call(
                user=user,
                model=provider_result.model,
                prompt_type="problem_generation",
                input_tokens=provider_result.usage.input_tokens,
                output_tokens=provider_result.usage.output_tokens,
                latency_ms=round((perf_counter() - started) * 1000),
                success=False,
                error_code="AI_OUTPUT_PARSE_ERROR",
                error_message="Ai Output Parse Error",
            )
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "AI_OUTPUT_PARSE_ERROR",
                    "message": "AI generated output could not be parsed",
                },
            ) from exc
        self._log_call(
            user=user,
            model=provider_result.model,
            prompt_type="problem_generation",
            input_tokens=provider_result.usage.input_tokens,
            output_tokens=provider_result.usage.output_tokens,
            latency_ms=round((perf_counter() - started) * 1000),
            success=True,
        )
        return AIResponseData(
            result=parsed.model_dump_json(indent=2),
            prompt_type="problem_generation",
            model=provider_result.model,
            usage=AIUsage(
                input_tokens=provider_result.usage.input_tokens,
                output_tokens=provider_result.usage.output_tokens,
            ),
        )

    def diagnose_submission(
        self,
        *,
        user: User,
        submission: Submission,
    ) -> SubmissionDiagnosisResponse:
        context = self.context_builder.build_submission_diagnosis_context(submission)
        user_profile = self.context_builder.build_user_profile_context(user)
        values = dict(context.values)
        values["problem_context"] = "\n\n".join(
            part for part in [user_profile, values["problem_context"]] if part
        )
        prompt = self.prompt_renderer.render(
            template_key="submission_diagnosis",
            values=values,
        )
        result = self._complete(
            user=user,
            prompt=prompt,
            prompt_type="submission_diagnosis",
        )
        return SubmissionDiagnosisResponse(
            submission_id=submission.id,
            verdict=submission.verdict,
            result=result.result,
            prompt_type="submission_diagnosis",
            model=result.model,
            usage=result.usage,
            context_info=context.info,
        )

    def generate_ladder_exam(
        self,
        *,
        user: User,
        node_title: str,
        node_summary: str,
        material: str,
        practice_items: object,
    ) -> LadderExamAIResult:
        context = self.context_builder.build_ladder_exam_context(
            user=user,
            node_title=node_title,
            node_summary=node_summary,
            material=material,
            practice_items=practice_items,
        )
        prompt = self.prompt_renderer.render(
            template_key="ladder_exam_generation",
            values=context.values,
        )
        started = perf_counter()
        provider_result = self._call_provider(
            prompt=prompt,
            prompt_type="ladder_exam_generation",
            started=started,
            user=user,
        )
        try:
            parsed = LadderExamPayload.model_validate(json.loads(_strip_json_fence(provider_result.content)))
        except (json.JSONDecodeError, ValidationError) as exc:
            self._log_call(
                user=user,
                model=provider_result.model,
                prompt_type="ladder_exam_generation",
                input_tokens=provider_result.usage.input_tokens,
                output_tokens=provider_result.usage.output_tokens,
                latency_ms=round((perf_counter() - started) * 1000),
                success=False,
                error_code="AI_OUTPUT_PARSE_ERROR",
                error_message="Ai Output Parse Error",
            )
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "LADDER_EXAM_GENERATION_FAILED",
                    "message": "AI generated exam could not be parsed",
                },
            ) from exc
        self._log_call(
            user=user,
            model=provider_result.model,
            prompt_type="ladder_exam_generation",
            input_tokens=provider_result.usage.input_tokens,
            output_tokens=provider_result.usage.output_tokens,
            latency_ms=round((perf_counter() - started) * 1000),
            success=True,
        )
        return LadderExamAIResult(
            payload=parsed,
            model=provider_result.model,
            usage=AIUsage(
                input_tokens=provider_result.usage.input_tokens,
                output_tokens=provider_result.usage.output_tokens,
            ),
        )

    def _complete(self, *, user: User, prompt: str, prompt_type: str) -> AIResponseData:
        started = perf_counter()
        provider_result = self._call_provider(prompt=prompt, prompt_type=prompt_type, started=started, user=user)
        self._log_call(
            user=user,
            model=provider_result.model,
            prompt_type=prompt_type,
            input_tokens=provider_result.usage.input_tokens,
            output_tokens=provider_result.usage.output_tokens,
            latency_ms=round((perf_counter() - started) * 1000),
            success=True,
        )
        return AIResponseData(
            result=provider_result.content,
            prompt_type=prompt_type,
            model=provider_result.model,
            usage=AIUsage(
                input_tokens=provider_result.usage.input_tokens,
                output_tokens=provider_result.usage.output_tokens,
            ),
        )

    def _call_provider(
        self,
        *,
        prompt: str,
        prompt_type: str,
        started: float,
        user: User,
    ) -> AIProviderResult:
        try:
            return self.provider.complete(prompt=prompt, prompt_type=prompt_type)
        except AIProviderError as exc:
            effective_settings = get_effective_ai_settings()
            self._log_call(
                user=user,
                model=effective_settings.model or "unconfigured",
                prompt_type=prompt_type,
                input_tokens=None,
                output_tokens=None,
                latency_ms=round((perf_counter() - started) * 1000),
                success=False,
                error_code=exc.code,
                error_message=_safe_error_message(exc.code),
            )
            raise HTTPException(
                status_code=exc.status_code,
                detail={"code": exc.code, "message": exc.message},
            ) from exc

    def _log_call(
        self,
        *,
        user: User,
        model: str,
        prompt_type: str,
        input_tokens: int | None,
        output_tokens: int | None,
        latency_ms: int,
        success: bool,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        create_ai_call_log(
            self.db,
            user_id=user.id,
            provider=self.provider.provider_name,
            model=model,
            prompt_type=prompt_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            success=success,
            error_code=error_code,
            error_message=error_message,
        )
