import sys
import os
import stat
import re
import socket
import subprocess
import base64
import tempfile
import json
import time
import threading

import paramiko

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox, QTabWidget,
    QTextEdit, QTreeWidget, QTreeWidgetItem, QProgressBar, QDialog, QMessageBox,
    QFileDialog, QInputDialog, QSplitter, QHeaderView, QSizePolicy, QToolButton,
    QScrollArea, QDialogButtonBox, QListWidget, QListWidgetItem, QMenu, QTabBar,
    QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QSize
from PyQt6.QtGui import QColor, QFont, QTextCursor, QTextCharFormat, QShortcut, QKeySequence, QAction


# ---------------------------------------------------------------------------
# ANSI / رنگ‌های ترمینال
# ---------------------------------------------------------------------------
FG_COLORS = {
    '30': '#4d4d4d', '31': '#ff5c5c', '32': '#55ff88', '33': '#ffd75f',
    '34': '#5fafff', '35': '#ff87d7', '36': '#5fd7d7', '37': '#e6e6e6',
    '90': '#808080', '91': '#ff8080', '92': '#8aff8a', '93': '#ffe680',
    '94': '#8ac6ff', '95': '#ffb3ea', '96': '#8ae8e8', '97': '#ffffff',
}

TAG_COLORS = {
    "msg_ok": "#3ddc97",
    "msg_err": "#ff5c5c",
    "msg_info": "#5fd7d7",
    "msg_warn": "#ffd75f",
}

SGR_RE = re.compile(r'\x1B\[([0-9;]*)m')
STRIP_OSC_RE = re.compile(r'\x1B\][^\x07\x1B]*(?:\x07|\x1B\\)')
STRIP_CHARSET_RE = re.compile(r'\x1B[()][A-Za-z0-9]')
STRIP_CSI_RE = re.compile(r'\x1B\[[0-9;?]*(?!m)[A-Za-z]')


# ---------------------------------------------------------------------------
# استایل Termius-like (QSS)
# ---------------------------------------------------------------------------
TERMIUS_ACCENT = "#3ddc97"

MODERN_QSS = """
QMainWindow, QDialog {
    background-color: #14151d;
}
QWidget {
    color: #e4e5ec;
    font-family: 'Segoe UI', 'Vazirmatn', 'Inter', 'Tahoma', sans-serif;
    font-size: 13px;
}

/* ---------- Sidebar (nav list: Hosts / Keychain / Port Forwarding ...) ---------- */
QFrame#sidebar {
    background-color: #14151d;
    border-right: 1px solid #1c1d28;
}
QLabel#sidebarBrand {
    color: #ffffff;
    font-size: 14px;
    font-weight: 700;
}
QLabel#sidebarSection {
    color: #565971;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 6px 2px 2px 2px;
}
QPushButton#navItem {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 8px 8px;
    text-align: left;
    color: #9498ab;
    font-size: 13px;
}
QPushButton#navItem:hover {
    background-color: #1b1c28;
    color: #e4e5ec;
}
QPushButton#navItem:checked {
    background-color: #23242f;
    color: #ffffff;
    font-weight: 600;
}

/* ---------- Top bar ---------- */
QFrame#topbar {
    background-color: #14151d;
    border-bottom: 1px solid #1c1d28;
}
QLabel#vaultPill {
    background-color: #1e1f2b;
    border-radius: 12px;
    padding: 5px 12px;
    color: #cfd1de;
    font-size: 12px;
    font-weight: 600;
}

/* ---------- Search / connect pill (Host browser) ---------- */
QLineEdit#searchBox {
    background-color: #1b1c28;
    border: 1px solid #262838;
    border-radius: 18px;
    padding: 9px 16px;
    color: #e4e5ec;
    font-size: 13px;
}
QLineEdit#searchBox:focus { border: 1px solid #4c6fff; }

QPushButton#pillBtn {
    background-color: #262838;
    border: 1px solid #323548;
    border-radius: 16px;
    padding: 8px 18px;
    color: #e4e5ec;
    font-weight: 600;
}
QPushButton#pillBtn:hover { background-color: #303245; }

QPushButton#pillBtnDark, QToolButton#pillBtnDark {
    background-color: #1b1c28;
    border: 1px solid #262838;
    border-radius: 8px;
    padding: 8px 14px;
    color: #e4e5ec;
    font-weight: 600;
}
QPushButton#pillBtnDark:hover, QToolButton#pillBtnDark:hover { background-color: #23242f; }

QPushButton#modeToggleActive {
    background-color: #23242f;
    border: 1px solid #323548;
    border-radius: 8px;
    padding: 7px 14px;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#modeToggle {
    background-color: transparent;
    border: 1px solid #262838;
    border-radius: 8px;
    padding: 7px 14px;
    color: #565971;
}

QToolButton#iconToolBtn {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 4px;
    font-size: 15px;
    color: #9498ab;
}
QToolButton#iconToolBtn:hover { background-color: #1b1c28; color: #ffffff; }

QLabel#avatarCircle {
    background-color: #e0a72e;
    border-radius: 14px;
    color: #1a1508;
    font-weight: 700;
    font-size: 12px;
}

QToolButton#cornerAddBtn {
    background-color: transparent;
    border: none;
    color: #9498ab;
    font-size: 18px;
    font-weight: 700;
    padding: 4px 10px;
}
QToolButton#cornerAddBtn:hover { color: #ffffff; }

/* ---------- Host cards (grid) ---------- */
QFrame#hostCard {
    background-color: #1b1c28;
    border: 1px solid #262838;
    border-radius: 10px;
}
QFrame#hostCard:hover {
    background-color: #20212e;
    border: 1px solid #323548;
}
QFrame#hostCard[selected="true"] {
    border: 1px solid #4c6fff;
    background-color: #1c2030;
}
QLabel#hostCardName { color: #f0f1f6; font-size: 13px; font-weight: 700; }
QLabel#hostCardSub { color: #6c7086; font-size: 11px; }
QLabel#hostCardDot { color: #3ddc97; font-size: 10px; }
QLabel#hostCardDotOff { color: #4a4d5e; font-size: 10px; }

/* ---------- Generic cards (settings dialog etc.) ---------- */
QFrame#card {
    background-color: #1b1c28;
    border: 1px solid #262838;
    border-radius: 12px;
}
QLabel#sectionTitle {
    color: #7d93ff;
    font-weight: 700;
    font-size: 12px;
    padding: 2px 0;
}
QLabel#fieldLabel {
    color: #8b8fa3;
    font-size: 12px;
}
QLabel#appTitle {
    color: #ffffff;
    font-size: 18px;
    font-weight: 700;
}
QLabel#appSubtitle {
    color: #6c7086;
    font-size: 11px;
}
QLineEdit, QComboBox {
    background-color: #101116;
    border: 1px solid #262838;
    border-radius: 8px;
    padding: 7px 10px;
    selection-background-color: #4c6fff;
    color: #e8eaf0;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #4c6fff;
}
QComboBox::drop-down {
    border: none;
    width: 22px;
}
QComboBox QAbstractItemView {
    background-color: #1b1c28;
    border: 1px solid #262838;
    selection-background-color: #4c6fff;
    outline: none;
}
QPushButton {
    background-color: #1e1f2b;
    border: 1px solid #2a2c3a;
    border-radius: 8px;
    padding: 7px 14px;
    color: #e4e5ec;
}
QPushButton:hover { background-color: #262838; }
QPushButton:pressed { background-color: #15161c; }
QPushButton:disabled { color: #52556a; border-color: #23242f; }

QPushButton#primary { background-color: #4c6fff; border: none; color: #ffffff; font-weight: 700; }
QPushButton#primary:hover { background-color: #6483ff; }
QPushButton#primary:disabled { background-color: #23283f; color: #565f8a; }

QPushButton#danger { background-color: #7a2b34; border: none; color: #ffffff; }
QPushButton#danger:hover { background-color: #99333f; }

QPushButton#success { background-color: #1f6f4a; border: none; color: #ffffff; }
QPushButton#success:hover { background-color: #278a5c; }

QPushButton#warn { background-color: #8a6a1a; border: none; color: #ffffff; }
QPushButton#warn:hover { background-color: #a67f22; }

QPushButton#ghost { background-color: transparent; border: 1px solid #2a2c3a; }
QPushButton#ghost:hover { background-color: #1b1c28; }

QCheckBox { spacing: 8px; color: #cfd1de; }
QCheckBox::indicator {
    width: 16px; height: 16px; border-radius: 4px;
    border: 1px solid #333548; background: #101116;
}
QCheckBox::indicator:checked {
    background-color: #4c6fff; border: 1px solid #4c6fff;
}

QTabWidget::pane {
    border: 1px solid #1c1d28;
    border-radius: 0px;
    top: -1px;
    background: #14151d;
}
QTabBar::tab {
    background: #1b1c28;
    padding: 7px 16px;
    border-radius: 16px;
    margin: 4px 3px;
    color: #8b8fa3;
}
QTabBar::tab:selected {
    background: #262838;
    color: #ffffff;
    font-weight: 600;
}
QTabBar::tab:hover { color: #cfd1de; }
QTabBar::close-button {
    subcontrol-position: right;
}

QTreeWidget {
    background-color: #101116;
    border: 1px solid #1c1d28;
    border-radius: 8px;
    alternate-background-color: #15161f;
    outline: none;
}
QTreeWidget::item { padding: 5px; }
QTreeWidget::item:selected { background-color: #2c4bd6; color: white; }
QHeaderView::section {
    background-color: #1b1c28;
    padding: 7px;
    border: none;
    border-bottom: 1px solid #1c1d28;
    color: #8b8fa3;
}

QTextEdit#terminal {
    background-color: #0a0a0f;
    border: 1px solid #1c1d28;
    border-radius: 0px;
    font-family: 'Consolas', 'Cascadia Mono', 'Courier New', monospace;
}

QProgressBar {
    background-color: #101116;
    border: 1px solid #1c1d28;
    border-radius: 7px;
    text-align: center;
    color: #cfd1de;
    height: 16px;
}
QProgressBar::chunk {
    background-color: #4c6fff;
    border-radius: 7px;
}

QScrollBar:vertical {
    background: #14151d; width: 10px; margin: 0;
}
QScrollBar::handle:vertical {
    background: #262838; border-radius: 5px; min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #323548; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: #14151d; height: 10px; margin: 0;
}
QScrollBar::handle:horizontal {
    background: #262838; border-radius: 5px; min-width: 24px;
}
"""


# ============================================================
# کلاس مدیریت نشست‌ها (Session Manager)
# ============================================================
class SessionManager:
    """مدیریت نشست‌های اتصال"""
    def __init__(self):
        self.sessions = []
        self.sessions_file = "sessions.json"
        self.load_sessions()
    
    def load_sessions(self):
        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r') as f:
                    self.sessions = json.load(f)
        except:
            self.sessions = []
    
    def save_sessions(self):
        try:
            with open(self.sessions_file, 'w') as f:
                json.dump(self.sessions, f, indent=2)
        except:
            pass
    
    def add_session(self, name, host, port, user, password="", key_path="", description=""):
        """افزودن نشست جدید"""
        for s in self.sessions:
            if s.get('name') == name:
                return False, "A session with this name already exists!"
        
        self.sessions.append({
            'name': name,
            'host': host,
            'port': int(port),
            'user': user,
            'password': password,
            'key_path': key_path,
            'description': description,
            'created_at': time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self.save_sessions()
        return True, "Session added successfully!"
    
    def update_session(self, old_name, name, host, port, user, password="", key_path="", description=""):
        """ویرایش نشست"""
        for i, s in enumerate(self.sessions):
            if s.get('name') == old_name:
                self.sessions[i] = {
                    'name': name,
                    'host': host,
                    'port': int(port),
                    'user': user,
                    'password': password,
                    'key_path': key_path,
                    'description': description,
                    'created_at': s.get('created_at', time.strftime("%Y-%m-%d %H:%M:%S"))
                }
                self.save_sessions()
                return True, "Session updated successfully!"
        return False, "Session not found!"
    
    def delete_session(self, name):
        """حذف نشست"""
        for i, s in enumerate(self.sessions):
            if s.get('name') == name:
                del self.sessions[i]
                self.save_sessions()
                return True, "Session deleted successfully!"
        return False, "Session not found!"
    
    def get_session(self, name):
        """دریافت اطلاعات نشست"""
        for s in self.sessions:
            if s.get('name') == name:
                return s
        return None
    
    def get_session_names(self):
        """دریافت لیست نام نشست‌ها"""
        return [s.get('name') for s in self.sessions]


class TabData:
    """نگهدارنده وضعیت هر تب سرور"""
    def __init__(self):
        self.ssh = None
        self.sftp = None
        self.channel = None
        self.connected = False
        self.current_path = "."
        self.password = ""
        self.reader_thread = None
        self.cmd_history = []
        self.history_pos = 0
        self.cur_color = None

        # ویجت‌ها
        self.term = None
        self.tree = None
        self.path_entry = None
        self.cmd = None
        self.progress_bar = None
        self.progress_label = None
        self.container = None
        self.bookmark_combo = None

        # پنل SFTP دوقلو (Local/Remote)
        self.local_path = os.path.expanduser("~")
        self.local_tree = None
        self.local_path_label = None
        self.remote_path_label = None
        self.stacked = None
        self.btn_mode_terminal = None
        self.btn_mode_sftp = None

        # وضعیت اتصال مخصوص همین تب (هر تب کنترل خودش را دارد)
        self.status_label = None
        self.connect_btn = None

        # تم رنگی ترمینال — هر تب پالت ANSI و رنگ پیش‌فرض خودش را دارد
        # (با تعویض تم، هم پس‌زمینه/متن پیش‌فرض و هم رنگ کدهای ANSI عوض می‌شود)
        self.fg_colors = dict(FG_COLORS)
        self.term_bg = "#0a0a0f"
        self.term_fg = "#e4e5ec"

        # جستجو
        self._last_search = ""
        self._search_pos = 0
        self._last_found_pos = 0


class ClickableFrame(QFrame):
    """QFrame قابل کلیک، برای کارت‌های هاست (تک‌کلیک = انتخاب، دابل‌کلیک = اتصال)"""
    clicked = pyqtSignal()
    doubleClicked = pyqtSignal()
    rightClicked = pyqtSignal(object)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        elif event.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit(event.globalPosition().toPoint())
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)


class SSHManager(QMainWindow):
    call_signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SSH Manager Pro")
        self.resize(1500, 860)

        self.call_signal.connect(lambda fn: fn())

        # وضعیت کلی
        self.ssh_key_path = None
        self.ssh_key_passphrase = None
        self.ssh_agent_enabled = False
        self.x11_forwarding = False

        self.bookmarks = []
        self.bookmarks_file = "bookmarks.json"
        self.load_bookmarks()

        self.settings_file = "settings.json"

        self.tabs = {}
        self.tab_counter = 0
        self.current_tab = None

        # Session Manager
        self.session_mgr = SessionManager()

        # فیلدهای اتصال (بدون نمایش مستقیم در UI؛ توسط سایدبار/دیالوگ‌ها پر می‌شوند)
        self.host = QLineEdit()
        self.port = QLineEdit()
        self.port.setText("22")
        self.user = QLineEdit()
        self.passw = QLineEdit()
        self.passw.setEchoMode(QLineEdit.EchoMode.Password)

        self._build_ui()
        self._build_settings_dialog()
        self.load_settings()
        self._add_host_browser_tab()
        self.add_new_tab("Server 1")
        self._populate_host_grid()
        self.tabview.setCurrentIndex(0)

    # ============================================================
    # ابزارهای thread-safe برای بروزرسانی UI از ترد پس‌زمینه
    # ============================================================
    def ui(self, fn):
        """اجرای fn روی ترد اصلی، بدون انتظار برای نتیجه."""
        self.call_signal.emit(fn)

    def sync_call(self, fn):
        """اجرای fn روی ترد اصلی و انتظار برای نتیجه (برای دیالوگ‌ها)."""
        if QThread.currentThread() is self.thread():
            return fn()
        result = {}
        event = threading.Event()

        def wrapper():
            try:
                result['v'] = fn()
            except Exception as e:
                result['e'] = e
            finally:
                event.set()

        self.call_signal.emit(wrapper)
        event.wait()
        if 'e' in result:
            raise result['e']
        return result.get('v')

    def msg_info(self, title, text):
        self.sync_call(lambda: QMessageBox.information(self, title, text))

    def msg_warn(self, title, text):
        self.sync_call(lambda: QMessageBox.warning(self, title, text))

    def msg_error(self, title, text):
        self.sync_call(lambda: QMessageBox.critical(self, title, text))

    def ask_yes_no(self, title, text):
        def _ask():
            res = QMessageBox.question(
                self, title, text,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            return res == QMessageBox.StandardButton.Yes
        return self.sync_call(_ask)

    def input_text(self, title, label, password=False):
        def _ask():
            echo = QLineEdit.EchoMode.Password if password else QLineEdit.EchoMode.Normal
            text, ok = QInputDialog.getText(self, title, label, echo)
            return text if ok else None
        return self.sync_call(_ask)

    def term_write(self, info: TabData, text, tag=None):
        self.ui(lambda: self._term_write_now(info, text, tag))

    def _term_write_now(self, info: TabData, text, tag=None):
        if info is None or info.term is None:
            return
        cursor = info.term.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        color = None
        if tag:
            if tag in TAG_COLORS:
                color = TAG_COLORS[tag]
            elif tag.startswith("fg"):
                # هر تب پالت رنگ ANSI مخصوص خودش را دارد (متناسب با تمی که
                # برای همان تب انتخاب شده)، نه یک دیکشنری رنگ ثابت سراسری.
                color = info.fg_colors.get(tag[2:])
        fmt.setForeground(QColor(color or info.term_fg))
        cursor.setCharFormat(fmt)
        cursor.insertText(text)
        info.term.setTextCursor(cursor)
        info.term.ensureCursorVisible()

    # ============================================================
    # ساخت رابط کاربری (سبک Termius: سایدبار + تب‌های ترمینال)
    # ============================================================
    # ============================================================
    # ساخت رابط کاربری (بر اساس اسکرین‌شات‌های واقعی Termius)
    # ============================================================
    def _build_ui(self):
        self.setStyleSheet(MODERN_QSS)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ================= سایدبار ناوبری =================
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(196)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(10, 16, 10, 14)
        side.setSpacing(2)

        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(6, 0, 6, 16)
        brand_row.setSpacing(6)
        brand_icon = QLabel("🛡️")
        brand_row.addWidget(brand_icon)
        brand_row.addWidget(self._label("SSH Manager", "sidebarBrand"))
        brand_row.addStretch()
        side.addLayout(brand_row)

        # ناوبری اصلی: فقط بخش‌هایی که واقعاً یک مقصد مستقل‌اند
        self._nav_buttons = {}
        nav_items = [
            ("hosts", "🖥️", "Hosts"),
            ("snippets", "{ }", "Snippets"),
            ("known_hosts", "📶", "Known Hosts"),
            ("logs", "🕓", "Logs"),
        ]
        for key, icon, text in nav_items:
            b = QPushButton(f"  {icon}   {text}")
            b.setObjectName("navItem")
            b.setCheckable(True)
            b.clicked.connect(lambda checked, k=key: self._nav_select(k))
            side.addWidget(b)
            self._nav_buttons[key] = b
        self._nav_buttons["hosts"].setChecked(True)

        side.addStretch()

        # کلید SSH + پراکسی + X11 همگی یک مفهوم واحدند (تنظیمات اتصال)
        # پس فقط یک نقطهٔ ورود منطقی برایشان می‌گذاریم، نه سه‌تا دکمهٔ تکراری
        btn_settings = QPushButton("  🔐   Connection Settings")
        btn_settings.setObjectName("navItem")
        btn_settings.clicked.connect(lambda: self.settings_dialog.exec())
        side.addWidget(btn_settings)

        root.addWidget(sidebar)

        # ================= بخش اصلی: فقط تب‌ها =================
        # (دکمهٔ سراسری Connect/Refresh/Clear حذف شد چون معلوم نبود روی کدام
        #  تب اثر می‌گذارد؛ این کنترل‌ها الان داخل خودِ هر تب و مخصوص همان تب‌اند)
        content_wrap = QWidget()
        content_layout = QVBoxLayout(content_wrap)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(0)

        self.tabview = QTabWidget()
        self.tabview.setTabsClosable(True)
        self.tabview.tabCloseRequested.connect(self._on_tab_close_requested)
        self.tabview.currentChanged.connect(self._on_tab_changed)

        add_tab_btn = QToolButton()
        add_tab_btn.setText("＋")
        add_tab_btn.setObjectName("cornerAddBtn")
        add_tab_btn.setToolTip("New Tab")
        add_tab_btn.clicked.connect(lambda: self.add_new_tab())
        self.tabview.setCornerWidget(add_tab_btn, Qt.Corner.TopRightCorner)

        content_layout.addWidget(self.tabview)

        root.addWidget(content_wrap, 1)

    def _nav_select(self, key):
        """سوییچ بین بخش‌های سایدبار: Hosts / Snippets / Known Hosts / Logs"""
        for k, b in self._nav_buttons.items():
            b.setChecked(k == key)

        if key == "hosts":
            self.tabview.setCurrentIndex(0)
        else:
            self.msg_info("Coming Soon", "این بخش (Snippets / Known Hosts / Logs) در این نسخه پیاده‌سازی نشده است.")
            self._nav_buttons["hosts"].setChecked(True)
            for k, b in self._nav_buttons.items():
                if k != "hosts":
                    b.setChecked(False)
            self.tabview.setCurrentIndex(0)

    # ------------------------------------------------------------
    # تب دائمی «Hosts» — پنل اصلی مرور میزبان‌ها
    # ------------------------------------------------------------
    def _add_host_browser_tab(self):
        page = self._build_host_browser_page()
        idx = self.tabview.addTab(page, "🗂  Hosts")
        try:
            self.tabview.tabBar().setTabButton(idx, QTabBar.ButtonPosition.RightSide, None)
            self.tabview.tabBar().setTabButton(idx, QTabBar.ButtonPosition.LeftSide, None)
        except Exception:
            pass

    def _build_host_browser_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(6, 14, 6, 6)
        layout.setSpacing(12)

        # --- نوار جستجو / اتصال ---
        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        self.search_box = QLineEdit()
        self.search_box.setObjectName("searchBox")
        self.search_box.setPlaceholderText("Find a host or ssh user@hostname...")
        self.search_box.textChanged.connect(self._filter_host_grid)
        self.search_box.returnPressed.connect(self._browser_connect_from_search)
        search_row.addWidget(self.search_box, 1)

        btn_connect_search = QPushButton("Connect")
        btn_connect_search.setObjectName("pillBtn")
        btn_connect_search.clicked.connect(self._browser_connect_from_search)
        search_row.addWidget(btn_connect_search)
        layout.addLayout(search_row)

        # --- نوار ابزار ---
        toolbar_row = QHBoxLayout()
        toolbar_row.setSpacing(8)

        btn_new_host = QPushButton("＋ New host")
        btn_new_host.setObjectName("pillBtnDark")
        btn_new_host.clicked.connect(self._sidebar_new_host)
        toolbar_row.addWidget(btn_new_host)

        btn_new_menu = QToolButton()
        btn_new_menu.setText("▾")
        btn_new_menu.setObjectName("pillBtnDark")
        menu = QMenu(self)
        act_quick = QAction("⚡ Quick Connect...", self)
        act_quick.triggered.connect(self._quick_connect_dialog)
        menu.addAction(act_quick)
        btn_new_menu.setMenu(menu)
        btn_new_menu.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        toolbar_row.addWidget(btn_new_menu)

        btn_manage = QPushButton("📋 Manage")
        btn_manage.setObjectName("pillBtnDark")
        btn_manage.setToolTip("Classic table view (search / add / edit / delete / connect)")
        btn_manage.clicked.connect(self.manage_sessions)
        toolbar_row.addWidget(btn_manage)

        toolbar_row.addStretch()

        btn_grid = QToolButton()
        btn_grid.setText("⊞")
        btn_grid.setObjectName("iconToolBtn")
        btn_grid.setToolTip("Toggle grid / list view")
        btn_grid.clicked.connect(self._toggle_grid_columns)
        toolbar_row.addWidget(btn_grid)

        layout.addLayout(toolbar_row)

        layout.addWidget(self._label("Hosts", "sidebarSection"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        grid_host_widget = QWidget()
        self.host_grid_layout = QGridLayout(grid_host_widget)
        self.host_grid_layout.setSpacing(12)
        self.host_grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(grid_host_widget)
        layout.addWidget(scroll, 1)

        self._host_cards = {}
        self._selected_host_name = None
        self._grid_columns = 3

        return page

    def _toggle_grid_columns(self):
        self._grid_columns = 1 if self._grid_columns == 3 else 3
        self._populate_host_grid()

    # ============================================================
    # مدیریت نشست‌ها (Session Manager) — نمای جدولی کلاسیک (مثل کد اولیه)
    # ============================================================
    def manage_sessions(self):
        """باز کردن پنجرهٔ کلاسیک مدیریت نشست‌ها (جدول با جستجو/افزودن/ویرایش/حذف/اتصال)"""
        dialog = QDialog(self)
        dialog.setWindowTitle("📋 Session Manager")
        dialog.resize(750, 450)
        dialog.setStyleSheet(MODERN_QSS)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.addWidget(self._label("📋 Manage Sessions", "sectionTitle"))
        header.addStretch()

        search_entry = QLineEdit()
        search_entry.setPlaceholderText("Search sessions...")
        search_entry.setFixedWidth(180)
        header.addWidget(search_entry)
        layout.addLayout(header)

        tree = QTreeWidget()
        tree.setColumnCount(5)
        tree.setHeaderLabels(["Name", "Host", "Port", "User", "Description"])
        tree.setRootIsDecorated(False)
        tree.setAlternatingRowColors(True)
        tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tree.header().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        layout.addWidget(tree, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_add = QPushButton("➕ Add")
        btn_add.setObjectName("success")
        btn_add.clicked.connect(lambda: (self._show_session_dialog(None), self._load_sessions_tree(tree)))
        btn_row.addWidget(btn_add)

        btn_edit = QPushButton("✏️ Edit")
        btn_edit.setObjectName("primary")
        btn_edit.clicked.connect(lambda: self._edit_session_from_tree(tree))
        btn_row.addWidget(btn_edit)

        btn_delete = QPushButton("🗑️ Delete")
        btn_delete.setObjectName("danger")
        btn_delete.clicked.connect(lambda: self._delete_session_from_tree(tree))
        btn_row.addWidget(btn_delete)

        btn_connect = QPushButton("🔌 Connect")
        btn_connect.setObjectName("primary")
        btn_connect.clicked.connect(lambda: self._connect_session_from_tree(tree, dialog))
        btn_row.addWidget(btn_connect)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dialog.accept)
        btn_row.addWidget(btn_close)

        layout.addLayout(btn_row)

        self._load_sessions_tree(tree)

        def filter_sessions(text):
            for i in range(tree.topLevelItemCount()):
                item = tree.topLevelItem(i)
                visible = text.lower() in item.text(0).lower() or text.lower() in item.text(4).lower()
                item.setHidden(not visible)

        search_entry.textChanged.connect(filter_sessions)
        tree.itemDoubleClicked.connect(lambda item, col: self._connect_session_from_tree(tree, dialog))

        dialog.exec()
        # پس از بسته‌شدن دیالوگ، کارت‌های Hosts هم به‌روزرسانی شود
        self._populate_host_grid()

    def _load_sessions_tree(self, tree):
        tree.clear()
        for s in self.session_mgr.sessions:
            QTreeWidgetItem(tree, [
                s.get('name', ''),
                s.get('host', ''),
                str(s.get('port', 22)),
                s.get('user', ''),
                s.get('description', '')
            ])

    def _edit_session_from_tree(self, tree):
        selected = tree.selectedItems()
        if not selected:
            self.msg_warn("Warning", "No session selected!")
            return
        name = selected[0].text(0)
        session_data = self.session_mgr.get_session(name)
        if session_data:
            self._show_session_dialog(session_data)
            self._load_sessions_tree(tree)

    def _delete_session_from_tree(self, tree):
        selected = tree.selectedItems()
        if not selected:
            self.msg_warn("Warning", "No session selected!")
            return
        name = selected[0].text(0)
        if not self.ask_yes_no("Delete Session", f"Are you sure you want to delete session '{name}'?"):
            return
        success, msg = self.session_mgr.delete_session(name)
        if success:
            self._load_sessions_tree(tree)
        else:
            self.msg_warn("Error", msg)

    def _connect_session_from_tree(self, tree, dialog):
        selected = tree.selectedItems()
        if not selected:
            self.msg_warn("Warning", "No session selected!")
            return
        name = selected[0].text(0)
        dialog.accept()
        self._connect_to_session_name(name)

    def _build_settings_dialog(self):
        """دیالوگ دائمی تنظیمات: کلید SSH (Keychain)، پراکسی/پورت‌فورواردینگ، X11، Agent"""
        dialog = QDialog(self)
        dialog.setWindowTitle("⚙️ Keychain · Port Forwarding · X11")
        dialog.resize(560, 420)
        dialog.setStyleSheet(MODERN_QSS)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # --- کلید SSH (Keychain) ---
        key_card = QFrame()
        key_card.setObjectName("card")
        key_layout = QVBoxLayout(key_card)
        key_layout.setContentsMargins(14, 12, 14, 12)
        key_layout.setSpacing(8)
        key_layout.addWidget(self._label("🔑  KEYCHAIN", "sectionTitle"))

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        row2.addWidget(self._label("Key:", "fieldLabel"))
        self.key_path_label = QLabel("None")
        self.key_path_label.setStyleSheet("color:#7d879e;")
        row2.addWidget(self.key_path_label, 1)
        key_layout.addLayout(row2)

        row2b = QHBoxLayout()
        row2b.setSpacing(8)
        btn_select_key = QPushButton("Select Key")
        btn_select_key.clicked.connect(self.select_ssh_key)
        row2b.addWidget(btn_select_key)

        btn_gen_key = QPushButton("Generate Key")
        btn_gen_key.clicked.connect(self.generate_ssh_key)
        row2b.addWidget(btn_gen_key)

        btn_show_pub = QPushButton("Show Public")
        btn_show_pub.clicked.connect(self.show_public_key)
        row2b.addWidget(btn_show_pub)

        btn_add_key = QPushButton("📤 Add to Server")
        btn_add_key.setObjectName("success")
        btn_add_key.clicked.connect(self.add_key_to_server)
        row2b.addWidget(btn_add_key)
        key_layout.addLayout(row2b)

        self.agent_check = QCheckBox("Use SSH Agent")
        self.agent_check.stateChanged.connect(self.toggle_agent)
        key_layout.addWidget(self.agent_check)

        layout.addWidget(key_card)

        # --- پورت‌فورواردینگ / پراکسی ---
        proxy_card = QFrame()
        proxy_card.setObjectName("card")
        proxy_layout = QVBoxLayout(proxy_card)
        proxy_layout.setContentsMargins(14, 12, 14, 12)
        proxy_layout.setSpacing(8)
        proxy_layout.addWidget(self._label("↔️  PORT FORWARDING / PROXY", "sectionTitle"))

        row3 = QHBoxLayout()
        row3.setSpacing(8)
        row3.addWidget(self._label("Type:", "fieldLabel"))
        self.proxy_type_var = QComboBox()
        self.proxy_type_var.addItems(["None", "HTTP", "HTTPS", "SOCKS5", "SOCKS4"])
        self.proxy_type_var.setFixedWidth(90)
        row3.addWidget(self.proxy_type_var)

        self.proxy_host = QLineEdit()
        self.proxy_host.setPlaceholderText("proxy.example.com")
        row3.addWidget(self.proxy_host, 1)

        self.proxy_port = QLineEdit()
        self.proxy_port.setPlaceholderText("8080")
        self.proxy_port.setFixedWidth(70)
        row3.addWidget(self.proxy_port)
        proxy_layout.addLayout(row3)

        row3b = QHBoxLayout()
        row3b.setSpacing(8)
        self.proxy_user = QLineEdit()
        self.proxy_user.setPlaceholderText("user (optional)")
        row3b.addWidget(self.proxy_user)

        self.proxy_pass = QLineEdit()
        self.proxy_pass.setPlaceholderText("pass (optional)")
        self.proxy_pass.setEchoMode(QLineEdit.EchoMode.Password)
        row3b.addWidget(self.proxy_pass)
        proxy_layout.addLayout(row3b)

        layout.addWidget(proxy_card)

        # --- X11 ---
        x11_card = QFrame()
        x11_card.setObjectName("card")
        x11_layout = QHBoxLayout(x11_card)
        x11_layout.setContentsMargins(14, 12, 14, 12)
        self.x11_check = QCheckBox("Enable X11 Forwarding")
        self.x11_check.stateChanged.connect(self.toggle_x11)
        x11_layout.addWidget(self.x11_check)
        x11_layout.addStretch()
        layout.addWidget(x11_card)

        layout.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setObjectName("primary")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)

        self.settings_dialog = dialog

    def _label(self, text, obj_name=None):
        lbl = QLabel(text)
        if obj_name:
            lbl.setObjectName(obj_name)
        return lbl

    def _field(self, layout, name, width=140):
        layout.addWidget(self._label(f"{name}:", "fieldLabel"))
        entry = QLineEdit()
        entry.setFixedWidth(width)
        layout.addWidget(entry)
        return entry

    def _on_tab_changed(self, index):
        if index < 0:
            return
        widget = self.tabview.widget(index)
        for name, info in self.tabs.items():
            if info.container is widget:
                self.current_tab = name
                return
        # تب «Hosts» انتخاب شده؛ current_tab (آخرین تب اتصال) بدون تغییر می‌ماند

    def _on_tab_close_requested(self, index):
        if index == 0:
            return  # نمی‌توان تب Hosts را بست
        widget = self.tabview.widget(index)
        name = None
        for n, info in self.tabs.items():
            if info.container is widget:
                name = n
                break
        if name:
            self.close_tab(name)

    # ============================================================
    # کارت‌های میزبان (Host grid — دقیقاً مثل صفحهٔ Hosts در Termius)
    # ============================================================
    def _create_host_card(self, session):
        name = session.get('name', '')
        card = ClickableFrame()
        card.setObjectName("hostCard")
        card.setFixedSize(252, 78)
        h = QHBoxLayout(card)
        h.setContentsMargins(12, 10, 12, 10)
        h.setSpacing(10)

        colors = ["#e8622c", "#4c6fff", "#8a5cf6", "#e0a72e", "#2fa876", "#d6455a", "#2f8fd6"]
        color = colors[abs(hash(name)) % len(colors)]
        icon = QLabel((session.get('host') or name or "?")[0].upper())
        icon.setFixedSize(40, 40)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(
            f"background-color:{color}; border-radius:9px; color:white; font-weight:700; font-size:16px;"
        )
        h.addWidget(icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        name_row = QHBoxLayout()
        name_row.setSpacing(6)
        dot = QLabel("●")
        dot.setObjectName("hostCardDotOff")
        dot.setFixedWidth(10)
        name_row.addWidget(dot)
        name_lbl = QLabel(name or session.get('host', ''))
        name_lbl.setObjectName("hostCardName")
        name_row.addWidget(name_lbl)
        name_row.addStretch()
        text_col.addLayout(name_row)

        sub_lbl = QLabel(f"{session.get('user','')}@{session.get('host','')}:{session.get('port', 22)}")
        sub_lbl.setObjectName("hostCardSub")
        text_col.addWidget(sub_lbl)
        h.addLayout(text_col, 1)

        card.clicked.connect(lambda n=name: self._select_host_card(n))
        card.doubleClicked.connect(lambda n=name: self._connect_to_session_name(n))
        card.rightClicked.connect(lambda pos, n=name: self._host_card_context_menu(pos, n))

        return card

    def _populate_host_grid(self):
        if not hasattr(self, 'host_grid_layout'):
            return
        while self.host_grid_layout.count():
            item = self.host_grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self._host_cards = {}
        cols = getattr(self, '_grid_columns', 3)
        for i, s in enumerate(self.session_mgr.sessions):
            card = self._create_host_card(s)
            row, col = divmod(i, cols)
            self.host_grid_layout.addWidget(card, row, col)
            self._host_cards[s.get('name')] = card

    def _select_host_card(self, name):
        self._selected_host_name = name
        for n, card in self._host_cards.items():
            card.setProperty("selected", n == name)
            card.style().unpolish(card)
            card.style().polish(card)

    def _host_card_context_menu(self, global_pos, name):
        menu = QMenu(self)
        act_connect = QAction("🔌 Connect", self)
        act_connect.triggered.connect(lambda: self._connect_to_session_name(name))
        menu.addAction(act_connect)
        act_edit = QAction("✏️ Edit", self)
        act_edit.triggered.connect(lambda: self._show_session_dialog(self.session_mgr.get_session(name)))
        menu.addAction(act_edit)
        act_delete = QAction("🗑️ Delete", self)
        act_delete.triggered.connect(lambda: self._delete_host_by_name(name))
        menu.addAction(act_delete)
        menu.exec(global_pos)

    def _delete_host_by_name(self, name):
        if not self.ask_yes_no("Delete Host", f"Are you sure you want to delete '{name}'?"):
            return
        success, msg = self.session_mgr.delete_session(name)
        if success:
            self._populate_host_grid()
        else:
            self.msg_warn("Error", msg)

    def _filter_host_grid(self, text):
        text = text.lower().strip()
        for name, card in self._host_cards.items():
            session = self.session_mgr.get_session(name) or {}
            haystack = f"{name} {session.get('host','')} {session.get('user','')} {session.get('description','')}".lower()
            card.setVisible(text in haystack)

    def _browser_connect_from_search(self):
        text = self.search_box.text().strip()
        if not text:
            self.msg_warn("Connect", "یک میزبان یا آدرس ssh وارد کنید (مثال: user@host).")
            return

        if self.session_mgr.get_session(text):
            self._connect_to_session_name(text)
            return

        m = re.match(r'^([^@\s]+)@([^:\s]+)(?::(\d+))?$', text)
        if m:
            user, host, port = m.group(1), m.group(2), m.group(3) or "22"
            self.host.setText(host)
            self.port.setText(port)
            self.user.setText(user)
            self.passw.setText("")
            current_info = self.get_info()
            if not current_info or current_info.connected:
                self.add_new_tab(host)
            self.do_connect()
            return

        self.msg_warn("Connect", "فرمت را به‌صورت user@host یا نام یک میزبان ذخیره‌شده وارد کنید.")

    def _sidebar_new_host(self):
        self._show_session_dialog(None)

    def _connect_to_session_name(self, name):
        session = self.session_mgr.get_session(name)
        if not session:
            self.msg_warn("Error", "Session not found!")
            return

        self.host.setText(session.get('host', ''))
        self.port.setText(str(session.get('port', 22)))
        self.user.setText(session.get('user', ''))
        self.passw.setText(session.get('password', ''))

        if session.get('key_path'):
            self.ssh_key_path = session.get('key_path')
            self.key_path_label.setText(os.path.basename(self.ssh_key_path))
            self.key_path_label.setStyleSheet("color:#3ddc97;")

        current_info = self.get_info()
        if not current_info or current_info.connected:
            self.add_new_tab(name)

        self.do_connect()

    def _quick_connect_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("⚡ Quick Connect")
        dialog.setFixedSize(380, 260)
        dialog.setStyleSheet(MODERN_QSS)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        fields = {}
        for key, label, echo in [
            ("host", "Host:", False), ("port", "Port:", False),
            ("user", "Username:", False), ("password", "Password:", True)
        ]:
            row = QHBoxLayout()
            row.addWidget(self._label(label, "fieldLabel"))
            entry = QLineEdit()
            if echo:
                entry.setEchoMode(QLineEdit.EchoMode.Password)
            if key == "port":
                entry.setText("22")
            row.addWidget(entry, 1)
            layout.addLayout(row)
            fields[key] = entry

        layout.addStretch()
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        def do_quick_connect():
            self.host.setText(fields['host'].text().strip())
            self.port.setText(fields['port'].text().strip() or "22")
            self.user.setText(fields['user'].text().strip())
            self.passw.setText(fields['password'].text())
            dialog.accept()
            current_info = self.get_info()
            if not current_info or current_info.connected:
                self.add_new_tab()
            self.do_connect()

        btn_connect = QPushButton("🔌 Connect")
        btn_connect.setObjectName("primary")
        btn_connect.clicked.connect(do_quick_connect)
        btn_row.addWidget(btn_connect)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_row.addWidget(btn_cancel)

        layout.addLayout(btn_row)
        dialog.exec()
    def _show_session_dialog(self, session_data):
        """نمایش دیالوگ افزودن/ویرایش میزبان"""
        is_edit = session_data is not None
        title = "✏️ Edit Host" if is_edit else "➕ New Host"

        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(460, 420)
        dialog.setStyleSheet(MODERN_QSS)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        fields = {}
        field_names = [
            ("name", "Session Name:"),
            ("host", "Host:"),
            ("port", "Port:"),
            ("user", "Username:"),
            ("password", "Password:"),
            ("key_path", "SSH Key Path:"),
            ("description", "Description:")
        ]

        for key, label in field_names:
            row = QHBoxLayout()
            row.addWidget(self._label(label, "fieldLabel"))
            entry = QLineEdit()
            if key == "port":
                entry.setText("22")
            elif key == "password":
                entry.setEchoMode(QLineEdit.EchoMode.Password)
            elif key == "key_path":
                row.addWidget(entry, 1)
                btn_browse = QPushButton("Browse...")
                btn_browse.setFixedWidth(80)
                btn_browse.clicked.connect(lambda e, ent=entry: self._browse_key_path(ent))
                row.addWidget(btn_browse)
                layout.addLayout(row)
                fields[key] = entry
                continue
            row.addWidget(entry, 1)
            layout.addLayout(row)
            fields[key] = entry

        if is_edit and session_data:
            for key, entry in fields.items():
                val = session_data.get(key, '')
                if key == "port":
                    entry.setText(str(val))
                else:
                    entry.setText(val)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_save = QPushButton("💾 Save")
        btn_save.setObjectName("success")
        btn_save.clicked.connect(lambda: self._save_session_dialog(dialog, fields, is_edit, session_data))
        btn_row.addWidget(btn_save)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(dialog.reject)
        btn_row.addWidget(btn_cancel)

        layout.addLayout(btn_row)
        dialog.exec()

    def _browse_key_path(self, entry):
        f, _ = QFileDialog.getOpenFileName(
            self, "Select SSH Private Key", "",
            "SSH Keys (*.pem *.key *.ppk id_rsa id_ed25519);;All Files (*.*)"
        )
        if f:
            entry.setText(f)

    def _save_session_dialog(self, dialog, fields, is_edit, session_data):
        data = {key: entry.text().strip() for key, entry in fields.items()}

        if not data['name'] or not data['host'] or not data['user']:
            QMessageBox.warning(dialog, "Error", "Name, Host and Username are required!")
            return

        try:
            data['port'] = int(data['port']) if data['port'] else 22
        except:
            QMessageBox.warning(dialog, "Error", "Invalid port number!")
            return

        if is_edit:
            old_name = session_data.get('name')
            success, msg = self.session_mgr.update_session(
                old_name, data['name'], data['host'], data['port'],
                data['user'], data['password'], data['key_path'], data['description']
            )
        else:
            success, msg = self.session_mgr.add_session(
                data['name'], data['host'], data['port'],
                data['user'], data['password'], data['key_path'], data['description']
            )

        if success:
            dialog.accept()
            self._populate_host_grid()
        else:
            QMessageBox.warning(dialog, "Error", msg)

    # ============================================================
    # تنظیمات
    # ============================================================
    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    if 'proxy_type' in settings:
                        idx = self.proxy_type_var.findText(settings.get('proxy_type', 'None'))
                        if idx >= 0:
                            self.proxy_type_var.setCurrentIndex(idx)
                    if 'proxy_host' in settings:
                        self.proxy_host.setText(settings.get('proxy_host', ''))
                    if 'proxy_port' in settings:
                        self.proxy_port.setText(settings.get('proxy_port', ''))
                    if 'proxy_user' in settings:
                        self.proxy_user.setText(settings.get('proxy_user', ''))
                    self.x11_forwarding = settings.get('x11', False)
                    if self.x11_forwarding:
                        self.x11_check.setChecked(True)
        except Exception:
            pass

    def save_settings(self):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump({
                    'proxy_type': self.proxy_type_var.currentText(),
                    'proxy_host': self.proxy_host.text(),
                    'proxy_port': self.proxy_port.text(),
                    'proxy_user': self.proxy_user.text(),
                    'x11': self.x11_forwarding
                }, f)
        except Exception:
            pass

    def toggle_x11(self):
        self.x11_forwarding = self.x11_check.isChecked()
        status = "enabled" if self.x11_forwarding else "disabled"
        info = self.get_info()
        if info:
            self.term_write(info, f"[X11] X11 Forwarding {status}\n", "msg_info")
        self.save_settings()

    def get_socket_proxy(self):
        proxy_type = self.proxy_type_var.currentText()
        if proxy_type == "None" or not self.proxy_host.text().strip():
            return None
        host = self.proxy_host.text().strip()
        port = int(self.proxy_port.text().strip()) if self.proxy_port.text().strip() else 8080
        return {
            'type': proxy_type.lower(),
            'host': host,
            'port': port,
            'user': self.proxy_user.text().strip() or None,
            'pass': self.proxy_pass.text().strip() or None
        }

    def create_proxy_socket(self, proxy_config, info):
        if not proxy_config:
            return None
        proxy_type = proxy_config['type']
        host = proxy_config['host']
        port = proxy_config['port']
        try:
            if proxy_type in ['http', 'https']:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect((host, port))
                return sock
            elif proxy_type in ['socks5', 'socks4']:
                try:
                    import socks
                    sock = socks.socksocket()
                    proxy_type_const = socks.SOCKS5 if proxy_type == 'socks5' else socks.SOCKS4
                    sock.set_proxy(proxy_type_const, host, port)
                    return sock
                except ImportError:
                    self.term_write(info, "[Proxy] ❌ Please install PySocks: pip install PySocks\n", "msg_err")
                    return None
        except Exception as e:
            self.term_write(info, f"[Proxy] ❌ Error: {str(e)}\n", "msg_err")
            return None
        return None

    # ============================================================
    # اجرای امن دستور روی سرور (رفع دِدلاک کلاسیک stdout/stderr پارامیکو)
    # ============================================================
    def _exec_ssh_command(self, info, cmd, timeout=20):
        """
        اجرای یک دستور روی سرور به‌صورت امن.

        مشکل اصلی نسخهٔ قبلی: exec_command سه استریم جدا برمی‌گرداند
        (stdin/stdout/stderr). اگر دستوری هم‌زمان روی stdout و هم روی
        stderr چیزی بنویسد و ما اول stdout را با read() بخوانیم، تا وقتی
        stdout به پایان نرسد stderr خوانده نمی‌شود؛ اگر بافر stderr پر شود
        (چون کسی آن را نمی‌خواند)، فرآیند سمت سرور برای نوشتن روی stderr
        بلاک می‌شود و برنامهٔ ما هم برای همیشه منتظر می‌ماند (دِدلاک).
        این دقیقاً چیزی است که در تست «Ping» رخ می‌داد، چون ping گاهی هم‌زمان
        روی هر دو استریم پیام می‌نویسد. در ترمینال تعاملی خودمان (invoke_shell)
        این مشکل وجود ندارد چون آنجا فقط یک کانال pty واحد داریم.

        راه‌حل: با set_combine_stderr(True) هر دو استریم را در یکی ادغام
        می‌کنیم، و با تنظیم timeout روی کانال، حتی اگر چیزی غیرمنتظره پیش
        بیاید، برنامه برای همیشه گیر نمی‌کند.

        خروجی: (output_text, exit_status) — در صورت خطا/timeout،
        output_text شامل پیام خطا و exit_status برابر None خواهد بود.
        """
        try:
            stdin, stdout, stderr = info.ssh.exec_command(cmd, timeout=timeout)
            stdout.channel.set_combine_stderr(True)
            output = stdout.read().decode(errors='ignore')
            exit_status = stdout.channel.recv_exit_status()
            return output, exit_status
        except socket.timeout:
            return f"[Timeout] Command did not finish within {timeout}s: {cmd}", None
        except Exception as e:
            return f"[Error] {str(e)}", None

    # ============================================================
    # مدیریت تب‌ها
    # ============================================================
    def get_info(self, tab_name=None):
        if not tab_name:
            tab_name = self.current_tab
        if tab_name and tab_name in self.tabs:
            return self.tabs[tab_name]
        return None

    def add_new_tab(self, name=None):
        self.tab_counter += 1
        tab_name = name or f"Server {self.tab_counter}"
        while tab_name in self.tabs:
            self.tab_counter += 1
            tab_name = f"Server {self.tab_counter}"

        info = TabData()
        self.tabs[tab_name] = info

        content = self._build_tab_content(tab_name, info)
        info.container = content
        self.tabview.addTab(content, tab_name)
        self.tabview.setCurrentWidget(content)
        self.current_tab = tab_name
        return tab_name

    def _build_tab_content(self, tab_name, info: TabData):
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        # ---------- ردیف ۱: وضعیت اتصال (مخصوص همین تب) + سوییچ نمای Terminal/SFTP ----------
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        status_label = QLabel("●  Disconnected")
        status_label.setStyleSheet("color:#ff5c5c; font-weight:600; font-size:12px;")
        row1.addWidget(status_label)
        info.status_label = status_label

        connect_btn = QPushButton("Connect")
        connect_btn.setObjectName("primary")
        connect_btn.setFixedWidth(100)
        connect_btn.clicked.connect(lambda: self._toggle_connect(tab_name))
        row1.addWidget(connect_btn)
        info.connect_btn = connect_btn

        row1.addStretch()

        btn_mode_terminal = QPushButton("🖥  Terminal")
        btn_mode_terminal.setObjectName("modeToggleActive")
        btn_mode_terminal.clicked.connect(lambda: self._switch_view_mode(tab_name, "terminal"))
        row1.addWidget(btn_mode_terminal)

        btn_mode_sftp = QPushButton("📁  SFTP")
        btn_mode_sftp.setObjectName("modeToggle")
        btn_mode_sftp.clicked.connect(lambda: self._switch_view_mode(tab_name, "sftp"))
        row1.addWidget(btn_mode_sftp)

        outer.addLayout(row1)
        info.btn_mode_terminal = btn_mode_terminal
        info.btn_mode_sftp = btn_mode_sftp

        # ---------- ردیف ۲: ابزارهای سرور/ترمینال (مجزا از مدیریت فایل) ----------
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        btn_tools = QToolButton()
        btn_tools.setText("🛠 Server Tools ▾")
        btn_tools.setObjectName("pillBtnDark")
        btn_tools.setToolTip("Run Script / Processes / Ping / Port Check")
        tools_menu = QMenu(self)
        for label, cb in [
            ("🚀 Run Script...", lambda: self.run_local_script(tab_name)),
            ("📊 Processes", lambda: self.show_processes(tab_name)),
            ("📡 Ping...", lambda: self.ping_host(tab_name)),
            ("🔍 Check Port...", lambda: self.check_port(tab_name)),
        ]:
            act = QAction(label, self)
            act.triggered.connect(cb)
            tools_menu.addAction(act)
        btn_tools.setMenu(tools_menu)
        btn_tools.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        row2.addWidget(btn_tools)

        row2.addStretch()

        btn_search = QToolButton()
        btn_search.setText("🔍")
        btn_search.setObjectName("iconToolBtn")
        btn_search.setToolTip("Search in Terminal (Ctrl+F)")
        btn_search.clicked.connect(lambda: self.search_in_terminal(tab_name))
        row2.addWidget(btn_search)

        btn_theme = QToolButton()
        btn_theme.setText("🎨")
        btn_theme.setObjectName("iconToolBtn")
        btn_theme.setToolTip("Terminal theme")
        btn_theme.clicked.connect(lambda: self._open_theme_picker(tab_name))
        row2.addWidget(btn_theme)

        btn_stop = QToolButton()
        btn_stop.setText("🛑")
        btn_stop.setObjectName("iconToolBtn")
        btn_stop.setToolTip("Send Ctrl+C")
        btn_stop.clicked.connect(lambda: self.stop_command(tab_name))
        row2.addWidget(btn_stop)

        btn_font_minus = QToolButton()
        btn_font_minus.setText("A−")
        btn_font_minus.setObjectName("iconToolBtn")
        btn_font_minus.clicked.connect(lambda: self.font_minus(tab_name))
        row2.addWidget(btn_font_minus)

        btn_font_plus = QToolButton()
        btn_font_plus.setText("A+")
        btn_font_plus.setObjectName("iconToolBtn")
        btn_font_plus.clicked.connect(lambda: self.font_plus(tab_name))
        row2.addWidget(btn_font_plus)

        btn_refresh = QToolButton()
        btn_refresh.setText("🔄")
        btn_refresh.setObjectName("iconToolBtn")
        btn_refresh.setToolTip("Refresh remote file list")
        btn_refresh.clicked.connect(lambda: self.refresh(tab_name))
        row2.addWidget(btn_refresh)

        btn_clear = QToolButton()
        btn_clear.setText("🧹")
        btn_clear.setObjectName("iconToolBtn")
        btn_clear.setToolTip("Clear terminal")
        btn_clear.clicked.connect(lambda: self.clear_terminal(tab_name))
        row2.addWidget(btn_clear)

        outer.addLayout(row2)

        # ---------- Stacked: صفحهٔ Terminal / صفحهٔ SFTP دوقلو ----------
        stacked = QStackedWidget()
        info.stacked = stacked

        # ===================== صفحهٔ ترمینال (تمام‌عرض) =====================
        term_page = QFrame()
        term_page.setObjectName("card")
        term_layout = QVBoxLayout(term_page)
        term_layout.setContentsMargins(12, 12, 12, 12)
        term_layout.setSpacing(8)

        term_title_row = QHBoxLayout()
        term_title_row.addWidget(self._label(f"Terminal — {tab_name}", "sectionTitle"))
        term_title_row.addStretch()
        term_layout.addLayout(term_title_row)

        term = QTextEdit()
        term.setObjectName("terminal")
        term.setReadOnly(True)
        term.setFont(QFont("Consolas", 12))
        term_layout.addWidget(term, 1)
        info.term = term

        shortcut = QShortcut(QKeySequence("Ctrl+F"), term)
        shortcut.activated.connect(lambda: self.search_in_terminal(tab_name))

        cmd_row = QHBoxLayout()
        cmd = QLineEdit()
        cmd.setPlaceholderText("Type command...")
        cmd.returnPressed.connect(lambda: self.exec_cmd(tab_name))
        cmd.installEventFilter(self)
        cmd.setProperty("tab_name", tab_name)
        cmd_row.addWidget(cmd, 1)
        info.cmd = cmd

        btn_run = QPushButton("Run")
        btn_run.setObjectName("primary")
        btn_run.setFixedWidth(60)
        btn_run.clicked.connect(lambda: self.exec_cmd(tab_name))
        cmd_row.addWidget(btn_run)
        term_layout.addLayout(cmd_row)

        stacked.addWidget(term_page)

        # ===================== صفحهٔ SFTP (پنل دوقلو Local | Remote) =====================
        sftp_page = QWidget()
        sftp_outer = QVBoxLayout(sftp_page)
        sftp_outer.setContentsMargins(0, 0, 0, 0)
        sftp_outer.setSpacing(8)

        sftp_splitter = QSplitter(Qt.Orientation.Horizontal)

        # ---------- پنل Local ----------
        local_pane = QFrame()
        local_pane.setObjectName("card")
        local_layout = QVBoxLayout(local_pane)
        local_layout.setContentsMargins(12, 10, 12, 12)
        local_layout.setSpacing(8)

        local_head = QHBoxLayout()
        local_head.addWidget(self._label("💻  Local", "sectionTitle"))
        local_head.addStretch()
        local_filter = QLineEdit()
        local_filter.setObjectName("searchBox")
        local_filter.setPlaceholderText("Filter...")
        local_filter.setFixedWidth(130)
        local_filter.textChanged.connect(lambda t, tn=tab_name: self._filter_tree_items(self.tabs[tn].local_tree, t))
        local_head.addWidget(local_filter)
        local_layout.addLayout(local_head)

        local_nav = QHBoxLayout()
        btn_local_up = QToolButton()
        btn_local_up.setText("⬅")
        btn_local_up.setObjectName("iconToolBtn")
        btn_local_up.clicked.connect(lambda: self._local_up(tab_name))
        local_nav.addWidget(btn_local_up)
        btn_local_home = QToolButton()
        btn_local_home.setText("🏠")
        btn_local_home.setObjectName("iconToolBtn")
        btn_local_home.clicked.connect(lambda: self._local_home(tab_name))
        local_nav.addWidget(btn_local_home)
        local_path_label = QLabel(info.local_path)
        local_path_label.setObjectName("fieldLabel")
        local_path_label.setStyleSheet("color:#cfd1de;")
        local_nav.addWidget(local_path_label, 1)
        info.local_path_label = local_path_label
        local_layout.addLayout(local_nav)

        local_btn_row = QHBoxLayout()
        local_btn_row.setSpacing(6)
        btn_local_upload_sel = QPushButton("⬆️ Upload Selected")
        btn_local_upload_sel.setObjectName("success")
        btn_local_upload_sel.clicked.connect(lambda: self._upload_selected_local(tab_name))
        local_btn_row.addWidget(btn_local_upload_sel)
        btn_local_refresh = QPushButton("🔄 Refresh")
        btn_local_refresh.clicked.connect(lambda: self._local_navigate(tab_name, self.tabs[tab_name].local_path))
        local_btn_row.addWidget(btn_local_refresh)
        local_layout.addLayout(local_btn_row)

        local_tree = QTreeWidget()
        local_tree.setColumnCount(3)
        local_tree.setHeaderLabels(["Name", "Type", "Size"])
        local_tree.setRootIsDecorated(False)
        local_tree.setAlternatingRowColors(True)
        local_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        local_tree.header().resizeSection(1, 80)
        local_tree.header().resizeSection(2, 80)
        local_tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        local_tree.itemDoubleClicked.connect(lambda item, col: self._on_local_dclick(tab_name, item))
        local_layout.addWidget(local_tree, 1)
        info.local_tree = local_tree

        sftp_splitter.addWidget(local_pane)

        # ---------- پنل Remote ----------
        remote_pane = QFrame()
        remote_pane.setObjectName("card")
        remote_layout = QVBoxLayout(remote_pane)
        remote_layout.setContentsMargins(12, 10, 12, 12)
        remote_layout.setSpacing(8)

        remote_head = QHBoxLayout()
        remote_head.addWidget(self._label(f"🖥️  {tab_name}", "sectionTitle"))
        remote_head.addStretch()
        remote_filter = QLineEdit()
        remote_filter.setObjectName("searchBox")
        remote_filter.setPlaceholderText("Filter...")
        remote_filter.setFixedWidth(130)
        remote_filter.textChanged.connect(lambda t, tn=tab_name: self._filter_tree_items(self.tabs[tn].tree, t))
        remote_head.addWidget(remote_filter)
        remote_layout.addLayout(remote_head)

        remote_nav = QHBoxLayout()
        path_entry = QLineEdit()
        path_entry.returnPressed.connect(lambda: self.go_path(tab_name))
        remote_nav.addWidget(path_entry, 1)
        info.path_entry = path_entry
        info.remote_path_label = path_entry

        btn_go = QToolButton()
        btn_go.setText("Go")
        btn_go.setObjectName("iconToolBtn")
        btn_go.clicked.connect(lambda: self.go_path(tab_name))
        remote_nav.addWidget(btn_go)

        btn_home = QToolButton()
        btn_home.setText("🏠")
        btn_home.setObjectName("iconToolBtn")
        btn_home.clicked.connect(lambda: self.go_home(tab_name))
        remote_nav.addWidget(btn_home)
        remote_layout.addLayout(remote_nav)

        # ردیف دکمه‌های عملیات فایل (فقط مربوط به مدیریت فایل — ابزارهای سرور
        # مثل Run Script/Processes/Ping/Port به «🛠 Server Tools» بالای تب منتقل شدند)
        remote_bf1 = QHBoxLayout()
        remote_bf1.setSpacing(6)
        for text, obj_name, cb in [
            ("Upload", None, lambda: self.upload(tab_name)),
            ("Download", None, lambda: self.download(tab_name)),
            ("New Folder", None, lambda: self.new_folder(tab_name)),
            ("New File", None, lambda: self.new_file(tab_name)),
            ("Delete", "danger", lambda: self.delete(tab_name)),
        ]:
            b = QPushButton(text)
            if obj_name:
                b.setObjectName(obj_name)
            b.clicked.connect(cb)
            remote_bf1.addWidget(b)
        remote_layout.addLayout(remote_bf1)

        bm_frame = QHBoxLayout()
        bm_frame.addWidget(self._label("Bookmarks:", "fieldLabel"))
        bookmark_combo = QComboBox()
        bookmark_combo.setMinimumWidth(140)
        bookmark_combo.addItem("")
        for bm in self.bookmarks:
            bookmark_combo.addItem(bm.split("|", 1)[0])
        bookmark_combo.activated.connect(lambda idx, tn=tab_name: self.go_to_bookmark(tn))
        info.bookmark_combo = bookmark_combo
        bm_frame.addWidget(bookmark_combo, 1)

        btn_bm_add = QToolButton()
        btn_bm_add.setText("📌")
        btn_bm_add.setObjectName("iconToolBtn")
        btn_bm_add.setToolTip("Add bookmark")
        btn_bm_add.clicked.connect(lambda: self.add_bookmark(tab_name))
        bm_frame.addWidget(btn_bm_add)

        btn_bm_rm = QToolButton()
        btn_bm_rm.setText("🗑️")
        btn_bm_rm.setObjectName("iconToolBtn")
        btn_bm_rm.setToolTip("Remove bookmark")
        btn_bm_rm.clicked.connect(lambda: self.remove_bookmark(tab_name))
        bm_frame.addWidget(btn_bm_rm)
        remote_layout.addLayout(bm_frame)

        progress_row = QHBoxLayout()
        progress_label = QLabel("")
        progress_label.setStyleSheet("color:#9aa3b8; font-size:11px;")
        progress_row.addWidget(progress_label)
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setTextVisible(False)
        progress_row.addWidget(progress_bar, 1)
        remote_layout.addLayout(progress_row)
        info.progress_bar = progress_bar
        info.progress_label = progress_label

        tree = QTreeWidget()
        tree.setColumnCount(3)
        tree.setHeaderLabels(["Name", "Type", "Size"])
        tree.setRootIsDecorated(False)
        tree.setAlternatingRowColors(True)
        tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tree.header().resizeSection(1, 90)
        tree.header().resizeSection(2, 90)
        tree.itemDoubleClicked.connect(lambda item, col: self.on_dclick(tab_name, item))
        remote_layout.addWidget(tree, 1)
        info.tree = tree

        sftp_splitter.addWidget(remote_pane)
        sftp_splitter.setSizes([480, 480])
        sftp_outer.addWidget(sftp_splitter)

        stacked.addWidget(sftp_page)
        stacked.setCurrentIndex(0)

        outer.addWidget(stacked, 1)

        self._term_write_now(info, "=== SSH Manager Pro ===\n")
        self._term_write_now(info, "✅ Proxy Support (HTTP/HTTPS/SOCKS4/SOCKS5)\n")
        self._term_write_now(info, "✅ X11 Forwarding\n")
        self._term_write_now(info, "✅ Session Manager\n")
        self._term_write_now(info, "✅ Search in Terminal (Ctrl+F)\n")
        self._term_write_now(info, "Connect to server using a host from the Hosts tab\n\n")

        # مقداردهی اولیهٔ پنل Local
        self._local_navigate(tab_name, info.local_path)

        return container

    def _switch_view_mode(self, tab_name, mode):
        info = self.get_info(tab_name)
        if not info or not info.stacked:
            return
        if mode == "terminal":
            info.stacked.setCurrentIndex(0)
            info.btn_mode_terminal.setObjectName("modeToggleActive")
            info.btn_mode_sftp.setObjectName("modeToggle")
        else:
            info.stacked.setCurrentIndex(1)
            info.btn_mode_terminal.setObjectName("modeToggle")
            info.btn_mode_sftp.setObjectName("modeToggleActive")
        for b in (info.btn_mode_terminal, info.btn_mode_sftp):
            b.style().unpolish(b)
            b.style().polish(b)

    def _filter_tree_items(self, tree, text):
        if not tree:
            return
        text = (text or "").lower().strip()
        for i in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(i)
            item.setHidden(text not in item.text(0).lower())

    # ============================================================
    # پنل Local (سمت چپ SFTP)
    # ============================================================
    def _local_navigate(self, tab_name, path):
        info = self.get_info(tab_name)
        if not info or not info.local_tree:
            return
        try:
            path = os.path.abspath(path)
            entries = os.listdir(path)
        except Exception as e:
            self.msg_warn("Local", f"Cannot open folder: {str(e)}")
            return

        info.local_path = path
        if info.local_path_label:
            info.local_path_label.setText(path)

        info.local_tree.clear()

        parent = os.path.dirname(path)
        if parent and parent != path:
            up_item = QTreeWidgetItem(info.local_tree, ["..", "Folder", "-"])

        rows = []
        for name in entries:
            if name.startswith('.'):
                continue
            full = os.path.join(path, name)
            try:
                if os.path.isdir(full):
                    rows.append((name, "Folder", "-"))
                else:
                    size = os.path.getsize(full)
                    rows.append((name, "File", self.fmt_size(size)))
            except Exception:
                continue

        rows.sort(key=lambda r: (r[1] != "Folder", r[0].lower()))
        for name, typ, size in rows:
            QTreeWidgetItem(info.local_tree, [name, typ, size])

    def _local_up(self, tab_name):
        info = self.get_info(tab_name)
        if not info:
            return
        parent = os.path.dirname(info.local_path.rstrip(os.sep))
        if parent:
            self._local_navigate(tab_name, parent)

    def _local_home(self, tab_name):
        self._local_navigate(tab_name, os.path.expanduser("~"))

    def _on_local_dclick(self, tab_name, item):
        info = self.get_info(tab_name)
        if not info:
            return
        name = item.text(0)
        typ = item.text(1)
        if name == "..":
            self._local_up(tab_name)
            return
        if typ == "Folder":
            self._local_navigate(tab_name, os.path.join(info.local_path, name))

    def _upload_selected_local(self, tab_name):
        info = self.get_info(tab_name)
        if not info or not info.connected or not info.sftp:
            self.msg_warn("Upload", "Not connected to server!")
            return
        selected = info.local_tree.selectedItems()
        files = [os.path.join(info.local_path, it.text(0)) for it in selected
                 if it.text(1) == "File" and it.text(0) != ".."]
        if not files:
            self.msg_warn("Upload", "Select one or more local files first!")
            return
        threading.Thread(target=self._upload_files, args=(info, files), daemon=True).start()

    # ============================================================
    # پنل انتخاب تم رنگی ترمینال
    # هر تم علاوه بر پس‌زمینه/متن پیش‌فرض، یک پالت کامل ۱۶ رنگی ANSI هم دارد
    # (دقیقاً مثل Termius: با عوض کردن تم، رنگ خروجی رنگی دستورات هم عوض می‌شود)
    # ============================================================
    TERMINAL_THEMES = [
        ("Default", "#0a0a0f", "#e4e5ec", {
            '30': '#4d4d4d', '31': '#ff5c5c', '32': '#55ff88', '33': '#ffd75f',
            '34': '#5fafff', '35': '#ff87d7', '36': '#5fd7d7', '37': '#e6e6e6',
            '90': '#808080', '91': '#ff8080', '92': '#8aff8a', '93': '#ffe680',
            '94': '#8ac6ff', '95': '#ffb3ea', '96': '#8ae8e8', '97': '#ffffff',
        }),
        ("Rosé Pine Moon", "#232136", "#e0def4", {
            '30': '#393552', '31': '#eb6f92', '32': '#9ccfd8', '33': '#f6c177',
            '34': '#3e8fb0', '35': '#c4a7e7', '36': '#9ccfd8', '37': '#e0def4',
            '90': '#6e6a86', '91': '#eb6f92', '92': '#9ccfd8', '93': '#f6c177',
            '94': '#3e8fb0', '95': '#c4a7e7', '96': '#9ccfd8', '97': '#ffffff',
        }),
        ("Cobalt2", "#132738", "#ffffff", {
            '30': '#142838', '31': '#ff5874', '32': '#3ad900', '33': '#ffc600',
            '34': '#0088ff', '35': '#ff9d00', '36': '#80fcff', '37': '#ffffff',
            '90': '#1f4662', '91': '#ff8080', '92': '#a5ff90', '93': '#ffe066',
            '94': '#5fc8ff', '95': '#ffc266', '96': '#c2feff', '97': '#ffffff',
        }),
        ("Octocat Dark", "#0d1117", "#c9d1d9", {
            '30': '#484f58', '31': '#ff7b72', '32': '#3fb950', '33': '#d29922',
            '34': '#58a6ff', '35': '#bc8cff', '36': '#39c5cf', '37': '#c9d1d9',
            '90': '#6e7681', '91': '#ffa198', '92': '#56d364', '93': '#e3b341',
            '94': '#79c0ff', '95': '#d2a8ff', '96': '#56d4dd', '97': '#f0f6fc',
        }),
        ("Ayu Dark", "#0f1419", "#e6e1cf", {
            '30': '#3d4149', '31': '#f28779', '32': '#d5ff80', '33': '#ffcc66',
            '34': '#73d0ff', '35': '#dfbfff', '36': '#95e6cb', '37': '#e6e1cf',
            '90': '#5c6773', '91': '#f28779', '92': '#d5ff80', '93': '#ffcc66',
            '94': '#73d0ff', '95': '#dfbfff', '96': '#95e6cb', '97': '#ffffff',
        }),
        ("Nord", "#2e3440", "#d8dee9", {
            '30': '#3b4252', '31': '#bf616a', '32': '#a3be8c', '33': '#ebcb8b',
            '34': '#81a1c1', '35': '#b48ead', '36': '#88c0d0', '37': '#e5e9f0',
            '90': '#4c566a', '91': '#bf616a', '92': '#a3be8c', '93': '#ebcb8b',
            '94': '#81a1c1', '95': '#b48ead', '96': '#8fbcbb', '97': '#eceff4',
        }),
        ("Cyberpunk", "#1a1030", "#39ffe4", {
            '30': '#2a1a4a', '31': '#ff2079', '32': '#00ff9f', '33': '#fff700',
            '34': '#00d9ff', '35': '#d400ff', '36': '#39ffe4', '37': '#ffffff',
            '90': '#5a3a8a', '91': '#ff5fa8', '92': '#5fffc4', '93': '#fff97f',
            '94': '#5fe8ff', '95': '#ef7fff', '96': '#8dfff0', '97': '#ffffff',
        }),
        ("Cyberpunk Scarlet", "#170810", "#ff2954", {
            '30': '#3a0f1a', '31': '#ff2954', '32': '#ff6b8a', '33': '#ffb347',
            '34': '#ff5c7a', '35': '#ff2954', '36': '#ff8fa3', '37': '#ffe0e6',
            '90': '#7a2f42', '91': '#ff5c7a', '92': '#ff9fb3', '93': '#ffcf8f',
            '94': '#ff7f9f', '95': '#ff5c7a', '96': '#ffb3c1', '97': '#ffffff',
        }),
    ]

    def _open_theme_picker(self, tab_name):
        dialog = QDialog(self)
        dialog.setWindowTitle("🎨 Terminal Theme")
        dialog.resize(360, 420)
        dialog.setStyleSheet(MODERN_QSS)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.addWidget(self._label("Themes", "sectionTitle"))

        grid = QGridLayout()
        grid.setSpacing(10)
        for i, (name, bg, fg, palette) in enumerate(self.TERMINAL_THEMES):
            btn = QPushButton(f"  {name}")
            btn.setFixedHeight(46)
            btn.setStyleSheet(
                f"text-align:left; padding-left:14px; border-radius:8px; "
                f"background-color:{bg}; color:{fg}; border:1px solid #262838; "
                f"border-left: 6px solid {fg}; font-weight:600;"
            )
            btn.clicked.connect(
                lambda checked, b=bg, f=fg, p=palette: self._apply_terminal_theme(tab_name, b, f, p, dialog)
            )
            grid.addWidget(btn, i // 2, i % 2)
        layout.addLayout(grid)
        layout.addStretch()

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dialog.reject)
        layout.addWidget(btn_close)

        dialog.exec()

    def _apply_terminal_theme(self, tab_name, bg, fg, palette, dialog=None):
        info = self.get_info(tab_name)
        if info and info.term:
            info.term.setStyleSheet(
                f"background-color:{bg}; color:{fg}; border:1px solid #1c1d28; "
                f"border-radius:0px; font-family:'Consolas','Cascadia Mono','Courier New',monospace;"
            )
            # پالت رنگ ANSI هم عوض می‌شود — از این به بعد خروجی رنگی دستورات
            # (مثل ls, git diff, prompt رنگی) با تم جدید هماهنگ می‌شود
            info.fg_colors = dict(palette)
            info.term_bg = bg
            info.term_fg = fg
        if dialog:
            dialog.accept()

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if isinstance(obj, QLineEdit) and event.type() == QEvent.Type.KeyPress:
            tab_name = obj.property("tab_name")
            if tab_name:
                if event.key() == Qt.Key.Key_Up:
                    self.history_up(tab_name)
                    return True
                elif event.key() == Qt.Key.Key_Down:
                    self.history_down(tab_name)
                    return True
        return super().eventFilter(obj, event)

    def close_tab(self, tab_name):
        if tab_name not in self.tabs:
            return

        info = self.tabs[tab_name]
        if info.connected:
            try:
                if info.channel:
                    info.channel.close()
                if info.sftp:
                    info.sftp.close()
                if info.ssh:
                    info.ssh.close()
            except Exception:
                pass

        idx = self.tabview.indexOf(info.container)
        if idx >= 0:
            self.tabview.removeTab(idx)
        del self.tabs[tab_name]

        if self.tabs:
            first_tab = list(self.tabs.keys())[0]
            self.tabview.setCurrentWidget(self.tabs[first_tab].container)
            self.current_tab = first_tab
        else:
            # هیچ تب اتصالی باقی نمانده؛ به تب Hosts برمی‌گردیم
            self.tabview.setCurrentIndex(0)
            self.current_tab = None

    # ============================================================
    # بوکمارک‌ها
    # ============================================================
    def load_bookmarks(self):
        try:
            if os.path.exists(self.bookmarks_file):
                with open(self.bookmarks_file, 'r') as f:
                    self.bookmarks = json.load(f)
        except Exception:
            self.bookmarks = []

    def save_bookmarks(self):
        try:
            with open(self.bookmarks_file, 'w') as f:
                json.dump(self.bookmarks, f)
        except Exception:
            pass

    def add_bookmark(self, tab_name):
        info = self.get_info(tab_name)
        if not info:
            return
        if not info.connected:
            self.msg_warn("Warning", "Not connected to server!")
            return

        current_path = info.current_path
        if not current_path:
            return

        for bm in self.bookmarks:
            name, path = bm.split("|", 1)
            if path == current_path:
                self.msg_info("Info", "This path is already in bookmarks!")
                return

        name = self.input_text("Add Bookmark", f"Enter a name for this bookmark:\n{current_path}")
        if name is None:
            return
        if not name:
            name = os.path.basename(current_path) or current_path

        bookmark_entry = f"{name}|{current_path}"
        self.bookmarks.append(bookmark_entry)
        self.update_bookmark_menus()
        self.save_bookmarks()

        self.term_write(info, f"[Bookmark] Added: {name} -> {current_path}\n", "msg_info")

    def remove_bookmark(self, tab_name):
        info = self.get_info(tab_name)
        if not info or not info.bookmark_combo:
            return
        selected = info.bookmark_combo.currentText()
        if not selected:
            self.msg_warn("Warning", "No bookmark selected!")
            return

        for i, bm in enumerate(self.bookmarks):
            name, path = bm.split("|", 1)
            if name == selected:
                if self.ask_yes_no("Remove Bookmark", f"Remove '{name}' from bookmarks?"):
                    del self.bookmarks[i]
                    self.update_bookmark_menus()
                    self.save_bookmarks()
                    self.term_write(info, f"[Bookmark] Removed: {name}\n", "msg_info")
                break

    def go_to_bookmark(self, tab_name):
        info = self.get_info(tab_name)
        if not info or not info.bookmark_combo:
            return
        selection = info.bookmark_combo.currentText()
        if not selection:
            return
        for bm in self.bookmarks:
            name, path = bm.split("|", 1)
            if name == selection:
                info.current_path = path
                info.path_entry.setText(path)
                self._refresh_files(info)
                self.term_write(info, f"[Bookmark] Navigated to: {name} -> {path}\n", "msg_info")
                break

    def update_bookmark_menus(self):
        names = [""] + [bm.split("|", 1)[0] for bm in self.bookmarks]
        for info in self.tabs.values():
            if info.bookmark_combo:
                info.bookmark_combo.blockSignals(True)
                info.bookmark_combo.clear()
                info.bookmark_combo.addItems(names)
                info.bookmark_combo.setCurrentIndex(0)
                info.bookmark_combo.blockSignals(False)

    # ============================================================
    # کلید SSH
    # ============================================================
    def select_ssh_key(self):
        key_file, _ = QFileDialog.getOpenFileName(
            self, "Select SSH Private Key", "",
            "SSH Keys (*.pem *.key *.ppk id_rsa id_ed25519);;All Files (*.*)"
        )
        if not key_file:
            return
        if key_file.endswith('.pub'):
            self.msg_warn("Warning", "Please select PRIVATE key (without .pub)")
            return

        self.ssh_key_path = key_file
        self.key_path_label.setText(os.path.basename(key_file))
        self.key_path_label.setStyleSheet("color:#3ddc97;")

        info = self.get_info()
        if info:
            self.term_write(info, f"[Key] Selected: {key_file}\n", "msg_info")

        has_passphrase = self.key_has_passphrase(key_file)
        if has_passphrase:
            self.ssh_key_passphrase = self.input_text("SSH Key Passphrase", "Enter passphrase for SSH key:", password=True)
        else:
            self.ssh_key_passphrase = None

        test_key = self.load_private_key()
        if test_key and info:
            self.term_write(info, "[Key] ✅ Key loaded successfully!\n", "msg_ok")

    def key_has_passphrase(self, key_path):
        try:
            with open(key_path, 'r') as f:
                content = f.read()

            if 'ENCRYPTED' in content:
                return True
            if 'Proc-Type: 4,ENCRYPTED' in content:
                return True
            if 'DEK-Info' in content:
                return True

            if 'BEGIN OPENSSH PRIVATE KEY' in content:
                try:
                    match = re.search(r'BEGIN OPENSSH PRIVATE KEY\s+(.+?)\s+END OPENSSH PRIVATE KEY', content, re.DOTALL)
                    if match:
                        b64_data = ''.join(match.group(1).split())
                        decoded = base64.b64decode(b64_data)
                        if len(decoded) > 15 and decoded[15] == 1:
                            return True
                except Exception:
                    pass
            return False
        except Exception:
            return False

    def load_private_key(self):
        if not self.ssh_key_path:
            return None
        try:
            with open(self.ssh_key_path, 'r') as f:
                content = f.read()

            if 'BEGIN RSA PRIVATE KEY' in content:
                return paramiko.RSAKey.from_private_key_file(self.ssh_key_path, password=self.ssh_key_passphrase)
            elif 'BEGIN OPENSSH PRIVATE KEY' in content:
                try:
                    return paramiko.Ed25519Key.from_private_key_file(self.ssh_key_path, password=self.ssh_key_passphrase)
                except paramiko.PasswordRequiredException:
                    self.ssh_key_passphrase = self.input_text("SSH Key Passphrase", "Passphrase required:", password=True)
                    if self.ssh_key_passphrase:
                        return paramiko.Ed25519Key.from_private_key_file(self.ssh_key_path, password=self.ssh_key_passphrase)
                    return None
            elif 'BEGIN EC PRIVATE KEY' in content:
                return paramiko.ECDSAKey.from_private_key_file(self.ssh_key_path, password=self.ssh_key_passphrase)
            else:
                return None
        except Exception:
            return None

    def generate_ssh_key(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Generate SSH Key")
        dialog.setFixedSize(380, 260)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        layout.addWidget(self._label("Key Type:", "fieldLabel"))
        key_type_combo = QComboBox()
        key_type_combo.addItems(["RSA", "ED25519"])
        layout.addWidget(key_type_combo)

        layout.addWidget(self._label("Passphrase (optional):", "fieldLabel"))
        passphrase_entry = QLineEdit()
        passphrase_entry.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(passphrase_entry)

        note = QLabel("⚠️ Leave empty for no passphrase")
        note.setStyleSheet("color:#7d879e;")
        layout.addWidget(note)
        layout.addStretch()

        btn_generate = QPushButton("Generate")
        btn_generate.setObjectName("primary")

        def do_generate():
            key_type = key_type_combo.currentText()
            passphrase = passphrase_entry.text() or None
            dialog.accept()
            threading.Thread(target=self._generate_key_thread, args=(key_type, passphrase), daemon=True).start()

        btn_generate.clicked.connect(do_generate)
        layout.addWidget(btn_generate)
        dialog.exec()

    def _generate_key_thread(self, key_type, passphrase):
        try:
            save_dir = self.sync_call(lambda: QFileDialog.getExistingDirectory(self, "Select directory to save key"))
            if not save_dir:
                return

            timestamp = int(time.time())
            key_name = f"id_{key_type.lower()}_{timestamp}"
            private_path = os.path.join(save_dir, key_name)

            cmd = ['ssh-keygen', '-t', key_type.lower(), '-f', private_path, '-N', passphrase if passphrase else ""]
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)

            if result.returncode == 0:
                public_path = f"{private_path}.pub"
                self.ui(lambda: self._key_generated_message(private_path, public_path))
            else:
                info = self.get_info()
                if info:
                    self.term_write(info, f"[Error] {result.stderr}\n", "msg_err")
        except Exception as e:
            info = self.get_info()
            if info:
                self.term_write(info, f"[Error] {str(e)}\n", "msg_err")

    def _key_generated_message(self, private_path, public_path):
        info = self.get_info()
        if info:
            self.term_write(info, "[Key] ✅ Key generated successfully!\n", "msg_ok")
            self.term_write(info, f"[Key] Private: {private_path}\n", "msg_info")
            self.term_write(info, f"[Key] Public: {public_path}\n", "msg_info")

        self.ssh_key_path = private_path
        self.key_path_label.setText(os.path.basename(private_path))
        self.key_path_label.setStyleSheet("color:#3ddc97;")
        QMessageBox.information(self, "Success", f"Key generated!\n\nPrivate: {private_path}\nPublic: {public_path}")

    def show_public_key(self):
        if not self.ssh_key_path:
            self.msg_warn("Warning", "No SSH key selected")
            return
        try:
            public_path = self.ssh_key_path + ".pub"
            if os.path.exists(public_path):
                with open(public_path, 'r') as f:
                    public_key = f.read().strip()
                QApplication.clipboard().setText(public_key)
                QMessageBox.information(self, "Public Key", f"Public key copied to clipboard!\n\n{public_key[:100]}...")
            else:
                self.msg_warn("Warning", "Public key file not found")
        except Exception:
            pass

    def toggle_agent(self):
        self.ssh_agent_enabled = self.agent_check.isChecked()
        status = "enabled" if self.ssh_agent_enabled else "disabled"
        info = self.get_info()
        if info:
            self.term_write(info, f"[Agent] SSH Agent {status}\n", "msg_info")

    # ============================================================
    # جستجو در ترمینال (Ctrl+F)
    # ============================================================
    def search_in_terminal(self, tab_name):
        info = self.get_info(tab_name)
        if not info or not info.term:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("🔍 Search in Terminal")
        dialog.setFixedSize(450, 180)
        dialog.setStyleSheet(MODERN_QSS)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        
        search_row = QHBoxLayout()
        search_row.addWidget(self._label("Search:", "fieldLabel"))
        search_entry = QLineEdit()
        search_entry.setPlaceholderText("Enter text to search...")
        search_entry.setMinimumWidth(250)
        search_row.addWidget(search_entry, 1)
        layout.addLayout(search_row)
        
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        btn_find = QPushButton("🔍 Find")
        btn_find.setObjectName("primary")
        btn_find.clicked.connect(lambda: self._find_in_terminal(info, search_entry.text(), dialog))
        btn_row.addWidget(btn_find)
        
        btn_next = QPushButton("⬇ Next")
        btn_next.clicked.connect(lambda: self._find_next(info))
        btn_row.addWidget(btn_next)
        
        btn_prev = QPushButton("⬆ Previous")
        btn_prev.clicked.connect(lambda: self._find_prev(info))
        btn_row.addWidget(btn_prev)
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dialog.accept)
        btn_row.addWidget(btn_close)
        
        layout.addLayout(btn_row)
        
        search_entry.returnPressed.connect(lambda: self._find_in_terminal(info, search_entry.text(), dialog))
        
        dialog.exec()
    
    def _find_in_terminal(self, info, text, dialog=None):
        if not text or not info.term:
            return
        
        info._last_search = text
        info._search_pos = 0
        
        content = info.term.toPlainText()
        
        cursor = info.term.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.setCharFormat(QTextCharFormat())
        
        pos = content.find(text, info._search_pos)
        if pos >= 0:
            cursor = info.term.textCursor()
            cursor.setPosition(pos)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, len(text))
            
            fmt = QTextCharFormat()
            fmt.setBackground(QColor("#3ddc97"))
            fmt.setForeground(QColor("#0b1310"))
            cursor.setCharFormat(fmt)
            
            info.term.setTextCursor(cursor)
            info.term.ensureCursorVisible()
            
            info._search_pos = pos + len(text)
            info._last_found_pos = pos
            
            if dialog:
                total = content.count(text)
                dialog.setWindowTitle(f"🔍 Search: {text} ({pos//len(text)+1 if total > 0 else 0}/{total})")
        else:
            if info._search_pos > 0:
                info._search_pos = 0
                self._find_in_terminal(info, text, dialog)
            else:
                self.term_write(info, f"[Search] ❌ '{text}' not found\n", "msg_err")
    
    def _find_next(self, info):
        if hasattr(info, '_last_search') and info._last_search:
            self._find_in_terminal(info, info._last_search)
    
    def _find_prev(self, info):
        if hasattr(info, '_last_search') and info._last_search:
            text = info._last_search
            content = info.term.toPlainText()
            
            pos = content.rfind(text, 0, info._search_pos - len(text))
            if pos >= 0:
                cursor = info.term.textCursor()
                cursor.setPosition(pos)
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, len(text))
                
                fmt = QTextCharFormat()
                fmt.setBackground(QColor("#3ddc97"))
                fmt.setForeground(QColor("#0b1310"))
                cursor.setCharFormat(fmt)
                
                info.term.setTextCursor(cursor)
                info.term.ensureCursorVisible()
                
                info._search_pos = pos + len(text)
                info._last_found_pos = pos

    # ============================================================
    # افزودن کلید به سرور
    # ============================================================
    def add_key_to_server(self):
        if not self.ssh_key_path:
            self.msg_warn("Warning", "No SSH key selected.")
            return

        info = self.get_info()
        if not info:
            return
        if not info.connected:
            self.msg_warn("Warning", "Not connected to server.")
            return

        try:
            public_path = self.ssh_key_path + ".pub"
            if not os.path.exists(public_path):
                self.msg_error("Error", "Public key file not found!")
                return
            with open(public_path, 'r') as f:
                public_key = f.read().strip()
            if not public_key:
                self.msg_error("Error", "Public key is empty!")
                return
        except Exception as e:
            self.msg_error("Error", f"Failed to read public key: {str(e)}")
            return

        if not self.ask_yes_no(
            "Add Key to Server",
            f"Add this public key to server?\n\n{public_key[:80]}...\n\nThis will allow you to connect without password."
        ):
            return

        self.term_write(info, "[Key] Adding public key to server...\n", "msg_info")
        threading.Thread(target=self._add_key_to_server, args=(info, public_key), daemon=True).start()

    def _add_key_to_server(self, info, public_key):
        try:
            commands = [
                'mkdir -p ~/.ssh',
                'chmod 700 ~/.ssh',
                f'echo "{public_key}" >> ~/.ssh/authorized_keys',
                'chmod 600 ~/.ssh/authorized_keys',
                'grep -q "' + public_key[:20] + '" ~/.ssh/authorized_keys && echo "KEY_ADDED_SUCCESS" || echo "KEY_ADDED_FAILED"'
            ]

            for cmd in commands:
                output, exit_status = self._exec_ssh_command(info, cmd, timeout=15)
                output = (output or "").strip()

                if "KEY_ADDED_SUCCESS" in output:
                    self.term_write(info, "[Key] ✅ Public key added successfully!\n", "msg_ok")
                    self.term_write(info, "[Key] You can now connect using SSH key authentication!\n", "msg_info")
                    self.msg_info("Success", "SSH key added to server!")
                    return

                if exit_status not in (0, None) and "KEY_ADDED" not in cmd:
                    self.term_write(info, f"[Error] {output}\n", "msg_err")
                    return

            self.term_write(info, "[Key] ❌ Failed to add key.\n", "msg_err")
        except Exception as e:
            self.term_write(info, f"[Error] {str(e)}\n", "msg_err")

    # ============================================================
    # اجرای اسکریپت محلی روی سرور
    # ============================================================
    def run_local_script(self, tab_name):
        info = self.get_info(tab_name)
        if not info:
            return
        if not info.connected:
            self.msg_warn("Warning", "Not connected to server!")
            return

        script_file, _ = QFileDialog.getOpenFileName(
            self, "Select Script to Run on Server", "",
            "Python (*.py);;Shell (*.sh *.bash);;JavaScript (*.js);;Ruby (*.rb);;Perl (*.pl);;All Files (*.*)"
        )
        if not script_file:
            return

        args = self.input_text("Script Arguments", "Enter arguments for script (optional):") or ""

        self.term_write(info, f"[Script] Running: {os.path.basename(script_file)}\n", "msg_info")
        threading.Thread(target=self._run_local_script, args=(info, script_file, args), daemon=True).start()

    def _run_local_script(self, info, script_file, args):
        try:
            script_name = os.path.basename(script_file)
            remote_path = f"/tmp/{script_name}_{int(time.time())}"

            self.term_write(info, "[Script] Uploading script to server...\n", "msg_info")
            info.sftp.put(script_file, remote_path)

            self._exec_ssh_command(info, f"chmod +x {remote_path}", timeout=10)

            if script_name.endswith('.py'):
                cmd = f"python3 {remote_path} {args}"
            elif script_name.endswith('.sh') or script_name.endswith('.bash'):
                cmd = f"bash {remote_path} {args}"
            elif script_name.endswith('.js'):
                cmd = f"node {remote_path} {args}"
            elif script_name.endswith('.rb'):
                cmd = f"ruby {remote_path} {args}"
            elif script_name.endswith('.pl'):
                cmd = f"perl {remote_path} {args}"
            else:
                cmd = f"{remote_path} {args}"

            self.term_write(info, f"[Script] Executing: {cmd}\n", "msg_info")
            self.term_write(info, "─" * 50 + "\n", "msg_info")

            output, exit_status = self._exec_ssh_command(info, cmd, timeout=120)
            output = (output or "").strip()

            if output:
                tag = "msg_ok" if exit_status == 0 else "msg_err"
                self.term_write(info, f"{output}\n", tag)

            self.term_write(info, "─" * 50 + "\n", "msg_info")

            if self.ask_yes_no("Cleanup", "Delete script from server after execution?"):
                self._exec_ssh_command(info, f"rm -f {remote_path}", timeout=10)
                self.term_write(info, "[Script] Cleanup: Script removed from server\n", "msg_info")

            self.term_write(info, "[Script] ✅ Execution completed!\n", "msg_ok")
        except Exception as e:
            self.term_write(info, f"[Script] ❌ Error: {str(e)}\n", "msg_err")

    # ============================================================
    # ویرایش فایل از راه دور
    # ============================================================
    def edit_remote_file(self, tab_name, file_path):
        info = self.get_info(tab_name)
        if not info or not info.connected or not info.sftp:
            self.msg_error("Error", "Not connected to server!")
            return

        ext = os.path.splitext(file_path)[1]

        try:
            temp_file = tempfile.NamedTemporaryFile(mode='w+', suffix=ext, delete=False, encoding='utf-8')
            temp_path = temp_file.name
            temp_file.close()

            self.term_write(info, f"[Editor] Downloading: {os.path.basename(file_path)}\n", "msg_info")
            info.sftp.get(file_path, temp_path)

            # به‌جای رد کردن کامل فایل بر اساس پسوند (مثل نسخهٔ قبلی که فقط
            # چند فرمت خاص را مجاز می‌دانست)، هر فرمتی قابل باز شدن است.
            # فقط اگر فایل احتمالاً باینری باشد (بایت null در ابتدای آن)،
            # قبل از باز کردن هشدار می‌دهیم — چون ذخیرهٔ دوبارهٔ یک باینری
            # به‌صورت متن می‌تواند آن را خراب کند.
            if self._looks_binary(temp_path):
                proceed = self.ask_yes_no(
                    "Binary File",
                    f"'{os.path.basename(file_path)}' looks like a binary file "
                    f"(not plain text). Editing and saving it may corrupt it.\n\n"
                    f"Open it anyway?"
                )
                if not proceed:
                    try:
                        os.unlink(temp_path)
                    except Exception:
                        pass
                    return

            self._open_editor(info, temp_path, file_path)
        except Exception as e:
            self.msg_error("Error", f"Failed to open file: {str(e)}")
            self.term_write(info, f"[Editor] ❌ Error: {str(e)}\n", "msg_err")

    def _looks_binary(self, path, sample_size=8192):
        """تشخیص ابتدایی باینری‌بودن فایل با بررسی وجود بایت null در نمونهٔ ابتدایی."""
        try:
            with open(path, 'rb') as f:
                chunk = f.read(sample_size)
            return b'\x00' in chunk
        except Exception:
            return False

    def _open_editor(self, info, temp_path, remote_path):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Editing: {os.path.basename(remote_path)}")
        dialog.resize(820, 620)
        dialog.setStyleSheet(MODERN_QSS)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.addWidget(self._label(f"File: {remote_path}", "fieldLabel"))
        top_row.addStretch()
        layout.addLayout(top_row)

        text_editor = QTextEdit()
        text_editor.setFont(QFont("Consolas", 12))
        try:
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            with open(temp_path, 'r', encoding='latin-1') as f:
                content = f.read()
        text_editor.setPlainText(content)
        layout.addWidget(text_editor, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        def save_file():
            new_content = text_editor.toPlainText()
            try:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                self.term_write(info, f"[Editor] Uploading: {os.path.basename(remote_path)}\n", "msg_info")
                info.sftp.put(temp_path, remote_path)
                self.term_write(info, "[Editor] ✅ File saved successfully!\n", "msg_ok")

                QMessageBox.information(dialog, "Success", "File saved successfully!")
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to save file: {str(e)}")
                self.term_write(info, f"[Editor] ❌ Error: {str(e)}\n", "msg_err")

        btn_save = QPushButton("💾 Save")
        btn_save.setObjectName("success")
        btn_save.clicked.connect(save_file)
        btn_row.addWidget(btn_save)

        btn_cancel = QPushButton("❌ Cancel")
        btn_cancel.setObjectName("danger")
        btn_cancel.clicked.connect(dialog.reject)
        btn_row.addWidget(btn_cancel)

        layout.addLayout(btn_row)

        QShortcut(QKeySequence("Ctrl+S"), dialog).activated.connect(save_file)
        QShortcut(QKeySequence("Escape"), dialog).activated.connect(dialog.reject)

        def cleanup():
            try:
                os.unlink(temp_path)
            except Exception:
                pass

        dialog.finished.connect(lambda _: cleanup())
        dialog.exec()

    # ============================================================
    # مدیریت فرآیندها
    # ============================================================
    def show_processes(self, tab_name):
        info = self.get_info(tab_name)
        if not info:
            return
        if not info.connected:
            self.msg_warn("Warning", "Not connected to server!")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Process Manager")
        dialog.resize(920, 600)
        dialog.setStyleSheet(MODERN_QSS)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(self._label("🔄 Running Processes", "sectionTitle"))
        header.addStretch()
        btn_refresh = QPushButton("🔄 Refresh")
        header.addWidget(btn_refresh)
        layout.addLayout(header)

        info_row = QHBoxLayout()
        hint = QLabel("Select a process and click 'Kill' to terminate it")
        hint.setStyleSheet("color:#7d879e;")
        info_row.addWidget(hint)
        info_row.addStretch()
        btn_kill = QPushButton("💀 Kill Selected")
        btn_kill.setObjectName("danger")
        info_row.addWidget(btn_kill)
        layout.addLayout(info_row)

        tree = QTreeWidget()
        tree.setColumnCount(5)
        tree.setHeaderLabels(["PID", "User", "CPU%", "MEM%", "Command"])
        tree.setRootIsDecorated(False)
        tree.setAlternatingRowColors(True)
        tree.header().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(tree, 1)

        btn_refresh.clicked.connect(lambda: self._refresh_processes(info, tree))
        btn_kill.clicked.connect(lambda: self._kill_process(info, tree))

        self._refresh_processes(info, tree)
        dialog.exec()

    def _refresh_processes(self, info, tree):
        try:
            output, exit_status = self._exec_ssh_command(
                info,
                'ps aux --sort=-%cpu | head -50 | awk \'{print $2","$1","$3","$4","$11}\'',
                timeout=15
            )
            output = (output or "").strip()

            if not output:
                output, exit_status = self._exec_ssh_command(
                    info,
                    'ps aux | head -50 | awk \'{print $2","$1","$3","$4","$11}\'',
                    timeout=15
                )
                output = (output or "").strip()

            tree.clear()
            for line in output.split('\n'):
                if not line.strip():
                    continue
                parts = line.split(',')
                if len(parts) >= 5:
                    pid, user, cpu, mem, cmd = parts[0], parts[1], parts[2], parts[3], parts[4]
                    if len(cmd) > 50:
                        cmd = cmd[:47] + "..."
                    QTreeWidgetItem(tree, [pid, user, cpu, mem, cmd])
        except Exception as e:
            self.msg_error("Error", f"Failed to get processes: {str(e)}")

    def _kill_process(self, info, tree):
        selected = tree.selectedItems()
        if not selected:
            self.msg_warn("Warning", "No process selected!")
            return

        item = selected[0]
        pid = item.text(0)
        cmd = item.text(4)

        if not self.ask_yes_no("Kill Process", f"Are you sure you want to kill process {pid} ({cmd})?"):
            return

        try:
            output, exit_status = self._exec_ssh_command(info, f"kill -9 {pid}", timeout=10)

            if exit_status not in (0, None):
                self.msg_error("Error", f"Failed to kill process: {output}")
            else:
                self.msg_info("Success", f"Process {pid} killed successfully!")
                self.term_write(info, f"[Process] Killed PID: {pid} ({cmd})\n", "msg_info")
                self._refresh_processes(info, tree)
        except Exception as e:
            self.msg_error("Error", f"Failed to kill process: {str(e)}")

    # ============================================================
    # پینگ و بررسی پورت
    # ============================================================
    def ping_host(self, tab_name):
        info = self.get_info(tab_name)
        if not info:
            return
        if not info.connected:
            self.msg_warn("Warning", "Not connected to server!")
            return

        host = self.input_text("Ping Host", "Enter hostname or IP to ping:")
        if not host:
            return

        self.term_write(info, f"[Ping] Pinging {host}...\n", "msg_info")
        threading.Thread(target=self._ping_host, args=(info, host), daemon=True).start()

    def _ping_host(self, info, host):
        try:
            # از shlex.quote استفاده می‌کنیم تا اگر کاربر هاست عجیبی وارد کرد،
            # در دستور شل مشکلی پیش نیاید.
            import shlex
            safe_host = shlex.quote(host)
            output, exit_status = self._exec_ssh_command(info, f"ping -c 4 -W 3 {safe_host}", timeout=20)
            output = output or ""

            self.term_write(info, "─" * 50 + "\n", "msg_info")
            if output.strip():
                tag = "msg_ok" if exit_status == 0 else "msg_err"
                self.term_write(info, output + "\n", tag)
            else:
                self.term_write(info, "[Ping] No output received (host unreachable or ping not available on server)\n", "msg_err")
            self.term_write(info, "─" * 50 + "\n", "msg_info")
        except Exception as e:
            self.term_write(info, f"[Error] {str(e)}\n", "msg_err")

    def check_port(self, tab_name):
        info = self.get_info(tab_name)
        if not info:
            return
        if not info.connected:
            self.msg_warn("Warning", "Not connected to server!")
            return

        host_port = self.input_text("Check Port", "Enter host and port (host:port):\nExample: google.com:80")
        if not host_port:
            return

        try:
            host, port = host_port.split(':')
            port = int(port)
        except Exception:
            self.msg_error("Error", "Invalid format! Use host:port")
            return

        self.term_write(info, f"[Port Check] Checking {host}:{port}...\n", "msg_info")
        threading.Thread(target=self._check_port, args=(info, host, port), daemon=True).start()

    def _check_port(self, info, host, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                self.term_write(info, f"[Port Check] ✅ {host}:{port} is OPEN\n", "msg_ok")
            else:
                self.term_write(info, f"[Port Check] ❌ {host}:{port} is CLOSED\n", "msg_err")
        except Exception as e:
            self.term_write(info, f"[Error] {str(e)}\n", "msg_err")

    # ============================================================
    # اتصال با پشتیبانی از Proxy و X11
    # ============================================================
    def _toggle_connect(self, tab_name):
        """دکمهٔ واحد Connect/Disconnect مخصوص همین تب — رفتار بر اساس وضعیت فعلی تعیین می‌شود."""
        info = self.get_info(tab_name)
        if info and info.connected:
            self.do_disconnect(tab_name)
        else:
            self.do_connect(tab_name)

    def do_connect(self, tab_name=None):
        tab_name = tab_name or self.current_tab
        if not tab_name or tab_name not in self.tabs:
            self.msg_warn("Warning", "No active tab!")
            return

        host = self.host.text().strip()
        user = self.user.text().strip()
        pwd = self.passw.text()

        try:
            port = int(self.port.text().strip())
        except Exception:
            port = 22

        if not host or not user:
            self.msg_warn("Error", "Enter IP and Username")
            return

        info = self.tabs[tab_name]
        info.password = pwd

        self.save_settings()
        if info.connect_btn:
            info.connect_btn.setEnabled(False)
            info.connect_btn.setText("Connecting...")

        proxy_config = self.get_socket_proxy()
        threading.Thread(target=self._connect, args=(info, host, port, user, pwd, proxy_config), daemon=True).start()

    def _connect(self, info, host, port, user, pwd, proxy_config):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            sock = None
            if proxy_config:
                self.term_write(info, f"[Proxy] Using {proxy_config['type'].upper()} proxy: {proxy_config['host']}:{proxy_config['port']}\n", "msg_info")
                sock = self.create_proxy_socket(proxy_config, info)
                if not sock:
                    self.ui(lambda: self.on_error(info, "Failed to create proxy connection"))
                    return

            connect_kwargs = {
                'hostname': host,
                'port': port,
                'username': user,
                'timeout': 30,
                'allow_agent': self.ssh_agent_enabled,
                'look_for_keys': False,
                'sock': sock
            }

            if self.ssh_key_path:
                private_key = self.load_private_key()
                if private_key:
                    connect_kwargs['pkey'] = private_key
                    self.term_write(info, "[Auth] Using SSH key\n", "msg_info")
                elif pwd:
                    connect_kwargs['password'] = pwd
                    self.term_write(info, "[Auth] Using password\n", "msg_info")
                else:
                    self.ui(lambda: self.on_error(info, "Key failed and no password"))
                    return
            elif pwd:
                connect_kwargs['password'] = pwd
                self.term_write(info, "[Auth] Using password\n", "msg_info")
            else:
                self.ui(lambda: self.on_error(info, "No authentication method"))
                return

            if self.x11_forwarding:
                self.term_write(info, "[X11] X11 Forwarding enabled\n", "msg_info")
                connect_kwargs['x11_forwarding'] = True

            ssh.connect(**connect_kwargs)
            sftp = ssh.open_sftp()
            channel = ssh.invoke_shell(term="xterm", width=220, height=50)
            channel.settimeout(0.0)

            info.ssh = ssh
            info.sftp = sftp
            info.channel = channel
            info.connected = True

            self.ui(lambda: self.on_connect(info))

            info.reader_thread = threading.Thread(target=self._read_loop, args=(info,), daemon=True)
            info.reader_thread.start()

            threading.Thread(target=self.load_files, args=(info,), daemon=True).start()

        except paramiko.AuthenticationException:
            self.ui(lambda: self.on_error(info, "Authentication failed!"))
        except Exception as e:
            msg = str(e)
            self.ui(lambda: self.on_error(info, msg))

    def on_connect(self, info):
        if info.connect_btn:
            info.connect_btn.setEnabled(True)
            info.connect_btn.setText("Disconnect")
        if info.status_label:
            info.status_label.setText("●  Connected")
            info.status_label.setStyleSheet("color:#3ddc97; font-weight:600; font-size:12px;")

        auth_method = "SSH Key" if self.ssh_key_path else ("SSH Agent" if self.ssh_agent_enabled else "Password")
        proxy_info = ""
        if self.proxy_type_var.currentText() != "None":
            proxy_info = f" via {self.proxy_type_var.currentText()} proxy"

        self.term_write(info, f"[✓] Connected! (Auth: {auth_method}{proxy_info})\n", "msg_ok")

        # به‌روزرسانی نقطهٔ وضعیت در کارت میزبان (در صورت وجود)
        self._refresh_host_dot(host=self.host.text().strip(), online=True)

    def on_error(self, info, msg):
        if info.connect_btn:
            info.connect_btn.setEnabled(True)
            info.connect_btn.setText("Connect")
        if info.status_label:
            info.status_label.setText("●  Error")
            info.status_label.setStyleSheet("color:#ff5c5c; font-weight:600; font-size:12px;")

        self.term_write(info, f"[✗] Error: {msg}\n", "msg_err")

    def _refresh_host_dot(self, host, online):
        """رنگ نقطهٔ وضعیت کنار هر کارت میزبان را به‌روزرسانی می‌کند."""
        for name, card in getattr(self, '_host_cards', {}).items():
            session = self.session_mgr.get_session(name)
            if session and session.get('host') == host:
                dot = card.findChild(QLabel, "hostCardDot") or card.findChild(QLabel, "hostCardDotOff")
                if dot:
                    dot.setObjectName("hostCardDot" if online else "hostCardDotOff")
                    dot.setStyleSheet("")
                    card.style().unpolish(dot)
                    card.style().polish(dot)

    def do_disconnect(self, tab_name=None):
        info = self.get_info(tab_name)
        if not info:
            return

        info.connected = False
        try:
            if info.channel:
                info.channel.close()
            if info.sftp:
                info.sftp.close()
            if info.ssh:
                info.ssh.close()
        except Exception:
            pass

        info.channel = None
        info.sftp = None
        info.ssh = None

        if info.connect_btn:
            info.connect_btn.setText("Connect")
        if info.status_label:
            info.status_label.setText("●  Disconnected")
            info.status_label.setStyleSheet("color:#ff5c5c; font-weight:600; font-size:12px;")

        self.term_write(info, "[✓] Disconnected\n", "msg_ok")

        self._refresh_host_dot(host=self.host.text().strip(), online=False)

        if info.tree:
            info.tree.clear()

    # ============================================================
    # ترمینال / اجرای دستور
    # ============================================================
    def exec_cmd(self, tab_name):
        info = self.get_info(tab_name)
        if not info:
            return
        cmd = info.cmd.text().strip()
        if not cmd or not info.channel or not info.connected:
            return
        info.cmd.clear()
        info.cmd_history.append(cmd)
        info.history_pos = len(info.cmd_history)
        try:
            info.channel.send(cmd + "\n")
        except Exception as ex:
            self.term_write(info, f"[Error] {str(ex)}\n", "msg_err")

    def _read_loop(self, info):
        while info.connected and info.channel:
            try:
                if info.channel.recv_ready():
                    data = info.channel.recv(4096).decode(errors="ignore")
                    if data:
                        self._handle_output(info, data)
                else:
                    time.sleep(0.05)
            except Exception:
                break
        if info.connected:
            self.term_write(info, "\n[!] Shell connection closed\n", "msg_err")

    def _handle_output(self, info, data):
        text = data.replace('\r', '')
        self._render_ansi(info, text)

        if info.password and 'password' in data.lower():
            try:
                info.channel.send(info.password + "\n")
            except Exception:
                pass

    def _render_ansi(self, info, text):
        try:
            text = STRIP_OSC_RE.sub('', text)
            text = STRIP_CHARSET_RE.sub('', text)
            text = STRIP_CSI_RE.sub('', text)

            pos = 0
            matches = list(SGR_RE.finditer(text))

            for match in matches:
                chunk = text[pos:match.start()]
                if chunk:
                    self.term_write(info, chunk, info.cur_color)
                self._apply_sgr(info, match.group(1))
                pos = match.end()

            if pos < len(text):
                self.term_write(info, text[pos:], info.cur_color)
        except Exception:
            self.term_write(info, text, info.cur_color)

    def _apply_sgr(self, info, codes):
        codes = codes or '0'
        for c in codes.split(';'):
            if c in ('', '0'):
                info.cur_color = None
            elif c == '39':
                info.cur_color = None
            elif c in FG_COLORS:
                info.cur_color = f"fg{c}"

    def history_up(self, tab_name):
        info = self.get_info(tab_name)
        if not info:
            return
        if info.cmd_history and info.history_pos > 0:
            info.history_pos -= 1
            info.cmd.setText(info.cmd_history[info.history_pos])

    def history_down(self, tab_name):
        info = self.get_info(tab_name)
        if not info:
            return
        if info.cmd_history and info.history_pos < len(info.cmd_history) - 1:
            info.history_pos += 1
            info.cmd.setText(info.cmd_history[info.history_pos])
        else:
            info.history_pos = len(info.cmd_history)
            info.cmd.clear()

    def font_plus(self, tab_name):
        info = self.get_info(tab_name)
        if not info:
            return
        f = info.term.font()
        f.setPointSize(f.pointSize() + 1)
        info.term.setFont(f)

    def font_minus(self, tab_name):
        info = self.get_info(tab_name)
        if not info:
            return
        f = info.term.font()
        if f.pointSize() > 8:
            f.setPointSize(f.pointSize() - 1)
            info.term.setFont(f)

    def stop_command(self, tab_name):
        info = self.get_info(tab_name)
        if not info:
            return
        if info.channel and info.connected:
            try:
                info.channel.send("\x03")
                self.term_write(info, "\n^C\n", "msg_info")
            except Exception:
                pass

    # ============================================================
    # مدیریت فایل‌ها
    # ============================================================
    def load_files(self, info):
        try:
            home = info.sftp.normalize(".")
            info.current_path = home
            self.ui(lambda: info.path_entry.setText(home))
            self._refresh_files(info)
        except Exception as e:
            self.term_write(info, f"[Error] {str(e)}\n", "msg_err")

    def _refresh_files(self, info):
        try:
            items = info.sftp.listdir_attr(info.current_path)
            items.sort(key=lambda x: (not stat.S_ISDIR(x.st_mode), x.filename.lower()))

            rows = []
            for item in items:
                if item.filename.startswith('.'):
                    continue
                is_dir = stat.S_ISDIR(item.st_mode)
                name = item.filename
                typ = "Folder" if is_dir else "File"
                size = "-" if is_dir else self.fmt_size(item.st_size)
                rows.append((name, typ, size))

            self.ui(lambda: self._populate_tree(info, rows))
        except Exception as e:
            self.term_write(info, f"[Error] {str(e)}\n", "msg_err")

    def _populate_tree(self, info, rows):
        info.tree.clear()
        for name, typ, size in rows:
            QTreeWidgetItem(info.tree, [name, typ, size])

    def fmt_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def go_path(self, tab_name):
        info = self.get_info(tab_name)
        if not info:
            return
        path = info.path_entry.text().strip()
        if path and info.connected and info.sftp:
            try:
                norm = info.sftp.normalize(path)
                info.sftp.listdir(norm)
                info.current_path = norm
                info.path_entry.setText(norm)
                self._refresh_files(info)
            except Exception as e:
                self.msg_error("Error", str(e))

    def go_home(self, tab_name):
        info = self.get_info(tab_name)
        if not info:
            return
        if info.connected and info.ssh:
            try:
                home, _ = self._exec_ssh_command(info, 'echo $HOME', timeout=10)
                home = (home or "").strip()
                if not home:
                    home = info.sftp.normalize(".")
                info.current_path = home
                info.path_entry.setText(home)
                self._refresh_files(info)
            except Exception as e:
                self.msg_error("Error", str(e))

    def on_dclick(self, tab_name, item: QTreeWidgetItem):
        info = self.get_info(tab_name)
        if not info:
            return
        name = item.text(0)
        typ = item.text(1)
        path = os.path.join(info.current_path, name).replace("\\", "/")
        if typ == "Folder":
            info.current_path = path
            info.path_entry.setText(path)
            self._refresh_files(info)
        else:
            self.edit_remote_file(tab_name, path)

    def upload(self, tab_name):
        info = self.get_info(tab_name)
        if not info:
            return
        if not info.connected or not info.sftp:
            self.msg_warn("Error", "Not connected")
            return
        files, _ = QFileDialog.getOpenFileNames(self, "Select files to upload")
        if not files:
            return
        threading.Thread(target=self._upload_files, args=(info, files), daemon=True).start()

    def _upload_files(self, info, files):
        for file in files:
            try:
                name = os.path.basename(file)
                remote = os.path.join(info.current_path, name).replace("\\", "/")

                def callback(current, total, name=name):
                    self.ui(lambda: self.update_progress(info, name, current, total))

                info.sftp.put(file, remote, callback=callback)
                self.term_write(info, f"[Uploaded] {name}\n", "msg_info")
                self.ui(lambda: self.reset_progress(info))
            except Exception as e:
                self.term_write(info, f"[Error] {str(e)}\n", "msg_err")
                self.ui(lambda: self.reset_progress(info))
        self._refresh_files(info)

    def download(self, tab_name):
        info = self.get_info(tab_name)
        if not info:
            return
        if not info.connected or not info.sftp:
            return
        selected = info.tree.selectedItems()
        if not selected:
            self.msg_warn("Error", "Select a file")
            return

        files_to_download = [item.text(0) for item in selected if item.text(1) != "Folder"]
        if not files_to_download:
            self.msg_warn("Error", "No files selected")
            return

        save_dir = QFileDialog.getExistingDirectory(self, "Select download directory")
        if not save_dir:
            return
        threading.Thread(target=self._download_files, args=(info, files_to_download, save_dir), daemon=True).start()

    def _download_files(self, info, files, save_dir):
        for name in files:
            remote = os.path.join(info.current_path, name).replace("\\", "/")
            local = os.path.join(save_dir, name)
            try:
                def callback(current, total, name=name):
                    self.ui(lambda: self.update_progress(info, name, current, total))

                info.sftp.get(remote, local, callback=callback)
                self.term_write(info, f"[Downloaded] {name}\n", "msg_info")
                self.ui(lambda: self.reset_progress(info))
            except Exception as e:
                self.term_write(info, f"[Error] {str(e)}\n", "msg_err")
                self.ui(lambda: self.reset_progress(info))

    def update_progress(self, info, filename, current, total):
        percent = (current / total) * 100 if total else 0
        info.progress_label.setText(f"{filename}: {percent:.1f}%")
        info.progress_bar.setValue(int(percent))

    def reset_progress(self, info):
        info.progress_label.setText("")
        info.progress_bar.setValue(0)

    def new_folder(self, tab_name):
        info = self.get_info(tab_name)
        if not info or not info.connected or not info.sftp:
            return
        name = self.input_text("New Folder", "Folder name:")
        if not name:
            return
        path = os.path.join(info.current_path, name).replace("\\", "/")
        try:
            info.sftp.mkdir(path)
            self.term_write(info, f"[Folder] {os.path.basename(path)}\n", "msg_info")
            self._refresh_files(info)
        except Exception as e:
            self.term_write(info, f"[Error] {str(e)}\n", "msg_err")

    def new_file(self, tab_name):
        info = self.get_info(tab_name)
        if not info or not info.connected or not info.sftp:
            return
        name = self.input_text("New File", "File name:")
        if not name:
            return
        path = os.path.join(info.current_path, name).replace("\\", "/")
        try:
            with info.sftp.file(path, "w") as f:
                f.write("")
            self.term_write(info, f"[File] {os.path.basename(path)}\n", "msg_info")
            self._refresh_files(info)
        except Exception as e:
            self.term_write(info, f"[Error] {str(e)}\n", "msg_err")

    def delete(self, tab_name):
        info = self.get_info(tab_name)
        if not info or not info.connected or not info.sftp:
            return
        selected = info.tree.selectedItems()
        if not selected:
            return
        item = selected[0]
        name = item.text(0)
        typ = item.text(1)
        if not self.ask_yes_no("Delete", f"Delete {name}?"):
            return
        path = os.path.join(info.current_path, name).replace("\\", "/")
        try:
            if typ == "Folder":
                info.sftp.rmdir(path)
            else:
                info.sftp.remove(path)
            self.term_write(info, f"[Deleted] {os.path.basename(path)}\n", "msg_info")
            self._refresh_files(info)
        except Exception as e:
            self.term_write(info, f"[Error] {str(e)}\n", "msg_err")

    def refresh(self, tab_name=None):
        info = self.get_info(tab_name)
        if info and info.connected:
            self._refresh_files(info)

    def clear_terminal(self, tab_name=None):
        info = self.get_info(tab_name)
        if info:
            info.term.clear()
            self._term_write_now(info, "=== Terminal Cleared ===\n")

    # ============================================================
    # خروج از برنامه
    # ============================================================
    def closeEvent(self, event):
        self.save_settings()
        for info in self.tabs.values():
            try:
                if info.channel:
                    info.channel.close()
                if info.sftp:
                    info.sftp.close()
                if info.ssh:
                    info.ssh.close()
            except Exception:
                pass
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = SSHManager()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()