import sys
import os
import json
import psutil
import time
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QListWidget,
                             QListWidgetItem, QFileDialog, QMessageBox, QCheckBox,
                             QSystemTrayIcon, QMenu, QAction, QStyle, QFrame,
                             QSpinBox, QLineEdit, QGroupBox)
from PyQt5.QtCore import Qt, QTimer, QSettings, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QDragEnterEvent, QDropEvent


# -----------------------------------------------------------
# Виджет для Drag & Drop
# -----------------------------------------------------------
class DropZone(QFrame):
    file_dropped = pyqtSignal(str)

    def __init__(self, placeholder_text="Перетащите файл сюда"):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(80)
        self.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 2px dashed #666;
                border-radius: 10px;
            }
            QFrame:hover {
                border-color: #aaa;
                background-color: #3a3a3a;
            }
        """)

        layout = QVBoxLayout()
        self.label = QLabel(placeholder_text)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: #aaa; font-size: 11px; border: none;")
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QFrame {
                    background-color: #3a5a3a;
                    border: 2px dashed #8f8;
                    border-radius: 10px;
                }
            """)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 2px dashed #666;
                border-radius: 10px;
            }
            QFrame:hover {
                border-color: #aaa;
                background-color: #3a3a3a;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 2px dashed #666;
                border-radius: 10px;
            }
            QFrame:hover {
                border-color: #aaa;
                background-color: #3a3a3a;
            }
        """)

        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith('.exe') or file_path.endswith('.lnk'):
                self.file_dropped.emit(file_path)
                self.label.setText(f"✓ {os.path.basename(file_path)}")
            else:
                self.label.setText("❌ Только .exe или .lnk")

    def set_text(self, text):
        self.label.setText(text)


# -----------------------------------------------------------
# Класс для связки программ
# -----------------------------------------------------------
class AppPair:
    def __init__(self, trigger_app="", target_app="", enabled=True):
        self.trigger_app = trigger_app  # Программа-триггер (которую запускает пользователь)
        self.target_app = target_app  # Целевая программа (запускается автоматически)
        self.enabled = enabled
        self.trigger_name = os.path.basename(trigger_app) if trigger_app else ""
        self.target_name = os.path.basename(target_app) if target_app else ""

    def to_dict(self):
        return {
            'trigger_app': self.trigger_app,
            'target_app': self.target_app,
            'enabled': self.enabled
        }

    @staticmethod
    def from_dict(data):
        return AppPair(
            data.get('trigger_app', ''),
            data.get('target_app', ''),
            data.get('enabled', True)
        )


# -----------------------------------------------------------
# Главное окно
# -----------------------------------------------------------
class AppLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔗 App Linker - Связанный запуск программ")
        self.setGeometry(100, 100, 550, 650)
        self.setFixedSize(550, 650)

        # Данные
        self.pairs = []  # Список связок программ
        self.settings = QSettings('AppLinker', 'Settings')
        self.monitoring = True
        self.monitor_thread = None

        # Настройка интерфейса
        self.setup_ui()

        # Загружаем сохраненные связки
        self.load_settings()

        # Системный трей
        self.setup_tray()

        # Запускаем мониторинг
        self.start_monitoring()

        # Применяем тему
        self.apply_theme()

    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #eee;
            }
            QGroupBox {
                border: 1px solid #555;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
                color: #ccc;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #5a5a5a;
                padding: 8px 15px;
                border-radius: 5px;
                color: white;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #505050;
                border-color: #888;
            }
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 5px;
                color: #eee;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:selected {
                background-color: #3a3a3a;
            }
            QLabel {
                color: #ccc;
                padding: 3px;
            }
            QCheckBox {
                color: #ccc;
            }
        """)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)

        # Заголовок
        title = QLabel("🔗 СВЯЗАННЫЙ ЗАПУСК ПРОГРАММ")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px; color: #fff;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Описание
        desc = QLabel("При запуске первой программы автоматически запустится вторая")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #aaa; padding: 5px;")
        layout.addWidget(desc)

        # Группа добавления связки
        add_group = QGroupBox("➕ Добавить новую связку")
        add_layout = QVBoxLayout(add_group)

        # Программа-триггер
        trigger_label = QLabel("🎯 Программа-триггер (которую вы запускаете):")
        add_layout.addWidget(trigger_label)

        trigger_layout = QHBoxLayout()
        self.trigger_drop = DropZone("Перетащите программу-триггер сюда")
        self.trigger_drop.file_dropped.connect(self.set_trigger)
        trigger_layout.addWidget(self.trigger_drop)

        trigger_browse = QPushButton("📁")
        trigger_browse.setFixedWidth(40)
        trigger_browse.clicked.connect(self.browse_trigger)
        trigger_layout.addWidget(trigger_browse)
        add_layout.addLayout(trigger_layout)

        # Стрелка
        arrow = QLabel("⬇")
        arrow.setAlignment(Qt.AlignCenter)
        arrow.setStyleSheet("font-size: 20px;")
        add_layout.addWidget(arrow)

        # Целевая программа
        target_label = QLabel("🎯 Целевая программа (запустится автоматически):")
        add_layout.addWidget(target_label)

        target_layout = QHBoxLayout()
        self.target_drop = DropZone("Перетащите целевую программу сюда")
        self.target_drop.file_dropped.connect(self.set_target)
        target_layout.addWidget(self.target_drop)

        target_browse = QPushButton("📁")
        target_browse.setFixedWidth(40)
        target_browse.clicked.connect(self.browse_target)
        target_layout.addWidget(target_browse)
        add_layout.addLayout(target_layout)

        # Кнопка добавления
        add_btn = QPushButton("➕ Добавить связку")
        add_btn.clicked.connect(self.add_pair)
        add_layout.addWidget(add_btn)

        layout.addWidget(add_group)

        # Список связок
        list_label = QLabel("📋 Активные связки:")
        list_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(list_label)

        self.pairs_list = QListWidget()
        self.pairs_list.setMinimumHeight(150)
        layout.addWidget(self.pairs_list)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        remove_btn = QPushButton("❌ Удалить")
        remove_btn.clicked.connect(self.remove_pair)
        toggle_btn = QPushButton("🔄 Вкл/Выкл")
        toggle_btn.clicked.connect(self.toggle_pair)
        clear_btn = QPushButton("🗑️ Очистить всё")
        clear_btn.clicked.connect(self.clear_all)
        btn_layout.addWidget(remove_btn)
        btn_layout.addWidget(toggle_btn)
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)

        # Настройки
        settings_group = QGroupBox("⚙️ Настройки")
        settings_layout = QVBoxLayout(settings_group)

        self.monitor_check = QCheckBox("🔄 Отслеживать запуск программ")
        self.monitor_check.setChecked(True)
        self.monitor_check.toggled.connect(self.toggle_monitoring)
        settings_layout.addWidget(self.monitor_check)

        self.autostart_check = QCheckBox("🚀 Запускать вместе с Windows")
        self.autostart_check.toggled.connect(self.toggle_autostart)
        settings_layout.addWidget(self.autostart_check)

        self.tray_check = QCheckBox("📌 Сворачивать в трей")
        self.tray_check.setChecked(True)
        settings_layout.addWidget(self.tray_check)

        layout.addWidget(settings_group)

        # Статус
        self.status_label = QLabel("✅ Мониторинг активен")
        self.status_label.setStyleSheet("color: #0f0; padding: 5px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Временные переменные для новой связки
        self.temp_trigger = ""
        self.temp_target = ""

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))

        tray_menu = QMenu()
        show_action = QAction("📂 Показать", self)
        show_action.triggered.connect(self.show_normal)
        quit_action = QAction("❌ Выход", self)
        quit_action.triggered.connect(self.close)

        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.tray_icon.activated.connect(self.tray_activated)

    def show_normal(self):
        self.show()
        self.activateWindow()

    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_normal()

    def browse_trigger(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите программу-триггер", "",
            "Исполняемые файлы (*.exe *.lnk);;Все файлы (*.*)"
        )
        if file_path:
            self.set_trigger(file_path)

    def browse_target(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите целевую программу", "",
            "Исполняемые файлы (*.exe *.lnk);;Все файлы (*.*)"
        )
        if file_path:
            self.set_target(file_path)

    def set_trigger(self, file_path):
        self.temp_trigger = self.resolve_shortcut(file_path)
        self.trigger_drop.set_text(f"✓ {os.path.basename(self.temp_trigger)}")

    def set_target(self, file_path):
        self.temp_target = self.resolve_shortcut(file_path)
        self.target_drop.set_text(f"✓ {os.path.basename(self.temp_target)}")

    def resolve_shortcut(self, file_path):
        if file_path.endswith('.lnk'):
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(file_path)
                real_path = shortcut.TargetPath
                if os.path.exists(real_path):
                    return real_path
            except:
                pass
        return file_path

    def add_pair(self):
        if not self.temp_trigger or not self.temp_target:
            QMessageBox.warning(self, "Внимание", "Выберите обе программы!")
            return

        if self.temp_trigger == self.temp_target:
            QMessageBox.warning(self, "Внимание", "Нельзя связать программу саму с собой!")
            return

        pair = AppPair(self.temp_trigger, self.temp_target)
        self.pairs.append(pair)

        # Очищаем временные
        self.temp_trigger = ""
        self.temp_target = ""
        self.trigger_drop.set_text("Перетащите программу-триггер сюда")
        self.target_drop.set_text("Перетащите целевую программу сюда")

        self.update_list()
        self.save_settings()
        self.status_label.setText(f"✓ Добавлена связка: {pair.trigger_name} → {pair.target_name}")

    def remove_pair(self):
        current = self.pairs_list.currentRow()
        if current >= 0:
            removed = self.pairs.pop(current)
            self.update_list()
            self.save_settings()
            self.status_label.setText(f"❌ Удалена связка: {removed.trigger_name}")

    def toggle_pair(self):
        current = self.pairs_list.currentRow()
        if current >= 0:
            self.pairs[current].enabled = not self.pairs[current].enabled
            self.update_list()
            self.save_settings()

    def clear_all(self):
        reply = QMessageBox.question(self, 'Подтверждение',
                                     'Удалить все связки?',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.pairs.clear()
            self.update_list()
            self.save_settings()
            self.status_label.setText("🗑️ Все связки удалены")

    def update_list(self):
        self.pairs_list.clear()
        for i, pair in enumerate(self.pairs):
            status = "✅" if pair.enabled else "❌"
            item = QListWidgetItem(f"{status} {pair.trigger_name} → {pair.target_name}")
            item.setToolTip(f"Триггер: {pair.trigger_app}\nЦель: {pair.target_app}")
            self.pairs_list.addItem(item)

    def toggle_monitoring(self, enabled):
        self.monitoring = enabled
        if enabled:
            self.start_monitoring()
            self.status_label.setText("✅ Мониторинг активен")
        else:
            self.status_label.setText("⏸️ Мониторинг остановлен")

    def start_monitoring(self):
        if self.monitor_thread and self.monitor_thread.is_alive():
            return

        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

    def monitor_loop(self):
        """Отслеживает запуск программ-триггеров"""
        known_processes = set()

        while self.monitoring:
            try:
                current_processes = set()

                for proc in psutil.process_iter(['name', 'exe']):
                    try:
                        exe = proc.info['exe']
                        if exe:
                            current_processes.add(exe.lower())
                    except:
                        pass

                # Проверяем новые процессы
                new_processes = current_processes - known_processes

                for exe in new_processes:
                    for pair in self.pairs:
                        if pair.enabled and pair.trigger_app.lower() == exe:
                            # Запускаем целевую программу
                            try:
                                os.startfile(pair.target_app)
                                print(f"🚀 Запущена целевая программа: {pair.target_name}")
                            except Exception as e:
                                print(f"❌ Ошибка запуска {pair.target_app}: {e}")

                known_processes = current_processes
                time.sleep(1)  # Проверяем каждую секунду

            except Exception as e:
                print(f"Ошибка мониторинга: {e}")
                time.sleep(5)

    def toggle_autostart(self, enabled):
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if enabled:
                if getattr(sys, 'frozen', False):
                    app_path = sys.executable
                else:
                    app_path = sys.argv[0]
                winreg.SetValueEx(key, "AppLinker", 0, winreg.REG_SZ, app_path)
            else:
                try:
                    winreg.DeleteValue(key, "AppLinker")
                except:
                    pass
            winreg.CloseKey(key)

            self.settings.setValue('autostart', enabled)
        except Exception as e:
            print(f"Ошибка автозагрузки: {e}")

    def save_settings(self):
        pairs_data = [pair.to_dict() for pair in self.pairs]
        self.settings.setValue('pairs', json.dumps(pairs_data))

    def load_settings(self):
        pairs_data = self.settings.value('pairs', '[]')
        try:
            pairs_list = json.loads(pairs_data)
            self.pairs = [AppPair.from_dict(data) for data in pairs_list]
        except:
            self.pairs = []

        autostart = self.settings.value('autostart', False, type=bool)
        self.autostart_check.setChecked(autostart)

        self.update_list()

    def closeEvent(self, event):
        if self.tray_check.isChecked():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "App Linker",
                "Программа свернута в трей. Мониторинг продолжается.",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            self.monitoring = False
            self.save_settings()
            event.accept()


# -----------------------------------------------------------
# Запуск
# -----------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Устанавливаем иконку
    try:
        app.setWindowIcon(QIcon('icon.ico'))
    except:
        pass

    launcher = AppLauncher()
    launcher.show()

    print("=" * 60)
    print("🔗 APP LINKER - СВЯЗАННЫЙ ЗАПУСК ПРОГРАММ")
    print("=" * 60)
    print("📌 Как это работает:")
    print("   1. Добавьте связку: программа-триггер → целевая программа")
    print("   2. Когда вы запускаете программу-триггер,")
    print("      целевая программа запустится автоматически!")
    print("   3. Программа работает в фоне и отслеживает запуски")
    print("=" * 60)

    sys.exit(app.exec_())