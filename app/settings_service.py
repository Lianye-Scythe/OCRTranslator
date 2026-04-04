from copy import deepcopy

from .app_defaults import DEFAULT_CAPTURE_HOTKEY, DEFAULT_INPUT_HOTKEY, DEFAULT_SELECTION_HOTKEY, DEFAULT_THEME_MODE
from .hotkey_listener import find_hotkey_conflicts
from .models import ApiProfile, AppConfig, PromptPreset
from .profile_utils import default_base_url_for_provider, default_model_for_provider, normalize_model_value, normalize_provider_name, unique_non_empty
from .settings_models import SettingsFormSnapshot, SettingsValidationResult, ValidationIssue


def validate_profile_name(name: str, existing_names: set[str], current_name: str | None, *, fallback_name: str) -> str:
    normalized = name.strip() or fallback_name
    if normalized in {item for item in existing_names if item != current_name}:
        raise ValueError(normalized)
    return normalized


def validate_prompt_preset_name(name: str, existing_names: set[str], current_name: str | None, *, fallback_name: str) -> str:
    normalized = name.strip() or fallback_name
    if normalized in {item for item in existing_names if item != current_name}:
        raise ValueError(normalized)
    return normalized


def snapshot_hotkeys(snapshot: SettingsFormSnapshot) -> dict[str, str]:
    return {
        "capture": snapshot.hotkey,
        "selection": snapshot.selection_hotkey,
        "input": snapshot.input_hotkey,
    }


def _validation_scope_flags(scope: str) -> dict[str, bool]:
    normalized = str(scope or "save").strip().lower() or "save"
    return {
        "validate_names": normalized == "save",
        "validate_api": normalized in {"save", "fetch_models", "test_profile", "image_request", "text_request"},
        "require_model": normalized in {"save", "test_profile", "image_request", "text_request"},
        "validate_prompts": normalized in {"save", "image_request", "text_request"},
        "require_image_prompt": normalized in {"save", "image_request"},
        "require_text_prompt": normalized in {"save", "text_request"},
        "require_target_language": normalized in {"save", "image_request", "text_request"},
        "validate_hotkeys": normalized == "save",
    }


def validate_settings_snapshot(
    snapshot: SettingsFormSnapshot,
    *,
    existing_profile_names: set[str],
    current_profile_name: str | None,
    existing_prompt_preset_names: set[str],
    current_prompt_preset_name: str | None,
    normalize_hotkey,
    hotkey_has_modifier,
    tr,
    scope: str = "save",
) -> SettingsValidationResult:
    issues: list[ValidationIssue] = []
    flags = _validation_scope_flags(scope)

    def add_issue(field_key: str, category: str, message: str):
        issues.append(ValidationIssue(field_key=field_key, category=category, message=message))

    if flags["validate_names"]:
        try:
            validate_profile_name(snapshot.profile_name, existing_profile_names, current_profile_name, fallback_name=tr("untitled_profile"))
        except ValueError as exc:
            add_issue("profile_name", "api", tr("profile_name_exists", name=str(exc)))

    if flags["validate_api"]:
        base_url = snapshot.base_url.strip()
        if not base_url:
            add_issue("base_url", "api", tr("validation_base_url_required"))
        elif not base_url.lower().startswith(("http://", "https://")):
            add_issue("base_url", "api", tr("validation_base_url_scheme"))

        if flags["require_model"] and not snapshot.model_text.strip():
            add_issue("model", "api", tr("validation_model_required"))

        if not unique_non_empty(snapshot.api_keys_text.splitlines()):
            add_issue("api_keys", "api", tr("validation_api_keys_required"))

    if flags["validate_names"]:
        try:
            validate_prompt_preset_name(
                snapshot.prompt_preset_name,
                existing_prompt_preset_names,
                current_prompt_preset_name,
                fallback_name=tr("untitled_prompt_preset"),
            )
        except ValueError as exc:
            add_issue("prompt_preset_name", "prompt", tr("prompt_preset_name_exists", name=str(exc)))

    if flags["validate_prompts"]:
        if flags["require_image_prompt"] and not snapshot.image_prompt.strip():
            add_issue("image_prompt", "prompt", tr("validation_prompt_image_required"))
        if flags["require_text_prompt"] and not snapshot.text_prompt.strip():
            add_issue("text_prompt", "prompt", tr("validation_prompt_text_required"))

    if flags["require_target_language"] and not snapshot.target_language.strip():
        add_issue("target_language", "reading", tr("validation_target_language_required"))

    if flags["validate_hotkeys"]:
        hotkeys = snapshot_hotkeys(snapshot)
        normalized_hotkeys: dict[str, str] = {}
        for field_key, hotkey_value in hotkeys.items():
            if snapshot.active_record_target == field_key:
                add_issue(field_key, "reading", tr("validation_hotkey_recording"))
                continue
            if not hotkey_value:
                add_issue(field_key, "reading", tr("validation_hotkey_required"))
                continue
            try:
                normalized = normalize_hotkey(hotkey_value)
                if not hotkey_has_modifier(hotkey_value):
                    add_issue(field_key, "reading", tr("validation_hotkey_requires_modifier"))
                    continue
                if normalized in normalized_hotkeys:
                    add_issue(field_key, "reading", tr("validation_hotkey_duplicate", hotkey=hotkey_value))
                    add_issue(normalized_hotkeys[normalized], "reading", tr("validation_hotkey_duplicate", hotkey=hotkey_value))
                    continue
                normalized_hotkeys[normalized] = field_key
            except Exception as exc:  # noqa: BLE001
                add_issue(field_key, "reading", tr("validation_hotkey_invalid", error=exc))

        for kind, left_action, right_action in find_hotkey_conflicts(hotkeys):
            if kind == "duplicate":
                message = tr("validation_hotkey_duplicate", hotkey=hotkeys.get(left_action) or hotkeys.get(right_action) or "")
            else:
                message = tr(
                    "validation_hotkey_conflict",
                    hotkey_a=hotkeys.get(left_action, ""),
                    hotkey_b=hotkeys.get(right_action, ""),
                )
            add_issue(left_action, "reading", message)
            add_issue(right_action, "reading", message)

    return SettingsValidationResult(issues=issues)


def build_profile_from_snapshot(snapshot: SettingsFormSnapshot, *, current_profile: ApiProfile) -> ApiProfile:
    provider = normalize_provider_name(snapshot.provider or "gemini")
    fallback_name = current_profile.name or "Default Gemini"
    profile_name = snapshot.profile_name.strip() or fallback_name
    api_keys = unique_non_empty(snapshot.api_keys_text.splitlines())
    available_models = unique_non_empty(normalize_model_value(item, provider) for item in snapshot.model_items)
    fallback_model = current_profile.model if current_profile.provider == provider else default_model_for_provider(provider)
    model = normalize_model_value(snapshot.model_text or fallback_model, provider)
    if not model and available_models:
        model = available_models[0]
    if model and model not in available_models:
        available_models.append(model)
    base_url = snapshot.base_url.strip()
    if not base_url:
        if current_profile.provider == provider and current_profile.base_url.strip():
            base_url = current_profile.base_url.strip()
        else:
            base_url = default_base_url_for_provider(provider)
    return ApiProfile(
        name=profile_name,
        provider=provider,
        base_url=base_url,
        api_keys=api_keys,
        model=model,
        available_models=available_models,
        retry_count=int(snapshot.retry_count),
        retry_interval=float(snapshot.retry_interval),
    )


def build_prompt_preset_from_snapshot(snapshot: SettingsFormSnapshot, *, current_prompt_preset: PromptPreset) -> PromptPreset:
    name = snapshot.prompt_preset_name.strip() or current_prompt_preset.name
    image_prompt = snapshot.image_prompt.strip() or current_prompt_preset.image_prompt.strip()
    text_prompt = snapshot.text_prompt.strip() or current_prompt_preset.text_prompt.strip()
    return PromptPreset(
        name=name,
        builtin_id=getattr(current_prompt_preset, "builtin_id", ""),
        image_prompt=image_prompt,
        text_prompt=text_prompt,
    )


def _upsert_profile(config: AppConfig, profile: ApiProfile, *, current_name: str):
    for index, item in enumerate(config.api_profiles):
        if item.name == current_name:
            config.api_profiles[index] = profile
            config.active_profile_name = profile.name
            return
    for index, item in enumerate(config.api_profiles):
        if item.name == profile.name:
            config.api_profiles[index] = profile
            config.active_profile_name = profile.name
            return
    config.api_profiles.append(profile)
    config.active_profile_name = profile.name


def _upsert_prompt_preset(config: AppConfig, prompt_preset: PromptPreset, *, current_name: str):
    for index, item in enumerate(config.prompt_presets):
        if item.name == current_name:
            config.prompt_presets[index] = prompt_preset
            config.active_prompt_preset_name = prompt_preset.name
            return
    for index, item in enumerate(config.prompt_presets):
        if item.name == prompt_preset.name:
            config.prompt_presets[index] = prompt_preset
            config.active_prompt_preset_name = prompt_preset.name
            return
    config.prompt_presets.append(prompt_preset)
    config.active_prompt_preset_name = prompt_preset.name


def build_candidate_config(
    base_config: AppConfig,
    snapshot: SettingsFormSnapshot,
    *,
    current_profile: ApiProfile,
    current_prompt_preset: PromptPreset,
) -> tuple[str, AppConfig, ApiProfile, PromptPreset]:
    candidate_config = deepcopy(base_config)
    previous_language = candidate_config.ui_language
    profile = build_profile_from_snapshot(snapshot, current_profile=current_profile)
    prompt_preset = build_prompt_preset_from_snapshot(snapshot, current_prompt_preset=current_prompt_preset)
    _upsert_profile(candidate_config, profile, current_name=base_config.active_profile_name)
    _upsert_prompt_preset(candidate_config, prompt_preset, current_name=base_config.active_prompt_preset_name)
    candidate_config.target_language = snapshot.target_language.strip() or candidate_config.target_language
    candidate_config.ui_language = snapshot.ui_language.strip() or candidate_config.ui_language
    candidate_config.theme_mode = snapshot.theme_mode or DEFAULT_THEME_MODE
    candidate_config.hotkey = snapshot.hotkey.strip() or DEFAULT_CAPTURE_HOTKEY
    candidate_config.selection_hotkey = snapshot.selection_hotkey.strip() or DEFAULT_SELECTION_HOTKEY
    candidate_config.input_hotkey = snapshot.input_hotkey.strip() or DEFAULT_INPUT_HOTKEY
    candidate_config.overlay_font_family = snapshot.overlay_font_family
    candidate_config.temperature = float(snapshot.temperature)
    candidate_config.overlay_font_size = int(snapshot.overlay_font_size)
    candidate_config.overlay_width = int(snapshot.overlay_width)
    candidate_config.overlay_height = int(snapshot.overlay_height)
    candidate_config.margin = int(snapshot.overlay_margin)
    candidate_config.overlay_auto_expand_top_margin = int(snapshot.overlay_auto_expand_top_margin)
    candidate_config.overlay_auto_expand_bottom_margin = int(snapshot.overlay_auto_expand_bottom_margin)
    candidate_config.close_to_tray_on_close = bool(snapshot.close_to_tray_on_close)
    candidate_config.mode = snapshot.mode or "book_lr"
    candidate_config.active_prompt_preset_name = prompt_preset.name
    return previous_language, candidate_config, profile, prompt_preset
