# browser_final.py - окончательная рабочая версия
import sys
import os
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QPushButton, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage


class RestrictedWebPage(QWebEnginePage):
    """Ограниченная веб-страница, открывающая только один сайт"""
    
    def __init__(self, allowed_url, parent=None):
        super().__init__(parent)
        self.allowed_url = allowed_url
    
    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        """Проверяем, можно ли перейти по URL"""
        url_str = url.toString()
        if url_str.startswith(self.allowed_url):
            return True
        elif navigation_type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            # Блокируем переходы по ссылкам на другие сайты
            return False
        return True


class FullScreenBrowserSimple(QMainWindow):
    """Простой полноэкранный браузер с панелью закрытия"""
    
    def __init__(self, site_url="https://xoqonclub.pythonanywhere.com/"):
        super().__init__()
        self.site_url = site_url
        self.init_ui()
    
    def init_ui(self):
        # Убираем стандартную рамку
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Основной виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Верхняя панель
        top_panel = QWidget()
        top_panel.setFixedHeight(40)
        top_panel.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border-bottom: 1px solid #444444;
            }
        """)
        
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(10, 0, 10, 0)
        
        # Кнопка закрытия
        close_btn = QPushButton("×")
        close_btn.setStyleSheet("""
            QPushButton {
                color: white;
                font-size: 24px;
                font-weight: bold;
                background-color: transparent;
                border: none;
                padding: 0px 10px;
                min-width: 40px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #ff4444;
                border-radius: 3px;
            }
            QPushButton:pressed {
                background-color: #cc0000;
            }
        """)
        close_btn.clicked.connect(self.close)
        close_btn.setFixedSize(40, 30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Растягивающийся элемент
        top_layout.addStretch()
        top_layout.addWidget(close_btn)
        
        main_layout.addWidget(top_panel)
        
        # Веб-вью
        self.web_view = QWebEngineView()
        
        # Создаем ограниченную страницу
        self.restricted_page = RestrictedWebPage(self.site_url, self.web_view)
        self.web_view.setPage(self.restricted_page)
        
        main_layout.addWidget(self.web_view)
        
        # Загружаем сайт
        self.web_view.setUrl(QUrl(self.site_url))
        
        # Устанавливаем фокус на веб-вью сразу
        self.web_view.setFocus()
    
    def showEvent(self, event):
        """Открываем на полный экран"""
        super().showEvent(event)
        self.showFullScreen()
        # Устанавливаем фокус после показа
        QApplication.processEvents()
        self.web_view.setFocus()
    
    def keyPressEvent(self, event):
        """Обработка клавиш только для управления окном"""
        # Alt+F4 для закрытия - всегда работает
        if event.modifiers() == Qt.KeyboardModifier.AltModifier and event.key() == Qt.Key.Key_F4:
            self.close()
            event.accept()
        # Ctrl+W для закрытия
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_W:
            self.close()
            event.accept()
        # Escape для выхода из полноэкранного режима
        elif event.key() == Qt.Key.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
            event.accept()
        # Ctrl+Q для закрытия
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Q:
            self.close()
            event.accept()
        else:
            # Все остальные клавиши передаем дальше сайту
            super().keyPressEvent(event)


def main():
    # Настройки для PyInstaller
    if getattr(sys, 'frozen', False):
        # Если запущено из EXE файла
        os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--no-sandbox --disable-gpu'
    
    app = QApplication(sys.argv)
    
    # Настройка стиля приложения
    app.setStyle('Fusion')
    
    # Создаем браузер
    browser = FullScreenBrowserSimple("https://xoqonclub.pythonanywhere.com/")
    
    # Показываем браузер
    browser.show()
    
    # Запускаем приложение
    sys.exit(app.exec())


if __name__ == '__main__':
    main()