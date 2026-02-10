import sys
import json
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QListWidget, QFileDialog, QMessageBox,
                             QLabel, QDialog, QListWidgetItem)
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QRegion, QIcon

class CircleButton(QWidget):
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
        
        # Область кнопки "+"
        self.plus_button_rect = (145, 10, 30, 30)  # x, y, width, height
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Цвет кнопки
        if self.dragging:
            color = QColor(90, 140, 245)
        else:
            color = QColor(70, 130, 255)
            
        # Рисуем прямоугольник с закругленными краями
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(255, 255, 255, 150), 2))
        painter.drawRoundedRect(2, 2, 176, 46, 15, 15)
        
        # Рисуем наклоненную букву "N"
        from PyQt5.QtGui import QFont, QFontMetrics
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
        plus_x, plus_y, plus_w, plus_h = self.plus_button_rect
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.setPen(QPen(QColor(70, 130, 255), 2))
        painter.drawRoundedRect(plus_x, plus_y, plus_w, plus_h, 8, 8)
        
        # Рисуем знак "+"
        painter.setPen(QPen(QColor(70, 130, 255), 3))
        center_x = plus_x + plus_w // 2
        center_y = plus_y + plus_h // 2
        painter.drawLine(center_x, center_y - 8, center_x, center_y + 8)
        painter.drawLine(center_x - 8, center_y, center_x + 8, center_y)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Проверяем, нажали ли на кнопку "+"
            plus_x, plus_y, plus_w, plus_h = self.plus_button_rect
            if (plus_x <= event.x() <= plus_x + plus_w and 
                plus_y <= event.y() <= plus_y + plus_h):
                # Клик по кнопке "+" - открываем меню
                if self.parent_window:
                    self.parent_window.show_menu()
                return
            
            # Иначе начинаем перетаскивание
            self.drag_start_pos = event.globalPos()
            self.offset = event.pos()
            self.update()
            
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_start_pos is not None:
            # Если мышь сдвинулась больше чем на 5 пикселей - это перетаскивание
            if (event.globalPos() - self.drag_start_pos).manhattanLength() > 5:
                self.dragging = True
                self.move(self.mapToParent(event.pos() - self.offset))
            
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
        self.setWindowTitle("Launcher Menu")
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        layout = QVBoxLayout()
        
        # Заголовок
        title = QLabel("Мои приложения")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Список приложений
        self.app_list = QListWidget()
        self.app_list.itemDoubleClicked.connect(self.launch_app)
        self.refresh_app_list()
        layout.addWidget(self.app_list)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Добавить")
        add_btn.clicked.connect(self.add_app)
        add_btn.setStyleSheet("padding: 8px; font-size: 12px;")
        button_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("🗑️ Удалить")
        remove_btn.clicked.connect(self.remove_app)
        remove_btn.setStyleSheet("padding: 8px; font-size: 12px;")
        button_layout.addWidget(remove_btn)
        
        launch_btn = QPushButton("▶️ Запустить")
        launch_btn.clicked.connect(self.launch_app)
        launch_btn.setStyleSheet("padding: 8px; font-size: 12px; background-color: #4CAF50; color: white;")
        button_layout.addWidget(launch_btn)
        
        layout.addLayout(button_layout)
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.hide)
        close_btn.setStyleSheet("padding: 8px; margin-top: 10px;")
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        
    def load_apps(self):
        if os.path.exists(self.apps_file):
            try:
                with open(self.apps_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_apps(self):
        with open(self.apps_file, 'w', encoding='utf-8') as f:
            json.dump(self.apps, f, ensure_ascii=False, indent=2)
    
    def refresh_app_list(self):
        self.app_list.clear()
        for app in self.apps:
            item = QListWidgetItem(f"{app['name']} ({app['path']})")
            self.app_list.addItem(item)
    
    def add_app(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите приложение",
            "",
            "Executable Files (*.exe);;All Files (*.*)"
        )
        
        if file_path:
            app_name = os.path.basename(file_path).replace('.exe', '')
            self.apps.append({
                'name': app_name,
                'path': file_path
            })
            self.save_apps()
            self.refresh_app_list()
            QMessageBox.information(self, "Успех", f"Приложение '{app_name}' добавлено!")
    
    def remove_app(self):
        current_row = self.app_list.currentRow()
        if current_row >= 0:
            app_name = self.apps[current_row]['name']
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Удалить '{app_name}' из списка?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                del self.apps[current_row]
                self.save_apps()
                self.refresh_app_list()
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите приложение для удаления")
    
    def launch_app(self):
        current_row = self.app_list.currentRow()
        if current_row >= 0:
            app = self.apps[current_row]
            try:
                subprocess.Popen(app['path'], shell=True)
                QMessageBox.information(self, "Запуск", f"Приложение '{app['name']}' запущено!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось запустить приложение:\n{str(e)}")
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите приложение для запуска")


class OverlayLauncher(QWidget):
    def __init__(self):
        super().__init__()
        
        # Создаем круглую кнопку
        self.circle_button = CircleButton(self)
        self.circle_button.show()
        
        # Создаем меню (скрыто по умолчанию)
        self.menu = AppLauncherMenu(self)
        
        # Таймер для проверки активности
        self.activity_timer = QTimer()
        self.activity_timer.timeout.connect(self.check_activity)
        self.activity_timer.start(1000)
        
    def show_menu(self):
        # Показываем меню рядом с кнопкой
        button_pos = self.circle_button.pos()
        menu_x = button_pos.x() - 260  # Слева от кнопки
        menu_y = button_pos.y()
        
        self.menu.move(menu_x, menu_y)
        self.menu.show()
        self.menu.raise_()
        self.menu.activateWindow()
    
    def check_activity(self):
        # Убеждаемся, что кнопка всегда поверх всех окон
        self.circle_button.raise_()
        self.circle_button.activateWindow()


def main():
    app = QApplication(sys.argv)
    
    # Устанавливаем стиль
    app.setStyle('Fusion')
    
    launcher = OverlayLauncher()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
