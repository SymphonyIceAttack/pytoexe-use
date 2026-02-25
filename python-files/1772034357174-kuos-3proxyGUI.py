import sys
import os
import subprocess
import json
import winreg
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QCheckBox, QMessageBox, QComboBox, QFrame)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette
import pystray
from PIL import Image, ImageDraw
import threading
import time

# Константы
CONFIG_FILE = "3proxy.cfg"
PROXY_EXE = "3proxy.exe"
SETTINGS_FILE = "3proxy_settings.json"

class ProxyGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.process = None
        self.is_running = False
        self.tray_icon = None
        self.tray_thread = None
        self.is_dark_theme = self.load_settings().get("dark_theme", False)
        self.auto_start_proxy = self.load_settings().get("auto_start_proxy", False)
        self.init_ui()
        self.setup_tray()
        self.load_config()
        self.apply_theme()
        
        # Автостарт прокси если включено
        if self.auto_start_proxy:
            QTimer.singleShot(1000, self.start_proxy)  # Задержка 1 секунда
        
    def init_ui(self):
        """Создание интерфейса"""
        self.setWindowTitle("3proxy Manager")
        self.setFixedSize(420, 280)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        
        # Заголовок
        title = QLabel("3proxy Manager")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # IP и порт
        ip_layout = QHBoxLayout()
        
        ip_label = QLabel("IP:")
        ip_label.setFixedWidth(30)
        ip_layout.addWidget(ip_label)
        
        self.ip_display = QLabel("127.0.0.1")
        self.ip_display.setFixedWidth(100)
        ip_layout.addWidget(self.ip_display)
        
        ip_layout.addSpacing(10)
        
        port_label = QLabel("Порт:")
        port_label.setFixedWidth(40)
        ip_layout.addWidget(port_label)
        
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Укажите порт")
        self.port_input.setFixedWidth(100)
        self.port_input.textChanged.connect(self.on_port_changed)
        ip_layout.addWidget(self.port_input)
        
        ip_layout.addStretch()
        layout.addLayout(ip_layout)
        
        # Статус
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Статус:"))
        self.status_label = QLabel("Остановлен")
        self.status_label.setStyleSheet("color: red;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("▶ Старт")
        self.start_button.setFixedSize(100, 35)
        self.start_button.clicked.connect(self.start_proxy)
        button_layout.addWidget(self.start_button)
        
        button_layout.addSpacing(20)
        
        self.stop_button = QPushButton("■ Стоп")
        self.stop_button.setFixedSize(100, 35)
        self.stop_button.clicked.connect(self.stop_proxy)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # Настройки
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(10)
        
        # Автозапуск программы с Windows
        self.autostart_check = QCheckBox("Автозапуск программы с Windows")
        self.autostart_check.stateChanged.connect(self.toggle_autostart)
        settings_layout.addWidget(self.autostart_check)
        
        # Автостарт прокси при запуске программы
        self.autostart_proxy_check = QCheckBox("Автостарт прокси при запуске программы")
        self.autostart_proxy_check.setChecked(self.auto_start_proxy)
        self.autostart_proxy_check.stateChanged.connect(self.toggle_auto_start_proxy)
        settings_layout.addWidget(self.autostart_proxy_check)
        
        # Тема
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Тема:"))
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная"])
        self.theme_combo.setCurrentIndex(0 if not self.is_dark_theme else 1)
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        
        settings_layout.addLayout(theme_layout)
        layout.addLayout(settings_layout)
        
        layout.addStretch()
        
    def setup_tray(self):
        """Настройка иконки в трее"""
        def create_image(color):
            image = Image.new('RGB', (64, 64), color)
            draw = ImageDraw.Draw(image)
            draw.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
            return image
        
        menu = pystray.Menu(
            pystray.MenuItem("Развернуть", self.show_window),
            pystray.MenuItem("Выход", self.quit_app)
        )
        
        self.tray_icon = pystray.Icon(
            "3proxy",
            create_image("red"),
            "3proxy Manager (Остановлен)",
            menu
        )
        
        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()
        
    def start_proxy(self):
        """Запуск прокси"""
        port = self.port_input.text().strip()
        if not port:
            self.show_error("Укажите порт")
            return
        
        try:
            port = int(port)
            if port < 1 or port > 65535:
                self.show_error("Порт должен быть от 1 до 65535")
                return
        except ValueError:
            self.show_error("Порт должен быть числом")
            return
        
        if self.process and self.process.poll() is None:
            return  # Уже запущен
        
        # Создаем конфиг
        self.create_config(port)
        
        try:
            # Запускаем 3proxy
            self.process = subprocess.Popen(
                [PROXY_EXE, CONFIG_FILE],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Проверяем запуск
            time.sleep(0.5)
            if self.process.poll() is None:
                self.is_running = True
                self.status_label.setText("Запущен")
                self.status_label.setStyleSheet("color: green;")
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.update_tray_icon("green", "3proxy Manager (Запущен)")
            else:
                self.show_error("Не удалось запустить 3proxy")
                
        except Exception as e:
            self.show_error(f"Ошибка запуска: {str(e)}")
    
    def stop_proxy(self):
        """Остановка прокси"""
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                time.sleep(1)
                if self.process.poll() is None:
                    self.process.kill()
                
                self.is_running = False
                self.status_label.setText("Остановлен")
                self.status_label.setStyleSheet("color: red;")
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.update_tray_icon("red", "3proxy Manager (Остановлен)")
            except Exception as e:
                self.show_error(f"Ошибка остановки: {str(e)}")
    
    def create_config(self, port):
        """Создание конфигурационного файла 3proxy"""
        config_content = f"""log 3proxy.log D
logformat "L%Y-%m-%d %H:%M:%S %N.%p %E %C:%c -> %R:%r %O %I %h %T"
auth none
allow * * * *
internal 127.0.0.1
proxy -p{port} -n
"""
        with open(CONFIG_FILE, 'w') as f:
            f.write(config_content)
    
    def update_tray_icon(self, color, tooltip):
        """Обновление иконки в трее"""
        def create_image(color):
            image = Image.new('RGB', (64, 64), color)
            draw = ImageDraw.Draw(image)
            draw.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
            return image
        
        self.tray_icon.icon = create_image(color)
        self.tray_icon.title = tooltip
    
    def toggle_autostart(self, state):
        """Включение/отключение автозапуска программы"""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        exe_path = os.path.abspath(sys.argv[0])
        
        try:
            if state == Qt.Checked:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "3proxyManager", 0, winreg.REG_SZ, exe_path)
                winreg.CloseKey(key)
            else:
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                    winreg.DeleteValue(key, "3proxyManager")
                    winreg.CloseKey(key)
                except FileNotFoundError:
                    pass
        except Exception as e:
            self.show_error(f"Ошибка настройки автозапуска: {str(e)}")
    
    def toggle_auto_start_proxy(self, state):
        """Включение/отключение автостарта прокси"""
        self.auto_start_proxy = (state == Qt.Checked)
        self.save_settings()
    
    def load_config(self):
        """Загрузка порта из конфига если есть"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    content = f.read()
                    import re
                    match = re.search(r'proxy -p(\d+)', content)
                    if match:
                        self.port_input.setText(match.group(1))
        except:
            pass
    
    def on_port_changed(self):
        """Сохранение порта при изменении"""
        if self.port_input.text().strip():
            # Создаем конфиг с новым портом, но не запускаем
            try:
                port = int(self.port_input.text().strip())
                if 1 <= port <= 65535:
                    self.create_config(port)
            except:
                pass
    
    def change_theme(self, index):
        """Смена темы"""
        self.is_dark_theme = (index == 1)
        self.apply_theme()
        self.save_settings()
    
    def apply_theme(self):
        """Применение темы"""
        if self.is_dark_theme:
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.WindowText, Qt.white)
            dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ToolTipBase, Qt.black)
            dark_palette.setColor(QPalette.ToolTipText, Qt.white)
            dark_palette.setColor(QPalette.Text, Qt.white)
            dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ButtonText, Qt.white)
            dark_palette.setColor(QPalette.BrightText, Qt.red)
            dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.HighlightedText, Qt.black)
            self.setPalette(dark_palette)
        else:
            self.setPalette(self.style().standardPalette())
    
    def save_settings(self):
        """Сохранение всех настроек"""
        settings = {
            "dark_theme": self.is_dark_theme,
            "auto_start_proxy": self.auto_start_proxy
        }
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f)
        except:
            pass
    
    def load_settings(self):
        """Загрузка всех настроек"""
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"dark_theme": False, "auto_start_proxy": False}
    
    def check_autostart(self):
        """Проверка наличия в автозагрузке"""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, "3proxyManager")
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except:
            return False
    
    def show_error(self, message):
        """Показ сообщения об ошибке"""
        QMessageBox.critical(self, "Ошибка", message)
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        event.ignore()
        self.hide()
    
    def show_window(self):
        """Показ окна (вызывается из трея)"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def quit_app(self):
        """Полное завершение программы"""
        # Останавливаем прокси
        self.stop_proxy()
        
        # Останавливаем трей
        self.tray_icon.stop()
        
        # Завершаем приложение
        QApplication.quit()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    window = ProxyGUI()
    window.show()
    
    # Проверка автозапуска
    window.autostart_check.setChecked(window.check_autostart())
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()