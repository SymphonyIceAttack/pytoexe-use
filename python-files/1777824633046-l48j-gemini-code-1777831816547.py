import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QListWidget,
                             QListWidgetItem, QLabel, QHBoxLayout, QPushButton,
                             QFileIconProvider)
from PyQt5.QtCore import Qt, QSize, QFileInfo
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtWidgets import QShortcut

class ConsoleLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_desktop_items()

    def initUI(self):
        # Включаем полноэкранный режим
        self.showFullScreen()
        
        # QSS Стилизация (настраивается как обычный CSS)
        self.setStyleSheet("""
            QWidget {
                background-color: #0e0e10; /* Темный фон */
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel#header {
                font-size: 40px;
                font-weight: bold;
                margin: 20px 0px 10px 20px;
                color: #f3f3f3;
                letter-spacing: 2px;
            }
            QListWidget {
                background-color: transparent;
                border: none;
                outline: 0;
            }
            /* Стиль карточки приложения */
            QListWidget::item {
                background-color: #1f1f23;
                border-radius: 15px;
                padding: 15px;
            }
            /* Стиль при навигации с клавиатуры/геймпада */
            QListWidget::item:selected {
                background-color: #107c10; /* Акцентный цвет Xbox (зеленый) */
                border: 2px solid white;
            }
            /* Стиль при наведении мыши */
            QListWidget::item:hover {
                background-color: #2a2a30;
                border: 1px solid #444;
            }
            /* Скрываем скроллбар для эстетики */
            QScrollBar:vertical {
                width: 0px;
            }
        """)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # --- Верхняя панель (Хедер) ---
        header_layout = QHBoxLayout()
        title = QLabel("MY GAMES & APPS", objectName="header")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Кнопка выхода
        exit_btn = QPushButton("Выход (Esc)")
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: bold;
                margin-right: 20px;
            }
            QPushButton:hover { background-color: #f44336; }
        """)
        exit_btn.clicked.connect(self.close)
        header_layout.addWidget(exit_btn)

        layout.addLayout(header_layout)

        # --- Сетка приложений ---
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.IconMode) # Режим сетки
        self.list_widget.setIconSize(QSize(128, 128))      # Размер иконок
        self.list_widget.setSpacing(25)                    # Расстояние между плитками
        self.list_widget.setResizeMode(QListWidget.Adjust) # Адаптация под размер экрана
        self.list_widget.setMovement(QListWidget.Static)
        
        # Запуск приложения по двойному клику мышью или нажатию Enter
        self.list_widget.itemDoubleClicked.connect(self.launch_app)
        self.list_widget.itemActivated.connect(self.launch_app) 
        
        layout.addWidget(self.list_widget)

        # Привязка клавиши Esc к выходу из лаунчера
        QShortcut(QKeySequence("Esc"), self, self.close)

    def load_desktop_items(self):
        """Считывает ярлыки, папки и файлы с рабочего стола пользователя и общего рабочего стола."""
        desktop_paths = [
            os.path.join(os.environ['USERPROFILE'], 'Desktop'),
            os.path.join(os.environ['PUBLIC'], 'Desktop')
        ]

        provider = QFileIconProvider() # Нативный класс для получения системных иконок

        for path in desktop_paths:
            if not os.path.exists(path):
                continue
            
            for item in os.listdir(path):
                # Игнорируем системные скрытые файлы
                if item.lower() == 'desktop.ini':
                    continue
                    
                full_path = os.path.join(path, item)
                
                # Убираем расширение (.lnk, .url) для красивого отображения имени
                name = os.path.splitext(item)[0]

                # Получаем системную иконку файла/ярлыка
                file_info = QFileInfo(full_path)
                icon = provider.icon(file_info)

                # Создаем плитку
                list_item = QListWidgetItem(icon, name)
                list_item.setFont(QFont("Segoe UI", 12, QFont.Bold))
                list_item.setTextAlignment(Qt.AlignCenter)
                
                # Сохраняем полный путь внутри объекта, чтобы потом его запустить
                list_item.setData(Qt.UserRole, full_path)

                self.list_widget.addItem(list_item)

    def launch_app(self, item):
        """Запускает выбранный файл/ярлык средствами Windows."""
        path = item.data(Qt.UserRole)
        try:
            os.startfile(path)
        except Exception as e:
            print(f"Ошибка при запуске {path}: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Делаем стиль приложения независимым от системной темы Windows
    app.setStyle("Fusion") 
    
    launcher = ConsoleLauncher()
    launcher.show()
    sys.exit(app.exec_())