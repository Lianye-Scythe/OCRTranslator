from dataclasses import dataclass, field


@dataclass(slots=True)
class SettingsFormSnapshot:
    profile_name: str
    provider: str
    base_url: str
    model_text: str
    model_items: list[str] = field(default_factory=list)
    api_keys_text: str = ""
    retry_count: int = 0
    retry_interval: float = 0.0
    target_language: str = ""
    ui_language: str = ""
    hotkey: str = ""
    selection_hotkey: str = ""
    input_hotkey: str = ""
    overlay_font_family: str = ""
    overlay_font_size: int = 12
    temperature: float = 0.2
    overlay_width: int = 440
    overlay_height: int = 520
    overlay_margin: int = 18
    close_to_tray_on_close: bool = False
    mode: str = "book_lr"
    prompt_preset_name: str = ""
    image_prompt: str = ""
    text_prompt: str = ""
    active_record_target: str | None = None


@dataclass(slots=True)
class ValidationIssue:
    field_key: str
    category: str
    message: str


@dataclass(slots=True)
class SettingsValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.issues

    @property
    def first_error(self) -> str:
        return self.issues[0].message if self.issues else ""

    def messages_for_category(self, category: str) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for issue in self.issues:
            if issue.category != category or issue.message in seen:
                continue
            seen.add(issue.message)
            result.append(issue.message)
        return result

    def messages_for_field(self, field_key: str) -> list[str]:
        return [issue.message for issue in self.issues if issue.field_key == field_key]

    def field_keys(self) -> set[str]:
        return {issue.field_key for issue in self.issues}
