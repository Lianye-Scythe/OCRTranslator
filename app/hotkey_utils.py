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

VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_LWIN = 0x5B
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_LMENU = 0xA4
VK_RMENU = 0xA5
VK_RWIN = 0x5C
VK_RETURN = 0x0D
VK_TAB = 0x09
VK_SPACE = 0x20
VK_BACK = 0x08
VK_DELETE = 0x2E
VK_INSERT = 0x2D
VK_HOME = 0x24
VK_END = 0x23
VK_PRIOR = 0x21
VK_NEXT = 0x22
VK_LEFT = 0x25
VK_RIGHT = 0x27
VK_UP = 0x26
VK_DOWN = 0x28
VK_ESCAPE = 0x1B

SPECIAL_VIRTUAL_KEYS = {
    "ctrl": VK_CONTROL,
    "alt": VK_MENU,
    "shift": VK_SHIFT,
    "win": VK_LWIN,
    "enter": VK_RETURN,
    "tab": VK_TAB,
    "space": VK_SPACE,
    "backspace": VK_BACK,
    "delete": VK_DELETE,
    "insert": VK_INSERT,
    "home": VK_HOME,
    "end": VK_END,
    "page_up": VK_PRIOR,
    "page_down": VK_NEXT,
    "left": VK_LEFT,
    "right": VK_RIGHT,
    "up": VK_UP,
    "down": VK_DOWN,
    "escape": VK_ESCAPE,
}

VK_NORMALIZATION_MAP = {
    VK_LSHIFT: VK_SHIFT,
    VK_RSHIFT: VK_SHIFT,
    VK_LCONTROL: VK_CONTROL,
    VK_RCONTROL: VK_CONTROL,
    VK_LMENU: VK_MENU,
    VK_RMENU: VK_MENU,
    VK_RWIN: VK_LWIN,
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


def hotkey_unsupported_parts(hotkey_text: str) -> list[str]:
    unsupported: list[str] = []
    for part in canonical_hotkey_parts(hotkey_text):
        if part in MODIFIER_TOKENS:
            continue
        if part in SPECIAL_VIRTUAL_KEYS:
            continue
        if len(part) == 1 and part.isalnum():
            continue
        if part.startswith("f") and part[1:].isdigit():
            index = int(part[1:])
            if 1 <= index <= 24:
                continue
        unsupported.append(part)
    return unsupported


def hotkey_has_primary_key(hotkey_text: str) -> bool:
    modifier_virtual_keys = {VK_CONTROL, VK_MENU, VK_SHIFT, VK_LWIN}
    return any(virtual_key not in modifier_virtual_keys for virtual_key in hotkey_signature(hotkey_text))


def hotkey_to_virtual_keys(hotkey_text: str) -> set[int]:
    result: set[int] = set()
    for part in canonical_hotkey_parts(hotkey_text):
        if part in SPECIAL_VIRTUAL_KEYS:
            result.add(SPECIAL_VIRTUAL_KEYS[part])
            continue
        if len(part) == 1 and part.isalnum():
            result.add(ord(part.upper()))
            continue
        if part.startswith("f") and part[1:].isdigit():
            index = int(part[1:])
            if 1 <= index <= 24:
                result.add(0x6F + index)
    return result


def hotkey_signature(hotkey_text: str) -> frozenset[int]:
    return frozenset(hotkey_to_virtual_keys(hotkey_text))


def find_hotkey_conflicts(hotkeys: dict[str, str]) -> list[tuple[str, str, str]]:
    combos = {action: hotkey_signature(hotkey_text) for action, hotkey_text in hotkeys.items()}
    actions = list(combos.items())
    conflicts: list[tuple[str, str, str]] = []
    for index, (left_action, left_combo) in enumerate(actions):
        if not left_combo:
            continue
        for right_action, right_combo in actions[index + 1 :]:
            if not right_combo:
                continue
            if left_combo == right_combo:
                conflicts.append(("duplicate", left_action, right_action))
                continue
            if left_combo.issubset(right_combo) or right_combo.issubset(left_combo):
                conflicts.append(("subset", left_action, right_action))
    return conflicts


__all__ = [
    "canonical_hotkey_parts",
    "display_hotkey_text",
    "find_hotkey_conflicts",
    "hotkey_has_modifier",
    "hotkey_to_virtual_keys",
    "hotkey_has_primary_key",
    "hotkey_unsupported_parts",
    "hotkey_signature",
    "normalize_hotkey_text",
    "SPECIAL_VIRTUAL_KEYS",
    "VK_NORMALIZATION_MAP",
]
