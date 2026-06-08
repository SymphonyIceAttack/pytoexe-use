#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Awaker Pocket - PyQt6 小而美重构版

功能：
- 番茄倒计时：开始 / 暂停 / 继续 / 重置 / 结束
- 双击时间数字快速设置倒计时
- +500 计数器：+500 / -500 / 重置
- 配置持久化：倒计时时长、计数、透明度、置顶、闪烁颜色
- 右键菜单：透明度、闪烁颜色、Windows 开机自启动、最小化、关闭
- 计时完成：提示、蜂鸣、按自定义颜色闪烁
- 长时间未操作提醒：默认 30 分钟后提醒

依赖：
    pip install PyQt6
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from PyQt6.QtCore import Qt, QEvent, QPoint, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QColorDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


APP_NAME = "Awaker"
DATA_FILE = Path.home() / "awaker_config.json"
STARTUP_BAT_NAME = "Awaker_Autostart.bat"

WINDOW_WIDTH = 248
WINDOW_HEIGHT = 392
STARTUP_RIGHT_MARGIN = 180
STARTUP_BOTTOM_MARGIN = 180

DEFAULT_TIMER_SECONDS = 5 * 60
DURATION_MAX_MINUTES = 1200
QUICK_TIMER_PRESETS = [
    ("3分", 3 * 60),
    ("5分", 5 * 60),
    ("10分", 10 * 60),
    ("25分", 25 * 60),
]

DURATION_DIALOG_IDLE_CLOSE_MS = 10_000
TOAST_AUTO_CLOSE_MS = 1800
TIMER_FINISHED_TOAST_MS = 10_000

ALARM_BEEP_COUNT = 3
ALARM_BEEP_GAP_MS = 650

TIMER_FINISHED_FLASH_DURATION_MS = 30_000
INACTIVITY_FIRST_REMINDER_SECONDS = 30 * 60
INACTIVITY_REPEAT_REMINDER_SECONDS = 5 * 60
INACTIVITY_FLASH_DURATION_MS = 30_000
FLASH_INTERVAL_MS = 500


COLORS = {
    "bg": "#F5F8FA",
    "shell": "#F8FAFC",
    "card": "#FFFFFF",
    "border": "#E2E8F0",
    "text": "#1F2A37",
    "muted": "#73808F",
    "soft": "#EEF5F2",
    "green": "#5FA978",
    "green_dark": "#4F9267",
    "blue": "#5E9ED6",
    "blue_soft": "#EAF4FF",
    "gold": "#B98A2E",
    "red": "#EF6A64",
    "red_soft": "#FFF1F2",
    "gray": "#6B7A86",
    "gray_soft": "#EEF2F4",
    "warning": "#D9A441",
}

FLASH_COLOR_PRESETS = [
    ("珊瑚红", "#EF6A64"),
    ("樱桃粉", "#EC4899"),
    ("琥珀橙", "#F59E0B"),
    ("薄荷绿", "#10B981"),
    ("海盐蓝", "#3B82F6"),
    ("紫藤紫", "#8B5CF6"),
]


def format_time(seconds: int) -> str:
    """中文注释：把秒数格式化为 MM:SS 的倒计时文本。"""
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def safe_int(value, default: int) -> int:
    """中文注释：安全地把配置值转换为整数，失败时返回默认值。"""
    try:
        return int(value)
    except Exception:
        return default


def normalize_hex_color(value: str | None, default: str = "#EF6A64") -> str:
    """中文注释：校验并规范化十六进制颜色值。"""
    value = str(value or "").strip()
    if not value.startswith("#"):
        value = "#" + value
    if len(value) != 7:
        return default
    try:
        int(value[1:], 16)
    except ValueError:
        return default
    return value.upper()


def mix_hex_color(color: str, target: str = "#FFFFFF", ratio: float = 0.85) -> str:
    """中文注释：把两个颜色按比例混合，用于生成柔和闪烁背景色。"""
    color = normalize_hex_color(color)
    target = normalize_hex_color(target, "#FFFFFF")
    ratio = max(0.0, min(1.0, float(ratio)))
    c = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
    t = tuple(int(target[i:i + 2], 16) for i in (1, 3, 5))
    mixed = tuple(round(c[i] * (1 - ratio) + t[i] * ratio) for i in range(3))
    return "#" + "".join(f"{v:02X}" for v in mixed)


def make_color_icon(color: str) -> QIcon:
    """中文注释：生成右键菜单中使用的颜色小图标。"""
    pixmap = QPixmap(16, 16)
    pixmap.fill(QColor(normalize_hex_color(color)))
    return QIcon(pixmap)


def load_config() -> dict:
    """中文注释：从用户目录读取 Awaker 的持久化配置。"""
    if not DATA_FILE.exists():
        return {}
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_config(data: dict) -> None:
    """中文注释：把当前设置写入配置文件，供下次启动恢复。"""
    try:
        DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def add_shadow(widget: QWidget, blur: int = 24, y: int = 8, alpha: int = 26) -> None:
    """中文注释：给控件添加柔和阴影，让卡片界面更精致。"""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, y)
    shadow.setColor(QColor(15, 23, 42, alpha))
    widget.setGraphicsEffect(shadow)


def repolish(widget: QWidget) -> None:
    """中文注释：刷新控件样式，使动态属性和颜色立即生效。"""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


class DoubleClickLabel(QLabel):
    double_clicked = pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        """中文注释：响应时间标签的双击事件，并发出自定义信号。"""
        self.double_clicked.emit()
        event.accept()


class Toast(QDialog):
    """主窗口旁边的小型提示 / 确认气泡。"""

    def __init__(
        self,
        parent: QWidget,
        title: str,
        message: str,
        kind: str = "info",
        duration_ms: int | None = TOAST_AUTO_CLOSE_MS,
        actions: list[tuple[str, callable | None, bool]] | None = None,
    ):
        """中文注释：初始化对象状态、窗口属性和界面控件。"""
        super().__init__(parent)
        self.actions = actions or []
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setObjectName("ToastWindow")

        accent = {
            "success": COLORS["green"],
            "warning": COLORS["warning"],
            "danger": COLORS["red"],
            "info": COLORS["blue"],
        }.get(kind, COLORS["blue"])
        icon = {
            "success": "✓",
            "warning": "!",
            "danger": "×",
            "info": "i",
        }.get(kind, "i")

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        card = QFrame()
        card.setObjectName("ToastCard")
        add_shadow(card, blur=28, y=8, alpha=38)
        root.addWidget(card)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        bar = QFrame()
        bar.setFixedWidth(4)
        bar.setStyleSheet(f"background:{accent}; border-top-left-radius:12px; border-bottom-left-radius:12px;")
        layout.addWidget(bar)

        body = QVBoxLayout()
        body.setContentsMargins(10, 8, 10, 8)
        body.setSpacing(5)
        layout.addLayout(body)

        header = QHBoxLayout()
        header.setSpacing(6)
        badge = QLabel(icon)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(18, 18)
        badge.setStyleSheet(
            f"background:{accent}; color:white; border-radius:9px; font-weight:800; font-size:11px;"
        )
        header.addWidget(badge)

        title_label = QLabel(title)
        title_label.setObjectName("ToastTitle")
        header.addWidget(title_label, stretch=1)

        close_btn = QPushButton("×")
        close_btn.setObjectName("TinyCloseButton")
        close_btn.setFixedSize(18, 18)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        body.addLayout(header)

        msg = QLabel(message)
        msg.setObjectName("ToastMessage")
        msg.setWordWrap(True)
        msg.setFixedWidth(180)
        body.addWidget(msg)

        if self.actions:
            row = QHBoxLayout()
            row.setContentsMargins(0, 5, 0, 0)
            row.addStretch()
            for text, callback, primary in self.actions:
                btn = QPushButton(text)
                btn.setObjectName("ToastPrimaryButton" if primary else "ToastGhostButton")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda _=False, cb=callback: self._run_action(cb))
                row.addWidget(btn)
            body.addLayout(row)
        elif duration_ms:
            QTimer.singleShot(duration_ms, self.close)

        self.setStyleSheet(APP_STYLE)
        self.adjustSize()
        self.place_near_parent()

    def _run_action(self, callback) -> None:
        """中文注释：关闭提示气泡并执行用户点击的确认动作。"""
        self.close()
        if callback:
            callback()

    def place_near_parent(self) -> None:
        """中文注释：把浮层窗口放在主窗口旁边并避免超出屏幕。"""
        parent = self.parentWidget()
        if not parent:
            return

        self.adjustSize()
        p = parent.frameGeometry()
        screen = parent.screen().availableGeometry() if parent.screen() else QApplication.primaryScreen().availableGeometry()
        gap = 8
        margin = 8
        w, h = self.width(), self.height()

        right_x = p.right() + gap
        left_x = p.left() - w - gap
        if right_x + w <= screen.right() - margin:
            x = right_x
        elif left_x >= screen.left() + margin:
            x = left_x
        else:
            x = max(screen.left() + margin, min(right_x, screen.right() - w - margin))

        y = p.top() + (p.height() - h) // 2
        y = max(screen.top() + margin, min(y, screen.bottom() - h - margin))
        self.move(x, y)


class DurationDialog(QDialog):
    applied = pyqtSignal(int)

    def __init__(self, parent: QWidget, current_seconds: int):
        """中文注释：初始化对象状态、窗口属性和界面控件。"""
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setObjectName("DurationWindow")

        self.idle_timer = QTimer(self)
        self.idle_timer.setSingleShot(True)
        self.idle_timer.timeout.connect(self.close)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        card = QFrame()
        card.setObjectName("DurationCard")
        add_shadow(card, blur=28, y=8, alpha=38)
        root.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(9)

        header = QHBoxLayout()
        title = QLabel("⏱ 快速设置")
        title.setObjectName("MiniTitle")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("×")
        close_btn.setObjectName("TinyCloseButton")
        close_btn.setFixedSize(18, 18)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        current_seconds = max(1, int(current_seconds))
        row = QHBoxLayout()
        row.setSpacing(6)
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, DURATION_MAX_MINUTES)
        self.minutes_spin.setValue(current_seconds // 60)
        self.minutes_spin.setFixedWidth(64)
        self.minutes_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self.minutes_spin)
        row.addWidget(QLabel("分"))

        self.seconds_spin = QSpinBox()
        self.seconds_spin.setRange(0, 59)
        self.seconds_spin.setValue(current_seconds % 60)
        self.seconds_spin.setFixedWidth(56)
        self.seconds_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self.seconds_spin)
        row.addWidget(QLabel("秒"))
        row.addStretch()
        layout.addLayout(row)

        presets = QHBoxLayout()
        presets.setSpacing(5)
        for text, seconds in QUICK_TIMER_PRESETS:
            btn = QPushButton(text)
            btn.setObjectName("PresetButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, s=seconds: self.apply_seconds(s))
            presets.addWidget(btn)
        layout.addLayout(presets)

        self.error_label = QLabel("")
        self.error_label.setObjectName("ErrorText")
        layout.addWidget(self.error_label)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("DialogGhostButton")
        cancel_btn.clicked.connect(self.close)
        buttons.addWidget(cancel_btn)

        apply_btn = QPushButton("应用")
        apply_btn.setObjectName("DialogPrimaryButton")
        apply_btn.clicked.connect(self.apply_from_inputs)
        buttons.addWidget(apply_btn)
        layout.addLayout(buttons)

        self.setStyleSheet(APP_STYLE)
        self.adjustSize()
        self.place_near_parent()

        for widget in [self, *self.findChildren(QWidget)]:
            widget.installEventFilter(self)
        self.restart_idle_timer()

    def showEvent(self, event) -> None:
        """中文注释：窗口显示后自动聚焦分钟输入框，方便快速输入。"""
        super().showEvent(event)
        self.minutes_spin.setFocus(Qt.FocusReason.PopupFocusReason)
        self.minutes_spin.selectAll()

    def eventFilter(self, obj, event) -> bool:
        """中文注释：监听浮层内操作并重置自动关闭计时。"""
        if event.type() in {
            QEvent.Type.KeyPress,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
            QEvent.Type.MouseMove,
            QEvent.Type.Wheel,
        }:
            self.restart_idle_timer()
        return super().eventFilter(obj, event)

    def restart_idle_timer(self) -> None:
        """中文注释：重新开始快速设置窗口的无操作自动关闭倒计时。"""
        self.idle_timer.start(DURATION_DIALOG_IDLE_CLOSE_MS)

    def place_near_parent(self) -> None:
        """中文注释：把浮层窗口放在主窗口旁边并避免超出屏幕。"""
        parent = self.parentWidget()
        if not parent:
            return
        p = parent.frameGeometry()
        screen = parent.screen().availableGeometry() if parent.screen() else QApplication.primaryScreen().availableGeometry()
        gap, margin = 8, 8
        w, h = self.width(), self.height()
        right_x = p.right() + gap
        left_x = p.left() - w - gap
        if right_x + w <= screen.right() - margin:
            x = right_x
        elif left_x >= screen.left() + margin:
            x = left_x
        else:
            x = max(screen.left() + margin, min(right_x, screen.right() - w - margin))
        y = p.top() + (p.height() - h) // 2
        y = max(screen.top() + margin, min(y, screen.bottom() - h - margin))
        self.move(x, y)

    def apply_from_inputs(self) -> None:
        """中文注释：读取分钟和秒数输入，校验后应用倒计时时长。"""
        total = self.minutes_spin.value() * 60 + self.seconds_spin.value()
        if total <= 0:
            self.error_label.setText("至少设置 1 秒")
            return
        self.apply_seconds(total)

    def apply_seconds(self, seconds: int) -> None:
        """中文注释：应用指定秒数并关闭快速设置窗口。"""
        self.applied.emit(max(1, int(seconds)))
        self.close()


class AwakerWindow(QWidget):
    def __init__(self):
        """中文注释：初始化对象状态、窗口属性和界面控件。"""
        super().__init__()
        self.config_data = load_config()

        self.default_total_seconds = self._load_total_seconds()
        self.total_seconds = self.default_total_seconds
        self.remaining_seconds = self.total_seconds
        self.counter = safe_int(self.config_data.get("amitabha_count", 0), 0)
        self.opacity = safe_int(self.config_data.get("opacity", 100), 100)
        self.is_topmost = bool(self.config_data.get("topmost", True))
        self.flash_color = normalize_hex_color(self.config_data.get("flash_color"), COLORS["red"])

        self.is_running = False
        self.is_paused = False
        self.flash_active = False
        self.flash_on = False
        self.current_flash_reason = None
        self._closing_now = False
        self._drag_pos: QPoint | None = None
        self.last_key_action_time = time.monotonic()
        self.next_inactivity_time = self.last_key_action_time + INACTIVITY_FIRST_REMINDER_SECONDS

        self.setWindowTitle(APP_NAME)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowOpacity(max(0.1, min(1.0, self.opacity / 100)))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.apply_window_flags()

        self.countdown_timer = QTimer(self)
        self.countdown_timer.setInterval(1000)
        self.countdown_timer.timeout.connect(self.tick)

        self.flash_timer = QTimer(self)
        self.flash_timer.setInterval(FLASH_INTERVAL_MS)
        self.flash_timer.timeout.connect(self.toggle_flash_color)

        self.flash_stop_timer = QTimer(self)
        self.flash_stop_timer.setSingleShot(True)
        self.flash_stop_timer.timeout.connect(self.stop_flash)

        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setInterval(1000)
        self.inactivity_timer.timeout.connect(self.check_inactivity)
        self.inactivity_timer.start()

        self.build_ui()
        self.apply_style()
        self.move_to_startup_position()

    def _load_total_seconds(self) -> int:
        """中文注释：读取倒计时时长，并兼容旧版配置字段。"""
        if "pomodoro_total_seconds" in self.config_data:
            return max(1, safe_int(self.config_data.get("pomodoro_total_seconds"), DEFAULT_TIMER_SECONDS))
        minutes = safe_int(self.config_data.get("pomodoro_minutes", DEFAULT_TIMER_SECONDS // 60), DEFAULT_TIMER_SECONDS // 60)
        seconds = safe_int(self.config_data.get("pomodoro_seconds", DEFAULT_TIMER_SECONDS % 60), DEFAULT_TIMER_SECONDS % 60)
        return max(1, minutes * 60 + seconds)

    def build_ui(self) -> None:
        """中文注释：构建主窗口的小巧卡片式界面布局。"""
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(0)

        self.shell = QFrame()
        self.shell.setObjectName("Shell")
        add_shadow(self.shell, blur=32, y=10, alpha=34)
        root.addWidget(self.shell)

        shell_layout = QVBoxLayout(self.shell)
        shell_layout.setContentsMargins(10, 10, 10, 10)
        shell_layout.setSpacing(9)

        self.header = QFrame()
        self.header.setObjectName("Header")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(4, 0, 0, 0)
        header_layout.setSpacing(4)

        self.title_label = QLabel("Awaker")
        self.title_label.setObjectName("AppTitle")
        header_layout.addWidget(self.title_label, stretch=1)

        self.pin_btn = self.make_icon_button("📌" if self.is_topmost else "📍", "IconPin")
        self.pin_btn.clicked.connect(self.toggle_topmost)
        header_layout.addWidget(self.pin_btn)

        self.stop_btn = self.make_icon_button("🛑", "IconDanger")
        self.stop_btn.setToolTip("结束当前计时")
        self.stop_btn.clicked.connect(self.stop_timer)
        header_layout.addWidget(self.stop_btn)

        self.setting_btn = self.make_icon_button("⚙", "IconNormal")
        self.setting_btn.setToolTip("快速设置倒计时")
        self.setting_btn.clicked.connect(self.open_duration_dialog)
        header_layout.addWidget(self.setting_btn)

        self.minimize_btn = self.make_icon_button("−", "IconMinimize")
        self.minimize_btn.setToolTip("最小化")
        self.minimize_btn.clicked.connect(self.minimize_window)
        header_layout.addWidget(self.minimize_btn)

        self.close_btn = self.make_icon_button("×", "IconClose")
        self.close_btn.clicked.connect(self.request_close)
        header_layout.addWidget(self.close_btn)

        shell_layout.addWidget(self.header)

        self.timer_card = self.make_card()
        timer_layout = QVBoxLayout(self.timer_card)
        timer_layout.setContentsMargins(12, 10, 12, 10)
        timer_layout.setSpacing(4)

        timer_top = QHBoxLayout()
        timer_title = QLabel("🍅 番茄倒计时")
        timer_title.setObjectName("CardTitle")
        timer_top.addWidget(timer_title)
        timer_top.addStretch()
        hint = QLabel("双击设置")
        hint.setObjectName("TinyHint")
        timer_top.addWidget(hint)
        timer_layout.addLayout(timer_top)

        self.time_label = DoubleClickLabel(format_time(self.remaining_seconds))
        self.time_label.setObjectName("TimerText")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.time_label.double_clicked.connect(self.on_time_double_clicked)
        timer_layout.addWidget(self.time_label)

        self.status_label = QLabel("准备开始")
        self.status_label.setObjectName("StatusText")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.addWidget(self.status_label)

        timer_buttons = QHBoxLayout()
        timer_buttons.setSpacing(8)
        self.start_btn = self.make_action_button("▶ 开始", "SuccessButton")
        self.start_btn.clicked.connect(self.toggle_timer)
        timer_buttons.addWidget(self.start_btn)

        self.reset_btn = self.make_action_button("↺ 重置", "DarkButton")
        self.reset_btn.clicked.connect(self.request_reset_timer)
        timer_buttons.addWidget(self.reset_btn)
        timer_layout.addLayout(timer_buttons)

        shell_layout.addWidget(self.timer_card)

        self.counter_card = self.make_card()
        counter_layout = QVBoxLayout(self.counter_card)
        counter_layout.setContentsMargins(12, 10, 12, 10)
        counter_layout.setSpacing(4)

        counter_top = QHBoxLayout()
        counter_title = QLabel("🌷 +500 计数")
        counter_title.setObjectName("CardTitle")
        counter_top.addWidget(counter_title)
        counter_top.addStretch()
        self.counter_reset_btn = self.make_icon_button("↻", "IconSuccess")
        self.counter_reset_btn.clicked.connect(self.confirm_reset_counter)
        counter_top.addWidget(self.counter_reset_btn)
        counter_layout.addLayout(counter_top)

        self.counter_label = QLabel(str(self.counter))
        self.counter_label.setObjectName("CounterText")
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        counter_layout.addWidget(self.counter_label)

        self.unit_label = QLabel("单位：500")
        self.unit_label.setObjectName("StatusText")
        self.unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        counter_layout.addWidget(self.unit_label)

        counter_buttons = QHBoxLayout()
        counter_buttons.setSpacing(8)
        self.minus_btn = self.make_action_button("−500", "SoftButton")
        self.minus_btn.clicked.connect(self.decrease_counter)
        counter_buttons.addWidget(self.minus_btn)

        self.plus_btn = self.make_action_button("+500", "SuccessButton")
        self.plus_btn.clicked.connect(self.increase_counter)
        counter_buttons.addWidget(self.plus_btn)
        counter_layout.addLayout(counter_buttons)

        shell_layout.addWidget(self.counter_card)

        self.footer = QLabel("右键：透明度 / 闪烁颜色 / 自启动 / 最小化 / 关闭")
        self.footer.setObjectName("FooterText")
        self.footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shell_layout.addWidget(self.footer)

    def make_card(self) -> QFrame:
        """中文注释：创建统一样式的白色卡片容器。"""
        card = QFrame()
        card.setObjectName("Card")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return card

    def make_icon_button(self, text: str, name: str) -> QPushButton:
        """中文注释：创建顶部或卡片内使用的小图标按钮。"""
        btn = QPushButton(text)
        btn.setObjectName(name)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(23, 23)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return btn

    def make_action_button(self, text: str, name: str) -> QPushButton:
        """中文注释：创建主要操作按钮，例如开始、重置、加减计数。"""
        btn = QPushButton(text)
        btn.setObjectName(name)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(30)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return btn

    def apply_style(self) -> None:
        """中文注释：把动态样式表应用到当前主窗口。"""
        self.setStyleSheet(build_app_style(self.flash_color))

    def apply_window_flags(self) -> None:
        """中文注释：根据置顶状态设置无边框窗口标志。"""
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        if self.is_topmost:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def move_to_startup_position(self) -> None:
        """中文注释：把窗口移动到屏幕右下角附近的默认位置。"""
        screen = QApplication.primaryScreen().availableGeometry()
        x = max(screen.left(), screen.right() - WINDOW_WIDTH - STARTUP_RIGHT_MARGIN)
        y = max(screen.top(), screen.bottom() - WINDOW_HEIGHT - STARTUP_BOTTOM_MARGIN)
        self.move(x, y)

    def request_close(self) -> None:
        """中文注释：关闭前弹出确认气泡，避免误关闭。"""
        Toast(
            self,
            "确认关闭",
            "确定要关闭 Awaker 吗？",
            kind="warning",
            actions=[
                ("取消", None, False),
                ("关闭", self.close_now, True),
            ],
        ).show()

    def close_now(self) -> None:
        """中文注释：确认关闭后保存配置并关闭窗口。"""
        self._closing_now = True
        self.save_current_config()
        self.close()

    def minimize_window(self) -> None:
        """中文注释：保存当前配置并最小化窗口。"""
        self.save_current_config()
        self.showMinimized()

    def closeEvent(self, event) -> None:
        """中文注释：拦截系统关闭事件，统一走关闭确认流程。"""
        if self._closing_now:
            self.save_current_config()
            event.accept()
        else:
            event.ignore()
            self.request_close()

    def mousePressEvent(self, event) -> None:
        """中文注释：处理鼠标按下事件，用于停止闪烁和准备拖动窗口。"""
        if self.flash_active:
            self.stop_flash()
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """中文注释：处理鼠标移动事件，实现无边框窗口拖动。"""
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """中文注释：鼠标释放时结束窗口拖动状态。"""
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:
        """中文注释：构建右键菜单，提供透明度、闪烁颜色、自启动、最小化和关闭。"""
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)

        opacity_menu = menu.addMenu("透明度")
        for value in [100, 90, 80, 70, 60, 50, 40, 30, 20]:
            label = f"{value}%" + ("  ✓" if self.opacity == value else "")
            action = QAction(label, self)
            action.triggered.connect(lambda _=False, v=value: self.set_opacity(v))
            opacity_menu.addAction(action)

        flash_menu = menu.addMenu("闪烁颜色")
        for name, color in FLASH_COLOR_PRESETS:
            label = f"{name}" + ("  ✓" if normalize_hex_color(color) == self.flash_color else "")
            action = QAction(make_color_icon(color), label, self)
            action.triggered.connect(lambda _=False, c=color, n=name: self.set_flash_color(c, n))
            flash_menu.addAction(action)
        flash_menu.addSeparator()
        custom_action = QAction(make_color_icon(self.flash_color), "自定义颜色…", self)
        custom_action.triggered.connect(self.choose_flash_color)
        flash_menu.addAction(custom_action)

        menu.addSeparator()
        if self.is_autostart_supported():
            autostart_text = "取消开机自启动" if self.is_autostart_enabled() else "开启开机自启动"
        else:
            autostart_text = "开机自启动（仅 Windows）"
        autostart_action = QAction(autostart_text, self)
        autostart_action.triggered.connect(self.toggle_autostart)
        menu.addAction(autostart_action)

        menu.addSeparator()
        minimize_action = QAction("最小化", self)
        minimize_action.triggered.connect(self.minimize_window)
        menu.addAction(minimize_action)

        close_action = QAction("关闭", self)
        close_action.triggered.connect(self.request_close)
        menu.addAction(close_action)
        menu.exec(event.globalPos())

    def save_current_config(self) -> None:
        """中文注释：保存当前倒计时、计数、透明度、置顶和闪烁颜色。"""
        save_config(
            {
                "pomodoro_total_seconds": self.default_total_seconds,
                "pomodoro_minutes": self.default_total_seconds // 60,
                "pomodoro_seconds": self.default_total_seconds % 60,
                "amitabha_count": self.counter,
                "opacity": self.opacity,
                "topmost": self.is_topmost,
                "flash_color": self.flash_color,
                "last_active_tab": 0,
            }
        )

    def show_toast(self, title: str, message: str, kind: str = "info", duration_ms: int = TOAST_AUTO_CLOSE_MS) -> None:
        """中文注释：显示精美的小型提示气泡。"""
        Toast(self, title, message, kind=kind, duration_ms=duration_ms).show()

    def mark_key_action(self) -> None:
        """中文注释：记录关键操作时间，并重置长时间未操作提醒。"""
        self.last_key_action_time = time.monotonic()
        self.next_inactivity_time = self.last_key_action_time + INACTIVITY_FIRST_REMINDER_SECONDS
        if self.flash_active:
            self.stop_flash()

    def update_time_display(self) -> None:
        """中文注释：刷新倒计时文本，并根据剩余时间切换警示颜色。"""
        self.time_label.setText(format_time(self.remaining_seconds))
        if self.remaining_seconds <= 60 and self.is_running:
            self.time_label.setProperty("danger", True)
        elif self.remaining_seconds <= 5 * 60 and self.is_running:
            self.time_label.setProperty("warning", True)
            self.time_label.setProperty("danger", False)
        else:
            self.time_label.setProperty("warning", False)
            self.time_label.setProperty("danger", False)
        repolish(self.time_label)

    def toggle_timer(self) -> None:
        """中文注释：在开始、暂停和继续之间切换倒计时状态。"""
        self.mark_key_action()
        if not self.is_running:
            if self.remaining_seconds <= 0:
                self.remaining_seconds = self.total_seconds
                self.update_time_display()
            self.start_timer()
        elif self.is_paused:
            self.resume_timer()
        else:
            self.pause_timer()

    def start_timer(self) -> None:
        """中文注释：启动倒计时并更新按钮与状态提示。"""
        self.is_running = True
        self.is_paused = False
        self.status_label.setText("计时中…")
        self.status_label.setProperty("state", "success")
        self.start_btn.setText("⏸ 暂停")
        self.start_btn.setObjectName("WarningButton")
        repolish(self.status_label)
        repolish(self.start_btn)
        self.countdown_timer.start()

    def pause_timer(self) -> None:
        """中文注释：暂停当前倒计时。"""
        self.is_paused = True
        self.status_label.setText("已暂停")
        self.status_label.setProperty("state", "warning")
        self.start_btn.setText("▶ 继续")
        self.start_btn.setObjectName("SuccessButton")
        repolish(self.status_label)
        repolish(self.start_btn)

    def resume_timer(self) -> None:
        """中文注释：继续已经暂停的倒计时。"""
        self.is_paused = False
        self.status_label.setText("计时中…")
        self.status_label.setProperty("state", "success")
        self.start_btn.setText("⏸ 暂停")
        self.start_btn.setObjectName("WarningButton")
        repolish(self.status_label)
        repolish(self.start_btn)

    def tick(self) -> None:
        """中文注释：每秒扣减倒计时时间，并在归零时触发完成逻辑。"""
        if not self.is_running or self.is_paused:
            return
        self.remaining_seconds -= 1
        self.update_time_display()
        if self.remaining_seconds <= 0:
            self.timer_finished()

    def timer_finished(self) -> None:
        """中文注释：处理倒计时完成后的提示、蜂鸣和闪烁提醒。"""
        self.countdown_timer.stop()
        self.is_running = False
        self.is_paused = False
        self.remaining_seconds = 0
        self.update_time_display()
        self.status_label.setText("时间到！")
        self.status_label.setProperty("state", "danger")
        self.start_btn.setText("▶ 开始")
        self.start_btn.setObjectName("SuccessButton")
        repolish(self.status_label)
        repolish(self.start_btn)
        self.save_current_config()

        self.show_toast("计时完成", "倒计时已完成。点击窗口可停止闪烁，并恢复到设定时长。", "success", TIMER_FINISHED_TOAST_MS)
        self.play_beeps()
        QTimer.singleShot(250, lambda: self.start_flash("timer_finished", TIMER_FINISHED_FLASH_DURATION_MS))

    def play_beeps(self) -> None:
        """中文注释：播放系统提示音作为倒计时完成提醒。"""
        for index in range(ALARM_BEEP_COUNT):
            QTimer.singleShot(index * ALARM_BEEP_GAP_MS, QApplication.beep)

    def request_reset_timer(self) -> None:
        """中文注释：重置倒计时前弹出确认气泡。"""
        Toast(
            self,
            "确认重置",
            "确定要重置当前倒计时吗？",
            kind="warning",
            actions=[
                ("取消", None, False),
                ("重置", self.reset_timer, True),
            ],
        ).show()

    def reset_timer(self) -> None:
        """中文注释：确认后重置倒计时到当前设定时长。"""
        self.countdown_timer.stop()
        self.is_running = False
        self.is_paused = False
        self.remaining_seconds = self.total_seconds
        self.update_time_display()
        self.status_label.setText("准备开始")
        self.status_label.setProperty("state", "normal")
        self.start_btn.setText("▶ 开始")
        self.start_btn.setObjectName("SuccessButton")
        repolish(self.status_label)
        repolish(self.start_btn)
        self.stop_flash()

    def stop_timer(self) -> None:
        """中文注释：请求结束当前倒计时，运行中才弹出确认。"""
        if not self.is_running:
            self.show_toast("没有运行中的计时", "当前没有需要结束的倒计时。", "info")
            return
        Toast(
            self,
            "结束计时",
            "确定要结束当前倒计时吗？",
            kind="warning",
            actions=[
                ("继续", None, False),
                ("结束", self.stop_timer_confirmed, True),
            ],
        ).show()

    def stop_timer_confirmed(self) -> None:
        """中文注释：确认后停止倒计时并恢复到初始状态。"""
        self.countdown_timer.stop()
        self.is_running = False
        self.is_paused = False
        self.remaining_seconds = self.total_seconds
        self.update_time_display()
        self.status_label.setText("已结束")
        self.status_label.setProperty("state", "normal")
        self.start_btn.setText("▶ 开始")
        self.start_btn.setObjectName("SuccessButton")
        repolish(self.status_label)
        repolish(self.start_btn)
        self.stop_flash()
        self.show_toast("已结束", "当前计时已停止。", "info")

    def on_time_double_clicked(self) -> None:
        """中文注释：双击时间数字时停止闪烁或打开快速设置窗口。"""
        if self.flash_active:
            self.stop_flash()
            return
        self.open_duration_dialog()

    def open_duration_dialog(self) -> None:
        """中文注释：打开快速倒计时设置浮层。"""
        dialog = DurationDialog(self, self.total_seconds)
        dialog.applied.connect(self.apply_duration)
        dialog.show()

    def apply_duration(self, seconds: int) -> None:
        """中文注释：应用新的倒计时时长并保存配置。"""
        self.countdown_timer.stop()
        self.default_total_seconds = max(1, int(seconds))
        self.total_seconds = self.default_total_seconds
        self.remaining_seconds = self.total_seconds
        self.is_running = False
        self.is_paused = False
        self.update_time_display()
        self.status_label.setText(f"已设置 {format_time(seconds)}")
        self.status_label.setProperty("state", "normal")
        self.start_btn.setText("▶ 开始")
        self.start_btn.setObjectName("SuccessButton")
        repolish(self.status_label)
        repolish(self.start_btn)
        self.stop_flash()
        self.save_current_config()
        self.show_toast("已设置", f"倒计时已设为 {format_time(seconds)}。", "success")

    def increase_counter(self) -> None:
        """中文注释：把 +500 计数器增加 500 并保存。"""
        self.mark_key_action()
        self.counter += 500
        self.counter_label.setText(str(self.counter))
        self.save_current_config()

    def decrease_counter(self) -> None:
        """中文注释：把 +500 计数器减少 500 并保存。"""
        self.counter -= 500
        self.counter_label.setText(str(self.counter))
        self.save_current_config()

    def confirm_reset_counter(self) -> None:
        """中文注释：重置 +500 计数器前弹出确认气泡。"""
        Toast(
            self,
            "确认重置",
            "确定要把 +500 计数器重置为 0 吗？",
            kind="warning",
            actions=[
                ("取消", None, False),
                ("重置", self.reset_counter, True),
            ],
        ).show()

    def reset_counter(self) -> None:
        """中文注释：确认后把 +500 计数器清零。"""
        self.counter = 0
        self.counter_label.setText(str(self.counter))
        self.save_current_config()
        self.show_toast("已重置", "+500 计数器已归零。", "success")

    def check_inactivity(self) -> None:
        """中文注释：定时检查是否长时间未操作，并触发提醒闪烁。"""
        if self.is_running or self.flash_active:
            return
        if time.monotonic() < self.next_inactivity_time:
            return

        self.show_toast("休息提醒", "已经较久没有点击“开始”或“+500”。", "warning", 3200)
        self.start_flash("inactivity", INACTIVITY_FLASH_DURATION_MS)
        self.next_inactivity_time = time.monotonic() + INACTIVITY_REPEAT_REMINDER_SECONDS

    def start_flash(self, reason: str, duration_ms: int) -> None:
        """中文注释：按当前记忆的闪烁颜色启动窗口闪烁。"""
        self.flash_active = True
        self.flash_on = False
        self.current_flash_reason = reason
        self.flash_timer.start()
        self.flash_stop_timer.start(duration_ms)
        self.raise_window_temporarily()

    def toggle_flash_color(self) -> None:
        """中文注释：在正常样式和闪烁样式之间切换。"""
        if not self.flash_active:
            return
        self.flash_on = not self.flash_on
        for widget in [self.shell, self.timer_card, self.counter_card]:
            widget.setProperty("flash", self.flash_on)
            repolish(widget)

    def stop_flash(self, restore_finished_timer: bool = True) -> None:
        """中文注释：停止闪烁并恢复正常窗口样式；如果是倒计时完成后的闪烁，则恢复倒计时时长。"""
        flash_reason = self.current_flash_reason
        self.flash_active = False
        self.flash_on = False
        self.flash_timer.stop()
        self.flash_stop_timer.stop()
        self.current_flash_reason = None
        for widget in [getattr(self, "shell", None), getattr(self, "timer_card", None), getattr(self, "counter_card", None)]:
            if widget:
                widget.setProperty("flash", False)
                repolish(widget)

        if restore_finished_timer and flash_reason == "timer_finished":
            self.restore_timer_after_finished_flash()

    def restore_timer_after_finished_flash(self) -> None:
        """中文注释：倒计时完成后停止闪烁时，把时间显示恢复到本轮设定的时长。"""
        self.countdown_timer.stop()
        self.is_running = False
        self.is_paused = False
        self.remaining_seconds = self.total_seconds
        self.update_time_display()
        self.status_label.setText("准备开始")
        self.status_label.setProperty("state", "normal")
        self.start_btn.setText("▶ 开始")
        self.start_btn.setObjectName("SuccessButton")
        repolish(self.status_label)
        repolish(self.start_btn)

    def raise_window_temporarily(self) -> None:
        """中文注释：提醒时临时抬起窗口，便于用户看到。"""
        self.showNormal()
        self.raise_()
        self.activateWindow()
        old_topmost = self.is_topmost
        if not old_topmost:
            self.is_topmost = True
            self.apply_window_flags()
            self.show()
            QTimer.singleShot(700, lambda: self.restore_topmost_after_raise(old_topmost))

    def restore_topmost_after_raise(self, old_topmost: bool) -> None:
        """中文注释：提醒抬窗后恢复原来的置顶状态。"""
        self.is_topmost = old_topmost
        self.apply_window_flags()
        self.show()

    def toggle_topmost(self) -> None:
        """中文注释：切换窗口置顶状态并保存。"""
        self.is_topmost = not self.is_topmost
        self.pin_btn.setText("📌" if self.is_topmost else "📍")
        self.apply_window_flags()
        self.show()
        self.save_current_config()
        self.show_toast("置顶已开启" if self.is_topmost else "置顶已关闭", "窗口置顶状态已更新。", "info")

    def set_opacity(self, value: int) -> None:
        """中文注释：设置窗口透明度并写入配置。"""
        self.opacity = int(value)
        self.setWindowOpacity(max(0.1, min(1.0, self.opacity / 100)))
        self.save_current_config()

    def set_flash_color(self, color: str, name: str | None = None) -> None:
        """中文注释：设置窗体闪烁颜色、刷新界面并写入配置。"""
        self.flash_color = normalize_hex_color(color, COLORS["red"])
        self.apply_style()
        self.save_current_config()
        label = name or self.flash_color
        self.show_toast("闪烁颜色已更新", f"当前闪烁颜色：{label}", "success")

    def choose_flash_color(self) -> None:
        """中文注释：打开系统颜色选择器，自定义窗体闪烁颜色。"""
        selected = QColorDialog.getColor(QColor(self.flash_color), self, "选择窗体闪烁颜色")
        if selected.isValid():
            self.set_flash_color(selected.name().upper(), "自定义")

    def is_autostart_supported(self) -> bool:
        """中文注释：判断当前系统是否支持启动文件夹自启动。"""
        return sys.platform.startswith("win")

    def get_startup_bat_path(self) -> Path | None:
        """中文注释：获取 Windows 启动文件夹内的自启动脚本路径。"""
        appdata = os.environ.get("APPDATA")
        if not appdata:
            return None
        startup = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        return startup / STARTUP_BAT_NAME

    def is_autostart_enabled(self) -> bool:
        """中文注释：检查自启动脚本是否已经存在。"""
        path = self.get_startup_bat_path()
        return bool(path and path.exists())

    def get_pythonw_path(self) -> str:
        """中文注释：优先寻找 pythonw.exe，避免自启动出现控制台窗口。"""
        exe = Path(sys.executable)
        if exe.name.lower() == "python.exe":
            pythonw = exe.with_name("pythonw.exe")
            if pythonw.exists():
                return str(pythonw)
        return str(exe)

    def write_autostart_bat(self, bat_path: Path) -> None:
        """中文注释：写入 Windows 开机自启动 bat 脚本。"""
        bat_path.parent.mkdir(parents=True, exist_ok=True)
        if getattr(sys, "frozen", False):
            target_path = Path(sys.executable).resolve()
            work_dir = target_path.parent
            content = f'@echo off\ncd /d "{work_dir}"\nstart "" "{target_path}"\n'
        else:
            script_path = Path(__file__).resolve()
            work_dir = script_path.parent
            python_path = self.get_pythonw_path()
            content = f'@echo off\ncd /d "{work_dir}"\nstart "" "{python_path}" "{script_path}"\n'
        bat_path.write_text(content, encoding="utf-8")

    def toggle_autostart(self) -> None:
        """中文注释：开启或关闭 Windows 开机自启动。"""
        if not self.is_autostart_supported():
            self.show_toast("暂不支持", "当前开机自启动仅支持 Windows。", "warning")
            return
        path = self.get_startup_bat_path()
        if not path:
            self.show_toast("开启失败", "没有找到 Windows 启动文件夹路径。", "danger")
            return
        try:
            if self.is_autostart_enabled():
                path.unlink(missing_ok=True)
                self.show_toast("已关闭自启动", "Awaker 不会再随系统启动。", "info")
            else:
                self.write_autostart_bat(path)
                self.show_toast("已开启自启动", "Awaker 将随 Windows 自动启动。", "success")
        except Exception as exc:
            self.show_toast("操作失败", f"自启动设置失败：{exc}", "danger", 3600)


def build_app_style(flash_color: str | None = None) -> str:
    """中文注释：根据当前闪烁颜色动态生成应用样式表。"""
    flash_color = normalize_hex_color(flash_color, COLORS["red"])
    flash_shell = mix_hex_color(flash_color, "#FFFFFF", 0.86)
    flash_card = mix_hex_color(flash_color, "#FFFFFF", 0.93)
    flash_border = mix_hex_color(flash_color, "#FFFFFF", 0.42)
    return f"""
QWidget {{
    font-family: "Microsoft YaHei UI", "Segoe UI", Arial;
    color: {COLORS['text']};
    font-size: 12px;
}}

QFrame#Shell {{
    background: {COLORS['shell']};
    border: 1px solid rgba(226, 232, 240, 210);
    border-radius: 20px;
}}
QFrame#Shell[flash="true"] {{
    background: {flash_shell};
    border: 1px solid {flash_border};
}}

QFrame#Header {{
    background: transparent;
}}

QFrame#Card {{
    background: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 16px;
}}
QFrame#Card[flash="true"] {{
    background: {flash_card};
    border: 1px solid {flash_border};
}}

QLabel#AppTitle {{
    color: {COLORS['text']};
    font-size: 15px;
    font-weight: 800;
}}

QLabel#CardTitle {{
    color: {COLORS['muted']};
    font-size: 12px;
    font-weight: 800;
}}

QLabel#TinyHint,
QLabel#FooterText {{
    color: #9AA6B2;
    font-size: 10px;
}}

QLabel#TimerText {{
    color: {COLORS['text']};
    font-size: 36px;
    font-weight: 900;
    letter-spacing: 1px;
}}
QLabel#TimerText[warning="true"] {{
    color: {COLORS['warning']};
}}
QLabel#TimerText[danger="true"] {{
    color: {COLORS['red']};
}}

QLabel#CounterText {{
    color: {COLORS['gold']};
    font-size: 34px;
    font-weight: 900;
}}

QLabel#StatusText {{
    color: {COLORS['muted']};
    font-size: 11px;
}}
QLabel#StatusText[state="success"] {{
    color: {COLORS['green']};
    font-weight: 700;
}}
QLabel#StatusText[state="warning"] {{
    color: {COLORS['warning']};
    font-weight: 700;
}}
QLabel#StatusText[state="danger"] {{
    color: {COLORS['red']};
    font-weight: 700;
}}

QPushButton {{
    border: none;
    border-radius: 10px;
    padding: 4px 8px;
    font-weight: 800;
}}
QPushButton:pressed {{
    padding-top: 5px;
    padding-left: 9px;
}}

QPushButton#SuccessButton {{
    background: {COLORS['green']};
    color: white;
}}
QPushButton#SuccessButton:hover {{
    background: {COLORS['green_dark']};
}}

QPushButton#WarningButton {{
    background: {COLORS['warning']};
    color: white;
}}
QPushButton#WarningButton:hover {{
    background: #C9902F;
}}

QPushButton#DarkButton {{
    background: {COLORS['gray']};
    color: white;
}}
QPushButton#DarkButton:hover {{
    background: #53636F;
}}

QPushButton#SoftButton {{
    background: {COLORS['gray_soft']};
    color: {COLORS['text']};
}}
QPushButton#SoftButton:hover {{
    background: #DDE6EA;
}}

QPushButton#IconNormal,
QPushButton#IconPin,
QPushButton#IconDanger,
QPushButton#IconSuccess,
QPushButton#IconClose,
QPushButton#IconMinimize,
QPushButton#TinyCloseButton {{
    background: transparent;
    border-radius: 8px;
    padding: 0;
    font-size: 13px;
}}
QPushButton#IconNormal:hover,
QPushButton#IconPin:hover,
QPushButton#IconSuccess:hover,
QPushButton#IconDanger:hover,
QPushButton#IconMinimize:hover {{
    background: {COLORS['blue_soft']};
}}
QPushButton#IconPin {{ color: {COLORS['red']}; }}
QPushButton#IconDanger {{ color: {COLORS['red']}; }}
QPushButton#IconSuccess {{ color: {COLORS['green']}; }}
QPushButton#IconMinimize {{ color: #98A4AE; font-size: 16px; }}
QPushButton#IconClose {{ color: #98A4AE; font-size: 15px; }}
QPushButton#IconClose:hover,
QPushButton#TinyCloseButton:hover {{
    background: {COLORS['red_soft']};
    color: {COLORS['red']};
}}

QFrame#ToastCard,
QFrame#DurationCard {{
    background: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 14px;
}}

QLabel#ToastTitle,
QLabel#MiniTitle {{
    color: {COLORS['text']};
    font-weight: 800;
    font-size: 12px;
}}
QLabel#ToastMessage {{
    color: {COLORS['muted']};
    font-size: 11px;
}}
QLabel#ErrorText {{
    color: {COLORS['red']};
    font-size: 10px;
}}

QPushButton#ToastPrimaryButton,
QPushButton#DialogPrimaryButton {{
    background: {COLORS['blue']};
    color: white;
    min-width: 46px;
    min-height: 22px;
    border-radius: 8px;
    font-size: 11px;
}}
QPushButton#ToastPrimaryButton:hover,
QPushButton#DialogPrimaryButton:hover {{
    background: #4C8EC8;
}}
QPushButton#ToastGhostButton,
QPushButton#DialogGhostButton {{
    background: {COLORS['gray_soft']};
    color: {COLORS['text']};
    min-width: 46px;
    min-height: 22px;
    border-radius: 8px;
    font-size: 11px;
}}
QPushButton#PresetButton {{
    background: {COLORS['blue_soft']};
    color: #3A6F9E;
    min-height: 24px;
    border-radius: 8px;
    font-size: 11px;
}}
QPushButton#PresetButton:hover {{
    background: #DBEAFE;
}}

QSpinBox {{
    background: #F8FAFC;
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 3px 5px;
    min-height: 24px;
}}
QSpinBox:focus {{
    border: 1px solid {COLORS['blue']};
    background: white;
}}
"""


APP_STYLE = build_app_style(COLORS["red"])
MENU_STYLE = f"""
QMenu {{
    background: white;
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    padding: 6px;
    font-family: "Microsoft YaHei UI";
    font-size: 12px;
}}
QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: 7px;
}}
QMenu::item:selected {{
    background: {COLORS['blue_soft']};
    color: {COLORS['text']};
}}
QMenu::separator {{
    height: 1px;
    background: {COLORS['border']};
    margin: 5px 4px;
}}
"""


def main() -> None:
    """中文注释：创建 QApplication 并启动主窗口事件循环。"""
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei UI", 9))
    window = AwakerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
