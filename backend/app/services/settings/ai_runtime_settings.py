from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

from app.core.config import settings


@dataclass(frozen=True)
class EffectiveAISettings:
    provider: str
    base_url: str | None
    api_key: str | None
    model: str | None
    source: str

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)

    @property
    def api_key_set(self) -> bool:
        return bool(self.api_key)


@dataclass(frozen=True)
class RuntimeAISettings:
    base_url: str
    api_key: str
    model: str


_runtime_ai_settings: RuntimeAISettings | None = None


def sanitize_base_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("base_url must use http or https")
    path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def set_runtime_ai_settings(*, base_url: str, api_key: str, model: str) -> RuntimeAISettings:
    global _runtime_ai_settings
    clean_api_key = api_key.strip()
    clean_model = model.strip()
    if not clean_api_key or not clean_model:
        raise ValueError("api_key and model are required")
    _runtime_ai_settings = RuntimeAISettings(
        base_url=sanitize_base_url(base_url),
        api_key=clean_api_key,
        model=clean_model,
    )
    return _runtime_ai_settings


def clear_runtime_ai_settings() -> None:
    global _runtime_ai_settings
    _runtime_ai_settings = None


def get_runtime_ai_settings() -> RuntimeAISettings | None:
    return _runtime_ai_settings


def get_effective_ai_settings() -> EffectiveAISettings:
    if _runtime_ai_settings is not None:
        return EffectiveAISettings(
            provider=settings.ai_provider,
            base_url=_runtime_ai_settings.base_url,
            api_key=_runtime_ai_settings.api_key,
            model=_runtime_ai_settings.model,
            source="runtime",
        )

    if settings.ai_base_url and settings.ai_api_key and settings.ai_model:
        try:
            base_url = sanitize_base_url(settings.ai_base_url)
        except ValueError:
            return EffectiveAISettings(
                provider=settings.ai_provider,
                base_url=None,
                api_key=None,
                model=None,
                source="none",
            )
        return EffectiveAISettings(
            provider=settings.ai_provider,
            base_url=base_url,
            api_key=settings.ai_api_key,
            model=settings.ai_model,
            source="env",
        )

    return EffectiveAISettings(
        provider=settings.ai_provider,
        base_url=None,
        api_key=None,
        model=None,
        source="none",
    )
