from pynput import keyboard


WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105

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
    "control": VK_CONTROL,
    "alt": VK_MENU,
    "shift": VK_SHIFT,
    "win": VK_LWIN,
    "windows": VK_LWIN,
    "cmd": VK_LWIN,
    "meta": VK_LWIN,
    "enter": VK_RETURN,
    "return": VK_RETURN,
    "tab": VK_TAB,
    "space": VK_SPACE,
    "backspace": VK_BACK,
    "delete": VK_DELETE,
    "insert": VK_INSERT,
    "home": VK_HOME,
    "end": VK_END,
    "pageup": VK_PRIOR,
    "page_up": VK_PRIOR,
    "pagedown": VK_NEXT,
    "page_down": VK_NEXT,
    "left": VK_LEFT,
    "right": VK_RIGHT,
    "up": VK_UP,
    "down": VK_DOWN,
    "esc": VK_ESCAPE,
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


def hotkey_to_virtual_keys(hotkey_text: str) -> set[int]:
    parts = [part.strip().lower() for part in str(hotkey_text or "").replace("-", "+").split("+") if part.strip()]
    result: set[int] = set()
    for part in parts:
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


def normalize_virtual_key(vk_code: int) -> int:
    return VK_NORMALIZATION_MAP.get(int(vk_code), int(vk_code))


class HotkeyListener:
    def __init__(self, hotkeys: dict[str, str], callback, *, log_func=None):
        self.hotkeys = dict(hotkeys)
        self.callback = callback
        self.log = log_func or (lambda message: None)
        self.listener = None
        self._combo_virtual_keys: dict[str, set[int]] = {}
        self._pressed_virtual_keys: set[int] = set()
        self._active_actions: set[str] = set()
        self._suppressed_virtual_keys: set[int] = set()

    def start(self):
        self._combo_virtual_keys = {action: hotkey_to_virtual_keys(hotkey_text) for action, hotkey_text in self.hotkeys.items()}
        self._pressed_virtual_keys.clear()
        self._active_actions.clear()
        self._suppressed_virtual_keys.clear()
        self.listener = keyboard.Listener(win32_event_filter=self._win32_event_filter)
        self.listener.start()
        for action, hotkey_text in self.hotkeys.items():
            self.log(f"Registered low-level hotkey: {hotkey_text} -> {action}")

    def stop(self):
        if self.listener:
            self.listener.stop()
            self.listener = None
        self._pressed_virtual_keys.clear()
        self._active_actions.clear()
        self._suppressed_virtual_keys.clear()

    def _refresh_active_state(self):
        active_actions = {
            action
            for action, combo_virtual_keys in self._combo_virtual_keys.items()
            if combo_virtual_keys and combo_virtual_keys.issubset(self._pressed_virtual_keys)
        }
        new_actions = active_actions - self._active_actions
        self._active_actions = active_actions
        suppressed_virtual_keys: set[int] = set()
        for action in self._active_actions:
            suppressed_virtual_keys.update(self._combo_virtual_keys.get(action, set()))
        self._suppressed_virtual_keys = suppressed_virtual_keys
        return new_actions

    def _win32_event_filter(self, msg, data):
        if not self.listener:
            return True
        virtual_key = normalize_virtual_key(int(getattr(data, "vkCode", 0)))

        if msg in {WM_KEYDOWN, WM_SYSKEYDOWN}:
            self._pressed_virtual_keys.add(virtual_key)
            new_actions = self._refresh_active_state()
            for action in new_actions:
                self.callback(action)
            if virtual_key in self._suppressed_virtual_keys:
                self.listener.suppress_event()
        elif msg in {WM_KEYUP, WM_SYSKEYUP}:
            should_suppress = virtual_key in self._suppressed_virtual_keys
            self._pressed_virtual_keys.discard(virtual_key)
            self._refresh_active_state()
            if should_suppress:
                self.listener.suppress_event()
        return True
