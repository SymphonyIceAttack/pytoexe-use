import sys
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QLineEdit, QPushButton, QTabWidget, QToolBar
)
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineUrlRequestInterceptor
from PyQt6.QtWebEngineWidgets import QWebEngineView

class AdBlocker(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        ad_keywords = ["/ads/", "googleads", "doubleclick", "adsystem", "analytics", "popunder"]
        if any(kw in url for kw in ad_keywords):
            info.block(True)

class SecureBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ブラウザ")
        self.setGeometry(100, 100, 1200, 800)

        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.setHttpUserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15")
        
        self.interceptor = AdBlocker()
        self.profile.setUrlRequestInterceptor(self.interceptor)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        self.create_navigation_bar()
        self.add_new_tab(QUrl("https://bing.com"), "ホーム")

    def create_navigation_bar(self):
        nav = QToolBar()
        self.addToolBar(nav)

        btn_back = QPushButton("◀")
        btn_back.clicked.connect(lambda: self.current_view().back())
        nav.addWidget(btn_back)

        btn_forward = QPushButton("▶")
        btn_forward.clicked.connect(lambda: self.current_view().forward())
        nav.addWidget(btn_forward)

        btn_reload = QPushButton("🔄")
        btn_reload.clicked.connect(lambda: self.current_view().reload())
        nav.addWidget(btn_reload)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav.addWidget(self.url_bar)

        btn_new = QPushButton("➕ 新タブ")
        btn_new.clicked.connect(lambda: self.add_new_tab(QUrl("https://bing.com"), "新しいタブ"))
        nav.addWidget(btn_new)

    def add_new_tab(self, qurl, label):
        view = QWebEngineView()
        view.setUrl(qurl)
        
        view.loadFinished.connect(lambda: view.page().runJavaScript("""
            var ads = document.querySelectorAll('.ad, .ads, .banner, #ad, #ads, [id*="google_ads"]');
            ads.forEach(function(ad) { ad.style.display = 'none'; });
        """))

        view.urlChanged.connect(lambda qurl: self.url_bar.setText(qurl.toString()))
        
        idx = self.tabs.addTab(view, label)
        self.tabs.setCurrentIndex(idx)

    def close_tab(self, i):
        if self.tabs.count() > 1:
            self.tabs.removeTab(i)

    def current_view(self):
        return self.tabs.currentWidget()

    def navigate_to_url(self):
        url = self.url_bar.text()
        if not url.startswith("http"):
            url = "https://" + url
        self.current_view().setUrl(QUrl(url))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SecureBrowser()
    win.show()
    sys.exit(app.exec())
