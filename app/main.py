import base64
import hashlib
import io
import json
import sys
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image, ImageGrab
from pynput import keyboard
from PySide6.QtCore import QObject, QPoint, QRect, QSize, Qt, Signal, QEvent, QLockFile
from PySide6.QtGui import QAction, QColor, QFont, QGuiApplication, QIcon, QMouseEvent, QPainter, QPen, QPixmap, QTextDocument
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFontComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QRubberBand,
    QSpinBox,
    QSystemTrayIcon,
    QTabWidget,
    QTextEdit,
    QDoubleSpinBox,
    QVBoxLayout,
    QWidget,
)


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
CONFIG_PATH = BASE_DIR / "config.json"
DEFAULT_MODEL = "models/gemini-3.1-flash-lite-preview"
DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com"
APP_LOCK_PATH = str(BASE_DIR / ".ocrtranslator.lock")
APP_SERVER_NAME = f"ocrtranslator-{hashlib.md5(str(BASE_DIR).encode('utf-8')).hexdigest()}"
MODEL_PREFIX = "models/"
PROVIDER_LABELS = {
    "gemini": {"zh-TW": "Gemini 相容", "en": "Gemini Compatible"},
    "openai": {"zh-TW": "OpenAI 相容", "en": "OpenAI Compatible"},
}
DEFAULT_PROMPT = (
    "You will receive a screenshot that mainly contains Japanese novel, light novel, or web text. "
    "Please do the following directly:\n"
    "1. Recognize the text in the image;\n"
    "2. Translate it into the specified target language;\n"
    "3. Preserve paragraph order and reading order as much as possible;\n"
    "4. Do not explain, do not add preface, and do not output the original text;\n"
    "5. If some text is unclear, translate as much as possible based on visible content and mark it as partially unclear;\n"
    "6. Output clean translated text suitable for direct reading."
)

I18N = {
    "zh-TW": {
        "window_title": "OCR 翻譯器",
        "title": "日文閱讀 OCR 翻譯工具",
        "subtitle": "為輕小說、網文與漫畫對話框打造的桌面 OCR 翻譯工作台",
        "quick_actions": "快速操作",
        "api_keys_hidden": "API Keys（已隱藏）",
        "show_api_keys": "顯示 Key",
        "hide_api_keys": "隱藏 Key",
        "api_keys_mask_hint": "API Key 預設遮罩顯示；按右側按鈕可切換顯示後再編輯。",
        "tab_settings": "設定",
        "tab_monitor": "預覽與 Log",
        "section_profiles": "設定檔管理",
        "section_api": "API 連線設定",
        "section_reading": "閱讀與翻譯設定",
        "section_preview_logs": "預覽與即時 Log",
        "profile": "API 設定檔",
        "new_profile": "新增設定檔",
        "delete_profile": "刪除設定檔",
        "profile_name": "設定檔名稱",
        "provider": "相容格式",
        "base_url": "Base URL",
        "api_keys": "API Keys",
        "api_keys_hint": "每行一個 Key，同一個 URL 會自動輪循。",
        "model": "模型",
        "fetch_models": "獲取模型列表",
        "test_api": "測試 API",
        "target_language": "目標語言",
        "ui_language": "介面語言",
        "display_mode": "顯示模式",
        "hotkey": "全域快捷鍵",
        "overlay_font_family": "翻譯字型",
        "overlay_font_size": "翻譯字級",
        "retry_count": "重試次數",
        "retry_interval": "重試間隔(秒)",
        "save_settings": "儲存設定",
        "start_capture": "開始框選截圖",
        "minimize_to_tray": "最小化到系統匣",
        "mode_book_lr": "雙頁左右(book_lr)",
        "mode_web_ud": "網頁上下(web_ud)",
        "hint": "提示：X 會直接退出程式；只有按「最小化到系統匣」才會進入系統匣。",
        "ready": "準備就緒",
        "settings_saved": "設定已儲存",
        "capturing": "截圖完成，正在請求模型翻譯...",
        "translated": "翻譯完成",
        "translate_failed": "翻譯失敗",
        "overlay_title": "翻譯結果",
        "empty_result": "模型沒有回傳可顯示的內容。",
        "tray_title": "OCR 翻譯器",
        "tray_show": "顯示主視窗",
        "tray_capture": "開始截圖",
        "tray_quit": "退出",
        "tray_minimized": "已最小化到系統匣。",
        "tray_capturing": "已截圖，正在翻譯中...",
        "error_title": "錯誤",
        "hotkey_registered": "快捷鍵已更新：{hotkey}",
        "hotkey_register_failed": "快捷鍵註冊失敗：{error}",
        "language_saved": "語言已切換並儲存",
        "logs": "即時 Log（最近 100 條，不落地保存）",
        "test_success": "API 測試成功。",
        "models_loaded": "已獲取 {count} 個模型。",
        "profile_deleted": "已刪除設定檔：{name}",
        "confirm_delete_profile": "確定要刪除設定檔「{name}」嗎？",
        "at_least_one_profile": "至少要保留一個設定檔。",
        "capture_cancelled": "已取消截圖。",
        "font_zoomed": "翻譯字級已調整為 {size}",
        "already_running_title": "程式已在執行",
        "already_running_message": "OCR 翻譯器已在執行中。\n\n請先檢查系統匣，或關閉既有視窗後再重試。",
    },
    "en": {
        "window_title": "OCR Translator",
        "title": "Japanese Reading OCR Translator",
        "subtitle": "A desktop OCR translation workspace for light novels, web novels, and dialogue-heavy reading",
        "quick_actions": "Quick Actions",
        "api_keys_hidden": "API Keys (Hidden)",
        "show_api_keys": "Show Keys",
        "hide_api_keys": "Hide Keys",
        "api_keys_mask_hint": "API keys are masked by default. Click the button on the right to reveal and edit them.",
        "tab_settings": "Settings",
        "tab_monitor": "Preview & Log",
        "section_profiles": "Profile Management",
        "section_api": "API Connection Settings",
        "section_reading": "Reading & Translation Settings",
        "section_preview_logs": "Preview & Runtime Log",
        "profile": "API Profile",
        "new_profile": "New Profile",
        "delete_profile": "Delete Profile",
        "profile_name": "Profile Name",
        "provider": "Compatibility",
        "base_url": "Base URL",
        "api_keys": "API Keys",
        "api_keys_hint": "One key per line. Keys under the same URL will rotate automatically.",
        "model": "Model",
        "fetch_models": "Fetch Models",
        "test_api": "Test API",
        "target_language": "Target Language",
        "ui_language": "UI Language",
        "display_mode": "Display Mode",
        "hotkey": "Global Hotkey",
        "overlay_font_family": "Translation Font",
        "overlay_font_size": "Translation Font Size",
        "retry_count": "Retry Count",
        "retry_interval": "Retry Interval (s)",
        "save_settings": "Save Settings",
        "start_capture": "Start Screen Capture",
        "minimize_to_tray": "Minimize to Tray",
        "mode_book_lr": "Dual-page Left/Right (book_lr)",
        "mode_web_ud": "Top/Bottom Web (web_ud)",
        "hint": "Tip: clicking X exits the app directly. Only the tray button minimizes it to the system tray.",
        "ready": "Ready",
        "settings_saved": "Settings saved",
        "capturing": "Screenshot captured, requesting translation...",
        "translated": "Translation completed",
        "translate_failed": "Translation failed",
        "overlay_title": "Translation",
        "empty_result": "The model returned no displayable content.",
        "tray_title": "OCR Translator",
        "tray_show": "Show Window",
        "tray_capture": "Capture Screen",
        "tray_quit": "Quit",
        "tray_minimized": "Minimized to system tray.",
        "tray_capturing": "Screenshot captured. Translating...",
        "error_title": "Error",
        "hotkey_registered": "Hotkey updated: {hotkey}",
        "hotkey_register_failed": "Hotkey registration failed: {error}",
        "language_saved": "Language switched and saved",
        "logs": "Runtime Log (latest 100 entries, memory only)",
        "test_success": "API test succeeded.",
        "models_loaded": "Loaded {count} models.",
        "profile_deleted": "Deleted profile: {name}",
        "confirm_delete_profile": "Delete profile '{name}'?",
        "at_least_one_profile": "At least one profile must remain.",
        "capture_cancelled": "Capture cancelled.",
        "font_zoomed": "Translation font size changed to {size}",
        "already_running_title": "Already Running",
        "already_running_message": "OCR Translator is already running.\n\nPlease check the system tray or close the existing window before launching again.",
    },
}


@dataclass
class ApiProfile:
    name: str = "Default Gemini"
    provider: str = "gemini"
    base_url: str = DEFAULT_BASE_URL
    api_keys: list[str] = field(default_factory=list)
    model: str = DEFAULT_MODEL
    available_models: list[str] = field(default_factory=lambda: [DEFAULT_MODEL])
    retry_count: int = 1
    retry_interval: float = 2.0


@dataclass
class AppConfig:
    target_language: str = "繁體中文"
    mode: str = "book_lr"
    temperature: float = 0.2
    overlay_width: int = 440
    overlay_height: int = 520
    margin: int = 18
    ui_language: str = "zh-TW"
    hotkey: str = "Shift+Win+A"
    overlay_font_family: str = "Microsoft JhengHei UI"
    overlay_font_size: int = 12
    active_profile_name: str = "Default Gemini"
    api_profiles: list[ApiProfile] = field(default_factory=lambda: [ApiProfile()])


class ApiClient:
    def __init__(self, log_func):
        self.log = log_func
        self.profile_key_index: dict[str, int] = {}

    @staticmethod
    def _image_to_base64(image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    @staticmethod
    def _normalize_base(base_url: str) -> str:
        return (base_url or "").rstrip("/")

    def _openai_url(self, base_url: str, path: str) -> str:
        base = self._normalize_base(base_url)
        if base.endswith("/v1"):
            return f"{base}{path}"
        return f"{base}/v1{path}"

    def _gemini_content_url(self, profile: ApiProfile, api_key: str) -> str:
        base = self._normalize_base(profile.base_url)
        if base.endswith("/v1beta"):
            return f"{base}/{quote(profile.model, safe='/:.-_')}:generateContent?key={api_key}"
        return f"{base}/v1beta/{quote(profile.model, safe='/:.-_')}:generateContent?key={api_key}"

    def _gemini_models_url(self, base_url: str, api_key: str) -> str:
        base = self._normalize_base(base_url)
        if base.endswith("/v1beta"):
            return f"{base}/models?key={api_key}"
        return f"{base}/v1beta/models?key={api_key}"

    def _request_openai_models(self, profile: ApiProfile, api_key: str) -> list[str]:
        response = requests.get(self._openai_url(profile.base_url, "/models"), headers={"Authorization": f"Bearer {api_key}"}, timeout=30)
        response.raise_for_status()
        return [item.get("id", "") for item in response.json().get("data", []) if item.get("id")]

    def _request_gemini_models(self, profile: ApiProfile, api_key: str) -> list[str]:
        response = requests.get(self._gemini_models_url(profile.base_url, api_key), timeout=30)
        response.raise_for_status()
        return [item.get("name", "") for item in response.json().get("models", []) if item.get("name")]

    def list_models(self, profile: ApiProfile) -> list[str]:
        keys = [key.strip() for key in profile.api_keys if key.strip()]
        if not keys:
            raise RuntimeError("No API key configured")
        last_error = None
        for key in keys:
            try:
                return self._request_openai_models(profile, key) if profile.provider == "openai" else self._request_gemini_models(profile, key)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                self.log(f"List models failed with one key: {exc}")
        raise RuntimeError(str(last_error) if last_error else "Failed to load models")

    def test_profile(self, profile: ApiProfile) -> str:
        models = self.list_models(profile)
        preview = ", ".join(models[:5]) if models else "(no models)"
        return f"OK | provider={profile.provider} | models={len(models)} | {preview}"

    def translate_image(self, image: Image.Image, profile: ApiProfile, target_language: str, temperature: float) -> str:
        keys = [key.strip() for key in profile.api_keys if key.strip()]
        if not keys:
            raise RuntimeError("No API key configured")
        prompt = f"{DEFAULT_PROMPT}\n\nTarget language: {target_language}"
        image_base64 = self._image_to_base64(image)
        attempts_total = max(1, profile.retry_count + 1) * len(keys)
        profile_key = f"{profile.provider}|{profile.base_url}|{profile.name}"
        start_index = self.profile_key_index.get(profile_key, 0) % len(keys)
        last_error = None

        for attempt in range(attempts_total):
            key_index = (start_index + attempt) % len(keys)
            api_key = keys[key_index]
            self.profile_key_index[profile_key] = (key_index + 1) % len(keys)
            try:
                self.log(f"Translate attempt {attempt + 1}/{attempts_total} | provider={profile.provider} | model={profile.model} | key#{key_index + 1}")
                if profile.provider == "openai":
                    result = self._translate_openai(profile, api_key, prompt, image_base64, temperature)
                else:
                    result = self._translate_gemini(profile, api_key, prompt, image_base64, temperature)
                if result:
                    return result.strip()
                raise RuntimeError("Empty response")
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                self.log(f"Translate failed on attempt {attempt + 1}: {exc}")
                if attempt < attempts_total - 1 and profile.retry_interval > 0:
                    time.sleep(profile.retry_interval)
        raise RuntimeError(str(last_error) if last_error else "Translation failed")

    def _translate_openai(self, profile: ApiProfile, api_key: str, prompt: str, image_base64: str, temperature: float) -> str:
        response = requests.post(
            self._openai_url(profile.base_url, "/chat/completions"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": profile.model,
                "temperature": temperature,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                    ],
                }],
            },
            timeout=120,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        if isinstance(content, list):
            return "\n".join(item.get("text", "") for item in content if isinstance(item, dict))
        return content

    def _translate_gemini(self, profile: ApiProfile, api_key: str, prompt: str, image_base64: str, temperature: float) -> str:
        response = requests.post(
            self._gemini_content_url(profile, api_key),
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "image/png", "data": image_base64}}]}],
                "generationConfig": {"temperature": temperature},
            },
            timeout=120,
        )
        response.raise_for_status()
        candidates = response.json().get("candidates", [])
        if not candidates:
            return ""
        return "\n".join(part.get("text", "") for part in candidates[0].get("content", {}).get("parts", []) if part.get("text"))


class WorkerThread(threading.Thread):
    def __init__(self, target, bridge, on_success):
        super().__init__(daemon=True)
        self._target = target
        self._bridge = bridge
        self._on_success = on_success

    def run(self):
        try:
            result = self._target()
            self._bridge.worker_success.emit(self._on_success, result)
        except Exception as exc:  # noqa: BLE001
            self._bridge.worker_error.emit(exc)


class AppBridge(QObject):
    hotkey_triggered = Signal()
    worker_success = Signal(object, object)
    worker_error = Signal(object)


class SelectionOverlay(QWidget):
    selected = Signal(tuple)
    cancelled = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
        self.virtual_rect = QGuiApplication.primaryScreen().virtualGeometry()
        self.setGeometry(self.virtual_rect)

    def show_overlay(self):
        self.setGeometry(QGuiApplication.primaryScreen().virtualGeometry())
        self.rubber_band.hide()
        self.showFullScreen()
        self.activateWindow()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.RightButton:
            self.hide()
            self.cancelled.emit()
            return
        if event.button() == Qt.LeftButton:
            self.origin = event.globalPosition().toPoint()
            self.rubber_band.setGeometry(QRect(self.origin - self.pos(), QSize()))
            self.rubber_band.show()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.rubber_band.isVisible():
            return
        current = event.globalPosition().toPoint()
        rect = QRect(self.origin, current).normalized()
        self.rubber_band.setGeometry(QRect(rect.topLeft() - self.pos(), rect.size()))

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() != Qt.LeftButton or not self.rubber_band.isVisible():
            return
        current = event.globalPosition().toPoint()
        rect = QRect(self.origin, current).normalized()
        self.rubber_band.hide()
        self.hide()
        if rect.width() < 20 or rect.height() < 20:
            self.cancelled.emit()
            return
        self.selected.emit((rect.left(), rect.top(), rect.right(), rect.bottom()))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
            self.cancelled.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))
        painter.setPen(QPen(QColor(77, 163, 255), 2))


class TranslationOverlay(QWidget):
    request_font_zoom = Signal(int)

    def __init__(self, app_window):
        super().__init__()
        self.app_window = app_window
        self.last_bbox = None
        self.last_text = ""
        self._drag_offset = QPoint()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.card = QFrame()
        self.card.setObjectName("overlayCard")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(42)
        shadow.setOffset(0, 18)
        shadow.setColor(QColor(3, 7, 18, 180))
        self.card.setGraphicsEffect(shadow)
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        self.header = QFrame()
        self.header.setObjectName("overlayHeader")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(14, 8, 8, 8)
        self.title_label = QLabel()
        self.close_button = QPushButton("×")
        self.close_button.setFixedWidth(30)
        self.close_button.clicked.connect(self.hide)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.close_button)

        self.body = QTextEdit()
        self.body.setReadOnly(True)
        self.body.setObjectName("overlayBody")
        self.body.viewport().installEventFilter(self)
        self.body.installEventFilter(self)

        card_layout.addWidget(self.header)
        card_layout.addWidget(self.body)
        outer.addWidget(self.card)
        self.apply_styles()
        self.refresh_language()

    def apply_styles(self):
        self.setStyleSheet(
            """
            #overlayCard {background:#111827; border:1px solid #334155; border-radius:18px;}
            #overlayHeader {background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #1d4ed8, stop:1 #0f172a); border-top-left-radius:18px; border-top-right-radius:18px;}
            #overlayBody {background:#111827; color:#f8fafc; border:none; padding:10px; border-bottom-left-radius:18px; border-bottom-right-radius:18px;}
            QPushButton {background:transparent; color:white; border:none; font-size:18px;}
            QPushButton:hover {background:rgba(255,255,255,0.12); border-radius:10px;}
            QLabel {color:white; font-weight:700; font-size:14px;}
            """
        )

    def refresh_language(self):
        self.title_label.setText(self.app_window.tr("overlay_title"))
        self.apply_typography()

    def apply_typography(self):
        self.body.setFont(QFont(self.app_window.config.overlay_font_family, self.app_window.config.overlay_font_size))

    def calculate_size(self, text: str):
        lines = [line for line in text.splitlines() if line.strip()] or [text]
        longest = max((len(line) for line in lines), default=18)
        font_size = max(10, self.app_window.config.overlay_font_size)
        width = max(380, min(860, int(longest * font_size * 0.8) + 140))
        height = max(240, min(900, int((len(lines) + 2) * font_size * 2.0) + 100))
        return width, height

    def measure_content_height(self, text: str, width: int) -> int:
        doc = QTextDocument()
        doc.setDefaultFont(self.body.font())
        doc.setPlainText(text)
        text_width = max(220, width - 40)
        doc.setTextWidth(text_width)
        header_height = 48
        body_padding = 42
        return int(doc.size().height()) + header_height + body_padding

    def remember_context(self, bbox, text: str):
        self.last_bbox = bbox
        self.last_text = text

    def show_text(self, text: str, x: int, y: int, width: int, height: int):
        self.setGeometry(x, y, width, height)
        self.body.setPlainText(text)
        self.last_text = text
        self.show()
        self.raise_()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Wheel and QApplication.keyboardModifiers() & Qt.ControlModifier:
            direction = 1 if event.angleDelta().y() > 0 else -1
            self.request_font_zoom.emit(direction)
            return True
        return super().eventFilter(watched, event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.bridge = AppBridge()
        self.bridge.hotkey_triggered.connect(self.start_selection)
        self.bridge.worker_success.connect(self._handle_worker_success)
        self.bridge.worker_error.connect(self.handle_error)

        self.config = load_config()
        self.logs = deque(maxlen=100)
        self.api_client = ApiClient(self.log)
        self.hotkey_listener = None
        self.preview_pixmap = None
        self.current_status_key = "ready"
        self.current_status_kwargs = {}
        self.is_quitting = False
        self.icon = self.create_app_icon()

        self.selection_overlay = SelectionOverlay()
        self.selection_overlay.selected.connect(self.handle_selection)
        self.selection_overlay.cancelled.connect(self.handle_capture_cancelled)

        self.translation_overlay = TranslationOverlay(self)
        self.translation_overlay.request_font_zoom.connect(self.adjust_overlay_font_size)

        self.build_ui()
        self.setup_tray()
        self.apply_styles()
        self.apply_language()
        self.load_profile_to_form(self.config.active_profile_name)
        self.setup_instance_server()
        self.setup_hotkey_listener(initial=True)
        self.log("Application started")

    def tr(self, key: str, **kwargs) -> str:
        lang = self.config.ui_language if self.config.ui_language in I18N else "zh-TW"
        text = I18N[lang].get(key, key)
        return text.format(**kwargs) if kwargs else text

    def build_ui(self):
        self.setWindowTitle(self.tr("window_title"))
        self.setWindowIcon(self.icon)
        self.resize(1100, 860)

        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(20, 18, 20, 16)
        root_layout.setSpacing(14)

        self.hero_card = QFrame()
        self.hero_card.setObjectName("HeroCard")
        self.add_shadow(self.hero_card, blur=44, y_offset=16, alpha=120)
        hero_layout = QHBoxLayout(self.hero_card)
        hero_layout.setContentsMargins(22, 20, 22, 20)
        hero_layout.setSpacing(18)

        hero_text_layout = QVBoxLayout()
        hero_text_layout.setSpacing(6)
        self.title_label = QLabel()
        self.title_label.setObjectName("TitleLabel")
        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("SubtitleLabel")
        self.subtitle_label.setWordWrap(True)
        hero_text_layout.addWidget(self.title_label)
        hero_text_layout.addWidget(self.subtitle_label)
        hero_layout.addLayout(hero_text_layout, 1)

        hero_actions = QVBoxLayout()
        hero_actions.setSpacing(10)
        self.quick_actions_label = QLabel()
        self.quick_actions_label.setObjectName("SectionEyebrow")
        quick_row = QHBoxLayout()
        quick_row.setSpacing(10)
        self.hero_capture_button = self.create_button(self.start_selection, success=True)
        self.hero_tray_button = self.create_button(self.minimize_to_tray, accent=False)
        quick_row.addWidget(self.hero_capture_button)
        quick_row.addWidget(self.hero_tray_button)
        hero_actions.addWidget(self.quick_actions_label, alignment=Qt.AlignRight)
        hero_actions.addLayout(quick_row)
        hero_layout.addLayout(hero_actions)
        root_layout.addWidget(self.hero_card)

        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        root_layout.addWidget(self.tab_widget, 1)

        self.settings_tab = QWidget()
        self.monitor_tab = QWidget()
        self.tab_widget.addTab(self.settings_tab, "")
        self.tab_widget.addTab(self.monitor_tab, "")

        self._build_settings_tab()
        self._build_monitor_tab()

        self.status_label = QLabel()
        self.status_label.setObjectName("StatusLabel")
        root_layout.addWidget(self.status_label)

    def _build_settings_tab(self):
        layout = QVBoxLayout(self.settings_tab)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)

        columns = QHBoxLayout()
        columns.setSpacing(14)
        layout.addLayout(columns, 1)

        left_column = QVBoxLayout()
        left_column.setSpacing(12)
        right_column = QVBoxLayout()
        right_column.setSpacing(12)
        columns.addLayout(left_column, 3)
        columns.addLayout(right_column, 2)

        self.profile_group = QGroupBox()
        self.add_shadow(self.profile_group)
        left_column.addWidget(self.profile_group)
        profile_layout = QHBoxLayout(self.profile_group)
        profile_layout.setSpacing(10)
        self.profile_selector_label = QLabel()
        self.profile_combo = QComboBox()
        self.profile_combo.currentTextChanged.connect(self.on_profile_selected)
        self.new_profile_button = self.create_button(self.create_new_profile, accent=False)
        self.delete_profile_button = self.create_button(self.delete_current_profile, accent=False, danger=True)
        profile_layout.addWidget(self.profile_selector_label)
        profile_layout.addWidget(self.profile_combo, 1)
        profile_layout.addWidget(self.new_profile_button)
        profile_layout.addWidget(self.delete_profile_button)

        self.api_group = QGroupBox()
        self.add_shadow(self.api_group)
        left_column.addWidget(self.api_group)
        api_grid = QGridLayout(self.api_group)
        api_grid.setHorizontalSpacing(14)
        api_grid.setVerticalSpacing(10)

        self.profile_name_label = QLabel()
        self.profile_name_edit = QLineEdit()
        self.provider_label = QLabel()
        self.provider_combo = QComboBox()
        self.provider_combo.currentTextChanged.connect(self.on_provider_selected)
        self.base_url_label = QLabel()
        self.base_url_edit = QLineEdit()
        self.model_label = QLabel()
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.retry_count_label = QLabel()
        self.retry_count_spin = QSpinBox()
        self.retry_count_spin.setRange(0, 10)
        self.retry_interval_label = QLabel()
        self.retry_interval_spin = QDoubleSpinBox()
        self.retry_interval_spin.setRange(0, 60)
        self.retry_interval_spin.setSingleStep(0.5)

        self.api_keys_label = QLabel()
        self.api_keys_toolbar = QHBoxLayout()
        self.api_keys_toolbar.setSpacing(8)
        self.api_keys_label_row = QLabel()
        self.api_keys_toggle_button = self.create_button(self.toggle_api_keys_visibility, accent=False)
        self.api_keys_toggle_button.setFixedWidth(110)
        self.api_keys_label_row.setObjectName("SectionEyebrow")
        self.api_keys_toolbar.addWidget(self.api_keys_label_row)
        self.api_keys_toolbar.addStretch(1)
        self.api_keys_toolbar.addWidget(self.api_keys_toggle_button)
        self.api_keys_edit = QPlainTextEdit()
        self.api_keys_edit.setFixedHeight(108)
        self.api_keys_edit.textChanged.connect(self.on_api_keys_text_changed)
        self.api_keys_hint = QLabel()
        self.api_keys_hint.setObjectName("HintLabel")
        self.api_keys_visible = False

        api_grid.addWidget(self.profile_name_label, 0, 0)
        api_grid.addWidget(self.profile_name_edit, 0, 1)
        api_grid.addWidget(self.provider_label, 1, 0)
        api_grid.addWidget(self.provider_combo, 1, 1)
        api_grid.addWidget(self.base_url_label, 2, 0)
        api_grid.addWidget(self.base_url_edit, 2, 1)
        api_grid.addWidget(self.model_label, 3, 0)
        api_grid.addWidget(self.model_combo, 3, 1)
        api_grid.addWidget(self.retry_count_label, 4, 0)
        api_grid.addWidget(self.retry_count_spin, 4, 1)
        api_grid.addWidget(self.retry_interval_label, 5, 0)
        api_grid.addWidget(self.retry_interval_spin, 5, 1)
        api_grid.addWidget(self.api_keys_label, 6, 0, alignment=Qt.AlignTop)
        api_grid.addLayout(self.api_keys_toolbar, 6, 1)
        api_grid.addWidget(self.api_keys_edit, 7, 1)
        api_grid.addWidget(self.api_keys_hint, 8, 1)

        self.reading_group = QGroupBox()
        self.add_shadow(self.reading_group)
        right_column.addWidget(self.reading_group)
        reading_grid = QGridLayout(self.reading_group)
        reading_grid.setHorizontalSpacing(14)
        reading_grid.setVerticalSpacing(10)

        self.target_language_label = QLabel()
        self.target_language_edit = QLineEdit(self.config.target_language)
        self.ui_language_label = QLabel()
        self.ui_language_combo = QComboBox()
        self.ui_language_combo.addItems(["zh-TW", "en"])
        self.ui_language_combo.currentTextChanged.connect(self.on_ui_language_changed)
        self.hotkey_label = QLabel()
        self.hotkey_edit = QLineEdit(self.config.hotkey)
        self.overlay_font_label = QLabel()
        self.overlay_font_combo = QFontComboBox()
        self.overlay_font_combo.setCurrentFont(QFont(self.config.overlay_font_family))
        self.overlay_font_size_label = QLabel()
        self.overlay_font_size_spin = QSpinBox()
        self.overlay_font_size_spin.setRange(10, 32)
        self.overlay_font_size_spin.setValue(self.config.overlay_font_size)
        self.mode_label = QLabel()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["book_lr", "web_ud"])

        reading_grid.addWidget(self.target_language_label, 0, 0)
        reading_grid.addWidget(self.target_language_edit, 0, 1)
        reading_grid.addWidget(self.ui_language_label, 1, 0)
        reading_grid.addWidget(self.ui_language_combo, 1, 1)
        reading_grid.addWidget(self.hotkey_label, 2, 0)
        reading_grid.addWidget(self.hotkey_edit, 2, 1)
        reading_grid.addWidget(self.overlay_font_label, 3, 0)
        reading_grid.addWidget(self.overlay_font_combo, 3, 1)
        reading_grid.addWidget(self.overlay_font_size_label, 4, 0)
        reading_grid.addWidget(self.overlay_font_size_spin, 4, 1)
        reading_grid.addWidget(self.mode_label, 5, 0)
        reading_grid.addWidget(self.mode_combo, 5, 1)

        self.quick_group = QGroupBox()
        self.add_shadow(self.quick_group)
        right_column.addWidget(self.quick_group)
        quick_group_layout = QVBoxLayout(self.quick_group)
        quick_group_layout.setSpacing(10)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        self.fetch_models_button = self.create_button(self.fetch_models)
        self.test_button = self.create_button(self.test_profile, secondary=True)
        self.save_button = self.create_button(self.save_settings)
        self.capture_button = self.create_button(self.start_selection, success=True)
        self.tray_button = self.create_button(self.minimize_to_tray, accent=False)
        for button in [self.fetch_models_button, self.test_button, self.save_button, self.capture_button, self.tray_button]:
            action_row.addWidget(button)
        quick_group_layout.addLayout(action_row)

        self.hint_label = QLabel()
        self.hint_label.setObjectName("HintLabel")
        self.hint_label.setWordWrap(True)
        quick_group_layout.addWidget(self.hint_label)
        right_column.addStretch(1)
        layout.addStretch(1)

    def _build_monitor_tab(self):
        layout = QVBoxLayout(self.monitor_tab)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        layout.addLayout(top_row, 1)

        self.preview_group = QGroupBox()
        self.add_shadow(self.preview_group)
        top_row.addWidget(self.preview_group, 3)
        preview_layout = QVBoxLayout(self.preview_group)
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(320)
        self.preview_label.setObjectName("PreviewLabel")
        preview_layout.addWidget(self.preview_label)

        self.log_group = QGroupBox()
        self.add_shadow(self.log_group)
        top_row.addWidget(self.log_group, 2)
        log_layout = QVBoxLayout(self.log_group)
        self.log_title_label = QLabel()
        self.log_title_label.setObjectName("SectionEyebrow")
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(320)
        log_layout.addWidget(self.log_title_label)
        log_layout.addWidget(self.log_text)

    def apply_styles(self):
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background:#07111f; color:#e5eefb; font-family:'Segoe UI Variable Text','Segoe UI','Microsoft JhengHei UI'; font-size:13px; }
            #HeroCard {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0f172a, stop:0.5 #111c34, stop:1 #0a1220);
                border:1px solid #24344d;
                border-radius:24px;
            }
            #TitleLabel { font-size:28px; font-weight:800; color:#f8fbff; }
            #SubtitleLabel { font-size:13px; color:#9db2ce; line-height:1.4; }
            #SectionEyebrow { color:#7dd3fc; font-size:12px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; }
            QTabWidget::pane { border:none; background:transparent; top:-4px; }
            QTabBar::tab { background:#122033; color:#b8c8de; padding:12px 20px; border-radius:14px; margin-right:10px; min-width:130px; }
            QTabBar::tab:hover { background:#17273d; }
            QTabBar::tab:selected { background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #3b82f6, stop:1 #2563eb); color:white; }
            QGroupBox {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0d1728, stop:1 #0b1423);
                border:1px solid #233247;
                border-radius:22px;
                margin-top:14px;
                font-weight:700;
                color:#dbeafe;
                padding:16px;
            }
            QGroupBox::title { subcontrol-origin: margin; left:16px; padding:0 8px; color:#dbeafe; }
            QLabel { color:#dbeafe; }
            #HintLabel { color:#91a4bd; }
            #StatusLabel {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0b1628, stop:1 #0f1d32);
                border:1px solid #24344d;
                border-radius:16px;
                padding:14px 16px;
                color:#b7f7cb;
                font-weight:600;
            }
            QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QFontComboBox, QSpinBox, QDoubleSpinBox {
                background:#081120;
                border:1px solid #2c3e56;
                border-radius:14px;
                padding:10px 12px;
                color:#f8fafc;
                selection-background-color:#2563eb;
            }
            QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus, QFontComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border:1px solid #7dd3fc;
                background:#0a1628;
            }
            QComboBox::drop-down, QFontComboBox::drop-down { border:none; width:28px; }
            QComboBox::down-arrow, QFontComboBox::down-arrow { image:none; }
            QPushButton { border:none; border-radius:16px; padding:11px 18px; font-weight:700; }
            QPushButton:hover { border:1px solid rgba(255,255,255,0.08); }
            #PreviewLabel {
                border:1px dashed #334155;
                border-radius:20px;
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #09111f, stop:1 #0d1728);
                color:#64748b;
            }
            QScrollBar:vertical { width:12px; background:transparent; }
            QScrollBar::handle:vertical { background:#334155; border-radius:6px; min-height:32px; }
            """
        )

    def create_button(self, callback, accent=True, secondary=False, success=False, danger=False):
        button = QPushButton()
        button.clicked.connect(callback)
        color = "#2563eb"
        hover = "#3b82f6"
        if secondary:
            color = "#0f766e"
            hover = "#0d9488"
        elif success:
            color = "#16a34a"
            hover = "#22c55e"
        elif danger:
            color = "#7f1d1d"
            hover = "#991b1b"
        elif not accent:
            color = "#334155"
            hover = "#475569"
        button.setStyleSheet(f"QPushButton {{ background:{color}; color:white; }} QPushButton:hover {{ background:{hover}; }}")
        return button

    def add_shadow(self, widget, blur=32, y_offset=10, alpha=90):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(blur)
        shadow.setOffset(0, y_offset)
        shadow.setColor(QColor(2, 6, 23, alpha))
        widget.setGraphicsEffect(shadow)

    def create_app_icon(self) -> QIcon:
        pix = QPixmap(64, 64)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#2563eb"))
        painter.drawRoundedRect(4, 4, 56, 56, 16, 16)
        painter.setBrush(QColor("#0f172a"))
        painter.drawRoundedRect(14, 10, 36, 44, 12, 12)
        painter.setPen(QPen(QColor("#c4b5fd"), 4))
        painter.drawLine(24, 20, 24, 44)
        painter.setPen(QPen(QColor("#34d399"), 4))
        painter.drawLine(24, 20, 38, 20)
        painter.setPen(QPen(QColor("#ffffff"), 3))
        painter.drawLine(24, 31, 44, 31)
        painter.setPen(QPen(QColor("#93c5fd"), 3))
        painter.drawLine(24, 41, 40, 41)
        painter.end()
        return QIcon(pix)

    def setup_instance_server(self):
        try:
            QLocalServer.removeServer(APP_SERVER_NAME)
        except Exception:  # noqa: BLE001
            pass
        self.instance_server = QLocalServer(self)
        self.instance_server.newConnection.connect(self._handle_instance_activation)
        if not self.instance_server.listen(APP_SERVER_NAME):
            self.log(f"Instance server listen failed: {self.instance_server.errorString()}")

    def _handle_instance_activation(self):
        while self.instance_server.hasPendingConnections():
            socket = self.instance_server.nextPendingConnection()
            socket.readyRead.connect(lambda socket=socket: self._read_instance_message(socket))
            socket.disconnected.connect(socket.deleteLater)

    def _read_instance_message(self, socket):
        message = bytes(socket.readAll()).decode("utf-8", errors="ignore").strip()
        if message == "show":
            self.log("Received activation request from another launch")
            self.show_main_window()
        socket.disconnectFromServer()

    def setup_tray(self):
        self.tray = QSystemTrayIcon(self.icon, self)
        self.tray.setToolTip(self.tr("tray_title"))
        menu = QMenu(self)
        self.tray_show_action = QAction(self)
        self.tray_capture_action = QAction(self)
        self.tray_quit_action = QAction(self)
        self.tray_show_action.triggered.connect(self.show_main_window)
        self.tray_capture_action.triggered.connect(self.start_selection)
        self.tray_quit_action.triggered.connect(self.quit_app)
        menu.addAction(self.tray_show_action)
        menu.addAction(self.tray_capture_action)
        menu.addSeparator()
        menu.addAction(self.tray_quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_main_window()

    def update_tray_texts(self):
        self.tray.setToolTip(self.tr("tray_title"))
        self.tray_show_action.setText(self.tr("tray_show"))
        self.tray_capture_action.setText(self.tr("tray_capture"))
        self.tray_quit_action.setText(self.tr("tray_quit"))

    def provider_display(self, provider: str) -> str:
        return PROVIDER_LABELS.get(provider, {}).get(self.config.ui_language, provider)

    def display_model_name(self, model_name: str) -> str:
        return model_name[len(MODEL_PREFIX):] if model_name.startswith(MODEL_PREFIX) else model_name

    def normalize_model_name(self, model_name: str) -> str:
        value = model_name.strip()
        if not value:
            return DEFAULT_MODEL
        return value if value.startswith(MODEL_PREFIX) else f"{MODEL_PREFIX}{value}"

    def refresh_log_view(self):
        self.log_text.setPlainText("\n".join(reversed(self.logs)))

    def log(self, message: str):
        self.logs.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        if hasattr(self, "log_text"):
            self.refresh_log_view()

    def apply_language(self):
        self.setWindowTitle(self.tr("window_title"))
        self.title_label.setText(self.tr("title"))
        self.subtitle_label.setText(self.tr("subtitle"))
        self.quick_actions_label.setText(self.tr("quick_actions"))
        self.hero_capture_button.setText(self.tr("start_capture"))
        self.hero_tray_button.setText(self.tr("minimize_to_tray"))
        self.tab_widget.setTabText(0, self.tr("tab_settings"))
        self.tab_widget.setTabText(1, self.tr("tab_monitor"))
        self.profile_group.setTitle(self.tr("section_profiles"))
        self.api_group.setTitle(self.tr("section_api"))
        self.reading_group.setTitle(self.tr("section_reading"))
        self.quick_group.setTitle(self.tr("quick_actions"))
        self.preview_group.setTitle(self.tr("tab_monitor"))
        self.log_group.setTitle(self.tr("logs"))
        if not self.preview_pixmap:
            self.preview_label.setText(self.tr("tab_monitor"))
        self.profile_selector_label.setText(self.tr("profile"))
        self.new_profile_button.setText(self.tr("new_profile"))
        self.delete_profile_button.setText(self.tr("delete_profile"))
        self.profile_name_label.setText(self.tr("profile_name"))
        self.provider_label.setText(self.tr("provider"))
        self.base_url_label.setText(self.tr("base_url"))
        self.model_label.setText(self.tr("model"))
        self.api_keys_label.setText(self.tr("api_keys"))
        self.api_keys_label_row.setText(self.tr("api_keys_hidden") if not self.api_keys_visible else self.tr("api_keys"))
        self.api_keys_hint.setText(self.tr("api_keys_mask_hint") if not self.api_keys_visible else self.tr("api_keys_hint"))
        self.retry_count_label.setText(self.tr("retry_count"))
        self.retry_interval_label.setText(self.tr("retry_interval"))
        self.target_language_label.setText(self.tr("target_language"))
        self.ui_language_label.setText(self.tr("ui_language"))
        self.hotkey_label.setText(self.tr("hotkey"))
        self.overlay_font_label.setText(self.tr("overlay_font_family"))
        self.overlay_font_size_label.setText(self.tr("overlay_font_size"))
        self.mode_label.setText(self.tr("display_mode"))
        self.fetch_models_button.setText(self.tr("fetch_models"))
        self.test_button.setText(self.tr("test_api"))
        self.save_button.setText(self.tr("save_settings"))
        self.capture_button.setText(self.tr("start_capture"))
        self.tray_button.setText(self.tr("minimize_to_tray"))
        self.hint_label.setText(self.tr("hint"))
        self.log_title_label.setText(self.tr("logs"))
        self.api_keys_toggle_button.setText(f"👁 {self.tr('show_api_keys')}" if not self.api_keys_visible else f"🙈 {self.tr('hide_api_keys')}")
        self.update_provider_options()
        self.update_mode_options()
        if hasattr(self, "tray"):
            self.update_tray_texts()
        self.translation_overlay.refresh_language()
        self.set_status(self.current_status_key, **self.current_status_kwargs)

    def update_mode_options(self):
        current = self.mode_combo.currentData() or self.config.mode
        self.mode_combo.blockSignals(True)
        self.mode_combo.clear()
        self.mode_combo.addItem(self.tr("mode_book_lr"), "book_lr")
        self.mode_combo.addItem(self.tr("mode_web_ud"), "web_ud")
        index = self.mode_combo.findData(current)
        self.mode_combo.setCurrentIndex(max(0, index))
        self.mode_combo.blockSignals(False)

    def update_provider_options(self):
        current = self.provider_combo.currentData() or self.get_active_profile().provider
        self.provider_combo.blockSignals(True)
        self.provider_combo.clear()
        for key in ("gemini", "openai"):
            self.provider_combo.addItem(self.provider_display(key), key)
        idx = self.provider_combo.findData(current)
        self.provider_combo.setCurrentIndex(max(0, idx))
        self.provider_combo.blockSignals(False)

    def on_provider_selected(self):
        provider = self.provider_combo.currentData() or "gemini"
        profile = self.get_active_profile()
        if provider == "gemini" and not self.base_url_edit.text().strip():
            self.base_url_edit.setText(DEFAULT_BASE_URL)
        if not self.model_combo.currentText().strip():
            default_model = profile.model if provider == profile.provider else DEFAULT_MODEL
            self.model_combo.setCurrentText(self.display_model_name(default_model))
        self.log(f"Provider changed to: {provider}")

    def refresh_profile_combo(self):
        names = [profile.name for profile in self.config.api_profiles]
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItems(names)
        idx = self.profile_combo.findText(self.config.active_profile_name)
        self.profile_combo.setCurrentIndex(max(0, idx))
        self.profile_combo.blockSignals(False)

    def get_profile_by_name(self, name: str) -> ApiProfile:
        for profile in self.config.api_profiles:
            if profile.name == name:
                return profile
        return self.config.api_profiles[0]

    def get_active_profile(self) -> ApiProfile:
        return self.get_profile_by_name(self.config.active_profile_name)

    def on_profile_selected(self, name: str):
        if not name:
            return
        self.load_profile_to_form(name)

    def mask_api_key_line(self, value: str) -> str:
        value = value.strip()
        if not value:
            return ""
        if len(value) <= 8:
            return value[:1] + "*" * max(1, len(value) - 2) + value[-1:]
        return f"{value[:4]}{'*' * max(3, len(value) - 8)}{value[-4:]}"

    def set_api_keys_editor_text(self, text: str):
        self._updating_api_keys = True
        self.api_keys_edit.setPlainText(text)
        self._updating_api_keys = False

    def refresh_api_keys_editor(self):
        masked_lines = [self.mask_api_key_line(line) for line in self.api_keys_actual_text.splitlines() if line.strip()]
        display_text = self.api_keys_actual_text if self.api_keys_visible else "\n".join(masked_lines)
        self.set_api_keys_editor_text(display_text)
        self.api_keys_edit.setReadOnly(not self.api_keys_visible)
        self.api_keys_label_row.setText(self.tr("api_keys") if self.api_keys_visible else self.tr("api_keys_hidden"))
        self.api_keys_toggle_button.setText(f"🙈 {self.tr('hide_api_keys')}" if self.api_keys_visible else f"👁 {self.tr('show_api_keys')}")
        self.api_keys_hint.setText(self.tr("api_keys_hint") if self.api_keys_visible else self.tr("api_keys_mask_hint"))

    def on_api_keys_text_changed(self):
        if getattr(self, "_updating_api_keys", False):
            return
        if self.api_keys_visible:
            self.api_keys_actual_text = self.api_keys_edit.toPlainText()

    def toggle_api_keys_visibility(self):
        if self.api_keys_visible:
            self.api_keys_actual_text = self.api_keys_edit.toPlainText()
            self.api_keys_visible = False
        else:
            self.api_keys_visible = True
        self.refresh_api_keys_editor()

    def get_api_keys_text(self) -> str:
        if self.api_keys_visible:
            self.api_keys_actual_text = self.api_keys_edit.toPlainText()
        return getattr(self, "api_keys_actual_text", "")

    def load_profile_to_form(self, profile_name: str):
        profile = self.get_profile_by_name(profile_name)
        self.config.active_profile_name = profile.name
        self.refresh_profile_combo()
        self.profile_name_edit.setText(profile.name)
        idx = self.provider_combo.findData(profile.provider)
        self.provider_combo.setCurrentIndex(max(0, idx))
        self.base_url_edit.setText(profile.base_url)
        self.model_combo.clear()
        self.model_combo.addItems([self.display_model_name(m) for m in (profile.available_models or [profile.model])])
        self.model_combo.setCurrentText(self.display_model_name(profile.model))
        self.api_keys_actual_text = "\n".join(profile.api_keys)
        self.refresh_api_keys_editor()
        self.retry_count_spin.setValue(profile.retry_count)
        self.retry_interval_spin.setValue(profile.retry_interval)
        self.target_language_edit.setText(self.config.target_language)
        self.ui_language_combo.setCurrentText(self.config.ui_language)
        self.hotkey_edit.setText(self.config.hotkey)
        self.overlay_font_combo.setCurrentFont(QFont(self.config.overlay_font_family))
        self.overlay_font_size_spin.setValue(self.config.overlay_font_size)
        self.update_mode_options()

    def build_profile_from_form(self) -> ApiProfile:
        api_keys = [line.strip() for line in self.get_api_keys_text().splitlines() if line.strip()]
        available_models = [self.normalize_model_name(self.model_combo.itemText(i)) for i in range(self.model_combo.count()) if self.model_combo.itemText(i).strip()]
        model = self.normalize_model_name(self.model_combo.currentText())
        if model not in available_models:
            available_models.append(model)
        return ApiProfile(
            name=self.profile_name_edit.text().strip() or "Untitled Profile",
            provider=self.provider_combo.currentData() or "gemini",
            base_url=self.base_url_edit.text().strip() or DEFAULT_BASE_URL,
            api_keys=api_keys,
            model=model,
            available_models=available_models,
            retry_count=self.retry_count_spin.value(),
            retry_interval=self.retry_interval_spin.value(),
        )

    def upsert_profile(self, profile: ApiProfile):
        for index, item in enumerate(self.config.api_profiles):
            if item.name == self.config.active_profile_name or item.name == profile.name:
                self.config.api_profiles[index] = profile
                self.config.active_profile_name = profile.name
                return
        self.config.api_profiles.append(profile)
        self.config.active_profile_name = profile.name

    def create_new_profile(self):
        existing = {profile.name for profile in self.config.api_profiles}
        index = 1
        while f"Profile {index}" in existing:
            index += 1
        profile = ApiProfile(name=f"Profile {index}")
        self.config.api_profiles.append(profile)
        self.load_profile_to_form(profile.name)
        self.log(f"Created new profile: {profile.name}")

    def delete_current_profile(self):
        if len(self.config.api_profiles) <= 1:
            QMessageBox.warning(self, self.tr("error_title"), self.tr("at_least_one_profile"))
            return
        name = self.config.active_profile_name
        if QMessageBox.question(self, self.tr("error_title"), self.tr("confirm_delete_profile", name=name)) != QMessageBox.Yes:
            return
        self.config.api_profiles = [profile for profile in self.config.api_profiles if profile.name != name]
        self.config.active_profile_name = self.config.api_profiles[0].name
        save_config(self.config)
        self.load_profile_to_form(self.config.active_profile_name)
        self.set_status("profile_deleted", name=name)

    def save_settings(self):
        previous_hotkey = self.config.hotkey
        previous_language = self.config.ui_language
        profile = self.build_profile_from_form()
        self.upsert_profile(profile)
        self.config.target_language = self.target_language_edit.text().strip() or "繁體中文"
        self.config.ui_language = self.ui_language_combo.currentText().strip() or "zh-TW"
        self.config.hotkey = self.hotkey_edit.text().strip() or "Shift+Win+A"
        self.config.overlay_font_family = self.overlay_font_combo.currentFont().family()
        self.config.overlay_font_size = self.overlay_font_size_spin.value()
        self.config.mode = self.mode_combo.currentData() or "book_lr"
        save_config(self.config)
        self.apply_language()
        self.load_profile_to_form(self.config.active_profile_name)
        if self.config.hotkey != previous_hotkey:
            self.setup_hotkey_listener()
        self.set_status("language_saved" if self.config.ui_language != previous_language else "settings_saved")
        self.log(f"Saved profile: {profile.name} | provider={profile.provider} | base_url={profile.base_url}")

    def on_ui_language_changed(self, value: str):
        if value in I18N:
            self.config.ui_language = value
            self.apply_language()

    def normalize_hotkey(self, hotkey_text: str) -> str:
        parts = [part.strip().lower() for part in hotkey_text.replace("-", "+").split("+") if part.strip()]
        key_map = {"ctrl": "<ctrl>", "control": "<ctrl>", "alt": "<alt>", "shift": "<shift>", "cmd": "<cmd>", "win": "<cmd>", "windows": "<cmd>"}
        mapped = [key_map.get(part, part) for part in parts]
        if not mapped:
            raise ValueError("Empty hotkey")
        return "+".join(mapped)

    def setup_hotkey_listener(self, initial: bool = False):
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None
        try:
            normalized = self.normalize_hotkey(self.config.hotkey)
            self.hotkey_listener = keyboard.GlobalHotKeys({normalized: self.bridge.hotkey_triggered.emit})
            self.hotkey_listener.start()
            self.log(f"Hotkey listener registered: {self.config.hotkey}")
            if not initial:
                self.set_status("hotkey_registered", hotkey=self.config.hotkey)
        except Exception as exc:  # noqa: BLE001
            self.log(f"Hotkey registration failed: {exc}")
            if not initial:
                QMessageBox.critical(self, self.tr("error_title"), self.tr("hotkey_register_failed", error=exc))

    def run_worker(self, fn, on_success):
        WorkerThread(fn, self.bridge, on_success).start()

    def _handle_worker_success(self, callback, result):
        if callable(callback):
            callback(result)

    def fetch_models(self):
        self.save_settings()
        profile = self.get_active_profile()
        self.log(f"Fetching models for profile: {profile.name}")
        self.run_worker(lambda: self.api_client.list_models(profile), self.on_models_loaded)

    def on_models_loaded(self, models: list[str]):
        if not models:
            return
        profile = self.build_profile_from_form()
        profile.available_models = models
        if profile.model not in models:
            profile.model = models[0]
        self.upsert_profile(profile)
        save_config(self.config)
        self.load_profile_to_form(profile.name)
        self.set_status("models_loaded", count=len(models))
        self.log(f"Loaded {len(models)} models")

    def test_profile(self):
        self.save_settings()
        profile = self.get_active_profile()
        self.log(f"Testing profile: {profile.name}")
        self.run_worker(lambda: self.api_client.test_profile(profile), self.on_test_success)

    def on_test_success(self, result: str):
        self.log(result)
        self.set_status("test_success")

    def set_status(self, key: str, **kwargs):
        self.current_status_key = key
        self.current_status_kwargs = kwargs
        self.status_label.setText(self.tr(key, **kwargs))

    def start_selection(self):
        self.save_settings()
        self.hide()
        self.translation_overlay.hide()
        self.selection_overlay.show_overlay()

    def handle_capture_cancelled(self):
        self.set_status("capture_cancelled")
        self.show_tray_toast(self.tr("capture_cancelled"))

    def handle_selection(self, bbox):
        image = ImageGrab.grab(bbox=bbox, all_screens=True)
        self.update_preview(image)
        self.set_status("capturing")
        self.show_tray_toast(self.tr("tray_capturing"))
        profile = self.get_active_profile()
        self.run_worker(lambda: self.api_client.translate_image(image, profile, self.config.target_language, self.config.temperature), lambda text: self.show_translation(bbox, text))

    def show_translation(self, bbox, text: str):
        text = text or self.tr("empty_result")
        width, height = self.translation_overlay.calculate_size(text)
        width, height = self.fit_overlay_size(bbox, text, width, height)
        x, y = self.compute_overlay_position(bbox, width, height)
        self.translation_overlay.remember_context(bbox, text)
        self.translation_overlay.show_text(text, x, y, width, height)
        self.set_status("translated")
        self.log("Translation finished")

    def get_target_screen_rect(self, bbox):
        left, top, right, bottom = bbox
        center = QPoint(int((left + right) / 2), int((top + bottom) / 2))
        screen = QGuiApplication.screenAt(center) or QGuiApplication.primaryScreen()
        return screen.availableGeometry() if screen else QGuiApplication.primaryScreen().availableGeometry()

    def fit_overlay_size(self, bbox, text: str, width, height):
        left, top, right, bottom = bbox
        screen_rect = self.get_target_screen_rect(bbox)
        margin = self.config.margin
        vertical_comfort_margin = max(42, margin * 2)
        screen_left = screen_rect.left()
        screen_top = screen_rect.top()
        screen_right = screen_rect.right()
        screen_bottom = screen_rect.bottom()

        if self.config.mode == "book_lr":
            left_space = max(240, left - screen_left - margin * 2)
            right_space = max(240, screen_right - right - margin * 2)
            preferred_width = left_space if ((left + right) / 2) >= screen_rect.center().x() else right_space
            width = min(width, preferred_width)
        else:
            top_space = max(200, top - screen_top - margin * 2)
            bottom_space = max(200, screen_bottom - bottom - margin * 2)
            preferred_height = bottom_space if ((top + bottom) / 2) < screen_rect.center().y() else top_space
            height = min(height, preferred_height)

        width = min(width, max(240, screen_rect.width() - margin * 2))
        soft_bottom_margin = vertical_comfort_margin
        available_height = max(220, screen_rect.height() - vertical_comfort_margin * 2)
        moderate_height_cap = max(260, int(screen_rect.height() * 0.72))
        desired_height = self.translation_overlay.measure_content_height(text, width)
        height = max(height, desired_height)
        height = min(height, available_height, moderate_height_cap)
        return int(width), int(height)

    def compute_overlay_position(self, bbox, width, height):
        left, top, right, bottom = bbox
        screen_rect = self.get_target_screen_rect(bbox)
        margin = self.config.margin
        soft_top_margin = max(42, margin * 2)
        soft_bottom_margin = soft_top_margin
        screen_left = screen_rect.left()
        screen_top = screen_rect.top()
        screen_right = screen_rect.right()
        screen_bottom = screen_rect.bottom()
        center_x = (left + right) / 2
        center_y = (top + bottom) / 2

        def clamp_x(value):
            return max(screen_left + margin, min(value, screen_right - width - margin + 1))

        def clamp_y(value):
            return max(screen_top + soft_top_margin, min(value, screen_bottom - height - soft_bottom_margin + 1))

        if self.config.mode == "book_lr":
            prefer_left = center_x >= screen_rect.center().x()
            preferred_x = left - width - margin if prefer_left else right + margin
            alternate_x = right + margin if prefer_left else left - width - margin
            if screen_left + margin <= preferred_x <= screen_right - width - margin + 1:
                x = preferred_x
            elif screen_left + margin <= alternate_x <= screen_right - width - margin + 1:
                x = alternate_x
            else:
                x = clamp_x(preferred_x)
            y = clamp_y(top + 12)
        else:
            prefer_below = center_y < screen_rect.center().y()
            preferred_y = bottom + margin if prefer_below else top - height - margin
            alternate_y = top - height - margin if prefer_below else bottom + margin
            if screen_top + margin <= preferred_y <= screen_bottom - height - margin + 1:
                y = preferred_y
            elif screen_top + margin <= alternate_y <= screen_bottom - height - margin + 1:
                y = alternate_y
            else:
                y = clamp_y(preferred_y)
            x = clamp_x(left)
        return int(x), int(y)

    def adjust_overlay_font_size(self, direction: int):
        new_size = max(10, min(32, self.config.overlay_font_size + direction))
        if new_size == self.config.overlay_font_size:
            return
        self.config.overlay_font_size = new_size
        self.overlay_font_size_spin.setValue(new_size)
        save_config(self.config)
        self.translation_overlay.apply_typography()
        self.set_status("font_zoomed", size=new_size)
        if self.translation_overlay.isVisible() and self.translation_overlay.last_bbox and self.translation_overlay.last_text:
            self.show_translation(self.translation_overlay.last_bbox, self.translation_overlay.last_text)

    def update_preview(self, image: Image.Image):
        preview = image.copy()
        preview.thumbnail((900, 280))
        data = io.BytesIO()
        preview.save(data, format="PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(data.getvalue(), "PNG")
        self.preview_pixmap = pixmap
        self.preview_label.setText("")
        self.preview_label.setPixmap(pixmap)

    def show_tray_toast(self, message: str):
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.showMessage(self.tr("tray_title"), message, self.icon, 2500)

    def minimize_to_tray(self):
        self.hide()
        self.translation_overlay.hide()
        self.set_status("tray_minimized")
        self.show_tray_toast(self.tr("tray_minimized"))

    def show_main_window(self):
        self.show()
        self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
        self.raise_()
        self.activateWindow()

    def handle_error(self, exc: Exception):
        self.set_status("translate_failed")
        self.log(f"Error: {exc}")
        QMessageBox.critical(self, self.tr("error_title"), str(exc))

    def closeEvent(self, event):
        self.quit_app()
        event.accept()

    def quit_app(self):
        if self.is_quitting:
            return
        self.is_quitting = True
        self.log("Application exiting")
        try:
            self.selection_overlay.hide()
        except Exception:  # noqa: BLE001
            pass
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None
        if hasattr(self, "instance_server") and self.instance_server.isListening():
            self.instance_server.close()
            QLocalServer.removeServer(APP_SERVER_NAME)
        self.translation_overlay.close()
        self.tray.hide()
        QApplication.instance().quit()


def _default_profile() -> ApiProfile:
    return ApiProfile()


def _config_to_dict(config: AppConfig) -> dict:
    data = asdict(config)
    data["api_profiles"] = [asdict(profile) for profile in config.api_profiles]
    return data


def _dict_to_profile(data: dict) -> ApiProfile:
    defaults = asdict(_default_profile())
    merged = {**defaults, **data}
    merged["api_keys"] = [key.strip() for key in merged.get("api_keys", []) if key and str(key).strip()]
    merged["available_models"] = [model for model in merged.get("available_models", []) if model]
    if not merged["available_models"]:
        merged["available_models"] = [merged.get("model") or DEFAULT_MODEL]
    if not merged.get("model"):
        merged["model"] = merged["available_models"][0]
    return ApiProfile(**merged)


def _migrate_legacy_config(data: dict) -> AppConfig:
    if "api_profiles" in data:
        profiles = [_dict_to_profile(item) for item in data.get("api_profiles", [])] or [_default_profile()]
        return AppConfig(
            target_language=data.get("target_language", "繁體中文"),
            mode=data.get("mode", "book_lr"),
            temperature=float(data.get("temperature", 0.2)),
            overlay_width=int(data.get("overlay_width", 440)),
            overlay_height=int(data.get("overlay_height", 520)),
            margin=int(data.get("margin", 18)),
            ui_language=data.get("ui_language", "zh-TW"),
            hotkey=data.get("hotkey", "Shift+Win+A"),
            overlay_font_family=data.get("overlay_font_family", "Microsoft JhengHei UI"),
            overlay_font_size=int(data.get("overlay_font_size", 12)),
            active_profile_name=data.get("active_profile_name") or profiles[0].name,
            api_profiles=profiles,
        )
    legacy_profile = ApiProfile(
        name="Default Gemini",
        provider="gemini",
        base_url=data.get("base_url", DEFAULT_BASE_URL),
        api_keys=[data.get("api_key", "")] if data.get("api_key") else [],
        model=data.get("model", DEFAULT_MODEL),
        available_models=[data.get("model", DEFAULT_MODEL)],
    )
    return AppConfig(
        target_language=data.get("target_language", "繁體中文"),
        mode=data.get("mode", "book_lr"),
        temperature=float(data.get("temperature", 0.2)),
        overlay_width=int(data.get("overlay_width", 440)),
        overlay_height=int(data.get("overlay_height", 520)),
        margin=int(data.get("margin", 18)),
        ui_language=data.get("ui_language", "zh-TW"),
        hotkey=data.get("hotkey", "Shift+Win+A"),
        overlay_font_family=data.get("overlay_font_family", "Microsoft JhengHei UI"),
        overlay_font_size=int(data.get("overlay_font_size", 12)),
        active_profile_name=legacy_profile.name,
        api_profiles=[legacy_profile],
    )


def load_config() -> AppConfig:
    if CONFIG_PATH.exists():
        return _migrate_legacy_config(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    config = AppConfig()
    save_config(config)
    return config


def save_config(config: AppConfig) -> None:
    CONFIG_PATH.write_text(json.dumps(_config_to_dict(config), ensure_ascii=False, indent=2), encoding="utf-8")


def acquire_single_instance_lock() -> QLockFile | None:
    lock = QLockFile(APP_LOCK_PATH)
    lock.setStaleLockTime(0)
    if lock.tryLock(100):
        return lock
    return None


def request_existing_instance_raise() -> bool:
    socket = QLocalSocket()
    socket.connectToServer(APP_SERVER_NAME)
    if not socket.waitForConnected(400):
        return False
    socket.write(b"show")
    socket.flush()
    socket.waitForBytesWritten(400)
    socket.disconnectFromServer()
    return True


def run_app():
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("OCRTranslator")
    lock = acquire_single_instance_lock()
    if lock is None:
        if not request_existing_instance_raise():
            message_config = load_config()
            lang = message_config.ui_language if message_config.ui_language in I18N else "zh-TW"
            QMessageBox.information(None, I18N[lang]["already_running_title"], I18N[lang]["already_running_message"])
        return
    window = MainWindow()
    app.instance_lock = lock
    window.show()
    app.exec()


if __name__ == "__main__":
    run_app()
