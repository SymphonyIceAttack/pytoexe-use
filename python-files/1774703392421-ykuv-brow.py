import sys
import PyQt5
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow, QToolBar, QLineEdit, QAction
from PyQt5.QtWebEngineWidgets import QWebEngineView

class SimpleBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("браузер")
        self.setGeometry(100, 100, 1200, 800)

        # Создаём веб‑виджет для отображения страниц
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://www.google.com"))
        self.setCentralWidget(self.browser)

        # Панели инструментов
        navbar = QToolBar()
        self.addToolBar(navbar)

        # Кнопка «Назад»
        back_btn = QAction("Назад", self)
        back_btn.triggered.connect(self.browser.back)
        navbar.addAction(back_btn)

        # Кнопка «Вперёд»
        forward_btn = QAction("Вперёд", self)
        forward_btn.triggered.connect(self.browser.forward)
        navbar.addAction(forward_btn)

        # Кнопка обновления
        reload_btn = QAction("Обновить", self)
        reload_btn.triggered.connect(self.browser.reload)
        navbar.addAction(reload_btn)

        # Кнопка домашней страницы
        home_btn = QAction("Домой", self)
        home_btn.triggered.connect(self.navigate_home)
        navbar.addAction(home_btn)

        # Строка адреса
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)

        # Отслеживание изменения URL
        self.browser.urlChanged.connect(self.update_url)

    def navigate_home(self):
        """Переход на домашнюю страницу (Google)"""
        self.browser.setUrl(QUrl("https://www.google.com"))

    def navigate_to_url(self):
        """Переход по URL из адресной строки"""
        url = self.url_bar.text()
        if not url.startswith("http"):
            url = "https://" + url
        self.browser.setUrl(QUrl(url))

    def update_url(self, q):
        """Обновление адресной строки при смене страницы"""
        self.url_bar.setText(q.toString())

# Запуск приложения
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Simple Python Browser")
    window = SimpleBrowser()
    window.show()
    sys.exit(app.exec_())
