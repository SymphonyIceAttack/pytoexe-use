import sys
import os
import time
import json
from datetime import datetime
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *

try:
    from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
    HAS_INTERCEPTOR = True
except ImportError:
    try:
        from PyQt5.QtWebEngineWidgets import QWebEngineUrlRequestInterceptor
        HAS_INTERCEPTOR = True
    except ImportError:
        HAS_INTERCEPTOR = False


# ══════════════════════════════════════════════════════
#  Темы
# ══════════════════════════════════════════════════════
THEMES = {
    "Тёмная": {
        "bg": "#1a1a2e", "panel": "#2d2d44", "tab_bg": "#1e1e32",
        "tab": "#2d2d44", "tab_sel": "#3a3a56", "tab_hover": "#353550",
        "nav": "#3a3a56", "url_bg": "#25253c", "url_focus": "#1e1e32",
        "bm_bar": "#32324c", "text": "#e0e0f0", "text2": "#b0b0cc",
        "text3": "#8888aa", "text_dim": "#555570", "border": "#4a4a66",
        "hover": "rgba(255,255,255,0.12)", "menu_bg": "#2d2d48",
        "dl_bg": "#222240", "dl_item": "#2d2d48",
        "float_bg": "rgba(28,28,48,0.93)", "scroll_bg": "#1e1e32",
        "scroll_h": "#4a4a66",
    },
    "Светлая": {
        "bg": "#f0f0f5", "panel": "#ffffff", "tab_bg": "#e8e8ee",
        "tab": "#ffffff", "tab_sel": "#f8f8fc", "tab_hover": "#eeeef4",
        "nav": "#ffffff", "url_bg": "#e8e8f0", "url_focus": "#ffffff",
        "bm_bar": "#f0f0f6", "text": "#1a1a2e", "text2": "#444466",
        "text3": "#777799", "text_dim": "#aaaacc", "border": "#d0d0dd",
        "hover": "rgba(0,0,0,0.07)", "menu_bg": "#ffffff",
        "dl_bg": "#f4f4fa", "dl_item": "#ffffff",
        "float_bg": "rgba(240,240,250,0.95)", "scroll_bg": "#e8e8ee",
        "scroll_h": "#c0c0d0",
    },
    "AMOLED": {
        "bg": "#000000", "panel": "#0a0a0a", "tab_bg": "#000000",
        "tab": "#111111", "tab_sel": "#1a1a1a", "tab_hover": "#151515",
        "nav": "#0a0a0a", "url_bg": "#111111", "url_focus": "#0a0a0a",
        "bm_bar": "#0a0a0a", "text": "#e0e0e0", "text2": "#aaaaaa",
        "text3": "#777777", "text_dim": "#444444", "border": "#222222",
        "hover": "rgba(255,255,255,0.08)", "menu_bg": "#111111",
        "dl_bg": "#080808", "dl_item": "#111111",
        "float_bg": "rgba(0,0,0,0.95)", "scroll_bg": "#000000",
        "scroll_h": "#333333",
    },
    "Ocean": {
        "bg": "#0d1b2a", "panel": "#1b2838", "tab_bg": "#0d1b2a",
        "tab": "#1b2838", "tab_sel": "#243447", "tab_hover": "#1f2f42",
        "nav": "#1b2838", "url_bg": "#162230", "url_focus": "#0d1b2a",
        "bm_bar": "#182635", "text": "#d0e8f0", "text2": "#8ab4c8",
        "text3": "#5a8aa0", "text_dim": "#3a6070", "border": "#2a4050",
        "hover": "rgba(100,180,220,0.15)", "menu_bg": "#1b2838",
        "dl_bg": "#12202e", "dl_item": "#1b2838",
        "float_bg": "rgba(13,27,42,0.95)", "scroll_bg": "#0d1b2a",
        "scroll_h": "#2a4050",
    },
    "Forest": {
        "bg": "#1a2e1a", "panel": "#2d442d", "tab_bg": "#1a2e1a",
        "tab": "#2d442d", "tab_sel": "#3a563a", "tab_hover": "#355035",
        "nav": "#2d442d", "url_bg": "#253c25", "url_focus": "#1e321e",
        "bm_bar": "#2a4028", "text": "#d8f0d8", "text2": "#a0c8a0",
        "text3": "#709070", "text_dim": "#506050", "border": "#3a5a3a",
        "hover": "rgba(100,200,100,0.12)", "menu_bg": "#2d442d",
        "dl_bg": "#1e351e", "dl_item": "#2d442d",
        "float_bg": "rgba(26,46,26,0.95)", "scroll_bg": "#1a2e1a",
        "scroll_h": "#3a5a3a",
    },
}

DEFAULT_ACCENT = "#6c6cff"

ACCENT_PRESETS = {
    "Фиолетовый": "#6c6cff", "Синий": "#4a90d9",
    "Голубой": "#00bcd4", "Зелёный": "#4caf50",
    "Жёлтый": "#ffc107", "Оранжевый": "#ff9800",
    "Красный": "#f44336", "Розовый": "#e91e63",
    "Белый": "#ffffff",
}


# ══════════════════════════════════════════════════════
#  Настройки / История
# ══════════════════════════════════════════════════════
def _cfg_dir():
    d = os.path.join(os.path.expanduser("~"), ".pybrowser")
    os.makedirs(d, exist_ok=True)
    return d

def _cfg_path():
    return os.path.join(_cfg_dir(), "settings.json")

def _history_path():
    return os.path.join(_cfg_dir(), "history.json")

def load_settings():
    try:
        with open(_cfg_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_settings(s):
    with open(_cfg_path(), "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)


class HistoryManager:
    def __init__(self):
        self._path = _history_path()
        self._items = []
        self._load()

    def _load(self):
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                self._items = json.load(f)
        except Exception:
            self._items = []

    def _save(self):
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._items[-5000:], f, ensure_ascii=False)

    def add(self, url, title):
        if not url or url in ("about:blank", ""):
            return
        self._items.append({
            "url": url, "title": title or url,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self._save()

    def items(self):
        return list(reversed(self._items))

    def clear(self):
        self._items = []
        self._save()

    def count(self):
        return len(self._items)


# ══════════════════════════════════════════════════════
#  Вспомогательные виджеты
# ══════════════════════════════════════════════════════
class TabCloseStyle(QProxyStyle):
    def __init__(self, color="#bbbbdd"):
        super().__init__()
        self._color = color
        self._icon = self._make(color)

    def _make(self, color):
        p = QPixmap(12, 12)
        p.fill(Qt.transparent)
        pt = QPainter(p)
        pt.setRenderHint(QPainter.Antialiasing)
        pt.setPen(QPen(QColor(color), 1.6))
        pt.drawLine(3, 3, 9, 9)
        pt.drawLine(9, 3, 3, 9)
        pt.end()
        return QIcon(p)

    def set_color(self, color):
        self._color = color
        self._icon = self._make(color)

    def standardIcon(self, std, opt=None, widget=None):
        if std == QStyle.SP_TabCloseButton:
            return self._icon
        return super().standardIcon(std, opt, widget)


class FloatingStatus(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("floatingStatus")
        self.setFixedHeight(18)
        self.setMaximumWidth(620)
        self.hide()
        self._t = QTimer(self)
        self._t.setSingleShot(True)
        self._t.timeout.connect(self.hide)

    def show_url(self, url):
        if url:
            self._t.stop()
            txt = url if len(url) < 90 else url[:87] + "…"
            self.setText(f"  {txt}")
            self.adjustSize()
            self.setFixedWidth(
                min(self.sizeHint().width() + 16, 620))
            if self.parentWidget():
                self.move(
                    0,
                    self.parentWidget().height() - self.height())
            self.show()
        else:
            self._t.start(500)


class ToastNotification(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(40)
        self.setMinimumWidth(200)
        self.setMaximumWidth(500)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out)
        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._opacity.setOpacity(1.0)
        self._anim = QPropertyAnimation(self._opacity, b"opacity")
        self._anim.setDuration(400)
        self._anim.finished.connect(self.hide)

    def show_message(self, text, duration=3000):
        self.setText(f"  {text}  ")
        self.adjustSize()
        self.setFixedWidth(
            min(self.sizeHint().width() + 40, 500))
        self._opacity.setOpacity(1.0)
        if self.parentWidget():
            pw = self.parentWidget()
            self.move(pw.width() - self.width() - 20,
                      pw.height() - self.height() - 20)
        self.show()
        self.raise_()
        self._timer.start(duration)

    def _fade_out(self):
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.start()


# ══════════════════════════════════════════════════════
#  Загрузки
# ══════════════════════════════════════════════════════
def _sz(b):
    if b < 1024:
        return f"{b} Б"
    if b < 1048576:
        return f"{b / 1024:.1f} КБ"
    if b < 1073741824:
        return f"{b / 1048576:.1f} МБ"
    return f"{b / 1073741824:.2f} ГБ"


def _sp(bps):
    if bps < 1024:
        return f"{bps:.0f} Б/с"
    if bps < 1048576:
        return f"{bps / 1024:.1f} КБ/с"
    return f"{bps / 1048576:.1f} МБ/с"


class DownloadWidget(QFrame):
    remove_requested = pyqtSignal(object)

    def __init__(self, dl, parent=None):
        super().__init__(parent)
        self.setObjectName("downloadItem")
        self._dl = dl
        self._speed = 0.0
        self._last_r = 0
        self._last_t = time.time()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(4)

        r1 = QHBoxLayout()
        r1.setSpacing(4)
        try:
            fn = dl.downloadFileName() or "file"
        except AttributeError:
            fn = os.path.basename(dl.path()) or "file"

        self.name_lbl = QLabel(fn)
        self.name_lbl.setObjectName("dlName")

        self.pause_btn = self._b("⏸", "Пауза")
        self.pause_btn.clicked.connect(self._toggle_pause)
        self.cancel_btn = self._b("✕", "Отменить")
        self.cancel_btn.clicked.connect(self._cancel)
        self.open_btn = self._b("📄", "Открыть")
        self.open_btn.clicked.connect(self._open_file)
        self.open_btn.hide()
        self.folder_btn = self._b("📂", "Папка")
        self.folder_btn.clicked.connect(self._open_folder)
        self.folder_btn.hide()
        self.rm_btn = self._b("🗑", "Убрать")
        self.rm_btn.clicked.connect(
            lambda: self.remove_requested.emit(self))
        self.rm_btn.hide()

        r1.addWidget(self.name_lbl, 1)
        for w in (self.pause_btn, self.cancel_btn,
                  self.open_btn, self.folder_btn, self.rm_btn):
            r1.addWidget(w)

        r2 = QHBoxLayout()
        r2.setSpacing(8)
        self.bar = QProgressBar()
        self.bar.setObjectName("dlBar")
        self.bar.setFixedHeight(6)
        self.bar.setTextVisible(False)
        self.st_lbl = QLabel("Подготовка…")
        self.st_lbl.setObjectName("dlStatus")
        self.st_lbl.setMinimumWidth(220)
        self.st_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        r2.addWidget(self.bar, 1)
        r2.addWidget(self.st_lbl)

        lay.addLayout(r1)
        lay.addLayout(r2)
        dl.downloadProgress.connect(self._prog)
        dl.finished.connect(self._fin)

    @staticmethod
    def _b(text, tip):
        b = QPushButton(text)
        b.setObjectName("dlActionBtn")
        b.setFixedSize(26, 26)
        b.setCursor(Qt.PointingHandCursor)
        b.setToolTip(tip)
        return b

    def _toggle_pause(self):
        try:
            if self._dl.isPaused():
                self._dl.resume()
                self.pause_btn.setText("⏸")
            else:
                self._dl.pause()
                self.pause_btn.setText("▶")
                self._speed = 0
        except AttributeError:
            self.pause_btn.setEnabled(False)

    def _cancel(self):
        self._dl.cancel()

    def _open_file(self):
        try:
            p = os.path.join(
                self._dl.downloadDirectory(),
                self._dl.downloadFileName())
        except AttributeError:
            p = self._dl.path()
        if os.path.exists(p):
            QDesktopServices.openUrl(QUrl.fromLocalFile(p))

    def _open_folder(self):
        try:
            d = self._dl.downloadDirectory()
        except AttributeError:
            d = os.path.dirname(self._dl.path())
        QDesktopServices.openUrl(QUrl.fromLocalFile(d))

    def _prog(self, recv, total):
        now = time.time()
        dt = now - self._last_t
        if dt >= 0.5:
            self._speed = (recv - self._last_r) / dt if dt else 0
            self._last_r = recv
            self._last_t = now
        if total > 0:
            self.bar.setRange(0, 100)
            self.bar.setValue(int(recv * 100 / total))
            s = f"{_sz(recv)} / {_sz(total)}"
        else:
            self.bar.setRange(0, 0)
            s = _sz(recv)
        try:
            if self._dl.isPaused():
                s += "  •  ⏸ Пауза"
            elif self._speed > 0:
                s += f"  •  {_sp(self._speed)}"
        except AttributeError:
            pass
        self.st_lbl.setText(s)

    def _fin(self):
        self.bar.setRange(0, 100)
        st = self._dl.state()
        if st == QWebEngineDownloadItem.DownloadCompleted:
            self.bar.setValue(100)
            t = self._dl.totalBytes()
            self.st_lbl.setText(
                f"✅ Загружено  •  {_sz(t)}" if t > 0
                else "✅ Загружено")
            self.pause_btn.hide()
            self.cancel_btn.hide()
            self.open_btn.show()
            self.folder_btn.show()
            self.rm_btn.show()
        elif st == QWebEngineDownloadItem.DownloadCancelled:
            self.bar.setValue(0)
            self.st_lbl.setText("❌ Отменено")
            self.pause_btn.hide()
            self.cancel_btn.hide()
            self.rm_btn.show()
        else:
            self.bar.setValue(0)
            self.st_lbl.setText("⚠ Ошибка")
            self.pause_btn.hide()
            self.cancel_btn.hide()
            self.rm_btn.show()


class DownloadPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("downloadPanel")
        self._items = []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        hdr = QWidget()
        hdr.setObjectName("dlHeader")
        hdr.setFixedHeight(32)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(12, 4, 8, 4)
        lbl = QLabel("⬇  Загрузки")
        lbl.setObjectName("dlTitle")
        clear = QPushButton("Очистить завершённые")
        clear.setObjectName("dlClearBtn")
        clear.setCursor(Qt.PointingHandCursor)
        clear.setFixedHeight(24)
        clear.clicked.connect(self.clear_completed)
        close = QPushButton("✕")
        close.setObjectName("dlCloseBtn")
        close.setFixedSize(24, 24)
        close.setCursor(Qt.PointingHandCursor)
        close.clicked.connect(self.hide_panel)
        hl.addWidget(lbl)
        hl.addStretch()
        hl.addWidget(clear)
        hl.addWidget(close)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.scroll.setObjectName("dlScroll")
        self.scr_w = QWidget()
        self.scr_l = QVBoxLayout(self.scr_w)
        self.scr_l.setContentsMargins(6, 6, 6, 6)
        self.scr_l.setSpacing(4)
        self.scr_l.addStretch()
        self.scroll.setWidget(self.scr_w)

        lay.addWidget(hdr)
        lay.addWidget(self.scroll)
        self.hide()

    def add_download(self, dl):
        w = DownloadWidget(dl, self)
        w.remove_requested.connect(self._remove)
        self.scr_l.insertWidget(0, w)
        self._items.append(w)
        self.show_panel()

    def _remove(self, w):
        if w in self._items:
            self._items.remove(w)
        self.scr_l.removeWidget(w)
        w.deleteLater()
        if not self._items:
            self.hide_panel()

    def clear_completed(self):
        done = (QWebEngineDownloadItem.DownloadCompleted,
                QWebEngineDownloadItem.DownloadCancelled)
        try:
            done += (QWebEngineDownloadItem.DownloadInterrupted,)
        except AttributeError:
            pass
        for w in self._items[:]:
            if w._dl.state() in done:
                self._remove(w)

    def active_count(self):
        return sum(
            1 for w in self._items
            if w._dl.state() ==
            QWebEngineDownloadItem.DownloadInProgress)

    def show_panel(self):
        self.setFixedHeight(200)
        self.show()

    def hide_panel(self):
        self.setFixedHeight(0)
        self.hide()


# ══════════════════════════════════════════════════════
#  Диалоги
# ══════════════════════════════════════════════════════
class SettingsDialog(QDialog):
    def __init__(self, parent, current_theme, current_accent):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setFixedSize(440, 520)
        self.chosen_theme = current_theme
        self.chosen_accent = current_accent

        lay = QVBoxLayout(self)
        lay.setSpacing(16)
        lay.setContentsMargins(24, 20, 24, 20)

        title = QLabel("⚙  Настройки")
        title.setObjectName("setTitle")
        lay.addWidget(title)
        lay.addWidget(self._section("Тема оформления"))

        self.theme_group = QButtonGroup(self)
        tg = QHBoxLayout()
        tg.setSpacing(6)
        for name in THEMES:
            rb = QRadioButton(name)
            rb.setCursor(Qt.PointingHandCursor)
            if name == current_theme:
                rb.setChecked(True)
            self.theme_group.addButton(rb)
            tg.addWidget(rb)
        lay.addLayout(tg)

        lay.addWidget(self._section("Акцентный цвет"))

        self.accent_group = QButtonGroup(self)
        ag = QGridLayout()
        ag.setSpacing(6)
        col = row = 0
        for name, color in ACCENT_PRESETS.items():
            btn = QPushButton()
            btn.setFixedSize(36, 36)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(name)
            btn.setCheckable(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background:{color};
                    border:2px solid transparent;
                    border-radius:18px;
                }}
                QPushButton:checked {{
                    border:3px solid #ffffff;
                }}
                QPushButton:hover {{
                    border:2px solid rgba(255,255,255,0.5);
                }}
            """)
            btn.setProperty("accent_color", color)
            if color == current_accent:
                btn.setChecked(True)
            self.accent_group.addButton(btn)
            ag.addWidget(btn, row, col)
            col += 1
            if col >= 5:
                col = 0
                row += 1

        custom_btn = QPushButton("🎨")
        custom_btn.setFixedSize(36, 36)
        custom_btn.setCursor(Qt.PointingHandCursor)
        custom_btn.setObjectName("accentCustom")
        custom_btn.clicked.connect(self._pick_color)
        ag.addWidget(custom_btn, row, col)
        lay.addLayout(ag)

        self.preview = QLabel("  Превью акцентного цвета")
        self.preview.setFixedHeight(32)
        self._update_preview(current_accent)
        lay.addWidget(self.preview)
        self.accent_group.buttonClicked.connect(
            lambda btn: self._update_preview(
                btn.property("accent_color")))
        lay.addStretch()

        bl = QHBoxLayout()
        bl.addStretch()
        cancel = QPushButton("Отмена")
        cancel.setObjectName("setBtn")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Применить")
        ok.setObjectName("setBtnPrimary")
        ok.setCursor(Qt.PointingHandCursor)
        ok.clicked.connect(self._apply)
        bl.addWidget(cancel)
        bl.addWidget(ok)
        lay.addLayout(bl)

    def _section(self, text):
        l = QLabel(text)
        l.setObjectName("setSection")
        return l

    def _update_preview(self, color):
        self.chosen_accent = color
        self.preview.setStyleSheet(
            f"background:{color}; border-radius:6px; "
            f"color:#fff; font-weight:bold; padding-left:10px;")

    def _pick_color(self):
        c = QColorDialog.getColor(
            QColor(self.chosen_accent), self)
        if c.isValid():
            self.chosen_accent = c.name()
            self._update_preview(c.name())
            checked = self.accent_group.checkedButton()
            if checked:
                self.accent_group.setExclusive(False)
                checked.setChecked(False)
                self.accent_group.setExclusive(True)

    def _apply(self):
        btn = self.theme_group.checkedButton()
        if btn:
            self.chosen_theme = btn.text()
        self.accept()


class HistoryDialog(QDialog):
    navigate_to = pyqtSignal(str)

    def __init__(self, parent, hm):
        super().__init__(parent)
        self.setWindowTitle("История")
        self.setMinimumSize(600, 450)
        self._hm = hm

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        hl = QHBoxLayout()
        title = QLabel(
            f"📋  История ({hm.count()} записей)")
        title.setObjectName("setTitle")
        hl.addWidget(title)
        hl.addStretch()
        clear_btn = QPushButton("🗑  Очистить")
        clear_btn.setObjectName("setBtnDanger")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_all)
        hl.addWidget(clear_btn)
        lay.addLayout(hl)

        self.search = QLineEdit()
        self.search.setObjectName("urlBar")
        self.search.setPlaceholderText("Поиск…")
        self.search.setFixedHeight(32)
        self.search.textChanged.connect(self._filter)
        lay.addWidget(self.search)

        self.list = QListWidget()
        self.list.setObjectName("historyList")
        self.list.itemDoubleClicked.connect(self._go)
        lay.addWidget(self.list, 1)

        bl = QHBoxLayout()
        bl.addStretch()
        close = QPushButton("Закрыть")
        close.setObjectName("setBtn")
        close.setCursor(Qt.PointingHandCursor)
        close.clicked.connect(self.accept)
        bl.addWidget(close)
        lay.addLayout(bl)
        self._populate()

    def _populate(self, flt=""):
        self.list.clear()
        for it in self._hm.items():
            t = it.get("title", "")
            u = it.get("url", "")
            tm = it.get("time", "")
            if flt:
                fl = flt.lower()
                if fl not in t.lower() and fl not in u.lower():
                    continue
            item = QListWidgetItem(f"{tm}  •  {t}\n{u}")
            item.setData(Qt.UserRole, u)
            self.list.addItem(item)

    def _filter(self, text):
        self._populate(text)

    def _go(self, item):
        u = item.data(Qt.UserRole)
        if u:
            self.navigate_to.emit(u)
            self.accept()

    def _clear_all(self):
        box = QMessageBox(self)
        box.setWindowTitle("Очистить историю")
        box.setText("Удалить всю историю?")
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if box.exec_() == QMessageBox.Yes:
            self._hm.clear()
            self._populate()


# ══════════════════════════════════════════════════════
#  ★ BrowserPage — ИСПРАВЛЕНО
#  Убрана бесконечная перезагрузка,
#  добавлен лимит на количество перезагрузок
# ══════════════════════════════════════════════════════
class BrowserPage(QWebEnginePage):

    def __init__(self, profile, parent_tab=None):
        super().__init__(profile, parent_tab)
        self._tab = parent_tab
        self._browser = None

        # ★ Счётчик крашей — максимум 2 перезагрузки,
        #   потом показываем ошибку вместо бесконечного цикла
        self._crash_count = 0
        self._max_crashes = 2

        # Разрешения для игр и медиа
        self.featurePermissionRequested.connect(
            self._on_permission)

        # Обработка крашей рендера С ЛИМИТОМ
        try:
            self.renderProcessTerminated.connect(
                self._on_render_crash)
        except AttributeError:
            pass

        # ★ Сброс счётчика крашей при успешной загрузке
        self.loadFinished.connect(self._on_load_ok)

    def set_browser(self, browser_window):
        self._browser = browser_window

    def _on_load_ok(self, ok):
        """При успешной загрузке сбрасываем счётчик крашей"""
        if ok:
            self._crash_count = 0

    def _on_permission(self, url, feature):
        """Автоматически выдаём разрешения"""
        self.setFeaturePermission(
            url, feature,
            QWebEnginePage.PermissionGrantedByUser)

    def _on_render_crash(self, status, exit_code):
        """
        ★ ИСПРАВЛЕНО: ограничиваем количество перезагрузок.
        Если рендер падает больше 2 раз подряд — НЕ перезагружаем,
        показываем страницу ошибки.
        """
        self._crash_count += 1
        print(f"[Render crash #{self._crash_count}] "
              f"status={status} code={exit_code}")

        if self._crash_count <= self._max_crashes:
            # Перезагружаем с увеличивающейся задержкой
            delay = self._crash_count * 1000  # 1с, 2с
            QTimer.singleShot(delay, self._safe_reload)
        else:
            # Показываем страницу ошибки вместо бесконечного цикла
            error_html = """
            <html>
            <body style="background:#1a1a2e; color:#e0e0f0;
                         font-family:sans-serif; text-align:center;
                         padding-top:100px;">
                <h1>⚠ Страница не может быть отображена</h1>
                <p style="color:#8888aa; font-size:16px;">
                    Рендер-процесс завершился с ошибкой.<br>
                    Попробуйте обновить страницу вручную (F5)
                    или перейти на другой сайт.
                </p>
                <p style="margin-top:30px;">
                    <a href="javascript:location.reload()"
                       style="color:#6c6cff; font-size:18px;">
                        🔄 Попробовать снова
                    </a>
                </p>
            </body>
            </html>
            """
            self.setHtml(error_html)
            # Сбрасываем счётчик чтобы ручное обновление работало
            self._crash_count = 0

    def _safe_reload(self):
        """Безопасная перезагрузка"""
        try:
            self.triggerAction(QWebEnginePage.Reload)
        except RuntimeError:
            pass  # Страница уже удалена

    def javaScriptConsoleMessage(self, level, msg, line, src):
        """Логируем только ошибки"""
        if level == QWebEnginePage.ErrorMessageLevel:
            print(f"[JS] {src}:{line} {msg}")

    def createWindow(self, win_type):
        """
        ★ Возвращаем QWebEnginePage (НЕ QWebEngineView!)
        """
        if self._browser:
            new_tab = self._browser.add_new_tab()
            return new_tab.page()
        return super().createWindow(win_type)


# ══════════════════════════════════════════════════════
#  Вкладка браузера
# ══════════════════════════════════════════════════════
class BrowserTab(QWebEngineView):
    def __init__(self, profile, browser_window=None):
        super().__init__(browser_window)
        self.browser_window = browser_window

        self._page = BrowserPage(profile, self)
        self.setPage(self._page)

    def set_browser(self, browser_window):
        self.browser_window = browser_window
        self._page.set_browser(browser_window)

    def contextMenuEvent(self, event):
        page = self.page()
        data = page.contextMenuData()
        if not data.isValid():
            return

        menu = QMenu(self)
        menu.setObjectName("ctxMenu")
        bw = self.browser_window

        has_link = data.linkUrl().isValid()
        has_img = (data.mediaType() ==
                   QWebEngineContextMenuData.MediaTypeImage)
        has_av = data.mediaType() in (
            QWebEngineContextMenuData.MediaTypeVideo,
            QWebEngineContextMenuData.MediaTypeAudio)
        has_sel = bool(data.selectedText())
        editable = data.isContentEditable()
        link = data.linkUrl().toString() if has_link else ""
        media = (data.mediaUrl().toString()
                 if data.mediaUrl().isValid() else "")
        sel = data.selectedText() if has_sel else ""

        if has_link:
            menu.addAction("Открыть в новой вкладке",
                           lambda: bw.add_new_tab(url=link))
            menu.addAction(
                "Копировать ссылку",
                lambda: QApplication.clipboard().setText(link))
            menu.addAction(
                "Сохранить ссылку как…",
                lambda: page.triggerAction(
                    QWebEnginePage.DownloadLinkToDisk))
            menu.addSeparator()

        if has_img:
            menu.addAction("Открыть изображение",
                           lambda: bw.add_new_tab(url=media))
            menu.addAction(
                "Сохранить изображение…",
                lambda: page.triggerAction(
                    QWebEnginePage.DownloadImageToDisk))
            menu.addAction(
                "Копировать изображение",
                lambda: page.triggerAction(
                    QWebEnginePage.CopyImageToClipboard))
            menu.addSeparator()

        if has_av:
            menu.addAction("Открыть медиа",
                           lambda: bw.add_new_tab(url=media))
            menu.addSeparator()

        if editable:
            fl = data.editFlags()
            a = menu.addAction(
                "Отменить",
                lambda: page.triggerAction(QWebEnginePage.Undo))
            a.setEnabled(
                bool(fl & QWebEngineContextMenuData.CanUndo))
            a = menu.addAction(
                "Повторить",
                lambda: page.triggerAction(QWebEnginePage.Redo))
            a.setEnabled(
                bool(fl & QWebEngineContextMenuData.CanRedo))
            menu.addSeparator()
            a = menu.addAction(
                "Вырезать",
                lambda: page.triggerAction(QWebEnginePage.Cut))
            a.setEnabled(
                bool(fl & QWebEngineContextMenuData.CanCut))
            a = menu.addAction(
                "Копировать",
                lambda: page.triggerAction(QWebEnginePage.Copy))
            a.setEnabled(
                bool(fl & QWebEngineContextMenuData.CanCopy))
            a = menu.addAction(
                "Вставить",
                lambda: page.triggerAction(QWebEnginePage.Paste))
            a.setEnabled(
                bool(fl & QWebEngineContextMenuData.CanPaste))
            menu.addSeparator()
            a = menu.addAction(
                "Выделить всё",
                lambda: page.triggerAction(
                    QWebEnginePage.SelectAll))
            a.setEnabled(
                bool(fl & QWebEngineContextMenuData.CanSelectAll))
            menu.addSeparator()
        elif has_sel:
            menu.addAction(
                "Копировать",
                lambda: page.triggerAction(QWebEnginePage.Copy))
            short = sel[:30] + ("…" if len(sel) > 30 else "")
            eng = bw.current_engine if bw else "Яндекс"
            menu.addAction(
                f'Искать «{short}» в {eng}',
                lambda: bw.add_new_tab(
                    url=bw._search_url(sel)))
            menu.addSeparator()

        if not editable and not has_sel:
            a = menu.addAction(
                "← Назад",
                lambda: page.triggerAction(
                    QWebEnginePage.Back))
            a.setEnabled(
                page.action(QWebEnginePage.Back).isEnabled())
            a = menu.addAction(
                "→ Вперёд",
                lambda: page.triggerAction(
                    QWebEnginePage.Forward))
            a.setEnabled(
                page.action(
                    QWebEnginePage.Forward).isEnabled())
            menu.addAction(
                "⟳ Обновить",
                lambda: page.triggerAction(
                    QWebEnginePage.Reload))
            menu.addSeparator()

        menu.addAction(
            "📷 Скриншот",
            lambda: bw.take_screenshot() if bw else None)
        menu.addSeparator()
        menu.addAction(
            "Код страницы",
            lambda: page.triggerAction(
                QWebEnginePage.ViewSource))
        if bw:
            menu.addAction("Инструменты разработчика",
                           bw.open_dev_tools)

        menu.exec_(event.globalPos())


# ══════════════════════════════════════════════════════
#  Профиль — настройки для WebGL и совместимости
# ══════════════════════════════════════════════════════
def setup_profile():
    profile = QWebEngineProfile.defaultProfile()

    cache_dir = os.path.join(_cfg_dir(), "cache")
    data_dir = os.path.join(_cfg_dir(), "data")
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    profile.setCachePath(cache_dir)
    profile.setPersistentStoragePath(data_dir)
    profile.setPersistentCookiesPolicy(
        QWebEngineProfile.AllowPersistentCookies)

    s = profile.settings()

    # ★ Всё что нужно для рендеринга и WebGL-игр
    enable_list = [
        "JavascriptEnabled",
        "AutoLoadImages",
        "PluginsEnabled",
        "LocalStorageEnabled",
        "ScrollAnimatorEnabled",
        "ErrorPageEnabled",
        "JavascriptCanOpenWindows",
        "JavascriptCanAccessClipboard",
        "FullScreenSupportEnabled",
        "FocusOnNavigationEnabled",
        "DnsPrefetchEnabled",
        "PdfViewerEnabled",
        # ★ WebGL — критично для игр
        "WebGLEnabled",
        "Accelerated2dCanvasEnabled",
        # Доп. для совместимости
        "AllowRunningInsecureContent",
        "AllowGeolocationOnInsecureOrigins",
    ]

    for attr_name in enable_list:
        attr = getattr(QWebEngineSettings, attr_name, None)
        if attr is not None:
            s.setAttribute(attr, True)

    s.setAttribute(
        QWebEngineSettings.HyperlinkAuditingEnabled, False)

    # ★ Увеличиваем лимит используемой памяти для WebGL-игр
    # (по умолчанию Chromium ограничивает)

    return profile


# ══════════════════════════════════════════════════════
#  Перехватчик — минимальный, НЕ ломающий сайты
# ══════════════════════════════════════════════════════
if HAS_INTERCEPTOR:
    class UrlRequestInterceptor(QWebEngineUrlRequestInterceptor):
        BLOCK = {
            "doubleclick.net",
            "googlesyndication.com",
            "googleadservices.com",
            "pagead2.googlesyndication.com",
            "adservice.google.com",
        }

        def interceptRequest(self, info):
            host = info.requestUrl().host().lower()
            for b in self.BLOCK:
                if host == b or host.endswith("." + b):
                    info.block(True)
                    return
            # ★ Всё остальное пропускаем — НЕ блокируем!
else:
    UrlRequestInterceptor = None


# ══════════════════════════════════════════════════════
#  Главное окно
# ══════════════════════════════════════════════════════
class BrowserWindow(QMainWindow):

    ENGINES = {
        "Яндекс": {
            "search": "https://yandex.ru/search/?text={}",
            "home": "https://yandex.ru"},
        "Google": {
            "search": "https://www.google.com/search?q={}",
            "home": "https://www.google.com"},
        "Mail.ru": {
            "search": "https://go.mail.ru/search?q={}",
            "home": "https://mail.ru"},
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Браузер")
        self.setGeometry(100, 100, 1300, 820)
        self.setMinimumSize(800, 600)

        self._settings = load_settings()
        self.current_engine = self._settings.get(
            "engine", "Яндекс")
        self.current_theme = self._settings.get(
            "theme", "Тёмная")
        self.accent = self._settings.get(
            "accent", DEFAULT_ACCENT)
        self.tabs = []
        self.bookmarks = []
        self.history = HistoryManager()

        self._profile = setup_profile()

        if UrlRequestInterceptor is not None:
            self._interceptor = UrlRequestInterceptor(self)
            self._profile.setUrlRequestInterceptor(
                self._interceptor)

        self._tab_style = TabCloseStyle()

        # ── UI ──
        cw = QWidget()
        self.setCentralWidget(cw)
        ml = QVBoxLayout(cw)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)

        top = QWidget()
        top.setObjectName("topPanel")
        tl = QVBoxLayout(top)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(0)

        # Tab bar
        tbw = QWidget()
        tbw.setObjectName("tabBarWidget")
        tbw.setFixedHeight(40)
        tbl = QHBoxLayout(tbw)
        tbl.setContentsMargins(5, 5, 5, 0)
        tbl.setSpacing(0)

        self.tab_bar = QTabBar()
        self.tab_bar.setObjectName("tabBar")
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.setMovable(True)
        self.tab_bar.setExpanding(False)
        self.tab_bar.setElideMode(Qt.ElideRight)
        self.tab_bar.setDrawBase(False)
        self.tab_bar.setStyle(self._tab_style)
        self.tab_bar.tabCloseRequested.connect(self.close_tab)
        self.tab_bar.currentChanged.connect(self.switch_tab)

        plus = QPushButton("+")
        plus.setObjectName("newTabBtn")
        plus.setFixedSize(28, 28)
        plus.setCursor(Qt.PointingHandCursor)
        plus.clicked.connect(
            lambda: self.add_new_tab(url=self._home()))

        tbl.addWidget(self.tab_bar, 1)
        tbl.addWidget(plus)
        tbl.addStretch()

        # Navigation
        nav = QWidget()
        nav.setObjectName("navWidget")
        nav.setFixedHeight(44)
        nl = QHBoxLayout(nav)
        nl.setContentsMargins(8, 4, 8, 6)
        nl.setSpacing(4)

        self.back_btn = self._nb("◀", "Назад", self.go_back)
        self.fwd_btn = self._nb("▶", "Вперёд", self.go_fwd)
        self.rel_btn = self._nb("⟳", "Обновить", self.reload)
        self.home_btn = self._nb(
            "🏠", "Домой", self.go_home, "homeBtn")

        self.ssl_btn = QPushButton("🔒")
        self.ssl_btn.setObjectName("sslBtn")
        self.ssl_btn.setFixedSize(28, 28)
        self.ssl_btn.setCursor(Qt.PointingHandCursor)

        self.url_bar = QLineEdit()
        self.url_bar.setObjectName("urlBar")
        self.url_bar.setPlaceholderText(
            "Адрес или поиск")
        self.url_bar.returnPressed.connect(self.navigate)
        self.url_bar.setFixedHeight(32)

        self.engine_cb = QComboBox()
        self.engine_cb.setObjectName("engineCombo")
        self.engine_cb.setFixedSize(110, 32)
        self.engine_cb.setCursor(Qt.PointingHandCursor)
        for n in self.ENGINES:
            self.engine_cb.addItem(n)
        self.engine_cb.setCurrentText(self.current_engine)
        self.engine_cb.currentTextChanged.connect(
            self._set_engine)

        self.bm_btn = self._nb(
            "☆", "Закладка", self.toggle_bookmark)
        self.screenshot_btn = self._nb(
            "📷", "Скриншот",
            self.take_screenshot, "screenshotBtn")
        self.menu_btn = self._nb(
            "☰", "Меню", self.show_menu, "menuBtn")

        for w in (self.back_btn, self.fwd_btn, self.rel_btn,
                  self.home_btn, self.ssl_btn):
            nl.addWidget(w)
        nl.addWidget(self.url_bar, 1)
        nl.addWidget(self.engine_cb)
        nl.addWidget(self.bm_btn)
        nl.addWidget(self.screenshot_btn)
        nl.addWidget(self.menu_btn)

        # Bookmarks
        self.bm_bar = QWidget()
        self.bm_bar.setObjectName("bookmarksBar")
        self.bm_bar.setFixedHeight(30)
        self.bm_lay = QHBoxLayout(self.bm_bar)
        self.bm_lay.setContentsMargins(8, 2, 8, 2)
        self.bm_lay.setSpacing(4)
        self.bm_lay.addStretch()
        self._default_bookmarks()

        tl.addWidget(tbw)
        tl.addWidget(nav)
        tl.addWidget(self.bm_bar)

        # Progress
        self.progress = QProgressBar()
        self.progress.setObjectName("progressBar")
        self.progress.setFixedHeight(3)
        self.progress.setTextVisible(False)
        self.progress.hide()

        # Pages
        self._page_container = QWidget()
        pcl = QVBoxLayout(self._page_container)
        pcl.setContentsMargins(0, 0, 0, 0)
        pcl.setSpacing(0)

        self.stack = QStackedWidget()
        self.download_panel = DownloadPanel(self)
        pcl.addWidget(self.stack, 1)
        pcl.addWidget(self.download_panel)

        self.floating = FloatingStatus(self._page_container)
        self.toast = ToastNotification(self._page_container)

        ml.addWidget(top)
        ml.addWidget(self.progress)
        ml.addWidget(self._page_container, 1)

        self.setStatusBar(None)
        self._profile.downloadRequested.connect(
            self._on_download)

        self.add_new_tab(url=self._home())
        self._shortcuts()
        self._apply_theme()

    # ──── helpers ────

    @staticmethod
    def _nb(text, tip, cb, name="navBtn"):
        b = QPushButton(text)
        b.setObjectName(name)
        b.setFixedSize(32, 32)
        b.setCursor(Qt.PointingHandCursor)
        b.setToolTip(tip)
        b.clicked.connect(cb)
        return b

    def _home(self):
        return self.ENGINES[self.current_engine]["home"]

    def _search_url(self, q):
        return self.ENGINES[self.current_engine][
            "search"].format(q)

    def _set_engine(self, n):
        self.current_engine = n
        self._settings["engine"] = n
        save_settings(self._settings)

    def cur(self):
        i = self.tab_bar.currentIndex()
        return self.tabs[i] if 0 <= i < len(self.tabs) else None

    # ──── tabs ────

    def add_new_tab(self, url=None):
        t = BrowserTab(self._profile, self)
        t.set_browser(self)

        t.urlChanged.connect(
            lambda u, _t=t: self._url_changed(u, _t))
        t.titleChanged.connect(
            lambda s, _t=t: self._title_changed(s, _t))
        t.iconChanged.connect(
            lambda ic, _t=t: self._icon_changed(ic, _t))
        t.loadStarted.connect(
            lambda _t=t: self._load_start(_t))
        t.loadFinished.connect(
            lambda ok, _t=t: self._load_end(ok, _t))
        t.loadProgress.connect(self._load_prog)
        t.page().linkHovered.connect(self.floating.show_url)

        try:
            t.page().fullScreenRequested.connect(
                self._handle_fullscreen)
        except AttributeError:
            pass

        self.tabs.append(t)
        self.stack.addWidget(t)
        idx = self.tab_bar.addTab("Новая вкладка")
        self.tab_bar.setCurrentIndex(idx)
        if url:
            t.setUrl(QUrl(url))
        return t

    def _handle_fullscreen(self, request):
        request.accept()
        if request.toggleOn():
            self.showFullScreen()
        else:
            self.showNormal()

    def close_tab(self, i):
        if i < 0 or i >= len(self.tabs):
            return
        if len(self.tabs) == 1:
            self.close()
            return
        t = self.tabs.pop(i)
        self.stack.removeWidget(t)
        self.tab_bar.removeTab(i)
        t.deleteLater()

    def switch_tab(self, i):
        if 0 <= i < len(self.tabs):
            t = self.tabs[i]
            self.stack.setCurrentWidget(t)
            self.url_bar.setText(t.url().toString())
            self.setWindowTitle(
                f"{t.title() or 'Браузер'} — Браузер")
            self._upd_nav()
            self._upd_bm()
            self._upd_ssl(t.url())

    # ──── navigation ────

    def navigate(self):
        txt = self.url_bar.text().strip()
        if not txt:
            return
        if self._looks_url(txt):
            if not txt.startswith(("http://", "https://")):
                txt = "https://" + txt
            url = QUrl(txt)
        else:
            url = QUrl(self._search_url(txt))
        t = self.cur()
        if t:
            t.setUrl(url)

    @staticmethod
    def _looks_url(s):
        if " " in s:
            return False
        if s.startswith(
                ("http://", "https://", "localhost", "127.")):
            return True
        if "." in s and len(s.rsplit(".", 1)[-1]) >= 2:
            return True
        return False

    def go_back(self):
        t = self.cur()
        if t:
            t.back()

    def go_fwd(self):
        t = self.cur()
        if t:
            t.forward()

    def reload(self):
        t = self.cur()
        if t:
            # ★ При ручном обновлении сбрасываем счётчик крашей
            if hasattr(t.page(), '_crash_count'):
                t.page()._crash_count = 0
            t.reload()

    def go_home(self):
        t = self.cur()
        if t:
            t.setUrl(QUrl(self._home()))

    def _upd_nav(self):
        t = self.cur()
        if t:
            self.back_btn.setEnabled(
                t.history().canGoBack())
            self.fwd_btn.setEnabled(
                t.history().canGoForward())

    def _upd_ssl(self, url):
        if url.scheme() == "https":
            self.ssl_btn.setText("🔒")
            self.ssl_btn.setToolTip("HTTPS")
        elif url.scheme() == "http":
            self.ssl_btn.setText("⚠")
            self.ssl_btn.setToolTip("HTTP")
        else:
            self.ssl_btn.setText("ℹ")
            self.ssl_btn.setToolTip(url.scheme())

    # ──── signals ────

    def _url_changed(self, u, t):
        if t == self.cur():
            self.url_bar.setText(u.toString())
            self._upd_nav()
            self._upd_bm()
            self._upd_ssl(u)

    def _title_changed(self, s, t):
        i = self.tabs.index(t) if t in self.tabs else -1
        if i >= 0:
            short = (s[:25] + "…" if len(s) > 25
                     else (s or "Новая вкладка"))
            self.tab_bar.setTabText(i, short)
            self.tab_bar.setTabToolTip(i, s)
        if t == self.cur():
            self.setWindowTitle(f"{s} — Браузер")

    def _icon_changed(self, ic, t):
        i = self.tabs.index(t) if t in self.tabs else -1
        if i >= 0:
            self.tab_bar.setTabIcon(i, ic)

    def _load_start(self, t):
        if t == self.cur():
            self.progress.show()
            self.progress.setValue(0)
            self.rel_btn.setText("✕")

    def _load_end(self, ok, t):
        if t == self.cur():
            self.progress.hide()
            self.rel_btn.setText("⟳")
            self._upd_nav()
        url = t.url().toString()
        title = t.title()
        if ok and url and url != "about:blank":
            self.history.add(url, title)

    def _load_prog(self, v):
        self.progress.setValue(v)

    # ──── bookmarks ────

    def _default_bookmarks(self):
        for n, u in [
            ("Яндекс", "https://yandex.ru"),
            ("Google", "https://google.com"),
            ("YouTube", "https://youtube.com"),
            ("Wikipedia", "https://ru.wikipedia.org"),
            ("GitHub", "https://github.com"),
        ]:
            self.bookmarks.append({"n": n, "u": u})
        self._rebuild_bm()

    def _rebuild_bm(self):
        while self.bm_lay.count():
            it = self.bm_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        for bm in self.bookmarks:
            b = QPushButton(bm["n"])
            b.setObjectName("bookmarkItem")
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(24)
            b.clicked.connect(
                lambda ch, _u=bm["u"]: self._go_url(_u))
            self.bm_lay.addWidget(b)
        self.bm_lay.addStretch()

    def _go_url(self, u):
        t = self.cur()
        if t:
            t.setUrl(QUrl(u))

    def toggle_bookmark(self):
        t = self.cur()
        if not t:
            return
        u = t.url().toString()
        for bm in self.bookmarks:
            if bm["u"] == u:
                self.bookmarks.remove(bm)
                self._rebuild_bm()
                self._upd_bm()
                return
        self.bookmarks.append(
            {"n": (t.title() or u)[:20], "u": u})
        self._rebuild_bm()
        self._upd_bm()

    def _upd_bm(self):
        t = self.cur()
        if not t:
            return
        u = t.url().toString()
        self.bm_btn.setText(
            "★" if any(b["u"] == u for b in self.bookmarks)
            else "☆")

    # ──── screenshot ────

    def take_screenshot(self):
        t = self.cur()
        if not t:
            return
        menu = QMenu(self)
        menu.setObjectName("mainMenu")
        menu.addAction("📷  Видимая область",
                       self._screenshot_viewport)
        menu.addAction("📄  Вся страница",
                       self._screenshot_full)
        menu.addAction("📋  В буфер обмена",
                       self._screenshot_clip)
        menu.exec_(QCursor.pos())

    def _screenshot_viewport(self):
        t = self.cur()
        if t:
            self._save_screenshot(t.grab())

    def _screenshot_full(self):
        t = self.cur()
        if not t:
            return
        js = (
            "(function(){"
            "return JSON.stringify({"
            "w:Math.max("
            "document.documentElement.scrollWidth,"
            "document.body.scrollWidth,"
            "document.documentElement.clientWidth),"
            "h:Math.max("
            "document.documentElement.scrollHeight,"
            "document.body.scrollHeight,"
            "document.documentElement.clientHeight)"
            "});})()"
        )
        t.page().runJavaScript(js, self._do_full_screenshot)

    def _do_full_screenshot(self, result):
        t = self.cur()
        if not t:
            return
        try:
            dims = (json.loads(result)
                    if isinstance(result, str) else result)
            fw = max(int(dims.get("w", 1280)), t.width())
            fh = min(int(dims.get("h", 900)), 16000)
        except Exception:
            self._save_screenshot(t.grab())
            return

        self._orig = (
            t.size(), t.minimumSize(), t.maximumSize())
        t.setMinimumSize(fw, fh)
        t.setMaximumSize(fw, fh)
        t.resize(fw, fh)
        QTimer.singleShot(800, self._grab_restore)

    def _grab_restore(self):
        t = self.cur()
        if not t:
            return
        pixmap = t.grab()
        s, mn, mx = self._orig
        t.setMinimumSize(mn)
        t.setMaximumSize(mx)
        t.resize(s)
        self._save_screenshot(pixmap)

    def _screenshot_clip(self):
        t = self.cur()
        if not t:
            return
        QApplication.clipboard().setPixmap(t.grab())
        self.toast.show_message("✅ Скопировано в буфер")

    def _save_screenshot(self, pixmap):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        desktop = QStandardPaths.writableLocation(
            QStandardPaths.DesktopLocation)
        if not desktop:
            desktop = os.path.expanduser("~")
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить скриншот",
            os.path.join(desktop, f"screenshot_{ts}.png"),
            "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp)")
        if path:
            ext = os.path.splitext(path)[1].lower()
            fmt = {".jpg": "JPEG", ".jpeg": "JPEG",
                   ".bmp": "BMP"}.get(ext, "PNG")
            if pixmap.save(
                    path, fmt, 95 if fmt == "JPEG" else -1):
                kb = os.path.getsize(path) / 1024
                self.toast.show_message(
                    f"✅ Сохранено ({kb:.0f} КБ)")
            else:
                self.toast.show_message("❌ Ошибка")

    # ──── downloads ────

    def _on_download(self, dl):
        try:
            sug = dl.downloadFileName() or "download"
            d = dl.downloadDirectory()
        except AttributeError:
            sug = (os.path.basename(dl.path())
                   or "download")
            d = (os.path.dirname(dl.path())
                 or os.path.expanduser("~"))
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить",
            os.path.join(d, sug), "Все (*.*)")
        if path:
            fi = QFileInfo(path)
            try:
                dl.setDownloadDirectory(fi.absolutePath())
                dl.setDownloadFileName(fi.fileName())
            except AttributeError:
                dl.setPath(path)
            dl.accept()
            self.download_panel.add_download(dl)
        else:
            dl.cancel()

    def toggle_downloads(self):
        if self.download_panel.isVisible():
            self.download_panel.hide_panel()
        else:
            self.download_panel.show_panel()

    # ──── menu ────

    def show_menu(self):
        m = QMenu(self)
        m.setObjectName("mainMenu")
        m.addAction("➕  Новая вкладка",
                     lambda: self.add_new_tab(
                         url=self._home()), "Ctrl+T")
        m.addSeparator()
        m.addAction("📋  История",
                     self.show_history, "Ctrl+H")
        m.addAction("⬇  Загрузки",
                     self.toggle_downloads, "Ctrl+J")
        m.addSeparator()
        m.addAction("🔍  Найти…",
                     self.find_on_page, "Ctrl+F")
        m.addAction("📷  Скриншот",
                     self.take_screenshot, "Ctrl+Shift+S")
        m.addSeparator()
        zm = m.addMenu("🔎  Масштаб")
        zm.addAction("Увеличить",
                     self.zoom_in, "Ctrl++")
        zm.addAction("Уменьшить",
                     self.zoom_out, "Ctrl+-")
        zm.addAction("Сбросить",
                     self.zoom_reset, "Ctrl+0")
        m.addSeparator()
        m.addAction("🎨  Настройки…",
                     self.show_settings)
        m.addSeparator()
        m.addAction("🛠  DevTools",
                     self.open_dev_tools, "Ctrl+Shift+I")
        m.addSeparator()
        m.addAction("❌  Выход",
                     self.close, "Ctrl+Q")

        pos = self.menu_btn.mapToGlobal(
            self.menu_btn.rect().bottomLeft())
        scr = QApplication.screenAt(pos)
        if scr:
            g = scr.availableGeometry()
            h = m.sizeHint()
            if pos.x() + h.width() > g.right():
                pos.setX(g.right() - h.width())
            if pos.y() + h.height() > g.bottom():
                pos = self.menu_btn.mapToGlobal(
                    self.menu_btn.rect().topLeft())
                pos.setY(pos.y() - h.height())
        m.exec_(pos)

    # ──── settings / history ────

    def show_settings(self):
        dlg = SettingsDialog(
            self, self.current_theme, self.accent)
        self._style_dialog(dlg)
        if dlg.exec_() == QDialog.Accepted:
            self.current_theme = dlg.chosen_theme
            self.accent = dlg.chosen_accent
            self._settings["theme"] = self.current_theme
            self._settings["accent"] = self.accent
            save_settings(self._settings)
            self._apply_theme()

    def _style_dialog(self, dlg):
        th = THEMES.get(
            self.current_theme, THEMES["Тёмная"])
        dlg.setStyleSheet(f"""
            QDialog {{
                background:{th['panel']};
                color:{th['text']};
            }}
            #setTitle {{
                font-size:18px; font-weight:bold;
                color:{th['text']};
            }}
            #setSection {{
                font-size:13px; font-weight:bold;
                color:{th['text2']}; margin-top:6px;
            }}
            QRadioButton {{
                color:{th['text']}; font-size:13px;
                spacing:6px;
            }}
            QRadioButton::indicator {{
                width:16px; height:16px;
                border:2px solid {th['border']};
                border-radius:9px;
                background:{th['url_bg']};
            }}
            QRadioButton::indicator:checked {{
                background:{self.accent};
                border-color:{self.accent};
            }}
            #setBtn {{
                background:{th['url_bg']};
                color:{th['text']};
                border:none; border-radius:6px;
                padding:8px 20px; font-size:13px;
            }}
            #setBtn:hover {{
                background:{th['hover']};
            }}
            #setBtnPrimary {{
                background:{self.accent}; color:#fff;
                border:none; border-radius:6px;
                padding:8px 20px; font-size:13px;
                font-weight:bold;
            }}
            #accentCustom {{
                background:{th['url_bg']};
                border:2px solid {th['border']};
                border-radius:18px; font-size:16px;
            }}
            #accentCustom:hover {{
                border-color:{th['text2']};
            }}
        """)

    def show_history(self):
        dlg = HistoryDialog(self, self.history)
        dlg.navigate_to.connect(
            lambda u: self._go_url(u))
        th = THEMES.get(
            self.current_theme, THEMES["Тёмная"])
        dlg.setStyleSheet(f"""
            QDialog {{
                background:{th['panel']};
                color:{th['text']};
            }}
            #setTitle {{
                font-size:16px; font-weight:bold;
                color:{th['text']};
            }}
            #urlBar {{
                background:{th['url_bg']};
                color:{th['text']};
                border:2px solid transparent;
                border-radius:8px;
                padding:4px 12px;
            }}
            #urlBar:focus {{
                border-color:{self.accent};
            }}
            #historyList {{
                background:{th['bg']};
                color:{th['text']};
                border:1px solid {th['border']};
                border-radius:6px; padding:4px;
            }}
            #historyList::item {{
                padding:6px 8px; border-radius:4px;
            }}
            #historyList::item:selected {{
                background:{self.accent}; color:#fff;
            }}
            #historyList::item:hover {{
                background:{th['hover']};
            }}
            #setBtn {{
                background:{th['url_bg']};
                color:{th['text']};
                border:none; border-radius:6px;
                padding:8px 20px;
            }}
            #setBtn:hover {{
                background:{th['hover']};
            }}
            #setBtnDanger {{
                background:#d32f2f; color:#fff;
                border:none; border-radius:6px;
                padding:8px 16px;
            }}
            #setBtnDanger:hover {{
                background:#b71c1c;
            }}
        """)
        dlg.exec_()

    # ──── misc ────

    def find_on_page(self):
        txt, ok = QInputDialog.getText(
            self, "Найти", "Поиск:")
        if ok and txt:
            t = self.cur()
            if t:
                t.findText(txt)

    def zoom_in(self):
        t = self.cur()
        if t:
            t.setZoomFactor(t.zoomFactor() + 0.1)

    def zoom_out(self):
        t = self.cur()
        if t:
            t.setZoomFactor(
                max(0.25, t.zoomFactor() - 0.1))

    def zoom_reset(self):
        t = self.cur()
        if t:
            t.setZoomFactor(1.0)

    def open_dev_tools(self):
        t = self.cur()
        if t:
            dt = self.add_new_tab()
            t.page().setDevToolsPage(dt.page())

    # ──── shortcuts ────

    def _shortcuts(self):
        sc = QShortcut
        sc(QKeySequence("Ctrl+T"), self,
           lambda: self.add_new_tab(url=self._home()))
        sc(QKeySequence("Ctrl+W"), self,
           lambda: self.close_tab(
               self.tab_bar.currentIndex()))
        sc(QKeySequence("Ctrl+L"), self,
           lambda: (self.url_bar.setFocus(),
                    self.url_bar.selectAll()))
        sc(QKeySequence("Ctrl+R"), self, self.reload)
        sc(QKeySequence("F5"), self, self.reload)
        sc(QKeySequence("Alt+Left"), self, self.go_back)
        sc(QKeySequence("Alt+Right"), self, self.go_fwd)
        sc(QKeySequence("Ctrl+D"), self,
           self.toggle_bookmark)
        sc(QKeySequence("Ctrl+Shift+I"), self,
           self.open_dev_tools)
        sc(QKeySequence("Ctrl+F"), self,
           self.find_on_page)
        sc(QKeySequence("Ctrl+J"), self,
           self.toggle_downloads)
        sc(QKeySequence("Ctrl+H"), self,
           self.show_history)
        sc(QKeySequence("Ctrl+Shift+S"), self,
           self.take_screenshot)
        sc(QKeySequence("Escape"), self,
           self._exit_fullscreen)
        for i in range(1, 10):
            sc(QKeySequence(f"Ctrl+{i}"), self,
               lambda _i=i - 1: (
                   self.tab_bar.setCurrentIndex(_i)
                   if _i < len(self.tabs) else None))

    def _exit_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()

    # ──── events ────

    def closeEvent(self, e):
        n = self.download_panel.active_count()
        if n:
            box = QMessageBox(self)
            box.setWindowTitle("Закрыть?")
            box.setText(
                f"Загрузка ({n}). Закрыть?")
            box.setStandardButtons(
                QMessageBox.Yes | QMessageBox.No)
            if box.exec_() == QMessageBox.No:
                e.ignore()
                return
        e.accept()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if (hasattr(self, "floating")
                and self.floating.isVisible()):
            p = self.floating.parentWidget()
            if p:
                self.floating.move(
                    0,
                    p.height() - self.floating.height())
        if (hasattr(self, "toast")
                and self.toast.isVisible()):
            pw = self.toast.parentWidget()
            if pw:
                self.toast.move(
                    pw.width() - self.toast.width() - 20,
                    pw.height() - self.toast.height() - 20)

    # ══════════════════════════════════════
    #  ТЕМА
    # ══════════════════════════════════════

    def _apply_theme(self):
        th = THEMES.get(
            self.current_theme, THEMES["Тёмная"])
        ac = self.accent
        self._tab_style.set_color(th["text2"])

        css = f"""
        QMainWindow {{
            background: {th['bg']};
        }}
        #topPanel {{
            background: {th['panel']};
        }}
        #tabBarWidget {{
            background: {th['tab_bg']};
        }}
        #tabBar {{
            background: transparent;
            qproperty-drawBase: 0;
        }}
        #tabBar::tab {{
            background: {th['tab']};
            color: {th['text2']};
            border: none;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            padding: 6px 12px;
            padding-right: 26px;
            margin-right: 2px;
            min-width: 100px;
            max-width: 220px;
            font-size: 12px;
        }}
        #tabBar::tab:selected {{
            background: {th['tab_sel']};
            color: {th['text']};
        }}
        #tabBar::tab:hover:!selected {{
            background: {th['tab_hover']};
            color: {th['text']};
        }}
        #tabBar::close-button {{
            subcontrol-position: right;
            padding: 4px;
            margin-right: 2px;
        }}
        #tabBar::close-button:hover {{
            background: rgba(255,70,70,0.45);
            border-radius: 3px;
        }}
        #newTabBtn {{
            background: transparent;
            color: {th['text2']};
            border: none;
            border-radius: 14px;
            font-size: 18px;
            font-weight: bold;
        }}
        #newTabBtn:hover {{
            background: {th['hover']};
            color: {th['text']};
        }}
        #navWidget {{
            background: {th['nav']};
            border-bottom: 1px solid {th['border']};
        }}
        #navBtn, #homeBtn, #menuBtn,
        #sslBtn, #screenshotBtn {{
            background: transparent;
            color: {th['text2']};
            border: none;
            border-radius: 6px;
            font-size: 16px;
        }}
        #navBtn:hover, #homeBtn:hover,
        #menuBtn:hover, #sslBtn:hover,
        #screenshotBtn:hover {{
            background: {th['hover']};
            color: {th['text']};
        }}
        #navBtn:pressed, #homeBtn:pressed,
        #menuBtn:pressed, #screenshotBtn:pressed {{
            background: {th['hover']};
        }}
        #navBtn:disabled {{
            color: {th['text_dim']};
        }}
        #urlBar {{
            background: {th['url_bg']};
            color: {th['text']};
            border: 2px solid transparent;
            border-radius: 8px;
            padding: 4px 12px;
            font-size: 14px;
            selection-background-color: {ac};
        }}
        #urlBar:focus {{
            border-color: {ac};
            background: {th['url_focus']};
        }}
        #urlBar:hover {{
            background: {th['url_focus']};
        }}
        #engineCombo {{
            background: {th['url_bg']};
            color: {th['text2']};
            border: 2px solid transparent;
            border-radius: 8px;
            padding: 4px 8px;
            font-size: 12px;
        }}
        #engineCombo:hover {{
            background: {th['url_focus']};
        }}
        #engineCombo::drop-down {{
            border: none;
            width: 20px;
        }}
        #engineCombo::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid {th['text2']};
            margin-right: 6px;
        }}
        #engineCombo QAbstractItemView {{
            background: {th['menu_bg']};
            color: {th['text']};
            border: 1px solid {th['border']};
            border-radius: 6px;
            selection-background-color: {ac};
            outline: 0;
            padding: 4px;
        }}
        #bookmarksBar {{
            background: {th['bm_bar']};
            border-bottom: 1px solid {th['border']};
        }}
        #bookmarkItem {{
            background: transparent;
            color: {th['text2']};
            border: none;
            border-radius: 4px;
            padding: 2px 10px;
            font-size: 12px;
        }}
        #bookmarkItem:hover {{
            background: {th['hover']};
            color: {th['text']};
        }}
        #progressBar {{
            background: transparent;
            border: none;
        }}
        #progressBar::chunk {{
            background: {ac};
            border-radius: 1px;
        }}
        #floatingStatus {{
            background: {th['float_bg']};
            color: {th['text3']};
            border-top-right-radius: 6px;
            font-size: 11px;
            padding: 1px 6px;
        }}
        #toast {{
            background: {th['panel']};
            color: {th['text']};
            border: 1px solid {th['border']};
            border-radius: 10px;
            font-size: 13px;
            font-weight: bold;
            padding: 8px 16px;
        }}
        #downloadPanel {{
            background: {th['dl_bg']};
            border-top: 1px solid {th['border']};
        }}
        #dlHeader {{
            background: {th['dl_bg']};
        }}
        #dlTitle {{
            color: {th['text']};
            font-size: 12px;
            font-weight: bold;
        }}
        #dlClearBtn {{
            background: {th['hover']};
            color: {th['text2']};
            border: none;
            border-radius: 4px;
            padding: 2px 10px;
            font-size: 11px;
        }}
        #dlClearBtn:hover {{
            color: {th['text']};
        }}
        #dlCloseBtn {{
            background: transparent;
            color: {th['text2']};
            border: none;
            border-radius: 4px;
            font-size: 13px;
        }}
        #dlCloseBtn:hover {{
            background: rgba(255,70,70,0.4);
            color: #fff;
        }}
        #dlScroll {{
            background: transparent;
            border: none;
        }}
        #downloadItem {{
            background: {th['dl_item']};
            border-radius: 6px;
        }}
        #dlName {{
            color: {th['text']};
            font-size: 12px;
        }}
        #dlStatus {{
            color: {th['text3']};
            font-size: 11px;
        }}
        #dlBar {{
            background: {th['bg']};
            border: none;
            border-radius: 3px;
        }}
        #dlBar::chunk {{
            background: {ac};
            border-radius: 3px;
        }}
        #dlActionBtn {{
            background: transparent;
            color: {th['text2']};
            border: none;
            border-radius: 4px;
            font-size: 13px;
        }}
        #dlActionBtn:hover {{
            background: {th['hover']};
        }}
        #dlActionBtn:disabled {{
            color: {th['text_dim']};
        }}
        QMenu {{
            background: {th['menu_bg']};
            color: {th['text']};
            border: 1px solid {th['border']};
            border-radius: 8px;
            padding: 6px 0;
            font-size: 13px;
        }}
        QMenu::item {{
            padding: 8px 24px;
            border-radius: 4px;
            margin: 2px 6px;
        }}
        QMenu::item:selected {{
            background: {ac};
            color: #fff;
        }}
        QMenu::item:disabled {{
            color: {th['text_dim']};
        }}
        QMenu::separator {{
            height: 1px;
            background: {th['border']};
            margin: 4px 12px;
        }}
        QMessageBox {{
            background: {th['panel']};
            color: {th['text']};
        }}
        QMessageBox QPushButton {{
            background: {th['url_bg']};
            color: {th['text']};
            border: none;
            border-radius: 6px;
            padding: 6px 18px;
            min-width: 80px;
        }}
        QMessageBox QPushButton:hover {{
            background: {th['hover']};
        }}
        QInputDialog {{
            background: {th['panel']};
            color: {th['text']};
        }}
        QInputDialog QLineEdit {{
            background: {th['url_bg']};
            color: {th['text']};
            border: 2px solid {th['border']};
            border-radius: 6px;
            padding: 6px;
        }}
        QInputDialog QLineEdit:focus {{
            border-color: {ac};
        }}
        QInputDialog QPushButton {{
            background: {th['url_bg']};
            color: {th['text']};
            border: none;
            border-radius: 6px;
            padding: 6px 18px;
        }}
        QInputDialog QPushButton:hover {{
            background: {th['hover']};
        }}
        QScrollBar:vertical {{
            background: {th['scroll_bg']};
            width: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {th['scroll_h']};
            border-radius: 4px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {th['text_dim']};
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        """
        self.setStyleSheet(css)


# ══════════════════════════════════════════════════════
#  ЗАПУСК
# ══════════════════════════════════════════════════════
def main():
    # ★ ДО создания QApplication!
    QApplication.setAttribute(
        Qt.AA_ShareOpenGLContexts, True)
    QApplication.setAttribute(
        Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(
        Qt.AA_UseHighDpiPixmaps, True)

    # ★ ИСПРАВЛЕННЫЕ Chromium-флаги:
    #   Убрано:
    #     --disable-web-security (вызывал краши рендера)
    #     --allow-running-insecure-content (дестабилизировал)
    #     --disable-renderer-backgrounding (мог зациклить)
    #
    #   Для WebGL-игр:
    #     --ignore-gpu-blocklist → WebGL работает на любой GPU
    #     --enable-gpu-rasterization → быстрый рендер
    #     --enable-accelerated-2d-canvas → Canvas-игры
    #     --use-gl=angle → стабильный WebGL через ANGLE
    #     --enable-unsafe-webgpu → WebGPU (новые игры)
    #     --max-active-webgl-contexts=32 → больше контекстов
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = " ".join([
        "--disable-logging",
        "--ignore-gpu-blocklist",
        "--enable-gpu-rasterization",
        "--enable-accelerated-2d-canvas",
        "--enable-webgl",
        "--enable-webgl2",
        "--use-gl=angle",
        "--max-active-webgl-contexts=32",
        "--autoplay-policy=no-user-gesture-required",
        "--disable-features=BackForwardCache",
        "--disable-background-timer-throttling",
    ])

    app = QApplication(sys.argv)
    app.setApplicationName("Браузер")
    app.setFont(QFont("Segoe UI", 10))

    w = BrowserWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()