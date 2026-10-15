import threading

from PySide6.QtCore import QEvent, Qt

from ..hotkey_utils import hotkey_has_modifier as hotkey_has_modifier_rule
from ..models import AppConfig


class MainWindowHotkeysMixin:
    def hotkey_fields(self) -> dict[str, tuple]:
        fields = {}
        if hasattr(self, "hotkey_edit") and hasattr(self, "hotkey_record_button"):
            fields["capture"] = (self.hotkey_edit, self.hotkey_record_button)
        if hasattr(self, "selection_hotkey_edit") and hasattr(self, "selection_hotkey_record_button"):
            fields["selection"] = (self.selection_hotkey_edit, self.selection_hotkey_record_button)
        if hasattr(self, "input_hotkey_edit") and hasattr(self, "input_hotkey_record_button"):
            fields["input"] = (self.input_hotkey_edit, self.input_hotkey_record_button)
        return fields

    def hotkey_field_key_for_widget(self, widget) -> str | None:
        for key, (edit, _) in self.hotkey_fields().items():
            if widget is edit:
                return key
        return None

    def hotkey_inputs(self) -> dict[str, object]:
        fields = self.hotkey_fields()
        return {key: edit for key, (edit, _) in fields.items()}

    def hotkey_value_map(self) -> dict[str, str]:
        values = {}
        for key, edit in self.hotkey_inputs().items():
            values[key] = edit.text().strip()
        return values

    def runtime_hotkey_actions_from_form(self) -> dict[str, str]:
        return self.build_hotkey_actions(
            config=AppConfig(
                hotkey=self.hotkey_edit.text().strip(), selection_hotkey=self.selection_hotkey_edit.text().strip(), input_hotkey=self.input_hotkey_edit.text().strip()
            )
        )

    def hotkey_field_label(self, field_key: str) -> str:
        label_map = {
            "capture": self.tr("capture_hotkey"),
            "selection": self.tr("selection_hotkey"),
            "input": self.tr("input_hotkey"),
        }
        return label_map.get(field_key, self.tr("hotkey"))

    def hotkey_has_modifier(self, hotkey_text: str) -> bool:
        return hotkey_has_modifier_rule(hotkey_text)

    @staticmethod
    def _mark_external_listener_daemon(listener) -> None:
        if listener is None:
            return
        try:
            listener.daemon = True
        except Exception:  # noqa: BLE001
            pass

    @staticmethod
    def _stop_external_listener_best_effort(listener, *, thread_name: str) -> None:
        if listener is None:
            return

        def request_stop():
            try:
                listener.stop()
            except Exception:  # noqa: BLE001
                return
            try:
                join = getattr(listener, "join", None)
                if callable(join) and listener is not threading.current_thread():
                    join(0.25)
            except Exception:  # noqa: BLE001
                pass

        threading.Thread(target=request_stop, name=thread_name, daemon=True).start()

    def start_hotkey_recording(self, field_key: str = "capture"):
        if getattr(self, "hotkey_record_target", None) == field_key:
            self.stop_hotkey_recording(cancelled=True)
            return
        self.stop_hotkey_recording(cancelled=False)
        field = self.hotkey_fields().get(field_key)
        if not field:
            return
        self.hotkey_record_target = field_key
        edit, button = field
        edit.setFocus()
        edit.selectAll()
        edit.setReadOnly(True)
        button.setText(self.tr("recording_hotkey"))
        if getattr(self, "hotkey_listener", None):
            self.hotkey_listener.stop()
            self.hotkey_listener = None
            self.hotkey_listener_paused_for_recording = True
        self._start_global_hotkey_recorder(field_key)
        self.set_status("hotkey_recording")
        self.validate_form_inputs()

    def stop_hotkey_recording(self, *, cancelled: bool = False, restore_hotkey_listener: bool = True):
        field_key = getattr(self, "hotkey_record_target", None)
        listener = getattr(self, "hotkey_record_listener", None)
        if listener:
            self._stop_external_listener_best_effort(listener, thread_name="HotkeyRecorderStop")
            self.hotkey_record_listener = None
        if not field_key:
            if restore_hotkey_listener and getattr(self, "hotkey_listener_paused_for_recording", False):
                self.hotkey_listener_paused_for_recording = False
                active_runtime_hotkeys = dict(getattr(self, "registered_hotkeys", {}))
                if active_runtime_hotkeys:
                    self.setup_hotkey_listener(initial=True, hotkey_actions=active_runtime_hotkeys)
                else:
                    self.setup_hotkey_listener(initial=True)
            else:
                self.hotkey_listener_paused_for_recording = False
            return
        self.hotkey_record_target = None
        field = self.hotkey_fields().get(field_key)
        if field:
            _, button = field
            field[0].setReadOnly(False)
            button.setText(self.tr("record_hotkey"))
        if restore_hotkey_listener and getattr(self, "hotkey_listener_paused_for_recording", False):
            self.hotkey_listener_paused_for_recording = False
            active_runtime_hotkeys = dict(getattr(self, "registered_hotkeys", {}))
            if active_runtime_hotkeys:
                self.setup_hotkey_listener(initial=True, hotkey_actions=active_runtime_hotkeys)
            else:
                self.setup_hotkey_listener(initial=True)
        else:
            self.hotkey_listener_paused_for_recording = False
        self.validate_form_inputs()
        if cancelled:
            self.set_status("hotkey_record_cancelled")

    @staticmethod
    def _normalize_recorded_key_token(key) -> str:
        from pynput import keyboard

        if key in {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}:
            return "Ctrl"
        if key in {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr}:
            return "Alt"
        if key in {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r}:
            return "Shift"
        if key in {keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r}:
            return "Win"

        special_keys = {
            keyboard.Key.enter: "Enter",
            keyboard.Key.tab: "Tab",
            keyboard.Key.space: "Space",
            keyboard.Key.backspace: "Backspace",
            keyboard.Key.delete: "Delete",
            keyboard.Key.insert: "Insert",
            keyboard.Key.home: "Home",
            keyboard.Key.end: "End",
            keyboard.Key.page_up: "PageUp",
            keyboard.Key.page_down: "PageDown",
            keyboard.Key.left: "Left",
            keyboard.Key.right: "Right",
            keyboard.Key.up: "Up",
            keyboard.Key.down: "Down",
            keyboard.Key.esc: "Esc",
        }
        if key in special_keys:
            return special_keys[key]

        if isinstance(key, keyboard.KeyCode):
            char = (key.char or "").strip()
            if char:
                return char.upper()
        name = getattr(key, "name", "") or ""
        if name.startswith("f") and name[1:].isdigit():
            return name.upper()
        if len(name) == 1 and name.isalnum():
            return name.upper()
        return ""

    @staticmethod
    def _format_recorded_hotkey(modifiers: set[str], key_token: str) -> str:
        ordered_modifiers = [token for token in ("Ctrl", "Alt", "Shift", "Win") if token in modifiers]
        parts = ordered_modifiers.copy()
        if key_token and key_token not in parts:
            parts.append(key_token)
        return "+".join(parts)

    def _start_global_hotkey_recorder(self, field_key: str):
        from pynput import keyboard

        modifier_tokens = {"Ctrl", "Alt", "Shift", "Win"}
        pressed_modifiers: set[str] = set()
        pressed_modifier_order: list[str] = []
        recorded = False

        def on_press(key):
            nonlocal recorded
            token = self._normalize_recorded_key_token(key)
            if not token:
                return
            if token == "Esc":
                recorded = True
                self.bridge.hotkey_recorded.emit(field_key, "")
                return False
            if token in modifier_tokens:
                pressed_modifiers.add(token)
                if token not in pressed_modifier_order:
                    pressed_modifier_order.append(token)
                return
            ordered_modifiers = [token for token in pressed_modifier_order if token in pressed_modifiers]
            hotkey_text = self._format_recorded_hotkey(set(ordered_modifiers), token)
            if hotkey_text:
                recorded = True
                self.bridge.hotkey_recorded.emit(field_key, hotkey_text)
                return False

        def on_release(key):
            nonlocal recorded
            token = self._normalize_recorded_key_token(key)
            if token in modifier_tokens:
                pressed_modifiers.discard(token)
            if recorded:
                return False

        self.hotkey_record_listener = keyboard.Listener(on_press=on_press, on_release=on_release, suppress=True)
        self._mark_external_listener_daemon(self.hotkey_record_listener)
        self.hotkey_record_listener.start()

    def handle_recorded_hotkey(self, field_key: str, hotkey_text: str):
        if getattr(self, "hotkey_record_target", None) != field_key:
            return
        if not hotkey_text:
            self.stop_hotkey_recording(cancelled=True)
            return
        field = self.hotkey_fields().get(field_key)
        if not field:
            self.stop_hotkey_recording(cancelled=True)
            return
        widget, _ = field
        widget.setText(hotkey_text)
        self.stop_hotkey_recording(cancelled=False)
        valid, first_error = self.validate_form_inputs(scope="hotkeys")
        if not valid:
            self.set_status("hotkey_register_failed", error=first_error)
            self.log_error(f"Recorded hotkey kept in form but not applied: {first_error}")
            return
        try:
            self.setup_hotkey_listener(initial=True, hotkey_actions=self.runtime_hotkey_actions_from_form(), raise_on_error=True)
        except Exception as exc:  # noqa: BLE001
            self.set_status("hotkey_register_failed", error=exc)
            self.log_error(f"Recorded hotkey kept in form but runtime apply failed: {exc}")
            return
        self.set_status("hotkeys_registered_pending_save")
        self.log(
            "Hotkeys applied from current form; save settings to persist them | "
            f"capture={self.hotkey_edit.text().strip()} | selection={self.selection_hotkey_edit.text().strip()} | input={self.input_hotkey_edit.text().strip()}"
        )

    def eventFilter(self, watched, event):
        field_key = self.hotkey_field_key_for_widget(watched)
        if field_key and getattr(self, "hotkey_record_target", None) == field_key:
            if event.type() == QEvent.Type.KeyPress:
                if event.key() == Qt.Key_Escape:
                    self.stop_hotkey_recording(cancelled=True)
                return True
            if event.type() in {QEvent.Type.ShortcutOverride, QEvent.Type.KeyRelease}:
                return True
        return super().eventFilter(watched, event)
