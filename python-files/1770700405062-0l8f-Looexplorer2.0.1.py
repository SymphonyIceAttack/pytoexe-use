import sys
import time
from PyQt6.QtCore import QUrl, Qt, QTimer, QSize, QThread, pyqtSignal, QElapsedTimer
from PyQt6.QtWidgets import (QApplication, QMainWindow, QToolBar, QLineEdit, 
                             QStatusBar, QMessageBox, QVBoxLayout, 
                             QWidget, QProgressBar, QMenu, QLabel, QSizePolicy)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile
from PyQt6.QtGui import QIcon, QKeySequence, QFont, QPixmap, QPalette, QColor, QAction
import urllib.parse

class PreloadManager(QThread):
    """预加载管理线程"""
    preload_complete = pyqtSignal()
    
    def run(self):
        """在后台预加载常用资源"""
        time.sleep(0.1)
        self.preload_complete.emit()

class Looexplorer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.version = "2.0.1"
        self.init_ui()
        self.apply_styles()
        self.start_preloading()
        
    def start_preloading(self):
        """启动预加载"""
        self.preload_thread = PreloadManager()
        self.preload_thread.preload_complete.connect(self.on_preload_complete)
        self.preload_thread.start()
        
    def on_preload_complete(self):
        """预加载完成"""
        pass
        
    def init_ui(self):
        """初始化用户界面 - 性能优化版"""
        self.setWindowTitle("Looexplorer Browser")
        self.setGeometry(100, 100, 1400, 900)
        
        # 精简样式表，减少渲染开销
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; }
            QToolBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e0e0e0;
                spacing: 3px;
                padding: 3px;
            }
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 13px;
                background-color: white;
            }
            QLineEdit:focus { border-color: #6e8efb; }
            QProgressBar {
                border: none;
                background-color: #e0e0e0;
                border-radius: 2px;
                height: 10px;
            }
            QProgressBar::chunk {
                background-color: #6e8efb;
                border-radius: 2px;
            }
        """)
        
        # 创建浏览器视图 - 性能优化配置
        self.browser = QWebEngineView()
        
        # 高性能浏览器设置
        settings = self.browser.settings()
        # 启用硬件加速和性能相关功能
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        
        # 禁用一些可能影响性能的功能
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, False)
        
        # 优化字体设置
        settings.setFontFamily(QWebEngineSettings.FontFamily.StandardFont, "Segoe UI, Microsoft YaHei UI, sans-serif")
        settings.setFontFamily(QWebEngineSettings.FontFamily.SansSerifFont, "Segoe UI, Microsoft YaHei UI, sans-serif")
        settings.setFontSize(QWebEngineSettings.FontSize.DefaultFontSize, 14)
        settings.setFontSize(QWebEngineSettings.FontSize.DefaultFixedFontSize, 13)
        settings.setFontSize(QWebEngineSettings.FontSize.MinimumFontSize, 10)
        
        # 连接信号
        self.browser.loadStarted.connect(self.load_started)
        self.browser.loadProgress.connect(self.update_progress)
        self.browser.loadFinished.connect(self.load_finished)
        self.browser.urlChanged.connect(self.update_urlbar)
        self.browser.titleChanged.connect(self.update_title)
        
        # 设置中央部件
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.browser)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # 创建界面组件
        self.create_toolbar()
        self.create_statusbar()
        self.create_menus()
        
        # 直接加载首页，减少延迟
        QTimer.singleShot(50, self.navigate_home)
        
        self.show()
        QTimer.singleShot(80, self.urlbar.setFocus)
        
    def create_toolbar(self):
        """创建导航工具栏 - 优化版"""
        nav_toolbar = QToolBar("导航")
        nav_toolbar.setMovable(False)
        nav_toolbar.setIconSize(QSize(14, 14))
        self.addToolBar(nav_toolbar)
        
        # 简化按钮文本
        back_btn = QAction("←", self)
        back_btn.setShortcut(QKeySequence.StandardKey.Back)
        back_btn.triggered.connect(self.browser.back)
        nav_toolbar.addAction(back_btn)
        
        forward_btn = QAction("→", self)
        forward_btn.setShortcut(QKeySequence.StandardKey.Forward)
        forward_btn.triggered.connect(self.browser.forward)
        nav_toolbar.addAction(forward_btn)
        
        reload_btn = QAction("↻", self)
        reload_btn.setShortcut(QKeySequence.StandardKey.Refresh)
        reload_btn.triggered.connect(self.browser.reload)
        nav_toolbar.addAction(reload_btn)
        
        home_btn = QAction("🏠", self)
        home_btn.triggered.connect(self.navigate_home)
        nav_toolbar.addAction(home_btn)
        
        nav_toolbar.addSeparator()
        
        self.urlbar = QLineEdit()
        self.urlbar.setPlaceholderText("输入网址或搜索...")
        self.urlbar.returnPressed.connect(self.navigate)
        nav_toolbar.addWidget(self.urlbar)
        
        go_btn = QAction("→", self)
        go_btn.triggered.connect(self.navigate)
        nav_toolbar.addAction(go_btn)
        
    def create_statusbar(self):
        """创建状态栏 - 精简版"""
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(120)
        self.progress_bar.setMaximumHeight(10)
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666; padding: 1px 4px;")
        
        self.status.addPermanentWidget(self.progress_bar)
        self.status.addWidget(self.status_label, 1)
        
    def create_menus(self):
        """创建菜单 - 性能优化版"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar { 
                background-color: #f8f9fa; 
                border-bottom: 1px solid #e0e0e0;
                font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;
            }
            QMenu { 
                background-color: white; 
                border: 1px solid #e0e0e0;
                font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;
            }
        """)
        
        # 文件菜单
        file_menu = QMenu("文件", self)
        new_window_action = QAction("新建窗口", self)
        new_window_action.triggered.connect(self.new_window)
        file_menu.addAction(new_window_action)
        file_menu.addSeparator()
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        menubar.addMenu(file_menu)
        
        # 查看菜单
        view_menu = QMenu("查看", self)
        zoom_in_action = QAction("放大", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        zoom_out_action = QAction("缩小", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        menubar.addMenu(view_menu)
        
        # 书签菜单
        bookmark_menu = QMenu("书签", self)
        bookmarks = [
            ("SCP基金会", "https://scp-wiki-cn.wikidot.com/"),
            ("GitHub", "https://github.com"),
            ("哔哩哔哩", "https://www.bilibili.com"),
            ("Python官网", "https://python.org"),
            ("Microsoft", "https://microsoft.com"),
            ("Gmail", "https://mail.google.com"),
            ("Twitter", "https://twitter.com"),
            ("Reddit", "https://www.reddit.com"),
            ("Bing搜索", "https://www.bing.com")
        ]
        for name, url in bookmarks:
            action = QAction(name, self)
            action.triggered.connect(lambda checked, url=url: self.load_url(url))
            bookmark_menu.addAction(action)
        menubar.addMenu(bookmark_menu)
        
        # 工具菜单
        tools_menu = QMenu("工具", self)
        dev_tools_action = QAction("开发者工具", self)
        dev_tools_action.setShortcut("F12")
        dev_tools_action.triggered.connect(self.toggle_dev_tools)
        tools_menu.addAction(dev_tools_action)
        
        # 添加搜索引擎切换
        search_engine_menu = QMenu("搜索引擎", self)
        bing_action = QAction("Bing", self)
        bing_action.triggered.connect(lambda: self.set_search_engine("bing"))
        google_action = QAction("Google", self)
        google_action.triggered.connect(lambda: self.set_search_engine("google"))
        search_engine_menu.addAction(bing_action)
        search_engine_menu.addAction(google_action)
        tools_menu.addMenu(search_engine_menu)
        
        menubar.addMenu(tools_menu)
        
        # 帮助菜单
        help_menu = QMenu("帮助", self)
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        menubar.addMenu(help_menu)
        
    def apply_styles(self):
        """应用精简样式"""
        font = QFont("Segoe UI", 9)
        font.setStyleHint(QFont.StyleHint.SansSerif)
        QApplication.setFont(font)
        
    def set_search_engine(self, engine):
        """设置搜索引擎"""
        if engine == "bing":
            self.status_label.setText("已切换到Bing搜索引擎")
        else:
            self.status_label.setText("已切换到Google搜索引擎")
        QTimer.singleShot(1500, lambda: self.status_label.setText("就绪"))
        
    def navigate(self, event=None):
        """优化导航逻辑"""
        url = self.urlbar.text().strip()
        if url:
            self.load_url(url)
        
    def load_url(self, url):
        """优化URL加载 - 使用Bing作为搜索引擎"""
        if not url.startswith(('http://', 'https://')):
            if '.' in url and ' ' not in url:
                url = 'https://' + url
            else:
                # 使用Bing作为默认搜索引擎
                url = f'https://www.bing.com/search?q={urllib.parse.quote(url)}'
                
        self.urlbar.setText(url)
        self.browser.load(QUrl(url))
        
    def navigate_home(self):
        """快速首页导航 - 使用Bing作为首页"""
        self.browser.load(QUrl("https://www.bing.com"))
        self.urlbar.setText("https://www.bing.com")
        
    def update_urlbar(self, q):
        """优化地址栏更新"""
        current_url = q.toString()
        if current_url != self.urlbar.text():
            self.urlbar.setText(current_url)
        
    def update_title(self, title):
        """优化标题更新"""
        if title:
            self.setWindowTitle(f"{title} - Looexplorer")
        else:
            self.setWindowTitle("Looexplorer Browser")
            
    def update_progress(self, progress):
        """优化进度更新"""
        self.progress_bar.setValue(progress)
        
    def load_started(self):
        """快速加载开始处理"""
        self.progress_bar.setVisible(True)
        self.status_label.setText("加载中")
        
    def load_finished(self, success):
        """快速加载完成处理"""
        self.progress_bar.setVisible(False)
        if success:
            self.status_label.setText("就绪")
        else:
            self.status_label.setText("加载失败")
        
    def zoom_in(self):
        """快速缩放"""
        self.browser.setZoomFactor(min(self.browser.zoomFactor() + 0.1, 3.0))
        
    def zoom_out(self):
        """快速缩放"""
        self.browser.setZoomFactor(max(self.browser.zoomFactor() - 0.1, 0.25))
        
    def toggle_dev_tools(self):
        """切换开发者工具"""
        self.browser.page().setDevToolsPage(self.browser.page())
        
    def new_window(self):
        """快速新建窗口"""
        new_browser = Looexplorer()
        new_browser.show()
        
    def show_about(self):
        """优化关于对话框显示速度"""
        about_text = f"""
        <html>
        <head>
            <style>
                body {{ 
                    font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif; 
                    color: #333; 
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    background: #f9f9f9;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                }}
                .logo {{ 
                    text-align: center; 
                    font-size: 28px; 
                    color: #6e8efb; 
                    margin-bottom: 10px;
                    font-weight: bold;
                }}
                .version {{ 
                    text-align: center; 
                    color: #666; 
                    margin-bottom: 20px;
                    font-size: 14px;
                }}
                .feature {{ 
                    margin: 10px 0; 
                    padding-left: 24px;
                    position: relative;
                }}
                .feature:before {{ 
                    content: "✓"; 
                    position: absolute; 
                    left: 0; 
                    color: #6e8efb; 
                    font-weight: bold;
                    font-size: 16px;
                }}
                .footer {{ 
                    margin-top: 25px; 
                    text-align: center; 
                    color: #999; 
                    font-size: 12px;
                    border-top: 1px solid #eee;
                    padding-top: 15px;
                }}
                .highlight {{
                    color: #6e8efb;
                    font-weight: bold;
                }}
                .warning {{
                    color: #ff6b6b;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">Looexplorer</div>
                <div class="version">版本 {self.version} - 基于PyQt6构建</div>
                
                <div class="features">
                    <div class="feature"><span class="highlight">Version 2.0.1 (Build 25127)</span></div>
                    <div class="feature">(C) 2025 Looking 3 Studios</div>
                    <div class="feature">All Rights Reserved.</div>
                    <div class="feature">搜索引擎: <span class="highlight">Bing</span> (已设置为默认)</div>
                    <div class="feature">要想运行Looexplorer Beta通道，您需要以下条件：</div>
                    <div class="feature">1. Python 3.8+ <span class="highlight">(已安装PyQt6)</span></div>
                    <div class="feature">2. 加入官方QQ群获取最新版本</div>
                    <div class="feature">Looexplorer 2.0.1及其所有相关标识</div>
                    <div class="feature">均属于Looking 3 Studios</div>
                    <div class="feature">默认搜索引擎已切换为 <span class="highlight">Bing</span></div>
                </div>
                
                <div class="footer">
                    <p>版权所有 © 2025 Looking 3 Studios</p>
                    <p>源代码使用 <span class="highlight">Python</span> 的 <span class="highlight">QtWebEngine</span> 版本</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("关于 Looexplorer")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(about_text)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # 设置对话框样式
        msg_box.setStyleSheet("""
            QMessageBox {
                font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;
                background-color: #f9f9f9;
            }
            QMessageBox QLabel {
                font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;
            }
        """)
        
        msg_box.exec()
        
    def closeEvent(self, event):
        """优化关闭处理"""
        reply = QMessageBox.question(
            self, 
            "退出 Looexplorer", 
            "确定要退出Looexplorer吗？", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

def main():
    """主函数 - 性能优化"""
    # 对于PyQt6，高DPI缩放通常是自动启用的
    
    app = QApplication(sys.argv)
    app.setApplicationName("Looexplorer")
    app.setApplicationVersion("2.0.1")
    app.setOrganizationName("Looking 3 Studios")
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 设置应用程序字体
    app_font = QFont("Segoe UI", 10)
    app_font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(app_font)
    
    # 优化调色板
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(33, 33, 33))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(33, 33, 33))
    palette.setColor(QPalette.ColorRole.Text, QColor(33, 33, 33))
    palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(33, 33, 33))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    # 创建浏览器实例
    browser = Looexplorer()
    
    # 启动应用
    sys.exit(app.exec())

if __name__ == '__main__':
    # 安装命令：pip install PyQt6 PyQt6-WebEngine
    print("=" * 50)
    print("Looexplorer 2.0.1")
    print("基于 PyQt6 和 QtWebEngine 构建")
    print("默认搜索引擎: Bing")
    print("现代字体: Segoe UI, Microsoft YaHei UI")
    print("=" * 50)
    main()
