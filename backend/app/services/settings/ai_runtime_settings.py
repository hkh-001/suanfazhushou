import json
import logging
import os
from pathlib import Path
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

from app.core.config import settings

logger = logging.getLogger(__name__)


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
_logged_persistent_paths: set[Path] = set()


def _persistent_settings_enabled() -> bool:
    return bool(settings.enable_persistent_ai_settings)


def persistent_settings_enabled() -> bool:
    return _persistent_settings_enabled()


def _persistent_settings_path() -> Path:
    path = Path(settings.persistent_ai_settings_path).expanduser()
    if path.is_absolute():
        return path
    return (settings.project_root / path).resolve()


def _load_persistent_ai_settings() -> RuntimeAISettings | None:
    if not _persistent_settings_enabled():
        return None

    path = _persistent_settings_path()
    if not path.exists():
        return None

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        base_url = raw.get("base_url")
        api_key = raw.get("api_key")
        model = raw.get("model")
        if not isinstance(base_url, str) or not isinstance(api_key, str) or not isinstance(model, str):
            return None
        clean_api_key = api_key.strip()
        clean_model = model.strip()
        if not clean_api_key or not clean_model:
            return None
        clean_base_url = sanitize_base_url(base_url)
        return RuntimeAISettings(
            base_url=clean_base_url,
            api_key=clean_api_key,
            model=clean_model,
        )
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def _save_persistent_ai_settings(config: RuntimeAISettings) -> None:
    if not _persistent_settings_enabled():
        return

    path = _persistent_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    temp_path.write_text(
        json.dumps(
            {
                "base_url": config.base_url,
                "api_key": config.api_key,
                "model": config.model,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    try:
        os.chmod(temp_path, 0o600)
    except OSError:
        pass
    temp_path.replace(path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _delete_persistent_ai_settings() -> None:
    if not _persistent_settings_enabled():
        return

    path = _persistent_settings_path()
    try:
        path.unlink()
    except FileNotFoundError:
        return


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
    _save_persistent_ai_settings(_runtime_ai_settings)
    return _runtime_ai_settings


def clear_runtime_ai_settings() -> None:
    global _runtime_ai_settings
    _runtime_ai_settings = None
    _delete_persistent_ai_settings()


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

    persistent = _load_persistent_ai_settings()
    if persistent is not None:
        path = _persistent_settings_path()
        if path not in _logged_persistent_paths:
            logger.info("AI settings loaded from persistent file: %s", path)
            _logged_persistent_paths.add(path)
        return EffectiveAISettings(
            provider=settings.ai_provider,
            base_url=persistent.base_url,
            api_key=persistent.api_key,
            model=persistent.model,
            source="persistent",
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
