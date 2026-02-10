import sys
import json
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QListWidget, QFileDialog, QMessageBox,
                             QLabel, QDialog, QListWidgetItem)
from PyQt5.QtCore import Qt, QPoint, QTimer, QRect
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont

class HelperButton(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.dragging = False
        self.drag_start_pos = None
        self.offset = QPoint()
        
        # Настройки окна
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(180, 50)
        
        # Позиция по умолчанию (правый верхний угол)
        screen = QApplication.desktop().screenGeometry()
        self.move(screen.width() - 200, 20)
        
    def get_plus_button_rect(self):
        """Возвращает прямоугольник области кнопки +"""
        return QRect(145, 10, 30, 30)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Цвет основной кнопки
        if self.dragging:
            color = QColor(90, 140, 245)
        else:
            color = QColor(70, 130, 255)
            
        # Рисуем основной прямоугольник с закругленными краями
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(255, 255, 255, 150), 2))
        painter.drawRoundedRect(2, 2, 176, 46, 15, 15)
        
        # Рисуем наклоненную букву "N"
        font = QFont("Arial", 24, QFont.Bold)
        font.setItalic(True)
        painter.setFont(font)
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.drawText(12, 35, "N")
        
        # Рисуем текст "Helper"
        font_text = QFont("Arial", 11, QFont.Normal)
        painter.setFont(font_text)
        painter.drawText(45, 30, "Helper")
        
        # Рисуем кнопку "+"
        plus_rect = self.get_plus_button_rect()
        painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
        painter.setPen(QPen(QColor(70, 130, 255), 2))
        painter.drawRoundedRect(plus_rect, 8, 8)
        
        # Рисуем знак "+"
        painter.setPen(QPen(QColor(70, 130, 255), 3))
        center_x = plus_rect.center().x()
        center_y = plus_rect.center().y()
        painter.drawLine(center_x, center_y - 8, center_x, center_y + 8)
        painter.drawLine(center_x - 8, center_y, center_x + 8, center_y)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Проверяем, нажали ли на кнопку "+"
            plus_rect = self.get_plus_button_rect()
            if plus_rect.contains(event.pos()):
                print("Клик по кнопке +!")  # Отладка
                if self.parent_window:
                    self.parent_window.show_menu()
                return
            
            # Иначе начинаем перетаскивание
            self.drag_start_pos = event.globalPos()
            self.offset = event.pos()
            
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_start_pos is not None:
            # Если мышь сдвинулась больше чем на 5 пикселей - это перетаскивание
            if (event.globalPos() - self.drag_start_pos).manhattanLength() > 5:
                self.dragging = True
                self.move(self.mapToParent(event.pos() - self.offset))
                self.update()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.drag_start_pos = None
            self.update()


class AppLauncherMenu(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.apps_file = "launcher_apps.json"
        self.apps = self.load_apps()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Helper - Мои приложения")
        self.setFixedSize(450, 550)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Заголовок
        title = QLabel("📱 Мои приложения")
        title.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            padding: 10px;
            color: #2c3e50;
        """)
        layout.addWidget(title)
        
        # Инструкция
        instruction = QLabel("Дважды кликните по приложению для запуска")
        instruction.setStyleSheet("color: #7f8c8d; font-size: 11px; padding: 0 10px;")
        layout.addWidget(instruction)
        
        # Список приложений
        self.app_list = QListWidget()
        self.app_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #3498db;
                border-radius: 8px;
                padding: 5px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
        """)
        self.app_list.itemDoubleClicked.connect(self.launch_app)
        self.refresh_app_list()
        layout.addWidget(self.app_list)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        add_btn = QPushButton("➕ Добавить приложение")
        add_btn.clicked.connect(self.add_app)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 15px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        button_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("🗑️ Удалить")
        remove_btn.clicked.connect(self.remove_app)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 15px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        button_layout.addWidget(remove_btn)
        
        layout.addLayout(button_layout)
        
        # Кнопка запуска
        launch_btn = QPushButton("▶️ Запустить выбранное приложение")
        launch_btn.clicked.connect(self.launch_app)
        launch_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        layout.addWidget(launch_btn)
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.hide)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 10px;
                font-size: 12px;
                border-radius: 6px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        
    def load_apps(self):
        """Загружает список приложений из файла"""
        if os.path.exists(self.apps_file):
            try:
                with open(self.apps_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_apps(self):
        """Сохраняет список приложений в файл"""
        with open(self.apps_file, 'w', encoding='utf-8') as f:
            json.dump(self.apps, f, ensure_ascii=False, indent=2)
    
    def refresh_app_list(self):
        """Обновляет отображение списка приложений"""
        self.app_list.clear()
        if len(self.apps) == 0:
            item = QListWidgetItem("Нет добавленных приложений. Нажмите '➕ Добавить приложение'")
            item.setFlags(Qt.NoItemFlags)
            self.app_list.addItem(item)
        else:
            for app in self.apps:
                item = QListWidgetItem(f"📦 {app['name']}")
                item.setToolTip(app['path'])
                self.app_list.addItem(item)
    
    def add_app(self):
        """Добавляет новое приложение в список"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите приложение для добавления",
            "",
            "Приложения (*.exe);;Все файлы (*.*)"
        )
        
        if file_path:
            app_name = os.path.basename(file_path).replace('.exe', '')
            
            # Проверяем, не добавлено ли уже это приложение
            for app in self.apps:
                if app['path'] == file_path:
                    QMessageBox.warning(self, "Внимание", 
                                      f"Приложение '{app_name}' уже добавлено!")
                    return
            
            self.apps.append({
                'name': app_name,
                'path': file_path
            })
            self.save_apps()
            self.refresh_app_list()
            QMessageBox.information(self, "Успех", 
                                  f"✅ Приложение '{app_name}' успешно добавлено!")
    
    def remove_app(self):
        """Удаляет выбранное приложение из списка"""
        current_row = self.app_list.currentRow()
        if current_row >= 0 and len(self.apps) > 0:
            app_name = self.apps[current_row]['name']
            reply = QMessageBox.question(
                self,
                "Подтверждение удаления",
                f"Вы уверены, что хотите удалить '{app_name}' из списка?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                del self.apps[current_row]
                self.save_apps()
                self.refresh_app_list()
                QMessageBox.information(self, "Удалено", 
                                      f"🗑️ Приложение '{app_name}' удалено из списка")
        else:
            QMessageBox.warning(self, "Ошибка", 
                              "⚠️ Выберите приложение для удаления из списка")
    
    def launch_app(self):
        """Запускает выбранное приложение"""
        current_row = self.app_list.currentRow()
        if current_row >= 0 and len(self.apps) > 0:
            app = self.apps[current_row]
            try:
                # Проверяем существование файла
                if not os.path.exists(app['path']):
                    QMessageBox.critical(self, "Ошибка", 
                                       f"❌ Файл не найден:\n{app['path']}\n\nВозможно, приложение было удалено или перемещено.")
                    return
                
                # Запускаем приложение
                subprocess.Popen(app['path'], shell=True)
                QMessageBox.information(self, "Запуск", 
                                      f"✅ Приложение '{app['name']}' запущено!")
                self.hide()  # Скрываем меню после запуска
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка запуска", 
                                   f"❌ Не удалось запустить приложение:\n{str(e)}")
        else:
            QMessageBox.warning(self, "Ошибка", 
                              "⚠️ Выберите приложение для запуска из списка")


class OverlayLauncher(QWidget):
    def __init__(self):
        super().__init__()
        
        # Скрываем главное окно
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(1, 1)
        
        # Создаем кнопку Helper
        self.helper_button = HelperButton(self)
        self.helper_button.show()
        
        # Создаем меню (скрыто по умолчанию)
        self.menu = AppLauncherMenu(self)
        
    def show_menu(self):
        """Показывает меню рядом с кнопкой"""
        print("Открываем меню!")  # Отладка
        
        # Позиционируем меню слева от кнопки
        button_pos = self.helper_button.pos()
        menu_x = button_pos.x() - 260
        menu_y = button_pos.y()
        
        # Проверяем, чтобы меню не выходило за пределы экрана
        screen = QApplication.desktop().screenGeometry()
        if menu_x < 0:
            menu_x = 10
        if menu_y + 550 > screen.height():
            menu_y = screen.height() - 560
        
        self.menu.move(menu_x, menu_y)
        self.menu.show()
        self.menu.raise_()
        self.menu.activateWindow()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    launcher = OverlayLauncher()
    
    print("Helper запущен! Нажмите на кнопку '+' чтобы открыть меню")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
