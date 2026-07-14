import sys
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView

class DedicatedBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        # Set window title and default startup size
        self.setWindowTitle("Docker Server UI")
        self.resize(1280, 800)
        
        # Initialize the embedded Chromium engine
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("http://127.0.0.1:7000/"))
        
        # Strip context menus (right-click) to keep it feeling like a native app
        self.browser.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        
        self.setCentralWidget(self.browser)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DedicatedBrowser()
    window.show()
    sys.exit(app.exec())