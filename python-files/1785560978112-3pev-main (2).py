import sys, os, re, json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

SETTING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reader_setting.json")

def load_setting():
    try:
        with open(SETTING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_setting(data):
    try:
        with open(SETTING_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except:
        pass

class ChapterParser:
    """智能章节解析器"""
    PATTERNS = [
        r'^\s*第\s*[0-9零一二三四五六七八九十百千]+\s*[章回节卷部篇话]\s*.{0,40}$',
        r'^\s*Chapter\s+\d+\s*.{0,40}$',
        r'^\s*[0-9]+\s*[\.\、]\s*.{1,40}$',
        r'^\s*[0-9]+\s*$',
    ]
    def __init__(self):
        self.compiled = [re.compile(p, re.MULTILINE) for p in self.PATTERNS]
    def parse(self, text):
        lines = text.split('\n')
        chapters = []
        current_title = "正文"
        current_lines = []
        for line in lines:
            is_chapter = False
            for pat in self.compiled:
                m = pat.match(line.strip())
                if m:
                    if current_lines:
                        chapters.append((current_title, '\n'.join(current_lines)))
                    current_title = line.strip()
                    current_lines = []
                    is_chapter = True
                    break
            if not is_chapter:
                current_lines.append(line)
        if current_lines:
            chapters.append((current_title, '\n'.join(current_lines)))
        if not chapters:
            chapters = [("全文", text)]
        return chapters

class ReaderWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setting = load_setting()
        self.chapters = []
        self.current_chapter = 0
        self.text_edit = None
        self.opacity_slider = None
        self.font_slider = None
        self.toc_list = None
        self.toc_dock = None
        self.search_box = None
        self.init_ui()
        self.apply_setting()
        last_file = self.setting.get("last_file")
        if last_file and os.path.exists(last_file):
            self.open_file(last_file)
            pos = self.setting.get("last_pos", 0)
            QTimer.singleShot(200, lambda: self.text_edit.verticalScrollBar().setValue(pos))

    def init_ui(self):
        self.setWindowTitle("悬浮小说阅读器")
        self.setMinimumSize(420, 600)
        w = self.setting.get("width", 480)
        h = self.setting.get("height", 720)
        x = self.setting.get("x")
        y = self.setting.get("y")
        self.resize(w, h)
        if x is not None and y is not None:
            self.move(x, y)

        # 中央文本区
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setCentralWidget(self.text_edit)

        # 目录Dock
        self.toc_dock = QDockWidget("目录", self)
        self.toc_dock.setAllowedAreas(Qt.RightDockWidgetArea)
        toc_widget = QWidget()
        toc_layout = QVBoxLayout(toc_widget)
        self.toc_list = QListWidget()
        self.toc_list.itemClicked.connect(self.jump_to_chapter)
        toc_layout.addWidget(self.toc_list)
        self.toc_dock.setWidget(toc_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.toc_dock)
        self.toc_dock.hide()

        # 工具栏
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        btn_open = QPushButton("📂 打开")
        btn_open.clicked.connect(self.choose_file)
        toolbar.addWidget(btn_open)

        toolbar.addWidget(QLabel(" 透明度:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(int(self.setting.get("opacity", 100)))
        self.opacity_slider.setFixedWidth(100)
        self.opacity_slider.valueChanged.connect(self.change_opacity)
        toolbar.addWidget(self.opacity_slider)

        btn_pin = QPushButton("📌 置顶")
        btn_pin.setCheckable(True)
        btn_pin.setChecked(True)
        btn_pin.clicked.connect(lambda: self.set_window_flags(btn_pin.isChecked()))
        self.btn_pin = btn_pin
        toolbar.addWidget(btn_pin)

        toolbar.addWidget(QLabel(" 字号:"))
        self.font_slider = QSlider(Qt.Horizontal)
        self.font_slider.setRange(12, 26)
        self.font_slider.setValue(int(self.setting.get("font_size", 16)))
        self.font_slider.setFixedWidth(80)
        self.font_slider.valueChanged.connect(self.change_font)
        toolbar.addWidget(self.font_slider)

        btn_prev = QPushButton("◀ 上一章")
        btn_prev.clicked.connect(self.prev_chapter)
        toolbar.addWidget(btn_prev)

        btn_next = QPushButton("下一章 ▶")
        btn_next.clicked.connect(self.next_chapter)
        toolbar.addWidget(btn_next)

        btn_toc = QPushButton("📑 目录")
        btn_toc.clicked.connect(self.toggle_toc)
        toolbar.addWidget(btn_toc)

        toolbar.addWidget(QLabel(" 🔎"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索关键词...")
        self.search_box.setFixedWidth(140)
        self.search_box.returnPressed.connect(self.search_text)
        toolbar.addWidget(self.search_box)

        btn_bookmark = QPushButton("🔖 书签")
        btn_bookmark.clicked.connect(self.save_bookmark)
        toolbar.addWidget(btn_bookmark)

        # 状态栏
        self.statusBar().showMessage("欢迎使用悬浮小说阅读器 | 打开txt开始阅读")

        # 快捷键
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(lambda: self.search_box.setFocus())
        QShortcut(QKeySequence("Alt+P"), self).activated.connect(lambda: self.btn_pin.click())
        QShortcut(QKeySequence(Qt.Key_Left), self).activated.connect(self.prev_chapter)
        QShortcut(QKeySequence(Qt.Key_Right), self).activated.connect(self.next_chapter)
        QShortcut(QKeySequence(Qt.Key_PageUp), self).activated.connect(self.prev_chapter)
        QShortcut(QKeySequence(Qt.Key_PageDown), self).activated.connect(self.next_chapter)

        # 深色样式
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1530, stop:1 #0f1b2d);
            }
            QTextEdit {
                background: rgba(20, 18, 35, 0.85);
                color: #e8e6f0;
                border: none;
                padding: 16px;
                font-family: "Microsoft YaHei", "SimSun", serif;
                selection-background-color: #5b4b9b;
            }
            QToolBar {
                background: rgba(30, 25, 55, 0.95);
                border: none;
                spacing: 6px;
                padding: 4px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6a5acd, stop:1 #483d8b);
                color: white;
                border: none;
                padding: 5px 12px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7b6be0, stop:1 #584da0); }
            QPushButton:pressed { background: #4a3f8a; }
            QPushButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff8c42, stop:1 #e56717);
            }
            QLabel { color: #b0a8d0; font-size: 13px; }
            QLineEdit {
                background: rgba(40, 35, 65, 0.9);
                color: #e8e6f0;
                border: 1px solid #5b4b9b;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #3a3260;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 16px;
                height: 16px;
                margin: -5px 0;
                background: #8a7bd8;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #6a5acd;
                border-radius: 3px;
            }
            QDockWidget {
                background: rgba(25, 20, 45, 0.95);
                color: #b0a8d0;
            }
            QListWidget {
                background: rgba(25, 20, 45, 0.95);
                color: #d0cce8;
                border: 1px solid #4a3f8a;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background: #5b4b9b;
                color: white;
            }
            QListWidget::item:hover { background: rgba(91, 75, 155, 0.5); }
            QScrollBar:vertical {
                background: rgba(30, 25, 55, 0.5);
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #6a5acd;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #8a7bd8; }
            QStatusBar {
                background: rgba(20, 15, 40, 0.95);
                color: #9088b8;
            }
        """)

    def apply_setting(self):
        self.change_opacity(self.opacity_slider.value())
        self.change_font(self.font_slider.value())

    def change_opacity(self, val):
        self.setWindowOpacity(val / 100.0)
        self.setting["opacity"] = val
        save_setting(self.setting)

    def change_font(self, val):
        fmt = QFont("Microsoft YaHei", val)
        self.text_edit.setFont(fmt)
        self.setting["font_size"] = val
        save_setting(self.setting)

    def set_window_flags(self, pin):
        flags = Qt.WindowStaysOnTopHint if pin else Qt.Widget
        self.setWindowFlags(flags)
        self.show()
        self.btn_pin.setText("📌 置顶" if pin else "📌 取消置顶")
        self.setting["pinned"] = pin
        save_setting(self.setting)

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择小说文件", "", "文本文件 (*.txt);;所有文件 (*.*)")
        if path:
            self.open_file(path)

    def open_file(self, path):
        encodings = ["utf-8", "gbk", "gb2312", "gb18030", "big5"]
        text = None
        for enc in encodings:
            try:
                with open(path, "r", encoding=enc) as f:
                    text = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        if text is None:
            QMessageBox.warning(self, "错误", "无法识别文件编码，请另存为UTF-8后重试")
            return
        self.parser = ChapterParser()
        self.chapters = self.parser.parse(text)
        self.current_chapter = 0
        self.toc_list.clear()
        for i, (title, _) in enumerate(self.chapters):
            item = QListWidgetItem(f"{i+1}. {title[:30]}")
            self.toc_list.addItem(item)
        self.setting["last_file"] = path
        save_setting(self.setting)
        self.show_chapter(0)
        self.statusBar().showMessage(f"已打开: {os.path.basename(path)} | 共 {len(self.chapters)} 章")

    def show_chapter(self, idx):
        if not self.chapters or idx < 0 or idx >= len(self.chapters):
            return
        self.current_chapter = idx
        title, content = self.chapters[idx]
        self.text_edit.setHtml(
            f'<div style="text-align:center;color:#8a7bd8;font-size:18px;margin-bottom:10px;">'
            f'{title}</div>'
            f'<div style="line-height:1.8;">{content.replace(chr(10), "<br>")}</div>'
        )
        self.text_edit.verticalScrollBar().setValue(0)
        self.set_setting_pos()
        # 高亮当前章
        for i in range(self.toc_list.count()):
            item = self.toc_list.item(i)
            if i == idx:
                item.setBackground(QColor(91, 75, 155, 120))
            else:
                item.setBackground(QColor(0, 0, 0, 0))

    def prev_chapter(self):
        if self.current_chapter > 0:
            self.show_chapter(self.current_chapter - 1)

    def next_chapter(self):
        if self.current_chapter < len(self.chapters) - 1:
            self.show_chapter(self.current_chapter + 1)

    def jump_to_chapter(self, item):
        idx = self.toc_list.row(item)
        self.show_chapter(idx)

    def toggle_toc(self):
        self.toc_dock.setVisible(not self.toc_dock.isVisible())
        if self.toc_dock.isVisible():
            self.toc_dock.setFixedWidth(220)

    def search_text(self):
        keyword = self.search_box.text().strip()
        if not keyword:
            return
        # 先在目录里搜
        toc_hit = []
        for i, (title, _) in enumerate(self.chapters):
            if keyword in title:
                toc_hit.append(i)
        if toc_hit:
            self.show_chapter(toc_hit[0])
            self.statusBar().showMessage(f"在目录中找到 '{keyword}'，跳转到第{toc_hit[0]+1}章")
            return
        # 全文搜
        for i, (title, content) in enumerate(self.chapters):
            if keyword in content:
                self.show_chapter(i)
                # 高亮搜索词
                cursor = self.text_edit.textCursor()
                doc = self.text_edit.document()
                cursor.setPosition(0)
                found = doc.find(keyword, cursor)
                if not found.isNull():
                    self.text_edit.setTextCursor(found)
                    self.text_edit.ensureCursorVisible()
                self.statusBar().showMessage(f"在第{i+1}章找到 '{keyword}'")
                return
        self.statusBar().showMessage(f"未找到 '{keyword}'")

    def save_bookmark(self):
        if not self.chapters:
            return
        self.setting["last_chapter"] = self.current_chapter
        self.setting["last_pos"] = self.text_edit.verticalScrollBar().value()
        save_setting(self.setting)
        self.statusBar().showMessage(f"已保存书签: 第{self.current_chapter+1}章")

    def set_setting_pos(self):
        self.setting["last_chapter"] = self.current_chapter
        self.setting["last_pos"] = 0
        save_setting(self.setting)

    def closeEvent(self, event):
        self.setting["width"] = self.width()
        self.setting["height"] = self.height()
        self.setting["x"] = self.x()
        self.setting["y"] = self.y()
        self.setting["last_chapter"] = self.current_chapter
        self.setting["last_pos"] = self.text_edit.verticalScrollBar().value()
        save_setting(self.setting)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 14))
    win = ReaderWindow()
    win.show()
    sys.exit(app.exec_())