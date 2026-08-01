# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║                   📖 悬浮小说阅读器 v2.0                      ║
║  ───────────────────────────────────────────────────────────  ║
║  ✦ 透明悬浮窗口，覆盖其他应用阅读                              ║
║  ✦ 透明度自由调节 (20%~100%)                                  ║
║  ✦ 智能章节解析 & 快速切换                                    ║
║  ✦ 全文搜索 & 关键词跳转                                      ║
║  ✦ 自动记忆阅读位置                                            ║
║  ✦ 自定义字号/行距 & 深色主题                                  ║
╚══════════════════════════════════════════════════════════════╝
"""

import sys, os, re, json
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QSlider, QPushButton, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QDockWidget, QFileDialog, QMessageBox,
    QFrame, QSystemTrayIcon, QMenu, QShortcut, QComboBox
)

# ──────────────────────────────────────────────
#  全局深色紫蓝渐变主题
# ──────────────────────────────────────────────
QSS = """
QMainWindow {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #2b2b3d, stop:1 #15152a);
    border-radius: 14px;
}
QFrame#titleBar {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #6c5ce7, stop:0.5 #8e7cc3, stop:1 #a55ee9);
    border-top-left-radius: 14px; border-top-right-radius: 14px;
}
QFrame#titleBar QLabel { color: white; font-size: 14px; font-weight: bold; }

QPushButton { background: rgba(108,92,231,0.72); color: white; border: none; padding: 6px 14px; border-radius: 6px; font-size: 13px; font-weight: bold; }
QPushButton:hover  { background: rgba(138,122,255,0.92); }
QPushButton:pressed { background: rgba(88,72,200,0.95); }

QPushButton#closeBtn { background: rgba(231,76,60,0.78); border-radius: 13px; padding: 0; font-size: 13px; }
QPushButton#closeBtn:hover { background: rgba(231,76,60,1.0); }
QPushButton#minBtn   { background: rgba(241,196,15,0.78); border-radius: 13px; padding: 0; font-size: 13px; }
QPushButton#minBtn:hover   { background: rgba(241,196,15,1.0); }

QTextEdit {
    background: rgba(26,26,44,0.90); color: #e4e4f0;
    border: 1px solid rgba(108,92,231,0.22); border-radius: 10px;
    padding: 18px 26px; font-size: 15px; line-height: 1.95;
    selection-background-color: rgba(108,92,231,0.55); selection-color: #fff;
}
QLineEdit {
    background: rgba(40,40,62,0.88); color: #e4e4f0;
    border: 1px solid rgba(108,92,231,0.4); border-radius: 6px;
    padding: 5px 10px; font-size: 13px;
}
QLineEdit:focus { border: 1px solid rgba(165,94,233,0.85); }

QSlider::groove:horizontal { background: rgba(60,60,85,0.55); height: 6px; border-radius: 3px; }
QSlider::handle:horizontal {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #c39bd3, stop:0.5 #a55ee9, stop:1 #6c5ce7);
    width: 18px; height: 18px; margin: -6px 0; border-radius: 9px;
    border: 2px solid rgba(255,255,255,0.35);
}
QSlider::handle:horizontal:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #d7bde2, stop:0.5 #bb8fce, stop:1 #8e7cc3);
}

QLabel { color: #9e9eb5; font-size: 12px; }

QListWidget {
    background: rgba(33,33,54,0.94); color: #d0d0e4;
    border: 1px solid rgba(108,92,231,0.28); border-radius: 8px;
    padding: 5px; font-size: 13px;
}
QListWidget::item { padding: 8px 12px; border-radius: 5px; margin: 2px 0; }
QListWidget::item:hover    { background: rgba(108,92,231,0.28); }
QListWidget::item:selected {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 rgba(108,92,231,0.65), stop:1 rgba(165,94,233,0.65));
    color: white; font-weight: bold;
}

QScrollBar:vertical { background: rgba(40,40,62,0.35); width: 10px; border-radius: 5px; margin: 0; }
QScrollBar::handle:vertical {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #a55ee9, stop:1 #6c5ce7);
    border-radius: 5px; min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #c39bd3, stop:1 #8e7cc3); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QDockWidget { background: rgba(28,28,48,0.96); color: #e0e0e0; }
QDockWidget::title {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #6c5ce7, stop:1 #a55ee9);
    padding: 6px 10px; border-radius: 6px; font-weight: bold;
}

QComboBox {
    background: rgba(40,40,62,0.88); color: #e0e0e0;
    border: 1px solid rgba(108,92,231,0.35); border-radius: 6px;
    padding: 3px 8px; font-size: 12px;
}
QComboBox:hover { border: 1px solid rgba(138,122,255,0.7); }
QComboBox QAbstractItemView {
    background: rgba(35,35,56,0.98); color: #e0e0e0;
    selection-background-color: rgba(108,92,231,0.6); border-radius: 6px;
}
"""


# ════════════════════════════════════════════════════════════
#  主窗口
# ════════════════════════════════════════════════════════════
class NovelReader(QMainWindow):

    # ───── 初始化 ─────
    def __init__(self):
        super().__init__()
        self.chapters = []
        self.current_chapter = 0
        self.novel_path = ""
        self._bookmark_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bookmark.json")
        self.dragging = False
        self.drag_offset = None
        self._init_window()
        self._init_ui()
        self._init_tray()
        self._init_shortcuts()
        self.show_welcome()
        QTimer.singleShot(500, self._restore_bookmark)

    def _init_window(self):
        self.setWindowTitle("悬浮小说阅读器")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.resize(540, 740)
        self.move(120, 80)
        self.setStyleSheet(QSS)

    # ───── UI ─────
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_title_bar())
        root.addWidget(self._build_tool_bar())
        root.addWidget(self._build_control_bar())
        root.addWidget(self._build_text_area(), 1)
        root.addWidget(self._build_status_bar())
        self._build_toc_dock()
        self.change_opacity(85)

    def _build_title_bar(self):
        bar = QFrame()
        bar.setObjectName("titleBar")
        bar.setFixedHeight(40)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 0, 8, 0)
        self.title_label = QLabel("📖 悬浮小说阅读器")
        lay.addWidget(self.title_label)
        lay.addStretch()
        self.pin_btn = QPushButton("📌")
        self.pin_btn.setFixedSize(28, 28)
        self.pin_btn.setCheckable(True)
        self.pin_btn.setChecked(True)
        self.pin_btn.setToolTip("取消/设置置顶 (Alt+P)")
        self.pin_btn.clicked.connect(self.toggle_pin)
        lay.addWidget(self.pin_btn)
        self.min_btn = QPushButton("—")
        self.min_btn.setObjectName("minBtn")
        self.min_btn.setFixedSize(28, 28)
        self.min_btn.clicked.connect(self.showMinimized)
        lay.addWidget(self.min_btn)
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.clicked.connect(self.close)
        lay.addWidget(self.close_btn)
        return bar

    def _build_tool_bar(self):
        bar = QFrame()
        bar.setStyleSheet("background: rgba(40,40,62,0.55); border-bottom: 1px solid rgba(108,92,231,0.15);")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(8)
        self.open_btn = QPushButton("📂 打开")
        self.open_btn.setFixedHeight(28)
        self.open_btn.clicked.connect(self.open_file)
        lay.addWidget(self.open_btn)
        self.prev_btn = QPushButton("◀ 上一章")
        self.prev_btn.setFixedHeight(28)
        self.prev_btn.clicked.connect(self.prev_chapter)
        lay.addWidget(self.prev_btn)
        self.chapter_label = QLabel("第 0/0 章")
        self.chapter_label.setStyleSheet("color:#c8c8d8; font-size:12px; min-width:72px; text-align:center;")
        lay.addWidget(self.chapter_label)
        self.next_btn = QPushButton("下一章 ▶")
        self.next_btn.setFixedHeight(28)
        self.next_btn.clicked.connect(self.next_chapter)
        lay.addWidget(self.next_btn)
        self.toc_btn = QPushButton("📑 目录")
        self.toc_btn.setFixedHeight(28)
        self.toc_btn.setCheckable(True)
        self.toc_btn.clicked.connect(self.toggle_toc)
        lay.addWidget(self.toc_btn)
        self.bookmark_btn = QPushButton("🔖 书签")
        self.bookmark_btn.setFixedHeight(28)
        self.bookmark_btn.setCheckable(True)
        self.bookmark_btn.clicked.connect(self.toggle_bookmark)
        lay.addWidget(self.bookmark_btn)
        lay.addStretch()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索...")
        self.search_input.setFixedWidth(150)
        self.search_input.setFixedHeight(26)
        self.search_input.returnPressed.connect(self.search_text)
        lay.addWidget(self.search_input)
        self.search_btn = QPushButton("搜索")
        self.search_btn.setFixedHeight(26)
        self.search_btn.clicked.connect(self.search_text)
        lay.addWidget(self.search_btn)
        return bar

    def _build_control_bar(self):
        bar = QFrame()
        bar.setStyleSheet("background: rgba(35,35,55,0.45);")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(12, 4, 12, 4)
        lay.setSpacing(8)
        lab = QLabel("🔍 透明度:")
        lab.setStyleSheet("color:#9e9eb5; font-size:11px;")
        lay.addWidget(lab)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(85)
        self.opacity_slider.setFixedWidth(180)
        self.opacity_slider.valueChanged.connect(self.change_opacity)
        lay.addWidget(self.opacity_slider)
        self.opacity_value_label = QLabel("85%")
        self.opacity_value_label.setStyleSheet("color:#b8b8cc; font-size:11px; min-width:35px;")
        lay.addWidget(self.opacity_value_label)
        lay.addStretch()
        flab = QLabel("字号:")
        flab.setStyleSheet("color:#9e9eb5; font-size:11px;")
        lay.addWidget(flab)
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setRange(12, 26)
        self.font_size_slider.setValue(15)
        self.font_size_slider.setFixedWidth(100)
        self.font_size_slider.valueChanged.connect(self.change_font_size)
        lay.addWidget(self.font_size_slider)
        self.font_size_label = QLabel("15px")
        self.font_size_label.setStyleSheet("color:#b8b8cc; font-size:11px; min-width:30px;")
        lay.addWidget(self.font_size_label)
        lhlab = QLabel("行距:")
        lhlab.setStyleSheet("color:#9e9eb5; font-size:11px;")
        lay.addWidget(lhlab)
        self.line_height_combo = QComboBox()
        self.line_height_combo.addItems(["紧凑", "标准", "宽松", "很宽"])
        self.line_height_combo.setCurrentIndex(1)
        self.line_height_combo.currentIndexChanged.connect(lambda: self.display_chapter(self.current_chapter, keep_pos=True) if self.chapters else None)
        lay.addWidget(self.line_height_combo)
        return bar

    def _build_text_area(self):
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        font = QFont("Microsoft YaHei", 15)
        font.setStyleHint(QFont.SansSerif)
        self.text_edit.setFont(font)
        return self.text_edit

    def _build_status_bar(self):
        bar = QFrame()
        bar.setStyleSheet("background: rgba(40,40,62,0.65); border-top: 1px solid rgba(108,92,231,0.15);")
        bar.setFixedHeight(26)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(12, 0, 12, 0)
        self.status_label = QLabel("点击 📂 打开小说文件开始阅读")
        self.status_label.setStyleSheet("color:#888899; font-size:11px;")
        lay.addWidget(self.status_label)
        lay.addStretch()
        self.word_count_label = QLabel("字数: 0")
        self.word_count_label.setStyleSheet("color:#888899; font-size:11px;")
        lay.addWidget(self.word_count_label)
        self.progress_label = QLabel("进度: 0%")
        self.progress_label.setStyleSheet("color:#888899; font-size:11px; min-width:50px;")
        lay.addWidget(self.progress_label)
        return bar

    def _build_toc_dock(self):
        self.toc_dock = QDockWidget("📑 章节目录", self)
        self.toc_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)
        self.toc_search = QLineEdit()
        self.toc_search.setPlaceholderText("🔍 搜索章节名...")
        self.toc_search.textChanged.connect(self.filter_chapters)
        lay.addWidget(self.toc_search)
        self.toc_list = QListWidget()
        self.toc_list.itemClicked.connect(self.jump_to_chapter)
        lay.addWidget(self.toc_list)
        self.toc_dock.setWidget(w)
        self.toc_dock.setFloating(False)
        self.toc_dock.setFeatures(QDockWidget.DockWidgetClosable)
        self.addDockWidget(Qt.RightDockWidgetArea, self.toc_dock)
        self.toc_dock.hide()

    # ───── 托盘 ─────
    def _init_tray(self):
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setToolTip("悬浮小说阅读器")
            m = QMenu()
            m.addAction("显示", self.showNormal)
            m.addAction("隐藏", self.hide)
            m.addSeparator()
            m.addAction("退出", QApplication.quit)
            self.tray_icon.setContextMenu(m)
            self.tray_icon.show()

    # ───── 快捷键 ─────
    def _init_shortcuts(self):
        QShortcut(Qt.Key_Left, self).activated.connect(self.prev_chapter)
        QShortcut(Qt.Key_Right, self).activated.connect(self.next_chapter)
        QShortcut(Qt.Key_PageUp, self).activated.connect(self.prev_chapter)
        QShortcut(Qt.Key_PageDown, self).activated.connect(self.next_chapter)
        QShortcut(Qt.CTRL + Qt.Key_O, self).activated.connect(self.open_file)
        QShortcut(Qt.CTRL + Qt.Key_F, self).activated.connect(self.search_input.setFocus)
        QShortcut(Qt.ALT + Qt.Key_P, self).activated.connect(lambda: [self.pin_btn.toggle(), self.toggle_pin()])

    # ───── 欢迎页 ─────
    def show_welcome(self):
        self.text_edit.setHtml("""
<div style="text-align:center; padding:50px 20px; color:#888899;">
<h2 style="color:#a55ee9; margin-bottom:16px;">📖 悬浮小说阅读器</h2>
<p style="font-size:15px; color:#9999aa;">点击 <b style="color:#a55ee9;">📂 打开</b> 选择小说 (.txt)</p><br>
<div style="font-size:13px; color:#777788; line-height:2.2;">
✦ 拖动标题栏移动窗口 &nbsp; ✦ 滑块调节透明度<br>
✦ 覆盖在游戏/视频上方 &nbsp; ✦ ← → 翻章<br>
✦ Ctrl+F 搜索 &nbsp; ✦ 🔖 自动记忆位置
</div></div>""")

    # ───── 鼠标拖动 ─────
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and e.y() < 40:
            self.dragging = True
            self.drag_offset = e.globalPos() - self.pos()

    def mouseMoveEvent(self, e):
        if self.dragging and self.drag_offset:
            self.move(e.globalPos() - self.drag_offset)

    def mouseReleaseEvent(self, e):
        self.dragging = False
        self.drag_offset = None

    # ───── 透明度/字号/行距 ─────
    def change_opacity(self, v):
        self.setWindowOpacity(v / 100.0)
        self.opacity_value_label.setText(f"{v}%")

    def change_font_size(self, v):
        f = self.text_edit.font()
        f.setPointSize(v)
        self.text_edit.setFont(f)
        self.font_size_label.setText(f"{v}px")
        if self.chapters:
            self.display_chapter(self.current_chapter, keep_pos=True)

    def _line_height(self):
        return [1.6, 1.9, 2.3, 2.7][self.line_height_combo.currentIndex()]

    # ───── 置顶 ─────
    def toggle_pin(self):
        if self.pin_btn.isChecked():
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.pin_btn.setText("📌")
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.pin_btn.setText("📍")
        self.show()

    # ───── 打开小说 ─────
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开小说文件", "", "文本文件 (*.txt);;所有文件 (*)")
        if path:
            self.load_novel(path)

    def load_novel(self, path):
        try:
            content = None
            for enc in ["utf-8", "gbk", "gb2312", "gb18030", "big5", "latin-1"]:
                try:
                    with open(path, "r", encoding=enc) as f:
                        content = f.read()
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            if content is None:
                QMessageBox.warning(self, "错误", "无法识别文件编码！")
                return
            self.novel_path = path
            self.title_label.setText(f"📖 {os.path.basename(path)}")
            self.chapters = self._parse_chapters(content)
            if not self.chapters:
                self.chapters = [("全文", content)]
            self._update_toc()
            self.current_chapter = 0
            self.display_chapter(0)
            self.status_label.setText(f"已加载: {os.path.basename(path)} | 共 {len(self.chapters)} 章")
            self._check_bookmark()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败:\n{str(e)}")

    # ───── 章节解析 ─────
    def _parse_chapters(self, content):
        patterns = [
            r"^第[一二三四五六七八九十百千零0-9]+章.*$",
            r"^第[一二三四五六七八九十百千零0-9]+[回节卷话篇].*$",
            r"^[Cc]hapter\s*\d+.*$",
            r"^CHAPTER\s*\d+.*$",
            r"^[0-9]{1,3}\s*[\.\、\．].*$",
            r"^卷[一二三四五六七八九十百千零0-9]+.*$",
        ]
        lines = content.split("\n")
        indices = []
        for i, line in enumerate(lines):
            s = line.strip()
            if not s:
                continue
            for p in patterns:
                if re.match(p, s):
                    indices.append(i)
                    break
        if len(indices) < 2:
            chunk = 5000
            return [(f"第{n+1}段", content[i:i+chunk].strip())
                    for n, i in enumerate(range(0, len(content), chunk)) if content[i:i+chunk].strip()]
        chapters = []
        for i, idx in enumerate(indices):
            title = re.sub(r"^[\s\d\.]+", "", lines[idx].strip()) or f"第{i+1}章"
            end = indices[i+1] if i+1 < len(indices) else len(lines)
            body = re.sub(r"\n{3,}", "\n\n", "\n".join(lines[idx+1:end]).strip())
            if body or title:
                chapters.append((title, body))
        return chapters

    # ───── 目录 ─────
    def _update_toc(self):
        self.toc_list.clear()
        for i, (t, _) in enumerate(self.chapters):
            item = QListWidgetItem(f"{i+1}. {t}")
            item.setData(Qt.UserRole, i)
            self.toc_list.addItem(item)

    def filter_chapters(self, text):
        for i in range(self.toc_list.count()):
            item = self.toc_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def toggle_toc(self):
        self.toc_dock.show() if self.toc_btn.isChecked() else self.toc_dock.hide()

    def jump_to_chapter(self, item):
        self.display_chapter(item.data(Qt.UserRole))

    # ───── 显示章节 ─────
    def display_chapter(self, idx, keep_pos=False):
        if not self.chapters or idx < 0 or idx >= len(self.chapters):
            return
        old_scroll = self.text_edit.verticalScrollBar().value() if keep_pos else 0
        self.current_chapter = idx
        title, content = self.chapters[idx]
        lh = self._line_height()
        body_html = "\n".join(
            f'<p style="text-indent:2em; margin:0.4em 0;">{p.strip()}</p>'
            for p in content.split("\n") if p.strip()
        )
        html = f"""
<div style="max-width:100%; margin:0 auto;">
<h2 style="text-align:center; color:#a55ee9; padding:10px 0;
     border-bottom:1px solid rgba(108,92,231,0.3); margin-bottom:16px;
     font-size:18px; letter-spacing:2px;">{title}</h2>
<div style="font-size:15px; line-height:{lh}; color:#d8d8e8;">{body_html}</div>
</div>"""
        self.text_edit.setHtml(html)
        self.text_edit.moveCursor(QTextCursor.Start)
        if keep_pos:
            QTimer.singleShot(50, lambda v=old_scroll: self.text_edit.verticalScrollBar().setValue(v))
        self.chapter_label.setText(f"第 {idx+1}/{len(self.chapters)} 章")
        self.word_count_label.setText(f"字数: {len(content)}")
        self.status_label.setText(f"📖 {title}")
        self.toc_list.setCurrentRow(idx)
        progress = int((idx + 1) / len(self.chapters) * 100)
        self.progress_label.setText(f"进度: {progress}%")
        self._save_bookmark()

    def prev_chapter(self):
        if self.chapters and self.current_chapter > 0:
            self.display_chapter(self.current_chapter - 1)

    def next_chapter(self):
        if self.chapters and self.current_chapter < len(self.chapters) - 1:
            self.display_chapter(self.current_chapter + 1)

    # ───── 搜索 ─────
    def search_text(self):
        query = self.search_input.text().strip()
        if not query:
            return
        if not self.chapters:
            QMessageBox.information(self, "提示", "请先打开小说文件！")
            return
        if self.text_edit.find(query, Qt.CaseInsensitive):
            self.status_label.setText(f"✅ 当前章节找到「{query}」")
            return
        for i in range(len(self.chapters)):
            if query.lower() in self.chapters[i][1].lower():
                self.display_chapter(i)
                QTimer.singleShot(150, lambda q=query: self.text_edit.find(q, Qt.CaseInsensitive))
                self.status_label.setText(f"🔍 在「{self.chapters[i][0]}」中找到「{query}」")
                return
        self.status_label.setText(f"❌ 未找到「{query}」")
        QMessageBox.information(self, "搜索结果", f"未找到「{query}」")

    # ───── 书签 ─────
    def _save_bookmark(self):
        if not self.novel_path or not self.chapters:
            return
        try:
            data = {
                "path": self.novel_path,
                "chapter": self.current_chapter,
                "scroll": self.text_edit.verticalScrollBar().value(),
                "mtime": os.path.getmtime(self.novel_path) if os.path.exists(self.novel_path) else 0
            }
            with open(self._bookmark_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass

    def _restore_bookmark(self):
        try:
            if not os.path.exists(self._bookmark_path):
                return
            with open(self._bookmark_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            path = data.get("path", "")
            if path and os.path.exists(path):
                self.load_novel(path)
                self.display_chapter(min(data.get("chapter", 0), len(self.chapters) - 1))
                QTimer.singleShot(300, lambda v=data.get("scroll", 0): self.text_edit.verticalScrollBar().setValue(v))
                self.status_label.setText("📌 已恢复上次阅读位置")
        except Exception:
            pass

    def _check_bookmark(self):
        try:
            if not os.path.exists(self._bookmark_path):
                return
            with open(self._bookmark_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("path") == self.novel_path:
                self.bookmark_btn.setChecked(True)
                self.bookmark_btn.setText("🔖 已收藏")
        except Exception:
            pass

    def toggle_bookmark(self):
        if self.bookmark_btn.isChecked():
            self._save_bookmark()
            self.bookmark_btn.setText("🔖 已收藏")
            self.status_label.setText("📌 已保存书签")
        else:
            self.bookmark_btn.setText("🔖 书签")
            if os.path.exists(self._bookmark_path):
                os.remove(self._bookmark_path)
            self.status_label.setText("🗑️ 已清除书签")

    # ───── 关闭 ─────
    def closeEvent(self, e):
        self._save_bookmark()
        if hasattr(self, "tray_icon"):
            self.tray_icon.hide()
        e.accept()


# ════════════════════════════════════════════════════════════
#  入口
# ════════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    app.setStyle("Fusion")
    win = NovelReader()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
