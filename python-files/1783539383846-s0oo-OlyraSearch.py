import sys, json, os
from PyQt5.QtCore import QUrl, QPropertyAnimation, QEasingCurve, pyqtProperty, Qt
from PyQt5.QtGui import QColor, QPainter, QLinearGradient
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QToolBar,
    QLineEdit, QMessageBox, QWidget, QHBoxLayout
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from cryptography.fernet import Fernet

HOME_URL = "https://olyrasearch.base44.app"
HISTORY_FILE = "history.json"
BOOKMARKS_FILE = "bookmarks.json"
PASSWORD_FILE = "passwords.enc"

# ---------------- PASSWORD MANAGER ---------------- #

def load_key():
    if not os.path.exists("key.key"):
        key = Fernet.generate_key()
        with open("key.key", "wb") as f:
            f.write(key)
    else:
        with open("key.key", "rb") as f:
            key = f.read()
    return key

fernet = Fernet(load_key())

def save_password(site, username, password):
    data = f"{site}|{username}|{password}"
    encrypted = fernet.encrypt(data.encode())
    with open(PASSWORD_FILE, "ab") as f:
        f.write(encrypted + b"\n")

def load_passwords():
    if not os.path.exists(PASSWORD_FILE):
        return []
    passwords = []
    with open(PASSWORD_FILE, "rb") as f:
        for line in f:
            try:
                decrypted = fernet.decrypt(line.strip()).decode()
                site, user, pw = decrypted.split("|")
                passwords.append((site, user, pw))
            except:
                pass
    return passwords

# ---------------- HISTORY & BOOKMARKS ---------------- #

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

# ---------------- GRADIENT BUTTON ---------------- #

class GradientButton(QWidget):
    def __init__(self, text, callback):
        super().__init__()
        self.text = text
        self.callback = callback
        self._fade = 0

        self.anim = QPropertyAnimation(self, b"fade")
        self.anim.setDuration(300)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

        self.setFixedHeight(32)
        self.setFixedWidth(90)

    def enterEvent(self, event):
        self.anim.setDirection(QPropertyAnimation.Forward)
        self.anim.start()

    def leaveEvent(self, event):
        self.anim.setDirection(QPropertyAnimation.Backward)
        self.anim.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.callback()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Gradient background
        grad = QLinearGradient(0, 0, self.width(), self.height())
        base_color = QColor(40, 30, 80)
        hover_color = QColor(120, 80, 255)

        grad.setColorAt(0, base_color)
        grad.setColorAt(1, hover_color)

        painter.setBrush(grad)
        painter.setOpacity(0.4 + self._fade * 0.6)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)

        # Text
        painter.setPen(QColor(220, 210, 255))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text)

    def getFade(self):
        return self._fade

    def setFade(self, value):
        self._fade = value
        self.update()

    fade = pyqtProperty(float, getFade, setFade)

# ---------------- BROWSER TAB ---------------- #

class BrowserTab(QWebEngineView):
    def __init__(self):
        super().__init__()
        self.load(QUrl(HOME_URL))
        self.urlChanged.connect(self.update_history)

    def update_history(self, url):
        history = load_json(HISTORY_FILE)
        history.append(url.toString())
        save_json(HISTORY_FILE, history)

# ---------------- MAIN WINDOW ---------------- #

class OlyraSearch(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Olyra Search")
        self.resize(1200, 800)

        # Apply purple/blue theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0d0b1e;
            }
            QToolBar {
                background: #1a1533;
                padding: 6px;
                border-bottom: 2px solid #5a3dfc;
            }
            QLineEdit {
                background: #120f26;
                color: #cfcaff;
                border: 2px solid #5a3dfc;
                border-radius: 8px;
                padding: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #7b5bff;
            }
            QTabWidget::pane {
                border: 2px solid #5a3dfc;
                background: #0d0b1e;
            }
            QTabBar::tab {
                background: #1a1533;
                color: #cfcaff;
                padding: 8px 14px;
                border-radius: 6px;
                margin: 4px;
                border: 1px solid #5a3dfc;
            }
            QTabBar::tab:selected {
                background: #2a2250;
                border: 1px solid #7b5bff;
                color: white;
            }
            QTabBar::tab:hover {
                background: #3a2a70;
            }
        """)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_urlbar)
        self.setCentralWidget(self.tabs)

        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # Button layout
        button_container = QWidget()
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_container.setLayout(button_layout)
        toolbar.addWidget(button_container)

        # Buttons
        button_layout.addWidget(GradientButton("Back", lambda: self.current_tab().back()))
        button_layout.addWidget(GradientButton("Reload", lambda: self.current_tab().reload()))
        button_layout.addWidget(GradientButton("New Tab", self.add_new_tab))
        button_layout.addWidget(GradientButton("Bookmark", self.add_bookmark))
        button_layout.addWidget(GradientButton("History", self.show_history))
        button_layout.addWidget(GradientButton("Clear Hist", self.delete_history))

        # URL bar
        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        toolbar.addWidget(self.urlbar)

        self.add_new_tab()

    def current_tab(self):
        return self.tabs.currentWidget()

    def add_new_tab(self):
        tab = BrowserTab()
        index = self.tabs.addTab(tab, "New tab")
        self.tabs.setCurrentIndex(index)
        tab.load(QUrl(HOME_URL))

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)

    def navigate_to_url(self):
        url = self.urlbar.text()
        if not url.startswith("http"):
            url = "https://" + url
        self.current_tab().load(QUrl(url))

    def update_urlbar(self):
        tab = self.current_tab()
        if tab.url().toString() == HOME_URL:
            self.urlbar.setText("New tab")
        else:
            self.urlbar.setText(tab.url().toString())

    def add_bookmark(self):
        bookmarks = load_json(BOOKMARKS_FILE)
        bookmarks.append(self.current_tab().url().toString())
        save_json(BOOKMARKS_FILE, bookmarks)
        QMessageBox.information(self, "Bookmark", "Added to bookmarks!")

    def show_history(self):
        history = load_json(HISTORY_FILE)
        QMessageBox.information(self, "History", "\n".join(history))

    def delete_history(self):
        save_json(HISTORY_FILE, [])
        QMessageBox.information(self, "History", "History cleared!")

# ---------------- RUN APP ---------------- #

app = QApplication(sys.argv)
window = OlyraSearch()
window.show()
sys.exit(app.exec_())
