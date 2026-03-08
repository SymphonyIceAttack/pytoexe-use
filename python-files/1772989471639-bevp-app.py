from __future__ import annotations

import html
import re
import sys

from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, QThread, Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sevaai import Client


APP_MODELS = [
    "gpt-4o-mini",
    "gpt-4.1-mini",
    "gpt-4o",
    "gpt-4.1",
    "gpt-5-mini",
    "gpt-oss:120b",
    "claude-sonnet-4",
    "qwen-3",
    "gemma-2-9b-it",
]

SYSTEM_PROMPT = (
    "You are a helpful assistant. "
    "Reply in the same language as the user when possible."
)

FENCED_CODE_RE = re.compile(r"```([A-Za-z0-9_:+#.-]*)\n(.*?)```", re.DOTALL)

TEXT = {
    "en": {
        "window_title": "SevaAI",
        "brand": "SevaAI",
        "subtitle": "Desktop AI Studio",
        "description": "A polished desktop chat built for fast conversations, clean reading, and quiet focus.",
        "hero_badge": "Official-style desktop client",
        "hero_title": "Talk to your models in one calm workspace.",
        "hero_body": "Switch models, keep the interface clean, and stay focused on the conversation.",
        "metric_label": "Active models",
        "metric_note": "Quiet UI, premium layout, no terminal clutter.",
        "model": "Model",
        "language": "Language",
        "new_chat": "New Chat",
        "send": "Send",
        "cancel": "Cancel",
        "thinking": "Thinking...",
        "ready": "Ready",
        "chat_empty_title": "Start a conversation",
        "chat_empty_body": "Choose a model, write a prompt, and send it.",
        "placeholder": "Write your message...",
        "status_model_changed": "Model switched",
        "status_chat_cleared": "Chat cleared",
        "status_empty": "Type a message first",
        "assistant": "SevaAI",
        "user": "You",
        "error_generic": "Something went wrong. Please try again.",
        "error_limited": "This model is temporarily limited. Please try again later.",
        "language_en": "English",
        "language_ru": "Russian",
    },
    "ru": {
        "window_title": "SevaAI",
        "brand": "SevaAI",
        "subtitle": "AI-приложение для Windows",
        "description": "Аккуратный desktop-чат для быстрых диалогов, удобного чтения и спокойной работы.",
        "hero_badge": "Десктоп-клиент в официальном стиле",
        "hero_title": "Общайтесь с моделями в одном спокойном окне.",
        "hero_body": "Переключайте модели, держите интерфейс чистым и сосредоточьтесь на самом диалоге.",
        "metric_label": "Активные модели",
        "metric_note": "Спокойный интерфейс, аккуратная подача, без терминального шума.",
        "model": "Модель",
        "language": "Язык",
        "new_chat": "Новый чат",
        "send": "Отправить",
        "cancel": "Отмена",
        "thinking": "Думаю...",
        "ready": "Готово",
        "chat_empty_title": "Начните диалог",
        "chat_empty_body": "Выберите модель, введите запрос и отправьте его.",
        "placeholder": "Введите сообщение...",
        "status_model_changed": "Модель переключена",
        "status_chat_cleared": "Чат очищен",
        "status_empty": "Сначала введите сообщение",
        "assistant": "SevaAI",
        "user": "Вы",
        "error_generic": "Что-то пошло не так. Попробуйте еще раз.",
        "error_limited": "Для этой модели сейчас действует лимит. Попробуйте позже.",
        "language_en": "Английский",
        "language_ru": "Русский",
    },
}


class ChatWorker(QThread):
    finished_ok = Signal(str)
    finished_error = Signal(str)

    def __init__(self, model: str, messages: list[dict[str, str]], language: str) -> None:
        super().__init__()
        self.model = model
        self.messages = messages
        self.language = language

    def run(self) -> None:
        client = Client()
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=self.messages,
            )
            self.finished_ok.emit(response.choices[0].message.content)
        except Exception as error:  # noqa: BLE001
            error_text = str(error).lower()
            if self.model == "gemma-2-9b-it" and (
                "gpu quota" in error_text
                or "no gpu was available" in error_text
                or "zerogpu" in error_text
                or "temporarily limited" in error_text
            ):
                self.finished_error.emit(TEXT[self.language]["error_limited"])
            else:
                self.finished_error.emit(TEXT[self.language]["error_generic"])


def _render_message_html(body: str) -> str:
    if "```" not in body:
        unfenced = _detect_unfenced_code_block(body)
        if unfenced is not None:
            intro, language, code = unfenced
            parts = []
            if intro:
                parts.append(_render_text_fragment(intro))
            parts.append(_render_code_block(language, code))
            return "<body>" + "".join(parts) + "</body>"

    parts: list[str] = []
    last_index = 0

    for match in FENCED_CODE_RE.finditer(body):
        before = body[last_index:match.start()]
        if before.strip():
            parts.append(_render_text_fragment(before))

        language = (match.group(1) or "CODE").strip().upper()
        code = match.group(2).rstrip()
        parts.append(_render_code_block(language, code))
        last_index = match.end()

    tail = body[last_index:]
    if tail.strip():
        parts.append(_render_text_fragment(tail))

    if not parts:
        parts.append(_render_text_fragment(body))

    return "<body>" + "".join(parts) + "</body>"


def _detect_unfenced_code_block(body: str) -> tuple[str, str, str] | None:
    lines = body.splitlines()
    if len(lines) < 4:
        return None

    best_start = -1
    best_score = 0
    language = "CODE"

    for index, line in enumerate(lines):
        candidate_language = _guess_code_language(line)
        score = _score_code_lines(lines[index:index + 18])
        if candidate_language:
            score += 3
        if score > best_score:
            best_score = score
            best_start = index
            if candidate_language:
                language = candidate_language

    if best_start == -1 or best_score < 8:
        return None

    intro = "\n".join(lines[:best_start]).strip()
    code = "\n".join(lines[best_start:]).strip()
    if len(code.splitlines()) < 4:
        return None
    return intro, language, code


def _guess_code_language(first_line: str) -> str | None:
    stripped = first_line.strip().lower()
    if stripped in {"html", "</>html"} or stripped.startswith("<!doctype html") or stripped.startswith("<html"):
        return "HTML"
    if stripped in {"css", "</>css"} or stripped.startswith("body {") or stripped.startswith(":root {"):
        return "CSS"
    if stripped in {"javascript", "js", "</>javascript"} or "document.getelementbyid" in stripped:
        return "JAVASCRIPT"
    if stripped in {"python", "py", "</>python"} or stripped.startswith("def ") or stripped.startswith("import "):
        return "PYTHON"
    if stripped in {"json", "</>json"} or stripped.startswith("{") or stripped.startswith("["):
        return "JSON"
    return None


def _score_code_lines(lines: list[str]) -> int:
    score = 0
    markers = (
        "<!doctype",
        "<html",
        "<head",
        "<body",
        "</",
        "function ",
        "const ",
        "let ",
        "var ",
        "def ",
        "class ",
        "import ",
        "return ",
        "{",
        "}",
        ";",
        "=>",
        "    ",
    )

    for line in lines:
        stripped = line.strip().lower()
        if not stripped:
            continue
        if any(marker in stripped for marker in markers):
            score += 1
        if stripped.startswith(("<", ".", "#", "@media", "body", "html", "if ", "for ", "while ")):
            score += 1
    return score


def _render_text_fragment(text: str) -> str:
    escaped = html.escape(text)

    escaped = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", escaped)
    escaped = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', escaped)

    blocks = []
    for paragraph in escaped.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        lines = paragraph.splitlines()
        if all(line.lstrip().startswith(("- ", "* ")) for line in lines):
            items = "".join(
                f"<li>{line.lstrip()[2:].strip()}</li>"
                for line in lines
            )
            blocks.append(f"<ul>{items}</ul>")
            continue
        blocks.append(f"<p>{'<br>'.join(lines)}</p>")
    return "".join(blocks)


def _render_code_block(language: str, code: str) -> str:
    escaped_code = html.escape(code)
    return (
        '<div class="code-card">'
        f'<div class="code-header"><span class="code-dot">&lt;/&gt;</span>'
        f'<span class="code-lang">{language}</span></div>'
        f"<pre><code>{escaped_code}</code></pre>"
        "</div>"
    )


class MessageBubble(QFrame):
    def __init__(self, author: str, body: str, is_user: bool) -> None:
        super().__init__()
        self.setObjectName("bubbleUser" if is_user else "bubbleAssistant")
        self.setMaximumWidth(780)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)

        author_label = QLabel(author)
        author_label.setObjectName("bubbleAuthorUser" if is_user else "bubbleAuthorAssistant")
        author_label.setWordWrap(True)

        body_label = QTextBrowser()
        body_label.setObjectName("bubbleBody")
        body_label.setOpenExternalLinks(True)
        body_label.setOpenLinks(True)
        body_label.setReadOnly(True)
        body_label.setFrameShape(QFrame.NoFrame)
        body_label.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body_label.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body_label.setContextMenuPolicy(Qt.NoContextMenu)
        body_label.setStyleSheet("background: transparent;")
        body_label.document().setDocumentMargin(0)
        body_label.document().setDefaultStyleSheet(
            """
            body { color: #edf4ff; font-size: 13px; }
            p { margin: 0 0 8px 0; }
            ul { margin: 6px 0 8px 18px; }
            li { margin: 2px 0; }
            .code-card {
                background: #0a1119;
                border: 1px solid #2b3f54;
                border-radius: 18px;
                margin: 8px 0;
            }
            .code-header {
                background: #0d151f;
                border-bottom: 1px solid #26384c;
                border-top-left-radius: 18px;
                border-top-right-radius: 18px;
                padding: 10px 14px;
            }
            .code-dot {
                color: #e4eefc;
                font-size: 12px;
                font-weight: 700;
                margin-right: 8px;
            }
            .code-lang {
                color: #ffffff;
                font-size: 12px;
                font-weight: 700;
            }
            pre {
                background: transparent;
                border: none;
                border-radius: 0;
                padding: 14px;
                margin: 0;
                color: #dff3ff;
                white-space: pre-wrap;
            }
            code {
                font-family: 'Cascadia Code', 'Consolas', monospace;
                font-size: 12px;
            }
            a {
                color: #7cefd8;
                text-decoration: none;
            }
            ul, ol {
                margin: 6px 0 6px 18px;
            }
            """
        )
        body_label.setHtml(_render_message_html(body))
        body_label.document().adjustSize()
        body_label.setMinimumHeight(int(body_label.document().size().height()) + 4)
        body_label.setMaximumHeight(int(body_label.document().size().height()) + 8)

        layout.addWidget(author_label)
        layout.addWidget(body_label)


class MessageRow(QWidget):
    def __init__(self, author: str, body: str, is_user: bool) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        bubble = MessageBubble(author, body, is_user)
        if is_user:
            layout.addStretch(1)
            layout.addWidget(bubble, 0, Qt.AlignRight)
        else:
            layout.addWidget(bubble, 0, Qt.AlignLeft)
            layout.addStretch(1)


class EmptyState(QFrame):
    def __init__(self, title: str, body: str) -> None:
        super().__init__()
        self.setObjectName("emptyState")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 100, 0, 0)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("emptyTitle")
        title_label.setAlignment(Qt.AlignCenter)

        body_label = QLabel(body)
        body_label.setObjectName("emptyBody")
        body_label.setAlignment(Qt.AlignCenter)
        body_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(body_label)


class TitleBar(QFrame):
    def __init__(self, window: QMainWindow) -> None:
        super().__init__()
        self._window = window
        self._drag_pos: QPoint | None = None
        self.setObjectName("titleBar")
        self.setFixedHeight(46)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(12)

        self.controls = QFrame()
        self.controls.setObjectName("trafficLights")
        controls_layout = QHBoxLayout(self.controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(6)

        self.close_button = QPushButton("")
        self.min_button = QPushButton("")
        self.max_button = QPushButton("")

        for button in (self.close_button, self.min_button, self.max_button):
            button.setProperty("traffic", True)
            button.setFixedSize(14, 14)
            button.setCursor(Qt.PointingHandCursor)

        self.close_button.setObjectName("trafficClose")
        self.min_button.setObjectName("trafficMin")
        self.max_button.setObjectName("trafficMax")

        self.close_button.setToolTip("Close")
        self.min_button.setToolTip("Minimize")
        self.max_button.setToolTip("Zoom")

        self.min_button.clicked.connect(self._window.showMinimized)
        self.max_button.clicked.connect(self._toggle_maximize)
        self.close_button.clicked.connect(self._window.close)

        self.title_label = QLabel("SevaAI")
        self.title_label.setObjectName("titleBarLabel")

        controls_layout.addWidget(self.close_button)
        controls_layout.addWidget(self.min_button)
        controls_layout.addWidget(self.max_button)

        layout.addWidget(self.controls, 0, Qt.AlignVCenter)
        layout.addWidget(self.title_label, 0, Qt.AlignVCenter)
        layout.addStretch(1)

    def _toggle_maximize(self) -> None:
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()

    def mouseDoubleClickEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self._toggle_maximize()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton and not self._window.isMaximized():
            self._drag_pos = event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._drag_pos is not None and not self._window.isMaximized():
            self._window.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        self._drag_pos = None
        super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.language = "en"
        self.copy = TEXT[self.language]
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.worker: ChatWorker | None = None
        self._animations: list[QPropertyAnimation] = []
        self.request_cancelled = False

        self.setMinimumSize(1160, 780)
        self.resize(1460, 920)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self._build_ui()
        self._apply_copy()
        self._render_empty()

    def _build_ui(self) -> None:
        self.setObjectName("root")
        central = QWidget()
        self.setCentralWidget(central)

        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.setSpacing(10)

        self.title_bar = TitleBar(self)
        outer_layout.addWidget(self.title_bar)

        root_layout = QHBoxLayout()
        root_layout.setContentsMargins(8, 0, 8, 8)
        root_layout.setSpacing(18)
        outer_layout.addLayout(root_layout, 1)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(330)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(24, 24, 24, 24)
        sidebar_layout.setSpacing(20)

        self.brand_orb = QFrame()
        self.brand_orb.setObjectName("brandOrb")
        self.brand_orb.setFixedSize(54, 54)

        self.brand_label = QLabel()
        self.brand_label.setObjectName("brand")

        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("subtitle")

        self.description_label = QLabel()
        self.description_label.setObjectName("description")
        self.description_label.setWordWrap(True)

        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(0, 0, 0, 0)
        brand_row.setSpacing(14)

        brand_copy = QVBoxLayout()
        brand_copy.setContentsMargins(0, 0, 0, 0)
        brand_copy.setSpacing(2)
        brand_copy.addWidget(self.brand_label)
        brand_copy.addWidget(self.subtitle_label)

        brand_row.addWidget(self.brand_orb, 0, Qt.AlignTop)
        brand_row.addLayout(brand_copy, 1)

        sidebar_layout.addLayout(brand_row)
        sidebar_layout.addWidget(self.description_label)

        self.settings_card = QFrame()
        self.settings_card.setObjectName("settingsCard")
        settings_layout = QVBoxLayout(self.settings_card)
        settings_layout.setContentsMargins(18, 18, 18, 18)
        settings_layout.setSpacing(12)

        self.model_title = QLabel()
        self.model_title.setObjectName("fieldLabel")
        self.model_combo = QComboBox()
        self.model_combo.addItems(APP_MODELS)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)

        self.language_title = QLabel()
        self.language_title.setObjectName("fieldLabel")
        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Russian"])
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)

        settings_layout.addWidget(self.model_title)
        settings_layout.addWidget(self.model_combo)
        settings_layout.addSpacing(8)
        settings_layout.addWidget(self.language_title)
        settings_layout.addWidget(self.language_combo)

        sidebar_layout.addWidget(self.settings_card)

        self.new_chat_button = QPushButton()
        self.new_chat_button.clicked.connect(self._reset_chat)
        sidebar_layout.addWidget(self.new_chat_button)

        sidebar_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        sidebar_layout.addWidget(self.status_label)

        self.content = QFrame()
        self.content.setObjectName("content")
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(18, 18, 18, 18)
        content_layout.setSpacing(14)

        self.hero = QFrame()
        self.hero.setObjectName("hero")
        hero_layout = QHBoxLayout(self.hero)
        hero_layout.setContentsMargins(22, 20, 22, 20)
        hero_layout.setSpacing(18)

        hero_copy = QVBoxLayout()
        hero_copy.setContentsMargins(0, 0, 0, 0)
        hero_copy.setSpacing(6)

        self.hero_badge = QLabel()
        self.hero_badge.setObjectName("heroBadge")

        self.hero_title = QLabel()
        self.hero_title.setObjectName("heroTitle")
        self.hero_title.setWordWrap(True)

        self.hero_body = QLabel()
        self.hero_body.setObjectName("heroBody")
        self.hero_body.setWordWrap(True)

        hero_copy.addWidget(self.hero_badge)
        hero_copy.addWidget(self.hero_title)
        hero_copy.addWidget(self.hero_body)

        self.hero_metric = QFrame()
        self.hero_metric.setObjectName("heroMetricCard")
        self.hero_metric.setFixedWidth(190)

        metric_layout = QVBoxLayout(self.hero_metric)
        metric_layout.setContentsMargins(18, 16, 18, 16)
        metric_layout.setSpacing(2)

        self.metric_value = QLabel(str(len(APP_MODELS)).zfill(2))
        self.metric_value.setObjectName("metricValue")

        self.metric_label = QLabel()
        self.metric_label.setObjectName("metricLabel")

        self.metric_note = QLabel()
        self.metric_note.setObjectName("metricNote")
        self.metric_note.setWordWrap(True)

        metric_layout.addWidget(self.metric_value)
        metric_layout.addWidget(self.metric_label)
        metric_layout.addSpacing(8)
        metric_layout.addWidget(self.metric_note)

        hero_layout.addLayout(hero_copy, 1)
        hero_layout.addWidget(self.hero_metric, 0, Qt.AlignTop)

        self.chat_list = QListWidget()
        self.chat_list.setObjectName("chatList")
        self.chat_list.setSpacing(12)
        self.chat_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)

        self.composer = QFrame()
        self.composer.setObjectName("composer")
        composer_layout = QHBoxLayout(self.composer)
        composer_layout.setContentsMargins(16, 16, 16, 16)
        composer_layout.setSpacing(14)

        input_column = QVBoxLayout()
        input_column.setContentsMargins(0, 0, 0, 0)
        input_column.setSpacing(8)

        self.thinking_label = QLabel()
        self.thinking_label.setObjectName("thinkingLabel")
        self.thinking_label.hide()

        self.input = QTextEdit()
        self.input.setObjectName("input")
        self.input.setMinimumHeight(84)
        self.input.setMaximumHeight(150)
        self.input.setAcceptRichText(False)

        self.send_button = QPushButton()
        self.send_button.clicked.connect(self._send_message)

        self.cancel_button = QPushButton()
        self.cancel_button.clicked.connect(self._cancel_request)
        self.cancel_button.hide()

        input_column.addWidget(self.thinking_label)
        input_column.addWidget(self.input, 1)

        composer_layout.addLayout(input_column, 1)
        composer_layout.addWidget(self.cancel_button, 0, Qt.AlignBottom)
        composer_layout.addWidget(self.send_button, 0, Qt.AlignBottom)

        content_layout.addWidget(self.hero)
        content_layout.addWidget(self.chat_list, 1)
        content_layout.addWidget(self.composer)

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(self.content, 1)

        self._apply_styles()

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget#root {
                background: #07111f;
                color: #edf4ff;
            }
            QFrame#titleBar {
                background: rgba(10, 20, 34, 0.72);
                border: 1px solid #1d3752;
                border-radius: 16px;
            }
            QFrame#trafficLights {
                background: transparent;
            }
            QLabel#titleBarLabel {
                color: #dce9fb;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton[traffic="true"] {
                border-radius: 7px;
                border: 1px solid rgba(0, 0, 0, 0.28);
                min-width: 14px;
                max-width: 14px;
                min-height: 14px;
                max-height: 14px;
                padding: 0;
            }
            QPushButton#trafficClose {
                background: #ff5f57;
            }
            QPushButton#trafficClose:hover {
                background: #ff736d;
            }
            QPushButton#trafficMin {
                background: #febc2e;
            }
            QPushButton#trafficMin:hover {
                background: #ffca52;
            }
            QPushButton#trafficMax {
                background: #28c840;
            }
            QPushButton#trafficMax:hover {
                background: #46d45b;
            }
            QFrame#sidebar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #091523, stop:0.6 #0d1d31, stop:1 #122640);
                border: 1px solid #21425e;
                border-radius: 26px;
            }
            QFrame#brandOrb {
                border-radius: 27px;
                background: qradialgradient(cx:0.35, cy:0.3, radius:0.9,
                    fx:0.35, fy:0.3, stop:0 #86f1db, stop:0.45 #38d8ff, stop:1 #0e2340);
                border: 1px solid rgba(255, 255, 255, 0.18);
            }
            QLabel#brand {
                font-size: 30px;
                font-weight: 700;
                color: #f8fbff;
            }
            QLabel#subtitle {
                font-size: 12px;
                font-weight: 700;
                color: #79f0d3;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }
            QLabel#description {
                font-size: 12px;
                color: #89a9cc;
                line-height: 1.5em;
            }
            QFrame#settingsCard {
                background: rgba(255, 255, 255, 0.045);
                border: 1px solid #284966;
                border-radius: 20px;
            }
            QLabel#fieldLabel {
                font-size: 11px;
                font-weight: 700;
                color: #8ca5c3;
                text-transform: uppercase;
                letter-spacing: 0.06em;
            }
            QComboBox {
                min-height: 42px;
                border-radius: 14px;
                border: 1px solid #2d4d6f;
                background: #0b1828;
                color: #edf4ff;
                padding: 0 12px;
                font-size: 13px;
            }
            QComboBox QAbstractItemView {
                background: #0d1a2a;
                color: #edf4ff;
                selection-background-color: #18314c;
                border: 1px solid #2a4565;
            }
            QPushButton {
                min-height: 46px;
                border-radius: 16px;
                border: none;
                font-size: 13px;
                font-weight: 700;
                padding: 0 18px;
            }
            QLabel#statusLabel {
                color: #7ff0c8;
                font-size: 11px;
                font-weight: 700;
            }
            QFrame#content {
                background: #0a1727;
                border: 1px solid #1e3a56;
                border-radius: 26px;
            }
            QFrame#hero {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f2136, stop:1 #122947);
                border: 1px solid #294766;
                border-radius: 22px;
            }
            QLabel#heroBadge {
                color: #7cf1d7;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }
            QLabel#heroTitle {
                color: #f7fbff;
                font-size: 24px;
                font-weight: 700;
            }
            QLabel#heroBody {
                color: #9db2ce;
                font-size: 12px;
                line-height: 1.45em;
            }
            QFrame#heroMetricCard {
                background: rgba(5, 14, 24, 0.42);
                border: 1px solid #2d4d6d;
                border-radius: 18px;
            }
            QLabel#metricValue {
                color: #f8fbff;
                font-size: 30px;
                font-weight: 700;
            }
            QLabel#metricLabel {
                color: #7ff0c8;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }
            QLabel#metricNote {
                color: #96aac8;
                font-size: 11px;
            }
            QLabel#thinkingLabel {
                color: #7ff0c8;
                font-size: 11px;
                font-weight: 700;
                padding-left: 4px;
            }
            QListWidget#chatList {
                background: transparent;
                border: none;
                padding: 6px 4px 2px 4px;
                outline: none;
            }
            QListWidget#chatList::item {
                border: none;
            }
            QFrame#composer {
                background: #0f1f33;
                border: 1px solid #213c58;
                border-radius: 22px;
            }
            QTextEdit#input {
                background: #0b1828;
                border: 1px solid #27415f;
                border-radius: 18px;
                color: #edf4ff;
                padding: 12px 14px;
                font-size: 13px;
            }
            QTextEdit#input:focus {
                border: 1px solid #78f0d6;
            }
            QFrame#bubbleAssistant {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #11243a, stop:1 #132c48);
                border: 1px solid #284764;
                border-radius: 20px;
            }
            QFrame#bubbleUser {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #16273c, stop:1 #1a3150);
                border: 1px solid #36587d;
                border-radius: 20px;
            }
            QLabel#bubbleAuthorAssistant {
                color: #79f0d3;
                font-size: 11px;
                font-weight: 700;
            }
            QLabel#bubbleAuthorUser {
                color: #ffbe72;
                font-size: 11px;
                font-weight: 700;
            }
            QTextBrowser#bubbleBody {
                color: #edf4ff;
                font-size: 13px;
                line-height: 1.55em;
            }
            QFrame#emptyState {
                background: transparent;
            }
            QLabel#emptyTitle {
                color: #f3f8ff;
                font-size: 30px;
                font-weight: 700;
            }
            QLabel#emptyBody {
                color: #8ea6c5;
                font-size: 13px;
            }
            """
        )

        self.new_chat_button.setStyleSheet(
            "QPushButton {background:#172a40; color:#edf4ff;}"
            "QPushButton:hover {background:#1c314d;}"
        )
        self.cancel_button.setStyleSheet(
            "QPushButton {background:#22364d; color:#dce8f7; min-width:116px;}"
            "QPushButton:hover {background:#2a425d;}"
        )
        self.send_button.setStyleSheet(
            "QPushButton {background:#78f0d6; color:#07111f; min-width:132px;}"
            "QPushButton:hover {background:#8af5df;}"
        )

    def _apply_copy(self) -> None:
        self.copy = TEXT[self.language]
        self.setWindowTitle(self.copy["window_title"])
        self.brand_label.setText(self.copy["brand"])
        self.subtitle_label.setText(self.copy["subtitle"])
        self.description_label.setText(self.copy["description"])
        self.hero_badge.setText(self.copy["hero_badge"])
        self.hero_title.setText(self.copy["hero_title"])
        self.hero_body.setText(self.copy["hero_body"])
        self.metric_label.setText(self.copy["metric_label"])
        self.metric_note.setText(self.copy["metric_note"])
        self.model_title.setText(self.copy["model"])
        self.language_title.setText(self.copy["language"])
        self.new_chat_button.setText(self.copy["new_chat"])
        self.cancel_button.setText(self.copy["cancel"])
        self.send_button.setText(self.copy["send"])
        self.status_label.setText(self.copy["ready"])
        self.thinking_label.setText(self.copy["thinking"])
        self.input.setPlaceholderText(self.copy["placeholder"])

        current = self.language_combo.currentIndex()
        self.language_combo.blockSignals(True)
        self.language_combo.clear()
        self.language_combo.addItems(
            [self.copy["language_en"], self.copy["language_ru"]]
        )
        self.language_combo.setCurrentIndex(current if current in (0, 1) else 0)
        self.language_combo.blockSignals(False)

    def _render_empty(self) -> None:
        self.chat_list.clear()
        empty = EmptyState(
            self.copy["chat_empty_title"],
            self.copy["chat_empty_body"],
        )
        item = QListWidgetItem()
        item.setFlags(Qt.NoItemFlags)
        item.setSizeHint(empty.sizeHint())
        self.chat_list.addItem(item)
        self.chat_list.setItemWidget(item, empty)

    def _add_chat_bubble(self, author: str, body: str, is_user: bool) -> None:
        if self.chat_list.count() == 1:
            first = self.chat_list.item(0)
            widget = self.chat_list.itemWidget(first)
            if isinstance(widget, EmptyState):
                self.chat_list.clear()

        row = MessageRow(author, body, is_user)
        item = QListWidgetItem()
        item.setFlags(Qt.NoItemFlags)
        item.setSizeHint(row.sizeHint())
        self.chat_list.addItem(item)
        self.chat_list.setItemWidget(item, row)
        self._animate_row(row)
        self.chat_list.scrollToBottom()

    def _animate_row(self, row: QWidget) -> None:
        effect = QGraphicsOpacityEffect(row)
        effect.setOpacity(0.0)
        row.setGraphicsEffect(effect)

        animation = QPropertyAnimation(effect, b"opacity", row)
        animation.setDuration(220)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        self._animations.append(animation)

        def _cleanup() -> None:
            if animation in self._animations:
                self._animations.remove(animation)

        animation.finished.connect(_cleanup)
        animation.start()

    def _on_language_changed(self, index: int) -> None:
        self.language = "en" if index == 0 else "ru"
        self._apply_copy()

    def _on_model_changed(self, _model: str) -> None:
        self.status_label.setText(self.copy["status_model_changed"])

    def _reset_chat(self) -> None:
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self._render_empty()
        self.status_label.setText(self.copy["status_chat_cleared"])

    def _set_busy(self, value: bool) -> None:
        self.send_button.setEnabled(not value)
        self.model_combo.setEnabled(not value)
        self.language_combo.setEnabled(not value)
        self.new_chat_button.setEnabled(not value)
        self.cancel_button.setVisible(value)
        self.cancel_button.setEnabled(value)
        self.thinking_label.setVisible(value)
        self.send_button.setText(self.copy["send"])
        self.status_label.setText(self.copy["thinking"] if value else self.copy["ready"])

    def _send_message(self) -> None:
        if self.worker and self.worker.isRunning():
            return

        prompt = self.input.toPlainText().strip()
        if not prompt:
            self.status_label.setText(self.copy["status_empty"])
            return

        self.input.clear()
        self.request_cancelled = False
        self.messages.append({"role": "user", "content": prompt})
        self._add_chat_bubble(self.copy["user"], prompt, True)
        self._set_busy(True)

        self.worker = ChatWorker(
            model=self.model_combo.currentText(),
            messages=list(self.messages),
            language=self.language,
        )
        self.worker.finished_ok.connect(self._handle_success)
        self.worker.finished_error.connect(self._handle_error)
        self.worker.start()

    def _cancel_request(self) -> None:
        if not self.worker or not self.worker.isRunning():
            return
        self.request_cancelled = True
        if self.messages and self.messages[-1]["role"] == "user":
            self.messages.pop()
        self._set_busy(False)
        self.status_label.setText(self.copy["ready"])

    def _handle_success(self, answer: str) -> None:
        if self.request_cancelled:
            self.request_cancelled = False
            self._set_busy(False)
            return
        self.messages.append({"role": "assistant", "content": answer})
        self._add_chat_bubble(self.copy["assistant"], answer, False)
        self._set_busy(False)

    def _handle_error(self, message: str) -> None:
        if self.request_cancelled:
            self.request_cancelled = False
            self._set_busy(False)
            return
        if self.messages and self.messages[-1]["role"] == "user":
            self.messages.pop()
        self._add_chat_bubble(self.copy["assistant"], message, False)
        self._set_busy(False)


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("SevaAI")
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))

    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, QColor("#07111f"))
    palette.setColor(palette.ColorRole.WindowText, QColor("#edf4ff"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
