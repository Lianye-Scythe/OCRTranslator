from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout


class PromptInputDialog(QDialog):
    def __init__(self, app_window, preset_name: str, target_language: str):
        super().__init__(app_window if app_window.isVisible() else None)
        self.app_window = app_window
        self.preset_name = preset_name
        self.target_language = target_language
        self.last_anchor_point = None
        self._build_ui()

    def _build_ui(self):
        self.setModal(True)
        self.setWindowTitle(self.app_window.tr("manual_input_title"))
        self.setMinimumSize(520, 360)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        title = QLabel(self.app_window.tr("manual_input_title"))
        title.setObjectName("SectionTitleLabel")
        layout.addWidget(title)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)

        self.preset_chip = QLabel(self.app_window.tr("meta_prompt", value=self.preset_name))
        self.preset_chip.setObjectName("InfoChip")
        self.target_chip = QLabel(self.app_window.tr("meta_target", value=self.target_language))
        self.target_chip.setObjectName("InfoChip")
        meta_row.addWidget(self.preset_chip)
        meta_row.addWidget(self.target_chip)
        meta_row.addStretch(1)
        layout.addLayout(meta_row)

        self.hint_label = QLabel(self.app_window.tr("manual_input_hint"))
        self.hint_label.setObjectName("HintLabel")
        self.hint_label.setWordWrap(True)
        layout.addWidget(self.hint_label)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText(self.app_window.tr("manual_input_placeholder"))
        self.text_edit.textChanged.connect(self._refresh_send_state)
        layout.addWidget(self.text_edit, 1)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        button_row.addStretch(1)
        self.cancel_button = self.app_window.create_button(self.reject, accent=False)
        self.send_button = self.app_window.create_button(self.accept, secondary=True)
        self.cancel_button.setText(self.app_window.tr("manual_input_cancel"))
        self.send_button.setText(self.app_window.tr("manual_input_send"))
        button_row.addWidget(self.cancel_button)
        button_row.addWidget(self.send_button)
        layout.addLayout(button_row)

        QShortcut(QKeySequence("Ctrl+Return"), self, self.accept)
        QShortcut(QKeySequence("Ctrl+Enter"), self, self.accept)
        self._refresh_send_state()

    def _refresh_send_state(self):
        self.send_button.setEnabled(bool(self.input_text()))

    def input_text(self) -> str:
        return self.text_edit.toPlainText().strip()

    def accept(self):
        if not self.input_text():
            self.app_window.set_status("manual_input_empty")
            self.text_edit.setFocus()
            return
        self.last_anchor_point = self.frameGeometry().center()
        super().accept()
