import sys
import json
import os
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLineEdit, QPushButton, QComboBox,
                             QToolBar, QAction, QSizePolicy)
from PyQt6.QtWebEngineWidgets import QWebEngineView

CONFIG_FILE = "url_config.json"

class VideoPlayerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("自定义网页视频播放器")
        self.resize(1200, 800)
        self.url_list = self.load_config()
        self.init_ui()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.url_list, f, ensure_ascii=False, indent=2)

    def init_ui(self):
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)

        self.cbx_url = QComboBox()
        self.cbx_url.addItems(self.url_list)
        self.cbx_url.setEditable(True)
        self.cbx_url.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        btn_go = QPushButton("打开播放")
        btn_go.clicked.connect(self.open_url)
        btn_add = QPushButton("保存网址")
        btn_add.clicked.connect(self.add_url)
        btn_del = QPushButton("删除选中")
        btn_del.clicked.connect(self.del_url)

        top_layout.addWidget(self.cbx_url)
        top_layout.addWidget(btn_go)
        top_layout.addWidget(btn_add)
        top_layout.addWidget(btn_del)

        self.web_view = QWebEngineView()
        self.web_view.urlChanged.connect(lambda u: self.cbx_url.setCurrentText(u.toString()))

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.addWidget(top_widget)
        main_layout.addWidget(self.web_view)
        self.setCentralWidget(main_widget)

        toolbar = QToolBar("快捷工具栏")
        self.addToolBar(toolbar)
        toolbar.addAction(QAction("后退", self, triggered=self.web_view.back))
        toolbar.addAction(QAction("前进", self, triggered=self.web_view.forward))
        toolbar.addAction(QAction("刷新", self, triggered=self.web_view.reload))
        toolbar.addAction(QAction("全屏", self, triggered=self.toggle_full))

    def open_url(self):
        url = self.cbx_url.currentText().strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        self.web_view.setUrl(QUrl(url))

    def add_url(self):
        url = self.cbx_url.currentText().strip()
        if url and url not in self.url_list:
            self.url_list.append(url)
            self.cbx_url.addItem(url)
            self.save_config()

    def del_url(self):
        idx = self.cbx_url.currentIndex()
        if 0 <= idx < len(self.url_list):
            self.url_list.pop(idx)
            self.cbx_url.removeItem(idx)
            self.save_config()

    def toggle_full(self):
        self.showFullScreen() if not self.isFullScreen() else self.showNormal()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = VideoPlayerWindow()
    win.show()
    sys.exit(app.exec())