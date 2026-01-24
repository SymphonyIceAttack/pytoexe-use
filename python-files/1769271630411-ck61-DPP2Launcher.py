import sys
import os
import subprocess
import threading
import time
import json
import tempfile
import urllib.request
import platform
from pathlib import Path
from datetime import datetime

# ========== ПРОВЕРКА И УСТАНОВКА PYSIDE6 ==========
try:
    from PySide6.QtWidgets import *
    from PySide6.QtCore import *
    from PySide6.QtGui import *

    QT_AVAILABLE = True
    QT_LIB = "PySide6"
    print("✓ PySide6 найден")
except ImportError:
    QT_AVAILABLE = False
    QT_LIB = None
    print("✗ PySide6 не найден, пробуем PyQt5...")

    try:
        print("\nПытаюсь установить PySide6 автоматически...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PySide6"])
        from PySide6.QtWidgets import *
        from PySide6.QtCore import *
        from PySide6.QtGui import *

        QT_AVAILABLE = True
        QT_LIB = "PySide6"
        print("✓ PySide6 успешно установлен!")
    except:
        print("✗ Не удалось установить PySide6 автоматически")
        input("Нажмите Enter для выхода...")
        sys.exit(1)


# ========== ПЕРЕМЕЩАЕМ КЛАСС PYTHONINSTALLER В НАЧАЛО! ==========
class PythonInstaller:
    """Класс для установки Python и библиотек"""

    @staticmethod
    def check_python_installed():
        if getattr(sys, 'frozen', False) or hasattr(sys, '_MEIPASS'):
            print("✓ Running as compiled application, Python check skipped")
            return True, "Compiled application"

        try:
            result = subprocess.run(['python', '--version'],
                                    capture_output=True,
                                    text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                                    timeout=5)

            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✓ Python found: {version}")
                return True, version

            result = subprocess.run(['python3', '--version'],
                                    capture_output=True,
                                    text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                                    timeout=5)

            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✓ Python3 found: {version}")
                return True, version

        except subprocess.TimeoutExpired:
            print("✗ Python check timeout")
        except Exception as e:
            print(f"✗ Python not found: {e}")

        return False, None

    @staticmethod
    def check_libraries():
        REQUIRED_LIBRARIES = [
            'pygame==2.5.2',
            'numpy==1.26.3',
            'pillow==12.1.0',
            'requests==2.31.0',
            'cryptography==42.0.5',
            'PySide6==6.7.0',
        ]

        if getattr(sys, 'frozen', False) or hasattr(sys, '_MEIPASS'):
            print("✓ Running as compiled application, library check skipped")
            return REQUIRED_LIBRARIES, []

        missing_libs = []
        installed_libs = []

        for lib in REQUIRED_LIBRARIES:
            lib_name = lib.split('==')[0]
            try:
                result = subprocess.run(
                    [sys.executable if hasattr(sys, 'executable') else 'python',
                     '-c', f'import {lib_name}'],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                    timeout=10
                )

                if result.returncode == 0:
                    installed_libs.append(lib)
                    print(f"✓ Library installed: {lib_name}")
                else:
                    missing_libs.append(lib)
                    print(f"✗ Library missing: {lib_name}")

            except subprocess.TimeoutExpired:
                missing_libs.append(lib)
                print(f"✗ Timeout checking library: {lib_name}")
            except Exception as e:
                missing_libs.append(lib)
                print(f"✗ Exception checking {lib_name}: {e}")

        return installed_libs, missing_libs

    @staticmethod
    def install_libraries(missing_libs, progress_callback=None):
        if not missing_libs:
            return True, "All libraries are already installed"

        try:
            total = len(missing_libs)
            installed_count = 0
            failed_libs = []

            for i, lib in enumerate(missing_libs):
                if progress_callback:
                    progress = int((i / total) * 100)
                    progress_callback(f"Installing {lib}...", progress)

                lib_name = lib.split('==')[0]
                print(f"Installing library: {lib}")

                # Пробуем разные команды установки
                pip_commands = [
                    ['pip', 'install', lib, '--timeout', '60', '--retries', '2', '--user'],
                    ['python', '-m', 'pip', 'install', lib, '--timeout', '60'],
                    ['pip', 'install', lib_name, '--timeout', '60'],  # Без версии
                    ['pip', 'install', lib, '--index-url', 'https://pypi.org/simple', '--trusted-host', 'pypi.org']
                ]

                installed = False
                for cmd in pip_commands:
                    try:
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                            timeout=180  # Увеличиваем таймаут
                        )

                        if result.returncode == 0:
                            installed_count += 1
                            print(f"✓ Successfully installed: {lib}")
                            installed = True
                            break
                        else:
                            print(f"  Command failed: {' '.join(cmd)}")

                    except subprocess.TimeoutExpired:
                        print(f"  Timeout with command: {' '.join(cmd)}")
                        continue
                    except Exception as e:
                        print(f"  Error with command: {e}")
                        continue

                if not installed:
                    failed_libs.append(lib)
                    print(f"✗ All installation attempts failed for: {lib}")

            # Результат
            if failed_libs:
                return False, f"Failed to install: {', '.join(failed_libs)}"
            else:
                return True, f"Successfully installed {installed_count} libraries"

        except Exception as e:
            error_msg = f"Error installing libraries: {str(e)}"
            print(error_msg)
            return False, error_msg

    @staticmethod
    def download_python_installer():
        python_url = "https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe"
        temp_dir = tempfile.gettempdir()
        installer_path = os.path.join(temp_dir, "python_installer.exe")

        try:
            # Проверка интернет-соединения
            import socket
            socket.setdefaulttimeout(3)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            print("✓ Internet connection detected")
        except:
            print("✗ No internet connection")
            return None

        try:
            print(f"Downloading Python installer to {installer_path}...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*'
            }
            req = urllib.request.Request(python_url, headers=headers)

            # Добавляем прогресс бар
            def show_progress(count, block_size, total_size):
                percent = int(count * block_size * 100 / total_size)
                sys.stdout.write(f"\rDownloading: {percent}%")
                sys.stdout.flush()

            urllib.request.urlretrieve(python_url, installer_path, show_progress)
            print("\n✓ Download complete")
            return installer_path

        except urllib.error.URLError as e:
            print(f"\n✗ URL Error: {e}")
            print("Trying alternative mirror...")

            # Альтернативный источник
            alt_url = "https://repo.anaconda.com/miniconda/Miniconda3-py311_23.5.2-0-Windows-x86_64.exe"
            try:
                urllib.request.urlretrieve(alt_url, installer_path, show_progress)
                print("\n✓ Download from alternative mirror complete")
                return installer_path
            except:
                return None

        except Exception as e:
            print(f"\n✗ Download error: {e}")
            return None

    @staticmethod
    def run_python_installer(installer_path):
        try:
            print(f"Running installer: {installer_path}")

            if not os.path.exists(installer_path):
                print(f"Installer file not found: {installer_path}")
                return False

            # ДЛЯ WINDOWS - проверяем права администратора
            if os.name == 'nt':
                try:
                    # Проверяем, есть ли права администратора
                    import ctypes
                    is_admin = ctypes.windll.shell32.IsUserAnAdmin()

                    if not is_admin:
                        print("⚠ No admin rights. Trying to request elevation...")

                        # Пытаемся запустить с правами администратора
                        args = [installer_path, '/quiet', 'InstallAllUsers=1', 'PrependPath=1', 'Include_test=0']

                        # Используем ShellExecute для запроса прав администратора
                        ctypes.windll.shell32.ShellExecuteW(
                            None, "runas", installer_path,
                            '/quiet InstallAllUsers=1 PrependPath=1 Include_test=0',
                            None, 1
                        )

                        print("Installer launched with admin rights request")
                        return True

                except Exception as admin_error:
                    print(f"Admin elevation failed: {admin_error}")
                    print("Trying non-admin installation...")

            # Стандартный запуск
            args = [installer_path, '/quiet', 'InstallAllUsers=1', 'PrependPath=1', 'Include_test=0']

            process = subprocess.run(args,
                                     creationflags=subprocess.CREATE_NO_WINDOW,
                                     timeout=300)

            if process.returncode == 0:
                print("Python installation completed successfully")
                return True
            else:
                print(f"Python installation error: code {process.returncode}")
                return False

        except subprocess.TimeoutExpired:
            print("Python installation timed out")
        except Exception as e:
            print(f"Error running installer: {e}")
            return False


# ========== ПОЛУЧЕНИЕ ПУТЕЙ ==========
def get_base_path():
    """Получить базовый путь"""
    if getattr(sys, 'frozen', False) or hasattr(sys, '_MEIPASS'):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return base_path


def find_file_relative(base_path, relative_path):
    """Найти файл относительно базового пути"""
    path = os.path.join(base_path, relative_path)

    if os.path.exists(path):
        return os.path.abspath(path)

    # Пробуем найти в родительских директориях
    parent_dir = os.path.dirname(base_path)
    attempts = 0
    while attempts < 3 and parent_dir:
        path = os.path.join(parent_dir, relative_path)
        if os.path.exists(path):
            return os.path.abspath(path)
        parent_dir = os.path.dirname(parent_dir)
        attempts += 1

    return os.path.abspath(os.path.join(base_path, relative_path))


BASE_PATH = get_base_path()
CLIENT_FILE = find_file_relative(BASE_PATH, r"DPP2serverUDP\Client\main.py")
CLIENT_OFFLINE_FILE = find_file_relative(BASE_PATH, r"DPP2serverUDP/Client/characters/DPP2.py")
SERVER_FILE = find_file_relative(BASE_PATH, r"DPP2serverUDP\Server\main.py")

print(f"Base path: {BASE_PATH}")
print(f"Client file: {CLIENT_FILE}")
print(f"Client offline file: {CLIENT_OFFLINE_FILE}")
print(f"Server file: {SERVER_FILE}")

# Также ищем EXE файлы если они есть
CLIENT_EXE = find_file_relative(BASE_PATH, "DPP2Client.exe")
CLIENT_OFFLINE_EXE = find_file_relative(BASE_PATH, "DPP2.exe")
SERVER_EXE = find_file_relative(BASE_PATH, "DPP2Server.exe")


# ========== КОНСТАНТЫ ДИЗАЙНА ==========
class Colors:
    """Цветовые схемы"""
    BLACK = {
        'DARK_BG': '#0a0a14',
        'DARKER_BG': '#05050a',
        'CARD_BG': '#151522',
        'TEXT_MAIN': '#ffffff',
        'ACCENT': '#00d4ff',
        'BTN_CLIENT': '#00ff88',
        'BTN_SERVER': '#00d4ff',
        'BTN_ALL': '#ff6b9d',
        'BTN_CLIENT_OFFLINE': '#8888aa',
        'BTN_SETTINGS': '#9d4edd',
        'WINDOW_BG': '#0a0a14',
        'TITLE_BAR': '#05050a',
        'TITLE_TEXT': '#ffffff',
        'ACCENT_HOVER': '#40e0ff',
        'ACCENT_LIGHT': '#202840',
        'BORDER': '#303050',
        'SUCCESS': '#00ff88',
        'ERROR': '#ff4444',
        'WARNING': '#ffaa00'
    }

    GRAY = {
        'DARK_BG': '#1a1a1a',
        'DARKER_BG': '#0d0d0d',
        'CARD_BG': '#2d2d2d',
        'TEXT_MAIN': '#e6e6e6',
        'ACCENT': '#4d4d4d',
        'BTN_CLIENT': '#2ecc71',
        'BTN_SERVER': '#3498db',
        'BTN_ALL': '#e74c3c',
        'BTN_CLIENT_OFFLINE': '#95a5a6',
        'BTN_SETTINGS': '#9b59b6',
        'WINDOW_BG': '#1a1a1a',
        'TITLE_BAR': '#0d0d0d',
        'TITLE_TEXT': '#e6e6e6',
        'ACCENT_HOVER': '#6d6d6d',
        'ACCENT_LIGHT': '#3a3a3a',
        'BORDER': '#404040',
        'SUCCESS': '#2ecc71',
        'ERROR': '#e74c3c',
        'WARNING': '#f39c12'
    }

    WHITE = {
        'DARK_BG': '#f0f0f0',
        'DARKER_BG': '#e0e0e0',
        'CARD_BG': '#ffffff',
        'TEXT_MAIN': '#333333',
        'ACCENT': '#007acc',
        'BTN_CLIENT': '#28a745',
        'BTN_SERVER': '#17a2b8',
        'BTN_ALL': '#dc3545',
        'BTN_CLIENT_OFFLINE': '#6c757d',
        'BTN_SETTINGS': '#6f42c1',
        'WINDOW_BG': '#f0f0f0',
        'TITLE_BAR': '#e0e0e0',
        'TITLE_TEXT': '#333333',
        'ACCENT_HOVER': '#0099e6',
        'ACCENT_LIGHT': '#cce5ff',
        'BORDER': '#cccccc',
        'SUCCESS': '#28a745',
        'ERROR': '#dc3545',
        'WARNING': '#ffc107'
    }

    def __init__(self):
        self.current_theme = 'BLACK'
        self.themes = {
            'BLACK': self.BLACK,
            'GRAY': self.GRAY,
            'WHITE': self.WHITE
        }

    def get_current(self):
        return self.themes[self.current_theme]

    def set_theme(self, theme_name):
        if theme_name in self.themes:
            self.current_theme = theme_name
            return True
        return False


# Список необходимых библиотек
REQUIRED_LIBRARIES = [
    'pygame==2.5.2',
    'numpy==1.26.3',
    'pillow==12.1.0',
    'requests==2.31.0',
    'cryptography==42.0.5',
    'PySide6==6.7.0',
]


# ========== КЛАССЫ GUI ==========
class ModernButton(QPushButton):
    """Современная кнопка"""

    def __init__(self, text, color, parent=None):
        super().__init__(parent)
        self.color = color
        self.hover_color = self._adjust_color(color, 50)
        self.press_color = self._adjust_color(color, -30)

        self.setFixedHeight(50)
        self.setMinimumWidth(250)

        self.content_widget = QWidget(self)
        self.content_layout = QHBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 0, 20, 0)

        self.label = QLabel(text)
        self.arrow = QLabel("→")

        self.content_layout.addWidget(self.label)
        self.content_layout.addStretch()
        self.content_layout.addWidget(self.arrow)

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {color};
                border: 2px solid {color};
                border-radius: 8px;
                padding: 0px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color}20;
                border-color: {self.hover_color};
            }}
            QPushButton:pressed {{
                background-color: {color}40;
                border-color: {self.press_color};
            }}
        """)

        self.label.setStyleSheet(f"color: {color}; font-weight: bold; background: transparent;")
        self.arrow.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 16px; background: transparent;")
        self.content_widget.setStyleSheet("background: transparent;")

        if QT_LIB == "PySide6":
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.PointingHandCursor)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.content_widget.setGeometry(0, 0, self.width(), self.height())

    def _adjust_color(self, color, delta):
        if color.startswith('#'):
            r = int(color[1:3], 16) + delta
            g = int(color[3:5], 16) + delta
            b = int(color[5:7], 16) + delta
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            return f'#{r:02x}{g:02x}{b:02x}'
        return color


class SettingsDialog(QDialog):
    """Окно настроек"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Settings")
        self.setFixedSize(500, 400)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        general_group = QGroupBox("General Settings")
        general_layout = QVBoxLayout(general_group)

        self.dev_checkbox = QCheckBox("Developer Mode")
        self.dev_checkbox.setChecked(self.parent.settings['developer_mode'])
        general_layout.addWidget(self.dev_checkbox)

        dev_label = QLabel("Shows Server and Start All buttons")
        dev_label.setStyleSheet("color: #888888; margin-left: 20px;")
        general_layout.addWidget(dev_label)

        self.auto_check_checkbox = QCheckBox("Auto-check environment on startup")
        self.auto_check_checkbox.setChecked(self.parent.settings.get('auto_check_environment', True))
        general_layout.addWidget(self.auto_check_checkbox)

        auto_check_label = QLabel("Automatically check Python and libraries on launch")
        auto_check_label.setStyleSheet("color: #888888; margin-left: 20px;")
        general_layout.addWidget(auto_check_label)

        general_layout.addStretch()

        theme_group = QGroupBox("Appearance")
        theme_layout = QVBoxLayout(theme_group)

        theme_label = QLabel("Color Theme:")
        theme_label.setStyleSheet("font-weight: bold;")
        theme_layout.addWidget(theme_label)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Black", "Gray", "White"])
        current_theme = self.parent.colors.current_theme
        self.theme_combo.setCurrentText(current_theme.title())
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()

        layout.addWidget(general_group)
        layout.addWidget(theme_group)

        button_layout = QHBoxLayout()

        save_btn = ModernButton("Apply & Save", "#00ff88")
        save_btn.clicked.connect(self.apply_settings)

        cancel_btn = ModernButton("Cancel", "#8888aa")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def apply_settings(self):
        self.parent.settings['developer_mode'] = self.dev_checkbox.isChecked()
        self.parent.settings['auto_check_environment'] = self.auto_check_checkbox.isChecked()

        theme_map = {"Black": "BLACK", "Gray": "GRAY", "White": "WHITE"}
        theme = theme_map[self.theme_combo.currentText()]
        self.parent.settings['theme'] = theme

        self.parent.save_settings()
        self.parent.apply_settings_changes()
        self.accept()


# ========== МЕНЕДЖЕР ПРОЦЕССОВ ==========
class ProcessManager:
    def __init__(self):
        self.processes = {}

    def add_process(self, name, process):
        self.processes[name] = process

    def remove_process(self, name):
        if name in self.processes:
            del self.processes[name]

    def get_active_count(self):
        return len(self.processes)


# ========== ИСПРАВЛЕННЫЙ МАСТЕР УСТАНОВКИ ==========
class InstallationWizard(QDialog):
    """Мастер установки"""

    # ОПРЕДЕЛЯЕМ СИГНАЛЫ (для PySide6)
    update_signal = Signal(int, str)  # процент, текст
    log_signal = Signal(str, str)  # сообщение, цвет

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.python_installer = PythonInstaller()
        self.is_checking = False
        self.missing_libs = []

        # Подключаем сигналы к слотам
        self.update_signal.connect(self.update_progress_slot)
        self.log_signal.connect(self.log_message_slot)

        self.system_info = self.get_system_info()
        self.setup_ui()

    def get_system_info(self):
        """Сбор информации о системе"""
        info = {
            'platform': platform.system(),
            'version': platform.version(),
            'architecture': platform.architecture()[0],
            'python_version': sys.version.split()[0],
            'is_admin': False
        }
        if os.name == 'nt':
            try:
                import ctypes
                info['is_admin'] = ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                pass
        return info

    def setup_ui(self):
        self.setWindowTitle("Environment Setup Wizard")
        self.setFixedSize(900, 700)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("🛠️ Environment Setup Wizard")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #00d4ff;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Info Section
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Shape.Box)
        info_frame.setStyleSheet("border: 1px solid #444; border-radius: 5px;")
        info_layout = QVBoxLayout(info_frame)

        sys_label = QLabel("System Information:")
        sys_label.setStyleSheet("font-weight: bold; padding: 5px;")
        info_layout.addWidget(sys_label)

        self.sys_info_text = QTextEdit()
        self.sys_info_text.setReadOnly(True)
        self.sys_info_text.setMaximumHeight(100)
        info_layout.addWidget(self.sys_info_text)
        layout.addWidget(info_frame)

        # Status Section
        self.info_frame = QFrame()
        self.info_frame.setFrameStyle(QFrame.Shape.Box)
        status_layout = QVBoxLayout(self.info_frame)

        self.status_label = QLabel("Ready to check environment...")
        self.status_label.setStyleSheet("font-weight: bold; padding: 10px; font-size: 14px;")
        status_layout.addWidget(self.status_label)
        layout.addWidget(self.info_frame)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)

        # Buttons
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setSpacing(10)

        self.check_button = QPushButton("🔍 Check Environment")
        self.check_button.setFixedHeight(40)
        self.check_button.setMinimumWidth(200)
        self.check_button.setStyleSheet("""
            QPushButton {
                background-color: #00ff88;
                color: #000000;
                border: 2px solid #00ff88;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #00dd77;
                border-color: #00dd77;
            }
            QPushButton:disabled {
                background-color: #666666;
                border-color: #666666;
                color: #999999;
            }
        """)
        self.check_button.clicked.connect(self.start_check)

        self.install_button = QPushButton("📦 Install All Missing")
        self.install_button.setFixedHeight(40)
        self.install_button.setMinimumWidth(200)
        self.install_button.setStyleSheet("""
            QPushButton {
                background-color: #00d4ff;
                color: #000000;
                border: 2px solid #00d4ff;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #00b8e0;
                border-color: #00b8e0;
            }
            QPushButton:disabled {
                background-color: #666666;
                border-color: #666666;
                color: #999999;
            }
        """)
        self.install_button.clicked.connect(self.install_missing)
        self.install_button.setEnabled(False)

        self.manual_button = QPushButton("📄 Manual Instructions")
        self.manual_button.setFixedHeight(40)
        self.manual_button.setMinimumWidth(200)
        self.manual_button.setStyleSheet("""
            QPushButton {
                background-color: #ffaa00;
                color: #000000;
                border: 2px solid #ffaa00;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ff9900;
                border-color: #ff9900;
            }
        """)
        self.manual_button.clicked.connect(self.show_manual_instructions)

        self.close_button = QPushButton("✖ Close")
        self.close_button.setFixedHeight(40)
        self.close_button.setMinimumWidth(100)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #8888aa;
                color: #ffffff;
                border: 2px solid #8888aa;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #9999bb;
                border-color: #9999bb;
            }
        """)
        self.close_button.clicked.connect(self.close)

        buttons_layout.addWidget(self.check_button)
        buttons_layout.addWidget(self.install_button)
        buttons_layout.addWidget(self.manual_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_button)

        layout.addWidget(buttons_container)
        self.update_system_info()

        # Автозапуск проверки через 500мс
        QTimer.singleShot(500, self.start_check)

    def update_system_info(self):
        info_text = f"""
        Platform: {self.system_info['platform']} {self.system_info['version']}
        Architecture: {self.system_info['architecture']}
        Python: {self.system_info['python_version']}
        Admin rights: {'Yes' if self.system_info['is_admin'] else 'No'}
        """
        self.sys_info_text.setPlainText(info_text.strip())

    # СЛОТЫ (Выполняются в главном потоке GUI)
    @Slot(str, str)
    def log_message_slot(self, message, color):
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        timestamp = datetime.now().strftime("%H:%M:%S")

        if color:
            self.log_text.insertHtml(f'<span style="color:{color}">[{timestamp}] {message}</span><br>')
        else:
            self.log_text.insertPlainText(f"[{timestamp}] {message}\n")

        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

        # Обновляем GUI сразу
        QApplication.processEvents()

    @Slot(int, str)
    def update_progress_slot(self, value, message):
        self.progress_bar.setValue(value)
        if message:
            self.status_label.setText(message)
            # Дублируем в лог без цвета для истории
            self.log_message_slot(message, None)

        # Обновляем GUI сразу
        QApplication.processEvents()

    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ДЛЯ ПОТОКОВ
    def log_thread_safe(self, message, color=None):
        safe_color = color if color else ""
        self.log_signal.emit(message, safe_color)

    def progress_thread_safe(self, value, message=None):
        safe_message = message if message else ""
        self.update_signal.emit(value, safe_message)

    def start_check(self):
        if self.is_checking:
            return

        self.is_checking = True
        self.check_button.setEnabled(False)
        self.install_button.setEnabled(False)
        self.log_text.clear()

        # Запускаем тяжелую задачу в потоке
        threading.Thread(target=self.perform_check, daemon=True).start()

    def perform_check(self):
        try:
            self.progress_thread_safe(10, "Checking system requirements...")

            # Проверка Python
            self.progress_thread_safe(20, "Checking Python installation...")
            python_installed, python_version = self.python_installer.check_python_installed()

            if not python_installed:
                self.log_thread_safe("Python not found!", "#ff4444")
                self.progress_thread_safe(30, "Python needs to be installed...")
                # Открываем диалог через QTimer в главном потоке
                QTimer.singleShot(0, self.show_python_dialog)
                return
            else:
                self.log_thread_safe(f"Python found: {python_version}", "#00ff88")
                self.progress_thread_safe(40, "Python installed ✓")

            # Проверка библиотек
            self.progress_thread_safe(50, "Checking required libraries...")
            try:
                installed_libs, missing_libs = self.python_installer.check_libraries()

                if installed_libs:
                    self.log_thread_safe(f"Found {len(installed_libs)} libraries", "#00ff88")

                if missing_libs:
                    self.log_thread_safe(f"Missing {len(missing_libs)} libraries", "#ffaa00")
                    for lib in missing_libs:
                        lib_name = lib.split('==')[0]
                        self.log_thread_safe(f"  - {lib_name}", "#ffaa00")

                    self.missing_libs = missing_libs
                    # Включаем кнопку установки в главном потоке
                    QTimer.singleShot(0, lambda: self.install_button.setEnabled(True))
                    self.progress_thread_safe(70, f"Found {len(missing_libs)} missing libraries")
                else:
                    self.log_thread_safe("All required libraries are installed!", "#00ff88")
                    self.progress_thread_safe(90, "Environment configured ✓")

            except Exception as lib_error:
                self.log_thread_safe(f"Error checking libraries: {lib_error}", "#ff4444")
                self.missing_libs = REQUIRED_LIBRARIES  # Fallback
                QTimer.singleShot(0, lambda: self.install_button.setEnabled(True))

            self.progress_thread_safe(100, "Check complete!")
            self.log_thread_safe("✓ Environment check completed", "#00ff88")

        except Exception as e:
            self.log_thread_safe(f"Critical error: {str(e)}", "#ff4444")
            self.progress_thread_safe(100, "Check failed!")
        finally:
            self.is_checking = False
            QTimer.singleShot(0, lambda: self.check_button.setEnabled(True))

    def show_python_dialog(self):
        """Диалог для установки Python"""
        reply = QMessageBox.question(
            self,
            "Python Required",
            "Python not found. Do you want to install it automatically?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            threading.Thread(target=self.install_python, daemon=True).start()
        else:
            self.log_message_slot("User cancelled Python installation", "#ffaa00")
            self.check_button.setEnabled(True)
            self.is_checking = False

    def show_manual_instructions(self):
        """Показать инструкции для ручной установки"""
        instructions = """
        <h3>Manual Installation Instructions</h3>

        <h4>1. Install Python</h4>
        <p>Download from: <a href="https://python.org">python.org</a></p>
        <p>✓ Check "Add Python to PATH" during installation</p>

        <h4>2. Install Required Libraries</h4>
        <p>Open Command Prompt as Administrator and run:</p>
        <pre>
        pip install pygame==2.5.2
        pip install numpy==1.26.3
        pip install Pillow==10.2.0
        pip install requests==2.31.0
        pip install cryptography==42.0.5
        pip install PySide6==6.7.0
        </pre>

        <h4>3. Restart the Launcher</h4>
        <p>After installation, restart the DPP2 Launcher</p>

        <h4>Need Help?</h4>
        <p>Check Python installation: <code>python --version</code></p>
        <p>Check pip installation: <code>pip --version</code></p>
        """

        dialog = QDialog(self)
        dialog.setWindowTitle("Manual Installation Instructions")
        dialog.setFixedSize(600, 500)

        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(instructions)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #8888aa;
                color: #ffffff;
                border: 2px solid #8888aa;
                border-radius: 5px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #9999bb;
                border-color: #9999bb;
            }
        """)
        close_btn.clicked.connect(dialog.close)

        layout.addWidget(text_edit)
        layout.addWidget(close_btn)

        dialog.exec()

    def install_python(self):
        try:
            self.progress_thread_safe(30, "Downloading Python installer...")
            installer_path = self.python_installer.download_python_installer()

            if installer_path:
                self.progress_thread_safe(50, "Running Python installer...")
                self.log_thread_safe("Please wait for installation to complete...", "#ffaa00")

                success = self.python_installer.run_python_installer(installer_path)

                if success:
                    self.progress_thread_safe(70, "Python successfully installed!")
                    self.log_thread_safe("Python installed successfully!", "#00ff88")
                    time.sleep(2)
                    self.progress_thread_safe(80, "Restarting check...")
                    self.perform_check()
                else:
                    self.log_thread_safe("Python installation failed!", "#ff4444")
                    self.progress_thread_safe(100)
            else:
                self.log_thread_safe("Failed to download Python installer", "#ff4444")
                self.log_thread_safe("Please install Python manually from python.org", "#ffaa00")
                self.progress_thread_safe(100)

        except Exception as e:
            self.log_thread_safe(f"Installation error: {str(e)}", "#ff4444")
            self.progress_thread_safe(100)
        finally:
            self.is_checking = False
            QTimer.singleShot(0, lambda: self.check_button.setEnabled(True))

    def install_missing(self):
        if not self.missing_libs:
            self.log_message_slot("No missing libraries to install", "#ffaa00")
            return

        self.install_button.setEnabled(False)
        self.check_button.setEnabled(False)

        self.log_message_safe(f"Starting installation of {len(self.missing_libs)} libraries...", "#00d4ff")

        threading.Thread(target=self.install_libraries_thread, daemon=True).start()

    def install_libraries_thread(self):
        try:
            self.progress_thread_safe(0, f"Installing {len(self.missing_libs)} libraries...")

            # Callback для pip, который безопасно обновляет GUI
            def progress_callback(msg, percent):
                self.progress_thread_safe(percent, msg)

            success, message = self.python_installer.install_libraries(self.missing_libs, progress_callback)

            if success:
                self.log_thread_safe(message, "#00ff88")
                self.progress_thread_safe(100, "All libraries installed!")
                self.log_thread_safe("✓ Libraries installed successfully!", "#00ff88")
                time.sleep(2)
                self.start_check()
            else:
                self.log_thread_safe(message, "#ff4444")
                self.progress_thread_safe(100)

        except Exception as e:
            self.log_thread_safe(f"Installation error: {str(e)}", "#ff4444")
            self.progress_thread_safe(100)
        finally:
            QTimer.singleShot(0, lambda: self.install_button.setEnabled(True))

    def log_message_safe(self, message, color=None):
        """Безопасный вывод сообщений через QTimer"""
        if color:
            QTimer.singleShot(0, lambda: self.log_message_slot(message, color))
        else:
            QTimer.singleShot(0, lambda: self.log_message_slot(message, None))


# ========== ОСНОВНОЙ ЛАУНЧЕР ==========
class UltraModernLauncher(QMainWindow):
    def __init__(self):
        super().__init__()

        self.colors = Colors()
        self.current_colors = self.colors.get_current()

        self.settings = {
            'developer_mode': False,
            'theme': 'BLACK',
            'auto_check_environment': True
        }
        self.load_settings()

        self.running_apps = []
        self.is_hidden = False
        self.python_installer = PythonInstaller()  # Теперь этот класс определен выше
        self.process_manager = ProcessManager()
        self.is_exe_mode = getattr(sys, 'frozen', False) or hasattr(sys, '_MEIPASS')

        self.check_files()
        self.setup_ui()

        if self.settings['auto_check_environment'] and not self.is_exe_mode:
            QTimer.singleShot(500, self.check_environment_on_startup)

    def check_files(self):
        print("\n" + "=" * 50)
        print("FILE CHECK:")
        print("=" * 50)

        files = []

        if self.is_exe_mode:
            print("EXE MODE: Searching for executables...")
            # Ищем EXE файлы
            exe_files = [
                ("CLIENT EXE", "DPP2Client.exe"),
                ("OFFLINE CLIENT EXE", "DPP2.exe"),
                ("SERVER EXE", "DPP2Server.exe"),
            ]

            for name, exe_name in exe_files:
                # Ищем EXE файлы
                exe_path = find_file_relative(BASE_PATH, exe_name)
                if os.path.exists(exe_path):
                    print(f"✓ {name}: {exe_path}")
                    files.append((name, exe_path))
                else:
                    print(f"✗ {name}: {exe_name} - NOT FOUND!")
                    # Если EXE не найден, пытаемся найти Python файлы
                    if name == "CLIENT EXE":
                        alt_path = find_file_relative(BASE_PATH, r"DPP2serverUDP\Client\main.py")
                    elif name == "OFFLINE CLIENT EXE":
                        alt_path = find_file_relative(BASE_PATH, r"DPP2serverUDP/Client/characters/DPP2.py")
                    else:  # SERVER EXE
                        alt_path = find_file_relative(BASE_PATH, r"DPP2serverUDP\Server\main.py")

                    if os.path.exists(alt_path):
                        print(f"  Found Python script instead: {alt_path}")
                        files.append((name, alt_path))
                    else:
                        files.append((name, exe_path))
        else:
            # Python режим
            print("PYTHON MODE: Searching for Python scripts...")
            self.client_path = CLIENT_FILE
            self.client_offline_path = CLIENT_OFFLINE_FILE
            self.server_path = SERVER_FILE

            files = [
                ("CLIENT", self.client_path),
                ("OFFLINE CLIENT", self.client_offline_path),
                ("SERVER", self.server_path)
            ]

        all_exist = True
        for name, path in files:
            if os.path.exists(path):
                print(f"✓ {name}: {path}")
            else:
                print(f"✗ {name}: {path} - NOT FOUND!")
                all_exist = False

        # Сохраняем пути
        if files:
            if self.is_exe_mode:
                self.client_path = files[0][1]
                self.client_offline_path = files[1][1]
                self.server_path = files[2][1]

        return all_exist

    def load_settings(self):
        try:
            settings_file = Path('launcher_settings.json')
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)

                    if 'theme' in loaded_settings:
                        self.colors.set_theme(loaded_settings['theme'])
                        self.current_colors = self.colors.get_current()
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            settings_file = Path('launcher_settings.json')
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def setup_ui(self):
        self.setWindowTitle("🎮 DPP2 LAUNCHER")
        self.setFixedSize(800, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header_widget = QWidget()
        header_widget.setObjectName("header")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 20, 0, 20)

        title = QLabel("🎮 DPP2 LAUNCHER")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            padding: 10px;
        """)

        subtitle = QLabel("Select an option below")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: #00d4ff;
            padding-bottom: 10px;
        """)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        if not self.is_exe_mode:
            env_btn = QPushButton("🛠️ Setup Environment")
            env_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            env_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #9d4edd;
                    border: 1px solid #9d4edd;
                    border-radius: 4px;
                    padding: 5px 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #9d4edd20;
                }
            """)
            env_btn.clicked.connect(self.open_environment_wizard)
            header_layout.addWidget(env_btn, 0, Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(header_widget)

        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(40, 0, 40, 40)

        left_panel = QWidget()
        left_panel.setFixedWidth(300)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)

        self.client_btn = ModernButton("Client", self.current_colors['BTN_CLIENT'])
        self.client_btn.clicked.connect(self.launch_client)

        self.client_offline_btn = ModernButton("Client Offline", self.current_colors['BTN_CLIENT_OFFLINE'])
        self.client_offline_btn.clicked.connect(self.launch_client_offline)

        self.server_btn = ModernButton("Server", self.current_colors['BTN_SERVER'])
        self.server_btn.clicked.connect(self.launch_server)

        self.all_btn = ModernButton("Start All (Server+Client)", self.current_colors['BTN_ALL'])
        self.all_btn.clicked.connect(self.launch_all)

        left_layout.addWidget(self.client_btn)
        left_layout.addWidget(self.client_offline_btn)
        left_layout.addWidget(self.server_btn)
        left_layout.addWidget(self.all_btn)
        left_layout.addStretch()

        container_layout.addWidget(left_panel)
        container_layout.addStretch()
        main_layout.addWidget(container)

        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #9d4edd;
                border: none;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
            }
            QPushButton:hover {
                color: #b97fdd;
            }
        """)
        settings_btn.clicked.connect(self.open_settings)

        bottom_right_widget = QWidget()
        bottom_right_layout = QHBoxLayout(bottom_right_widget)
        bottom_right_layout.addStretch()
        bottom_right_layout.addWidget(settings_btn)

        main_layout.addWidget(bottom_right_widget)
        self.apply_styles()
        self.update_hidden_buttons_visibility()

    def apply_styles(self):
        style = f"""
            QMainWindow {{
                background-color: {self.current_colors['WINDOW_BG']};
            }}
            QWidget#header {{
                background-color: {self.current_colors['WINDOW_BG']};
                border-bottom: 1px solid {self.current_colors['BORDER']};
            }}
            QLabel {{
                color: {self.current_colors['TEXT_MAIN']};
            }}
            QGroupBox {{
                color: {self.current_colors['TEXT_MAIN']};
                border: 1px solid {self.current_colors['BORDER']};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: {self.current_colors['TEXT_MAIN']};
            }}
            QTextEdit {{
                background-color: {self.current_colors['DARKER_BG']};
                color: {self.current_colors['TEXT_MAIN']};
                border: 1px solid {self.current_colors['BORDER']};
                border-radius: 4px;
                font-family: Consolas, Monospace;
            }}
            QProgressBar {{
                border: 1px solid {self.current_colors['BORDER']};
                border-radius: 4px;
                text-align: center;
                background: {self.current_colors['DARKER_BG']};
            }}
            QProgressBar::chunk {{
                background-color: {self.current_colors['ACCENT']};
                border-radius: 4px;
            }}
        """
        self.setStyleSheet(style)

    def check_environment_on_startup(self):
        if self.is_exe_mode:
            print("✓ Running as EXE, skipping Python check")
            return

        try:
            python_installed, _ = self.python_installer.check_python_installed()
            if not python_installed:
                self.show_environment_warning()
        except:
            pass

    def show_environment_warning(self):
        reply = QMessageBox.question(
            self,
            "Environment Setup",
            "Python and required libraries are needed to run the game.\n"
            "Do you want to run the environment setup wizard?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.open_environment_wizard()

    def open_environment_wizard(self):
        wizard = InstallationWizard(self)
        wizard.exec()

    def open_settings(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec()

    def apply_settings_changes(self):
        self.save_settings()
        self.current_colors = self.colors.get_current()
        self.apply_styles()
        self.update_button_colors()
        self.update_hidden_buttons_visibility()

    def update_button_colors(self):
        self.client_btn.color = self.current_colors['BTN_CLIENT']
        self.client_offline_btn.color = self.current_colors['BTN_CLIENT_OFFLINE']
        self.server_btn.color = self.current_colors['BTN_SERVER']
        self.all_btn.color = self.current_colors['BTN_ALL']

    def update_hidden_buttons_visibility(self):
        if self.settings['developer_mode']:
            self.server_btn.show()
            self.all_btn.show()
        else:
            self.server_btn.hide()
            self.all_btn.hide()

    def launch_process(self, path, name):
        """Запускает процесс"""
        if not os.path.exists(path):
            QMessageBox.critical(self, "Error", f"File {name} not found!\n\nPath: {path}")
            return None

        try:
            current_dir = os.path.dirname(path)

            if path.lower().endswith('.exe'):
                # Запуск EXE файла
                print(f"Launching EXE: {path}")

                if os.name == 'nt':
                    process = subprocess.Popen(
                        [path],
                        cwd=current_dir,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                else:
                    process = subprocess.Popen(
                        [path],
                        cwd=current_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
            else:
                # Запуск Python скрипта
                print(f"Launching Python script: {path}")

                process = subprocess.Popen(
                    [sys.executable, path],
                    cwd=current_dir,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.DEVNULL
                )

            print(f"✅ {name} launched (PID: {process.pid})")

            # Читаем вывод для отладки
            def read_output():
                try:
                    stdout, stderr = process.communicate(timeout=2)
                    if stdout:
                        print(f"STDOUT {name}: {stdout[:200].decode('utf-8', errors='ignore')}")
                    if stderr:
                        print(f"STDERR {name}: {stderr[:200].decode('utf-8', errors='ignore')}")
                except subprocess.TimeoutExpired:
                    # Процесс еще работает, это нормально
                    pass

            # Запускаем чтение вывода в отдельном потоке
            threading.Thread(target=read_output, daemon=True).start()

            self.process_manager.add_process(name, process)
            return process

        except Exception as e:
            print(f"❌ Error launching {name}: {e}")
            import traceback
            traceback.print_exc()

            QMessageBox.critical(self, "Error", f"Failed to launch {name}:\n{str(e)}")
            return None

    def restore_launcher(self):
        if self.is_hidden:
            self.show()
            self.is_hidden = False
            self.raise_()
            self.activateWindow()

    def launch_client(self):
        print("\n🎮 Launching Client...")
        self.hide()
        self.is_hidden = True

        if not os.path.exists(self.client_path):
            QMessageBox.critical(self, "Error", "Client file not found!")
            QTimer.singleShot(100, self.restore_launcher)
            return

        process = self.launch_process(self.client_path, "Client")
        if not process:
            QTimer.singleShot(100, self.restore_launcher)

    def launch_client_offline(self):
        print("\n🎮 Launching Client Offline...")
        self.hide()
        self.is_hidden = True

        if not os.path.exists(self.client_offline_path):
            QMessageBox.critical(self, "Error", "Client Offline file not found!")
            QTimer.singleShot(100, self.restore_launcher)
            return

        process = self.launch_process(self.client_offline_path, "Client Offline")
        if not process:
            QTimer.singleShot(100, self.restore_launcher)

    def launch_server(self):
        print("\n🖥️ Launching Server...")
        self.hide()
        self.is_hidden = True

        if not os.path.exists(self.server_path):
            QMessageBox.critical(self, "Error", "Server file not found!")
            QTimer.singleShot(100, self.restore_launcher)
            return

        process = self.launch_process(self.server_path, "Server")
        if not process:
            QTimer.singleShot(100, self.restore_launcher)

    def launch_all(self):
        print("\n🚀 Launching All (Server + Client)...")
        self.hide()
        self.is_hidden = True

        def launch():
            print("Starting Server...")
            server_process = self.launch_process(self.server_path, "Server")

            if server_process:
                print("Waiting 3 seconds for Server to start...")
                time.sleep(3)
                print("Starting Client...")
                self.launch_process(self.client_path, "Client")
            else:
                print("❌ Failed to launch Server")
                QTimer.singleShot(1000, self.restore_launcher)

        threading.Thread(target=launch, daemon=True).start()


# ========== ЗАПУСК ПРИЛОЖЕНИЯ ==========
if __name__ == "__main__":
    try:
        print("=" * 50)
        print("DPP2 LAUNCHER - Starting...")
        print("=" * 50)
        print(f"Current directory: {os.getcwd()}")
        print(f"Python version: {sys.version}")
        print(f"Operating system: {platform.system()} {platform.release()}")
        print(f"Base path: {BASE_PATH}")
        print(f"EXE mode: {getattr(sys, 'frozen', False)}")
        print(f"GUI library: {QT_LIB}")

        if not QT_AVAILABLE:
            print("\n❌ GUI libraries not available!")
            input("Press Enter to exit...")
            sys.exit(1)

        app = QApplication(sys.argv)
        app.setApplicationName("DPP2 Launcher")
        app.setOrganizationName("DPP2")

        try:
            app.setStyle("Fusion")
        except:
            pass

        font = QFont("Segoe UI", 9)
        app.setFont(font)

        launcher = UltraModernLauncher()
        launcher.show()

        sys.exit(app.exec())

    except Exception as e:
        print(f"CRITICAL ERROR: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        input("Press Enter to exit...")