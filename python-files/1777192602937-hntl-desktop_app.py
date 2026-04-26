import sys
import os
import subprocess
import shutil
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QListWidget, QListWidgetItem,
    QSplitter, QTabWidget, QToolBar, QLineEdit, QStatusBar,
    QMessageBox, QProgressBar, QFrame, QScrollArea, QSizePolicy
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineDownloadItem, QWebEngineProfile
from PyQt5.QtCore import Qt, QUrl, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QDragEnterEvent, QDropEvent, QPixmap

# ── папка для скачанных файлов ──────────────────────────────────────────────
DOWNLOADS_DIR = Path.home() / "DesktopApp_Downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)


# ════════════════════════════════════════════════════════════════════════════
#  Файловый менеджер (левая панель)
# ════════════════════════════════════════════════════════════════════════════
class FileManagerWidget(QWidget):
    file_opened = pyqtSignal(str)   # путь к открытому файлу

    def __init__(self, parent=None):
        super().__init__(parent)
        self.files: list[Path] = []
        self._build_ui()
        self.setAcceptDrops(True)

    # ── интерфейс ──────────────────────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # заголовок
        header = QLabel("📁  Файловый менеджер")
        header.setStyleSheet("""
            background: #1e1e2e;
            color: #cdd6f4;
            font-size: 14px;
            font-weight: bold;
            padding: 12px 16px;
            border-bottom: 1px solid #313244;
        """)
        layout.addWidget(header)

        # кнопки действий
        btn_bar = QHBoxLayout()
        btn_bar.setContentsMargins(8, 8, 8, 8)
        btn_bar.setSpacing(6)

        self.btn_add = self._make_btn("➕ Добавить", "#89b4fa", self._add_files)
        self.btn_open = self._make_btn("▶ Открыть", "#a6e3a1", self._open_selected)
        self.btn_remove = self._make_btn("🗑 Удалить", "#f38ba8", self._remove_selected)

        for btn in (self.btn_add, self.btn_open, self.btn_remove):
            btn_bar.addWidget(btn)

        layout.addLayout(btn_bar)

        # список файлов
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: #181825;
                color: #cdd6f4;
                border: none;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #1e1e2e;
            }
            QListWidget::item:selected {
                background: #313244;
                color: #89b4fa;
            }
            QListWidget::item:hover {
                background: #242436;
            }
        """)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_click)
        layout.addWidget(self.list_widget)

        # подсказка drag-n-drop
        self.hint = QLabel("Перетащите файлы сюда\nили нажмите «Добавить»")
        self.hint.setAlignment(Qt.AlignCenter)
        self.hint.setStyleSheet("color: #585b70; font-size: 12px; padding: 20px;")
        layout.addWidget(self.hint)

        # папка загрузок
        dl_header = QLabel(f"⬇  Загрузки браузера")
        dl_header.setStyleSheet("""
            background: #1e1e2e;
            color: #cdd6f4;
            font-size: 13px;
            font-weight: bold;
            padding: 10px 16px;
            border-top: 1px solid #313244;
            border-bottom: 1px solid #313244;
        """)
        layout.addWidget(dl_header)

        self.dl_list = QListWidget()
        self.dl_list.setFixedHeight(140)
        self.dl_list.setStyleSheet(self.list_widget.styleSheet())
        self.dl_list.itemDoubleClicked.connect(self._on_dl_double_click)
        layout.addWidget(self.dl_list)

        self._refresh_downloads()

        # авто-обновление папки загрузок каждые 3 с
        timer = QTimer(self)
        timer.timeout.connect(self._refresh_downloads)
        timer.start(3000)

    # ── helpers ────────────────────────────────────────────────────────────
    @staticmethod
    def _make_btn(text: str, color: str, slot) -> QPushButton:
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: #313244;
                color: {color};
                border: 1px solid {color}55;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background: {color}22; }}
            QPushButton:pressed {{ background: {color}44; }}
        """)
        btn.clicked.connect(slot)
        return btn

    def _icon_for(self, path: Path) -> str:
        ext = path.suffix.lower()
        icons = {
            ".exe": "⚙️", ".msi": "📦",
            ".pdf": "📄", ".txt": "📝", ".doc": "📝", ".docx": "📝",
            ".xls": "📊", ".xlsx": "📊", ".csv": "📊",
            ".png": "🖼", ".jpg": "🖼", ".jpeg": "🖼", ".gif": "🖼", ".bmp": "🖼",
            ".mp3": "🎵", ".wav": "🎵", ".flac": "🎵",
            ".mp4": "🎬", ".avi": "🎬", ".mkv": "🎬",
            ".zip": "🗜", ".rar": "🗜", ".7z": "🗜",
            ".py": "🐍", ".js": "🟨", ".html": "🌐",
        }
        return icons.get(ext, "📄")

    # ── drag-n-drop ────────────────────────────────────────────────────────
    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent):
        for url in e.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file():
                self._add_path(path)

    # ── слоты ─────────────────────────────────────────────────────────────
    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Выбрать файлы")
        for p in paths:
            self._add_path(Path(p))

    def _add_path(self, path: Path):
        if path not in self.files:
            self.files.append(path)
            icon = self._icon_for(path)
            item = QListWidgetItem(f"{icon}  {path.name}")
            item.setData(Qt.UserRole, str(path))
            item.setToolTip(str(path))
            self.list_widget.addItem(item)
            self.hint.hide()

    def _open_selected(self):
        for item in self.list_widget.selectedItems():
            self._launch(item.data(Qt.UserRole))

    def _remove_selected(self):
        for item in self.list_widget.selectedItems():
            path = Path(item.data(Qt.UserRole))
            if path in self.files:
                self.files.remove(path)
            self.list_widget.takeItem(self.list_widget.row(item))
        if not self.files:
            self.hint.show()

    def _on_item_double_click(self, item: QListWidgetItem):
        self._launch(item.data(Qt.UserRole))

    def _on_dl_double_click(self, item: QListWidgetItem):
        self._launch(item.data(Qt.UserRole))

    def _launch(self, path_str: str):
        path = Path(path_str)
        if not path.exists():
            QMessageBox.warning(self, "Ошибка", f"Файл не найден:\n{path}")
            return
        self.file_opened.emit(str(path))
        try:
            if sys.platform == "win32":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as ex:
            QMessageBox.critical(self, "Ошибка запуска", str(ex))

    def _refresh_downloads(self):
        current = {
            self.dl_list.item(i).data(Qt.UserRole)
            for i in range(self.dl_list.count())
        }
        for f in sorted(DOWNLOADS_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.is_file() and str(f) not in current:
                icon = self._icon_for(f)
                item = QListWidgetItem(f"{icon}  {f.name}")
                item.setData(Qt.UserRole, str(f))
                item.setToolTip(str(f))
                self.dl_list.insertItem(0, item)

    def add_downloaded_file(self, path: str):
        """Вызывается после завершения загрузки браузером."""
        self._refresh_downloads()


# ════════════════════════════════════════════════════════════════════════════
#  Браузер
# ════════════════════════════════════════════════════════════════════════════
class BrowserWidget(QWidget):
    download_finished = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._setup_downloads()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # панель навигации
        nav = QHBoxLayout()
        nav.setContentsMargins(8, 8, 8, 8)
        nav.setSpacing(6)

        def nav_btn(text, tip, slot):
            b = QPushButton(text)
            b.setToolTip(tip)
            b.setFixedSize(34, 34)
            b.setStyleSheet("""
                QPushButton {
                    background: #313244; color: #cdd6f4;
                    border: none; border-radius: 6px; font-size: 14px;
                }
                QPushButton:hover { background: #45475a; }
                QPushButton:pressed { background: #585b70; }
            """)
            b.clicked.connect(slot)
            return b

        self.btn_back = nav_btn("◀", "Назад", lambda: self.view.back())
        self.btn_fwd  = nav_btn("▶", "Вперёд", lambda: self.view.forward())
        self.btn_reload = nav_btn("⟳", "Обновить", lambda: self.view.reload())
        self.btn_home = nav_btn("🏠", "Домой", self._go_home)

        self.url_bar = QLineEdit("https://www.google.com")
        self.url_bar.setStyleSheet("""
            QLineEdit {
                background: #181825; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 6px;
                padding: 5px 12px; font-size: 13px;
            }
            QLineEdit:focus { border-color: #89b4fa; }
        """)
        self.url_bar.returnPressed.connect(self._navigate)

        self.btn_go = nav_btn("→", "Перейти", self._navigate)

        for w in (self.btn_back, self.btn_fwd, self.btn_reload,
                  self.btn_home, self.url_bar, self.btn_go):
            nav.addWidget(w) if isinstance(w, QPushButton) else nav.addWidget(w, 1)

        nav_widget = QWidget()
        nav_widget.setLayout(nav)
        nav_widget.setStyleSheet("background: #1e1e2e; border-bottom: 1px solid #313244;")
        layout.addWidget(nav_widget)

        # прогресс загрузки страницы
        self.progress = QProgressBar()
        self.progress.setFixedHeight(3)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar { background: #181825; border: none; }
            QProgressBar::chunk { background: #89b4fa; }
        """)
        self.progress.hide()
        layout.addWidget(self.progress)

        # статус загрузки файлов
        self.dl_status = QLabel()
        self.dl_status.setStyleSheet("""
            background: #1e1e2e; color: #a6e3a1;
            font-size: 12px; padding: 4px 12px;
            border-bottom: 1px solid #313244;
        """)
        self.dl_status.hide()
        layout.addWidget(self.dl_status)

        # веб-вью
        self.view = QWebEngineView()
        self.view.setUrl(QUrl("https://www.google.com"))
        self.view.loadStarted.connect(lambda: (self.progress.show(), self.progress.setValue(0)))
        self.view.loadProgress.connect(self.progress.setValue)
        self.view.loadFinished.connect(lambda: self.progress.hide())
        self.view.urlChanged.connect(lambda u: self.url_bar.setText(u.toString()))
        layout.addWidget(self.view)

    def _setup_downloads(self):
        profile = self.view.page().profile()
        profile.downloadRequested.connect(self._on_download)

    def _on_download(self, item: QWebEngineDownloadItem):
        save_path = DOWNLOADS_DIR / Path(item.path()).name
        item.setPath(str(save_path))
        item.accept()

        self.dl_status.setText(f"⬇  Скачивание: {save_path.name}")
        self.dl_status.show()

        item.downloadProgress.connect(self._on_dl_progress)
        item.finished.connect(lambda: self._on_dl_done(str(save_path)))

    def _on_dl_progress(self, received: int, total: int):
        if total > 0:
            pct = int(received / total * 100)
            name = Path(self.sender().path()).name
            self.dl_status.setText(f"⬇  {name}  —  {pct}%  ({received // 1024} КБ / {total // 1024} КБ)")

    def _on_dl_done(self, path: str):
        self.dl_status.setText(f"✅  Скачано: {Path(path).name}  →  {DOWNLOADS_DIR}")
        QTimer.singleShot(4000, self.dl_status.hide)
        self.download_finished.emit(path)

    def _navigate(self):
        text = self.url_bar.text().strip()
        if not text.startswith(("http://", "https://")):
            # если это не URL — ищем в Google
            if "." in text and " " not in text:
                text = "https://" + text
            else:
                text = "https://www.google.com/search?q=" + text.replace(" ", "+")
        self.view.setUrl(QUrl(text))

    def _go_home(self):
        self.view.setUrl(QUrl("https://www.google.com"))


# ════════════════════════════════════════════════════════════════════════════
#  Главное окно
# ════════════════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Desktop App — Файловый менеджер + Браузер")
        self.resize(1400, 860)
        self._apply_theme()
        self._build_ui()

    def _apply_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #181825; color: #cdd6f4; }
            QSplitter::handle { background: #313244; }
            QStatusBar { background: #1e1e2e; color: #585b70; font-size: 12px; padding: 2px 8px; }
            QTabWidget::pane { border: none; }
            QTabBar::tab {
                background: #1e1e2e; color: #585b70;
                padding: 8px 20px; border: none;
                border-right: 1px solid #313244;
                font-size: 13px;
            }
            QTabBar::tab:selected { background: #181825; color: #cdd6f4; border-top: 2px solid #89b4fa; }
            QTabBar::tab:hover { background: #242436; color: #cdd6f4; }
            QScrollBar:vertical { background: #181825; width: 8px; }
            QScrollBar::handle:vertical { background: #45475a; border-radius: 4px; }
        """)

    def _build_ui(self):
        # сплиттер: файловый менеджер | браузер
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)

        # левая панель — файловый менеджер
        self.file_manager = FileManagerWidget()
        self.file_manager.setMinimumWidth(260)
        self.file_manager.file_opened.connect(self._on_file_opened)
        splitter.addWidget(self.file_manager)

        # правая панель — браузер
        self.browser = BrowserWidget()
        self.browser.download_finished.connect(self.file_manager.add_downloaded_file)
        splitter.addWidget(self.browser)

        splitter.setSizes([300, 1100])
        self.setCentralWidget(splitter)

        # статус-бар
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage(
            f"Загрузки сохраняются в: {DOWNLOADS_DIR}   |   "
            "Перетащите файлы в левую панель или нажмите «Добавить»"
        )

    def _on_file_opened(self, path: str):
        self.status.showMessage(f"Открыт: {path}", 5000)


# ════════════════════════════════════════════════════════════════════════════
#  Точка входа
# ════════════════════════════════════════════════════════════════════════════
def main():
    # Необходимо для QtWebEngine на некоторых платформах
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox")

    app = QApplication(sys.argv)
    app.setApplicationName("Desktop App")

    # проверка зависимостей
    try:
        from PyQt5.QtWebEngineWidgets import QWebEngineView
    except ImportError:
        print("Установите: pip install PyQt5 PyQtWebEngine")
        sys.exit(1)

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
