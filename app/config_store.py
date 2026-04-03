import json
import shutil
import time
from dataclasses import asdict
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from .constants import (
    CONFIG_PATH,
    DEFAULT_BASE_URL,
    DEFAULT_CAPTURE_HOTKEY,
    DEFAULT_INPUT_HOTKEY,
    DEFAULT_MODEL,
    DEFAULT_SELECTION_HOTKEY,
)
from .models import ApiProfile, AppConfig, PromptPreset, default_prompt_presets
from .profile_utils import (
    default_base_url_for_provider,
    default_model_for_provider,
    normalize_model_value,
    normalize_provider_name,
    unique_non_empty,
)


def show_startup_warning(message: str):
    created_app = QApplication.instance() is None
    app = QApplication.instance() or QApplication([])
    QMessageBox.warning(None, "OCRTranslator", message)
    if created_app:
        app.quit()


def _default_profile() -> ApiProfile:
    return ApiProfile()


def _default_prompt_preset() -> PromptPreset:
    return default_prompt_presets()[0]


def _config_to_dict(config: AppConfig) -> dict:
    data = asdict(config)
    data["api_profiles"] = [asdict(profile) for profile in config.api_profiles]
    data["prompt_presets"] = [asdict(preset) for preset in config.prompt_presets]
    return data


def _coerce_text(value, default: str) -> str:
    text = str(value).strip() if value is not None else ""
    return text or default


def _coerce_int(value, default: int, *, min_value: int | None = None, max_value: int | None = None) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError):
        result = default
    if min_value is not None:
        result = max(min_value, result)
    if max_value is not None:
        result = min(max_value, result)
    return result


def _coerce_float(value, default: float, *, min_value: float | None = None, max_value: float | None = None) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        result = default
    if min_value is not None:
        result = max(min_value, result)
    if max_value is not None:
        result = min(max_value, result)
    return result


def _coerce_str_list(value) -> list[str]:
    if value is None:
        raw_values = []
    elif isinstance(value, str):
        raw_values = value.splitlines() if any(sep in value for sep in ("\n", "\r")) else [value]
    elif isinstance(value, (list, tuple, set)):
        raw_values = list(value)
    else:
        raw_values = [value]
    return unique_non_empty(raw_values)


def _normalize_active_profile_name(profiles: list[ApiProfile], active_name: str | None) -> str:
    names = {profile.name for profile in profiles}
    if active_name in names:
        return active_name
    return profiles[0].name


def _normalize_active_prompt_preset_name(presets: list[PromptPreset], active_name: str | None) -> str:
    names = {preset.name for preset in presets}
    if active_name in names:
        return active_name
    return presets[0].name


def _dict_to_profile(data: dict) -> ApiProfile:
    source = data if isinstance(data, dict) else {}
    defaults = asdict(_default_profile())
    merged = {**defaults, **source}
    provider = normalize_provider_name(str(merged.get("provider", "gemini")).strip().lower())
    available_models = _coerce_str_list(merged.get("available_models", []))

    model_value = str(merged.get("model", "")).strip()
    normalized_model = normalize_model_value(model_value, provider) if model_value else ""
    normalized_models = unique_non_empty(normalize_model_value(model, provider) for model in available_models)

    if not normalized_model and normalized_models:
        normalized_model = normalized_models[0]
    if not normalized_model:
        normalized_model = default_model_for_provider(provider)
    if normalized_model and normalized_model not in normalized_models:
        normalized_models.append(normalized_model)

    return ApiProfile(
        name=_coerce_text(merged.get("name"), defaults["name"]),
        provider=provider,
        base_url=_coerce_text(merged.get("base_url"), default_base_url_for_provider(provider)),
        api_keys=_coerce_str_list(merged.get("api_keys", [])),
        model=normalized_model,
        available_models=normalized_models,
        retry_count=_coerce_int(merged.get("retry_count"), defaults["retry_count"], min_value=0, max_value=10),
        retry_interval=_coerce_float(merged.get("retry_interval"), defaults["retry_interval"], min_value=0, max_value=60),
    )


def _dict_to_prompt_preset(data: dict) -> PromptPreset:
    source = data if isinstance(data, dict) else {}
    default_map = {preset.builtin_id: preset for preset in default_prompt_presets()}
    builtin_id = str(source.get("builtin_id", "")).strip()
    default_preset = default_map.get(builtin_id, _default_prompt_preset())
    defaults = asdict(default_preset)
    merged = {**defaults, **source}
    return PromptPreset(
        name=_coerce_text(merged.get("name"), defaults["name"]),
        builtin_id=str(merged.get("builtin_id", builtin_id or defaults.get("builtin_id", ""))).strip(),
        image_prompt=_coerce_text(merged.get("image_prompt"), defaults["image_prompt"]),
        text_prompt=_coerce_text(merged.get("text_prompt"), defaults["text_prompt"]),
    )


def _migrate_legacy_config(data: dict) -> AppConfig:
    source = data if isinstance(data, dict) else {}

    if "api_profiles" in source:
        profiles_data = source.get("api_profiles", [])
        if not isinstance(profiles_data, list):
            profiles_data = [profiles_data]
        profiles = [_dict_to_profile(item) for item in profiles_data] or [_default_profile()]
    else:
        profiles = [
            _dict_to_profile(
                {
                    "name": "Default Gemini",
                    "provider": "gemini",
                    "base_url": source.get("base_url", DEFAULT_BASE_URL),
                    "api_keys": [source.get("api_key", "")] if source.get("api_key") else [],
                    "model": source.get("model", DEFAULT_MODEL),
                    "available_models": [source.get("model", DEFAULT_MODEL)],
                }
            )
        ]

    if "prompt_presets" in source:
        presets_data = source.get("prompt_presets", [])
        if not isinstance(presets_data, list):
            presets_data = [presets_data]
        prompt_presets = [_dict_to_prompt_preset(item) for item in presets_data] or default_prompt_presets()
    else:
        prompt_presets = default_prompt_presets()

    ui_language = str(source.get("ui_language", "zh-TW")).strip()
    mode = str(source.get("mode", "book_lr")).strip()

    return AppConfig(
        target_language=_coerce_text(source.get("target_language"), "繁體中文"),
        mode=mode if mode in {"book_lr", "web_ud"} else "book_lr",
        temperature=_coerce_float(source.get("temperature"), 0.2, min_value=0, max_value=2),
        overlay_width=_coerce_int(source.get("overlay_width"), 440, min_value=240, max_value=1600),
        overlay_height=_coerce_int(source.get("overlay_height"), 520, min_value=220, max_value=1600),
        margin=_coerce_int(source.get("margin"), 18, min_value=8, max_value=120),
        ui_language=ui_language if ui_language in {"zh-TW", "en"} else "zh-TW",
        hotkey=_coerce_text(source.get("hotkey"), DEFAULT_CAPTURE_HOTKEY),
        selection_hotkey=_coerce_text(source.get("selection_hotkey"), DEFAULT_SELECTION_HOTKEY),
        input_hotkey=_coerce_text(source.get("input_hotkey"), DEFAULT_INPUT_HOTKEY),
        overlay_font_family=_coerce_text(source.get("overlay_font_family"), "Microsoft JhengHei UI"),
        overlay_font_size=_coerce_int(source.get("overlay_font_size"), 12, min_value=10, max_value=32),
        overlay_opacity=_coerce_int(source.get("overlay_opacity"), 96, min_value=55, max_value=100),
        overlay_pinned=bool(source.get("overlay_pinned", False)),
        active_profile_name=_normalize_active_profile_name(profiles, str(source.get("active_profile_name", "")).strip() or None),
        active_prompt_preset_name=_normalize_active_prompt_preset_name(
            prompt_presets,
            str(source.get("active_prompt_preset_name", "")).strip() or None,
        ),
        api_profiles=profiles,
        prompt_presets=prompt_presets,
    )


def load_config() -> AppConfig:
    config = AppConfig()

    if CONFIG_PATH.exists():
        try:
            return _migrate_legacy_config(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001
            backup_path = CONFIG_PATH.with_suffix(f".broken-{time.strftime('%Y%m%d-%H%M%S')}.json")
            try:
                shutil.copy2(CONFIG_PATH, backup_path)
            except Exception:  # noqa: BLE001
                backup_path = None
            message = "Failed to load config.json. A fresh config will be created."
            if backup_path:
                message += f" Backup: {backup_path.name}"
            try:
                show_startup_warning(message)
            except Exception:  # noqa: BLE001
                pass

    save_config(config)
    return config


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.tmp-{time.time_ns()}")
    try:
        temp_path.write_text(content, encoding="utf-8")
        temp_path.replace(path)
    except Exception:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except Exception:  # noqa: BLE001
            pass
        raise


def save_config(config: AppConfig) -> None:
    payload = json.dumps(_config_to_dict(config), ensure_ascii=False, indent=2) + "\n"
    _atomic_write_text(CONFIG_PATH, payload)
