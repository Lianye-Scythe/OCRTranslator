from __future__ import annotations

MODIFIER_ALIASES = {
    "ctrl": "ctrl",
    "control": "ctrl",
    "alt": "alt",
    "shift": "shift",
    "cmd": "win",
    "win": "win",
    "windows": "win",
    "meta": "win",
}

SPECIAL_KEY_ALIASES = {
    "enter": "enter",
    "return": "enter",
    "tab": "tab",
    "space": "space",
    "backspace": "backspace",
    "delete": "delete",
    "insert": "insert",
    "home": "home",
    "end": "end",
    "pageup": "page_up",
    "page_up": "page_up",
    "pagedown": "page_down",
    "page_down": "page_down",
    "left": "left",
    "right": "right",
    "up": "up",
    "down": "down",
    "esc": "escape",
    "escape": "escape",
}

NORMALIZED_SPECIAL_TOKENS = {
    "ctrl": "<ctrl>",
    "alt": "<alt>",
    "shift": "<shift>",
    "win": "<cmd>",
    "enter": "<enter>",
    "tab": "<tab>",
    "space": "<space>",
    "backspace": "<backspace>",
    "delete": "<delete>",
    "insert": "<insert>",
    "home": "<home>",
    "end": "<end>",
    "page_up": "<page_up>",
    "page_down": "<page_down>",
    "left": "<left>",
    "right": "<right>",
    "up": "<up>",
    "down": "<down>",
    "escape": "<esc>",
}

DISPLAY_TOKENS = {
    "ctrl": "Ctrl",
    "alt": "Alt",
    "shift": "Shift",
    "win": "Win",
    "enter": "Enter",
    "tab": "Tab",
    "space": "Space",
    "backspace": "Backspace",
    "delete": "Delete",
    "insert": "Insert",
    "home": "Home",
    "end": "End",
    "page_up": "PageUp",
    "page_down": "PageDown",
    "left": "Left",
    "right": "Right",
    "up": "Up",
    "down": "Down",
    "escape": "Esc",
}

MODIFIER_TOKENS = ("ctrl", "alt", "shift", "win")


def split_hotkey_parts(hotkey_text: str) -> list[str]:
    return [part.strip().lower() for part in str(hotkey_text or "").replace("-", "+").split("+") if part.strip()]


def canonical_hotkey_part(part: str) -> str:
    token = str(part or "").strip().lower()
    if not token:
        return ""
    if token in MODIFIER_ALIASES:
        return MODIFIER_ALIASES[token]
    if token in SPECIAL_KEY_ALIASES:
        return SPECIAL_KEY_ALIASES[token]
    if len(token) == 1 and token.isalnum():
        return token
    if token.startswith("f") and token[1:].isdigit():
        index = int(token[1:])
        if 1 <= index <= 24:
            return token
    return token


def canonical_hotkey_parts(hotkey_text: str) -> list[str]:
    result: list[str] = []
    for part in split_hotkey_parts(hotkey_text):
        normalized = canonical_hotkey_part(part)
        if normalized:
            result.append(normalized)
    return result


def hotkey_has_modifier(hotkey_text: str) -> bool:
    return any(part in MODIFIER_TOKENS for part in canonical_hotkey_parts(hotkey_text))


def normalize_hotkey_text(hotkey_text: str) -> str:
    mapped: list[str] = []
    for part in canonical_hotkey_parts(hotkey_text):
        mapped.append(NORMALIZED_SPECIAL_TOKENS.get(part, f"<{part}>" if part.startswith("f") and part[1:].isdigit() else part))
    if not mapped:
        raise ValueError("Empty hotkey")
    return "+".join(mapped)


def display_hotkey_text(hotkey_text: str) -> str:
    parts = canonical_hotkey_parts(hotkey_text)
    if not parts:
        return ""
    display_parts = [DISPLAY_TOKENS.get(part, part.upper() if len(part) == 1 else part.upper() if part.startswith("f") else part) for part in parts]
    return "+".join(display_parts)
