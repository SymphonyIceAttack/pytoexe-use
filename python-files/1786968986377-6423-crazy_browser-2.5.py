# crazy_browser-2.5.py
# 一个用 Python + PyQt6 写的浏览器
# 版本 2.5：修复 bug，增加语言设置（中文/English），在设置中显示版权和版本信息

import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QToolBar,
    QTabWidget,
    QLabel,
    QProgressBar,
    QComboBox,
    QMessageBox,
    QDialog,
    QFormLayout,
    QRadioButton,
    QDialogButtonBox,
    QGroupBox,
    QCheckBox
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtCore import QUrl, QSize
from PyQt6.QtGui import QAction, QIcon


class BrowserTab(QWebEngineView):
    """浏览器标签页类"""
    def __init__(self, parent=None):
        super().__init__(parent)
        if hasattr(parent, 'update_progress'):
            self.loadProgress.connect(parent.update_progress)


class SettingsDialog(QDialog):
    """设置对话框"""
    def __init__(self, parent=None, current_language="zh", version="2.5", translations=None):
        super().__init__(parent)
        self.current_language = current_language
        self.version = version
        self.trans = translations or {}
        self.setWindowTitle(self.trans.get("settings_title", "设置") if self.trans else ("设置" if current_language == "zh" else "Settings"))
        self.setFixedSize(380, 240)

        layout = QFormLayout()

        # 主题设置
        theme_group = QGroupBox(self.trans.get("ui_theme", "界面主题"))
        theme_layout = QVBoxLayout()
        self.light_radio = QRadioButton(self.trans.get("light_mode", "浅色模式"))
        self.dark_radio = QRadioButton(self.trans.get("dark_mode", "深色模式"))
        self.light_radio.setChecked(True)
        theme_layout.addWidget(self.light_radio)
        theme_layout.addWidget(self.dark_radio)
        theme_group.setLayout(theme_layout)
        layout.addRow(theme_group)

        # 隐私设置
        privacy_group = QGroupBox(self.trans.get("privacy", "隐私设置"))
        privacy_layout = QVBoxLayout()
        self.persist_check = QCheckBox(self.trans.get("persist_history", "保留历史记录和登录状态"))
        self.persist_check.setChecked(True)
        privacy_layout.addWidget(self.persist_check)

        # 清除数据按钮
        clear_btn = QPushButton(self.trans.get("clear_data", "清除浏览器数据"))
        clear_btn.clicked.connect(self.clear_browser_data)
        privacy_layout.addWidget(clear_btn)
        privacy_group.setLayout(privacy_layout)
        layout.addRow(privacy_group)

        # 语言设置
        lang_group = QGroupBox(self.trans.get("language", "语言"))
        lang_layout = QVBoxLayout()
        self.lang_zh = QRadioButton("中文 (简体)")
        self.lang_en = QRadioButton("English")
        if current_language == "en":
            self.lang_en.setChecked(True)
        else:
            self.lang_zh.setChecked(True)
        lang_layout.addWidget(self.lang_zh)
        lang_layout.addWidget(self.lang_en)
        lang_group.setLayout(lang_layout)
        layout.addRow(lang_group)

        # 版本 / 版权显示
        version_label = QLabel(f"Crazy Browser {self.version} © Fantastic Star")
        version_label.setStyleSheet("color: gray;")
        layout.addRow(version_label)

        # 确定/取消按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def clear_browser_data(self):
        """清除浏览器数据（使用翻译，如果可用）"""
        parent = self.parent()
        t = None
        if parent and hasattr(parent, 'translations'):
            t = parent.translations.get(parent.language, {})
        title = (t.get("confirm_clear_title") if t else self.trans.get("confirm_clear_title", "确认清除"))
        msg = (t.get("confirm_clear_msg") if t else self.trans.get("confirm_clear_msg", "确定要清除所有缓存、Cookie和历史记录吗？\n此操作不可撤销。"))
        yes = QMessageBox.StandardButton.Yes
        no = QMessageBox.StandardButton.No

        reply = QMessageBox.question(
            self, title,
            msg,
            yes | no
        )

        if reply == yes:
            profile = QWebEngineProfile.defaultProfile()
            profile.clearHttpCache()
            profile.clearAllVisitedLinks()

            # 清除Cookie
            cookie_store = profile.cookieStore()
            cookie_store.deleteAllCookies()

            info_title = (t.get("cleared_info_title") if t else self.trans.get("cleared_info_title", "操作完成"))
            info_msg = (t.get("cleared_info_msg") if t else self.trans.get("cleared_info_msg", "浏览器数据已清除"))
            QMessageBox.information(self, info_title, info_msg)

            # 刷新所有标签页
            if hasattr(self.parent(), 'refresh_all_tabs'):
                self.parent().refresh_all_tabs()


class CrazyBrowser(QMainWindow):
    """主浏览器窗口"""
    def __init__(self):
        super().__init__()

        # 版本与语言设置
        self.version = "2.5"
        self.language = "zh"  # 默认中文，可改为 "en"

        # 简单翻译字典
        self.translations = {
            "zh": {
                "app_title": f"Crazy Browser {self.version} © Fantastic Star",
                "home_label": "首页",
                "new_tab": "+ 新标签页",
                "settings": "⚙ 设置",
                "device": " 设备: ",
                "placeholder": "输入网址或搜索内容...",
                "back_tip": "后退",
                "forward_tip": "前进",
                "reload_tip": "刷新",
                "home_tip": "主页",
                "ua_items": ["桌面模式", "手机模式"],
                "privacy_restart": "隐私设置将在浏览器重启后生效",
                "confirm_clear_title": "确认清除",
                "confirm_clear_msg": "确定要清除所有缓存、Cookie和历史记录吗？\n此操作不可撤销。",
                "cleared_info_title": "操作完成",
                "cleared_info_msg": "浏览器数据已清除",
                "settings_title": "设置",
                "ui_theme": "界面主题",
                "light_mode": "浅色模式",
                "dark_mode": "深色模式",
                "privacy": "隐私设置",
                "persist_history": "保留历史记录和登录状态",
                "clear_data": "清除浏览器数据",
                "language": "语言"
            },
            "en": {
                "app_title": f"Crazy Browser {self.version} © Fantastic Star",
                "home_label": "Home",
                "new_tab": "+ New Tab",
                "settings": "⚙ Settings",
                "device": " Device: ",
                "placeholder": "Enter URL or search...",
                "back_tip": "Back",
                "forward_tip": "Forward",
                "reload_tip": "Reload",
                "home_tip": "Home",
                "ua_items": ["Desktop", "Mobile"],
                "privacy_restart": "Privacy settings will take effect after restart",
                "confirm_clear_title": "Confirm Clear",
                "confirm_clear_msg": "Clear all cache, cookies and history?\nThis action cannot be undone.",
                "cleared_info_title": "Done",
                "cleared_info_msg": "Browser data cleared",
                "settings_title": "Settings",
                "ui_theme": "UI Theme",
                "light_mode": "Light Mode",
                "dark_mode": "Dark Mode",
                "privacy": "Privacy",
                "persist_history": "Keep history and login state",
                "clear_data": "Clear browser data",
                "language": "Language"
            }
        }

        # 窗口基础设置
        self.setWindowTitle(self.translations[self.language]["app_title"])
        self.resize(1280, 860)

        # 浏览器配置
        self.profile = QWebEngineProfile.defaultProfile()
        self.home_url = "https://www.google.com"

        # 初始化UI组件
        self.init_ui_components()

        # 设置工具栏
        self.setup_toolbar()

        # 设置主布局
        self.setup_main_layout()

        # 打开第一个标签页（使用当前语言的名称）
        self.add_new_tab(self.home_url, self.translations[self.language]["home_label"])

        # 应用默认主题
        self.apply_light_theme()

    def init_ui_components(self):
        """初始化UI组件"""
        # 标签页控件
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_ui_from_current_tab)

        # URL地址栏
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText(self.translations[self.language]["placeholder"])
        self.url_bar.returnPressed.connect(self.navigate_to_url)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setVisible(False)

        # 用户代理选择
        self.ua_combo = QComboBox()
        self.ua_combo.addItems(self.translations[self.language]["ua_items"])
        self.ua_combo.currentIndexChanged.connect(self.change_user_agent)

    def setup_toolbar(self):
        """设置工具栏"""
        navbar = QToolBar("导航栏")
        navbar.setMovable(False)
        self.addToolBar(navbar)

        # 导航按钮
        self.back_btn = QAction("←", self)
        self.back_btn.setToolTip(self.translations[self.language]["back_tip"])
        self.back_btn.triggered.connect(self.go_back)
        navbar.addAction(self.back_btn)

        self.forward_btn = QAction("→", self)
        self.forward_btn.setToolTip(self.translations[self.language]["forward_tip"])
        self.forward_btn.triggered.connect(self.go_forward)
        navbar.addAction(self.forward_btn)

        self.reload_btn = QAction("↻", self)
        self.reload_btn.setToolTip(self.translations[self.language]["reload_tip"])
        self.reload_btn.triggered.connect(self.reload_page)
        navbar.addAction(self.reload_btn)

        self.home_btn = QAction("🏠", self)
        self.home_btn.setToolTip(self.translations[self.language]["home_tip"])
        self.home_btn.triggered.connect(self.go_home)
        navbar.addAction(self.home_btn)

        # URL地址栏
        navbar.addWidget(self.url_bar)

        # 用户代理选择
        self.ua_label = QLabel(self.translations[self.language]["device"])
        navbar.addWidget(self.ua_label)
        navbar.addWidget(self.ua_combo)

        # 新标签页按钮（保存为成员以便语言更新）
        self.new_tab_btn = QPushButton(self.translations[self.language]["new_tab"])
        self.new_tab_btn.clicked.connect(self.add_new_tab)
        navbar.addWidget(self.new_tab_btn)

        # 设置按钮
        self.settings_btn = QPushButton(self.translations[self.language]["settings"])
        self.settings_btn.clicked.connect(self.show_settings)
        navbar.addWidget(self.settings_btn)

    def setup_main_layout(self):
        """设置主布局"""
        central = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.tabs)
        central.setLayout(layout)
        self.setCentralWidget(central)

    def add_new_tab(self, url=None, title=None, *args, **kwargs):
        """添加新标签页（兼容按钮 clicked 传入 bool 的情况）"""
        # 处理被 QPushButton.clicked 或 QAction.triggered 触发时可能传入的多余参数
        if isinstance(url, bool):
            url = None
        if isinstance(title, bool):
            title = None

        if url is None:
            url = self.home_url

        if title is None:
            title = self.translations[self.language]["home_label"]

        # 创建标签页
        page = QWebEnginePage(self.profile, self)
        view = BrowserTab(self)
        view.setPage(page)
        view.setUrl(QUrl(url))

        # 连接信号
        view.titleChanged.connect(
            lambda t: self.tabs.setTabText(self.tabs.indexOf(view), (t or title)[:30])
        )
        view.urlChanged.connect(self.sync_url_bar)
        view.loadStarted.connect(self.page_load_started)
        view.loadFinished.connect(self.page_load_finished)

        # 添加到标签页控件
        index = self.tabs.addTab(view, title)
        self.tabs.setCurrentIndex(index)

        return view

    def page_load_started(self):
        """页面开始加载"""
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

    def page_load_finished(self, ok):
        """页面加载完成"""
        self.progress_bar.setValue(100)
        if ok:
            self.progress_bar.setVisible(False)

        # 更新导航按钮状态
        view = self.current_view()
        if view:
            self.back_btn.setEnabled(view.history().canGoBack())
            self.forward_btn.setEnabled(view.history().canGoForward())

    def close_tab(self, index):
        """关闭标签页"""
        if self.tabs.count() > 1:
            widget = self.tabs.widget(index)
            self.tabs.removeTab(index)
            widget.deleteLater()

    def current_view(self):
        """获取当前标签页"""
        return self.tabs.currentWidget()

    def go_back(self):
        """后退"""
        view = self.current_view()
        if view:
            view.back()

    def go_forward(self):
        """前进"""
        view = self.current_view()
        if view:
            view.forward()

    def reload_page(self):
        """刷新页面"""
        view = self.current_view()
        if view:
            view.reload()

    def go_home(self):
        """返回主页"""
        view = self.current_view()
        if view:
            view.setUrl(QUrl(self.home_url))

    def navigate_to_url(self):
        """导航到URL"""
        text = self.url_bar.text().strip()
        if not text:
            return

        # 处理URL格式
        if not text.startswith(("http://", "https://")):
            if "." in text:  # 可能是域名
                text = "https://" + text
            else:  # 可能是搜索词
                text = f"https://www.google.com/search?q={text}"

        # 导航
        view = self.current_view()
        if view:
            view.setUrl(QUrl(text))

    def sync_url_bar(self, qurl):
        """同步URL地址栏"""
        if self.tabs.currentWidget() == self.sender():
            self.url_bar.setText(qurl.toString())
            self.url_bar.setCursorPosition(0)

    def update_ui_from_current_tab(self, index):
        """从当前标签页更新UI"""
        if index < 0:
            return

        view = self.tabs.widget(index)
        if view:
            self.url_bar.setText(view.url().toString())

            # 更新导航按钮状态
            self.back_btn.setEnabled(view.history().canGoBack())
            self.forward_btn.setEnabled(view.history().canGoForward())

    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)

    def change_user_agent(self, index):
        """更改用户代理"""
        ua = ""
        if index == 1:  # 手机模式
            ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"

        self.profile.setHttpUserAgent(ua)

        # 重新加载当前页面
        view = self.current_view()
        if view and view.url().toString():
            view.reload()

    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self, current_language=self.language, version=self.version,
                                translations=self.translations.get(self.language, {}))

        # 加载当前主题设置
        current_theme = "light" if self.styleSheet() == "" else "dark"
        if current_theme == "dark":
            dialog.dark_radio.setChecked(True)
        else:
            dialog.light_radio.setChecked(True)

        # 加载当前语言选择
        if self.language == "en":
            dialog.lang_en.setChecked(True)
        else:
            dialog.lang_zh.setChecked(True)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 应用主题
            if dialog.dark_radio.isChecked():
                self.apply_dark_theme()
            else:
                self.apply_light_theme()

            # 应用语言设置（即时）
            new_lang = "zh" if dialog.lang_zh.isChecked() else "en"
            if new_lang != self.language:
                self.set_language(new_lang)

            # 显示持久化设置提示
            if not dialog.persist_check.isChecked():
                QMessageBox.information(
                    self, self.translations[self.language]["app_title"],
                    self.translations[self.language]["privacy_restart"]
                )

    def set_language(self, lang):
        """切换语言并更新界面文本"""
        if lang not in self.translations:
            return
        self.language = lang
        t = self.translations[self.language]

        # 标题
        self.setWindowTitle(t["app_title"])

        # 工具提示 / 按钮 / 占位符 / UA 列表
        self.back_btn.setToolTip(t["back_tip"])
        self.forward_btn.setToolTip(t["forward_tip"])
        self.reload_btn.setToolTip(t["reload_tip"])
        self.home_btn.setToolTip(t["home_tip"])
        self.ua_label.setText(t["device"])
        self.new_tab_btn.setText(t["new_tab"])
        self.settings_btn.setText(t["settings"])
        self.url_bar.setPlaceholderText(t["placeholder"])
        self.ua_combo.clear()
        self.ua_combo.addItems(t["ua_items"])

        # 更新已有标签的默认名（只有未加载标题时）
        for i in range(self.tabs.count()):
            if not self.tabs.tabText(i):
                self.tabs.setTabText(i, t["home_label"])

    def apply_dark_theme(self):
        """应用深色主题"""
        dark_theme = """
            QMainWindow, QWidget {
                background: #1e1e1e;
                color: #e0e0e0;
            }
            QToolBar {
                background: #252525;
                border: none;
                padding: 4px;
            }
            QLineEdit {
                background: #333;
                color: #eee;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 6px;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                background: #222;
            }
            QTabBar::tab {
                background: #333;
                color: #ccc;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #444;
                color: #fff;
            }
            QProgressBar {
                background: #333;
                border: none;
            }
            QProgressBar::chunk {
                background: #4CAF50;
            }
            QPushButton {
                background: #444;
                color: #eee;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #555;
            }
            QComboBox {
                background: #333;
                color: #eee;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
            }
        """
        self.setStyleSheet(dark_theme)

    def apply_light_theme(self):
        """应用浅色主题"""
        self.setStyleSheet("")

    def refresh_all_tabs(self):
        """刷新所有标签页"""
        for i in range(self.tabs.count()):
            view = self.tabs.widget(i)
            if view and view.url().toString():
                view.reload()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置应用程序图标（可选）
    # app.setWindowIcon(QIcon("browser_icon.png"))

    window = CrazyBrowser()
    window.show()

    sys.exit(app.exec())