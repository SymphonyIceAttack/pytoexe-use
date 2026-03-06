import sys
import subprocess
import os
import json
import requests
import webbrowser
from tkinter import filedialog
from pathlib import Path


# Функция для установки пакетов
def install_package(package):
    """Установка pip пакета"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Пакет {package} успешно установлен")
        return True
    except Exception as e:
        print(f"❌ Ошибка установки {package}: {e}")
        return False


# Проверяем и устанавливаем необходимые библиотеки
required_packages = [
    'pillow',
    'pyautogui',
    'pynput',
    'requests'
]

print("🔍 Проверка установленных библиотек...")
for package in required_packages:
    try:
        __import__(package)
        print(f"✅ {package} уже установлен")
    except ImportError:
        print(f"📦 Устанавливаю {package}...")
        if not install_package(package):
            print(f"⚠️ Не удалось установить {package}")
            print("Попробуй установить вручную: pip install " + package)
            input("Нажми Enter для продолжения...")

# Теперь импортируем все библиотеки
try:
    from PIL import ImageGrab, Image
    import pyautogui
    import threading
    import time
    import datetime
    from pathlib import Path
    import tkinter as tk
    from tkinter import messagebox, ttk
    from pynput import keyboard as pynput_keyboard

except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("\nПожалуйста, выполни в терминале PyCharm команду:")
    print("pip install pillow pyautogui pynput requests")
    print("\nИли установи через настройки: File → Settings → Project → Python Interpreter → +")
    input("\nНажми Enter для выхода...")
    sys.exit(1)


class YandexDiskUploader:
    """Класс для работы с Яндекс.Диском через REST API"""

    def __init__(self):
        self.token = None
        self.authenticated = False
        self.token_file = Path(__file__).parent / 'yandex_token.json'
        self.client_id = "9bc6c562c83d4b3d8e7265cc8eb0fca2"  # Твой ClientID
        self.client_secret = ""

        # Загружаем сохраненный токен
        self.load_token()

    def load_token(self):
        """Загружает сохраненный токен"""
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'token' in data:
                        self.token = data['token']
                        # Проверяем токен
                        if self.check_token():
                            self.authenticated = True
                            print("✅ Токен Яндекс.Диска загружен")
                        else:
                            print("⚠️ Токен устарел или недействителен")
            except:
                pass

    def save_token(self, token):
        """Сохраняет токен в файл"""
        try:
            with open(self.token_file, 'w', encoding='utf-8') as f:
                json.dump({'token': token}, f, ensure_ascii=False, indent=2)
            self.token = token
            self.authenticated = True
            print("✅ Токен сохранен")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения токена: {e}")
            return False

    def check_token(self):
        """Проверяет, работает ли токен и есть ли права на запись"""
        if not self.token:
            return False
        try:
            headers = {'Authorization': f'OAuth {self.token}'}
            response = requests.get('https://cloud-api.yandex.net/v1/disk', headers=headers)

            if response.status_code == 200:
                disk_info = response.json()
                print(f"✅ Диск доступен. Всего места: {disk_info.get('total_space', 0) / 1024 ** 3:.1f} ГБ")
                return True
            else:
                print(f"❌ Ошибка проверки токена: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка при проверке токена: {e}")
            return False

    def get_auth_url(self):
        """Получить ссылку для авторизации - БЕЗ ПАРАМЕТРА SCOPE"""
        # Убираем scope полностью - будут использоваться права из настроек приложения
        return f"https://oauth.yandex.ru/authorize?response_type=code&client_id={self.client_id}"

    def exchange_code_for_token(self, code):
        """Обменять код подтверждения на токен"""
        url = "https://oauth.yandex.ru/token"
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                result = response.json()
                if 'access_token' in result:
                    return True, result['access_token']
                else:
                    return False, f"Ошибка: {result}"
            else:
                return False, f"HTTP ошибка: {response.status_code}. Возможно, код устарел или неверный."
        except Exception as e:
            return False, str(e)

    def check_folder_exists(self, folder_path):
        """Проверяет существование папки"""
        if not self.token:
            return False
        try:
            headers = {'Authorization': f'OAuth {self.token}'}
            url = 'https://cloud-api.yandex.net/v1/disk/resources'
            response = requests.get(url, headers=headers, params={'path': folder_path})
            return response.status_code == 200
        except:
            return False

    def create_folder(self, folder_path):
        """Создание папки"""
        if not self.token:
            print("❌ Нет токена")
            return False

        headers = {'Authorization': f'OAuth {self.token}'}
        url = 'https://cloud-api.yandex.net/v1/disk/resources'

        try:
            # Проверяем, существует ли папка
            if self.check_folder_exists(folder_path):
                print(f"✅ Папка уже существует: {folder_path}")
                return True

            # Создаем папку
            print(f"📁 Создаю папку: {folder_path}")
            response = requests.put(url, headers=headers, params={'path': folder_path})

            if response.status_code == 201:
                print(f"✅ Папка создана: {folder_path}")
                return True
            elif response.status_code == 202:
                print(f"⏳ Папка создается: {folder_path}")
                # Ждем немного и проверяем
                time.sleep(2)
                return self.check_folder_exists(folder_path)
            elif response.status_code == 409:
                print(f"✅ Папка уже существует (код 409): {folder_path}")
                return True
            else:
                print(f"❌ Ошибка создания папки: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Исключение при создании папки: {e}")
            return False

    def ensure_folder_exists(self, folder_path):
        """Гарантирует существование папки, создавая все промежуточные папки"""
        # Разбиваем путь на части
        parts = folder_path.strip('/').split('/')
        current_path = ""

        for part in parts:
            current_path += f"/{part}"
            if not self.check_folder_exists(current_path):
                if not self.create_folder(current_path):
                    return False
        return True

    def upload_file(self, local_path, remote_path):
        """Загрузка файла"""
        if not self.token:
            return False

        headers = {'Authorization': f'OAuth {self.token}'}

        try:
            # Получаем ссылку для загрузки
            url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
            params = {'path': remote_path, 'overwrite': 'true'}
            response = requests.get(url, headers=headers, params=params)

            if response.status_code != 200:
                print(f"❌ Ошибка получения ссылки: {response.status_code} - {response.text}")
                return False

            href = response.json().get('href')
            if not href:
                return False

            # Загружаем файл
            with open(local_path, 'rb') as f:
                upload_response = requests.put(href, files={'file': f})
                if upload_response.status_code in [201, 202]:
                    print(f"✅ Файл загружен: {remote_path}")
                    return True
                else:
                    print(f"❌ Ошибка загрузки файла: {upload_response.status_code}")
                    return False

        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return False


def add_context_menu(widget):
    """Добавляет контекстное меню для поля ввода"""
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Вставить", command=lambda: widget.event_generate("<<Paste>>"))
    menu.add_command(label="Копировать", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Вырезать", command=lambda: widget.event_generate("<<Cut>>"))

    def show_menu(event):
        menu.tk_popup(event.x_root, event.y_root)

    widget.bind("<Button-3>", show_menu)  # Правая кнопка мыши
    widget.bind("<Control-v>", lambda e: widget.event_generate("<<Paste>>"))  # Ctrl+V
    widget.bind("<Control-c>", lambda e: widget.event_generate("<<Copy>>"))  # Ctrl+C
    widget.bind("<Control-x>", lambda e: widget.event_generate("<<Cut>>"))  # Ctrl+X


class NotificationWindow:
    """Всплывающее окно уведомлений"""

    def __init__(self):
        self.window = None
        self.is_visible = False
        self.hide_after_id = None

    def show(self, message, duration=2, is_error=False):
        """Показать уведомление на заданное время"""
        if self.hide_after_id:
            try:
                self.window.after_cancel(self.hide_after_id)
            except:
                pass
        if self.window:
            try:
                self.window.destroy()
            except:
                pass

        self.window = tk.Toplevel()
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.attributes('-alpha', 0.9)

        screen_width = self.window.winfo_screenwidth()
        width = 400
        height = 60
        x = (screen_width - width) // 2
        y = 20

        self.window.geometry(f"{width}x{height}+{x}+{y}")

        bg_color = "#FF9800" if is_error else "#4CAF50"
        text_color = "white"
        self.window.configure(bg=bg_color)

        label = tk.Label(
            self.window,
            text=message,
            font=("Times New Roman", 12, "bold"),
            bg=bg_color,
            fg=text_color,
            wraplength=380
        )
        label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        self.is_visible = True
        self.hide_after_id = self.window.after(int(duration * 1000), self.hide)

    def hide(self):
        if self.window:
            try:
                self.window.destroy()
            except:
                pass
            self.window = None
            self.is_visible = False
            self.hide_after_id = None


class HintWindow:
    """Полупрозрачное окно с подсказками - кликабельно сквозь окно"""

    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.is_visible = False

    def create_window(self):
        if self.window:
            return

        self.window = tk.Toplevel()
        self.window.title("EMS Logger from LAPESHA")
        self.window.geometry("280x460")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.attributes('-alpha', 0.5)

        # ВАЖНО: Делаем окно прозрачным для событий мыши
        if os.name == 'nt':
            self.window.attributes('-transparentcolor', 'magenta')
            self.window.configure(bg='magenta')
        else:
            self.window.attributes('-alpha', 0.3)

        screen_width = self.window.winfo_screenwidth()
        x = screen_width - 290
        y = 10
        self.window.geometry(f"280x460+{x}+{y}")

        # Создаем внутренний фрейм с реальным фоном
        inner_frame = tk.Frame(self.window, bg="#2C3E50")
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        title_frame = tk.Frame(inner_frame, bg="#34495E", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="🚑 EMS ЛОГГЕР\nот ЛЯПЕША",
            font=("Times New Roman", 12, "bold"),
            bg="#34495E",
            fg="#ECF0F1"
        )
        title_label.pack(expand=True)

        content_frame = tk.Frame(inner_frame, bg="#2C3E50")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Управление
        tk.Label(
            content_frame,
            text="🔄 УПРАВЛЕНИЕ:",
            font=("Times New Roman", 11, "bold"),
            bg="#2C3E50",
            fg="#F1C40F"
        ).pack(anchor=tk.W, pady=(0, 3))

        control_frame1 = tk.Frame(content_frame, bg="#2C3E50")
        control_frame1.pack(fill=tk.X, pady=2)
        tk.Label(control_frame1, text="Alt+Num3", font=("Times New Roman", 10, "bold"),
                 bg="#2C3E50", fg="#E74C3C", width=8).pack(side=tk.LEFT)
        tk.Label(control_frame1, text="Вкл/Выкл", font=("Times New Roman", 10),
                 bg="#2C3E50", fg="#ECF0F1").pack(side=tk.LEFT, padx=3)

        control_frame2 = tk.Frame(content_frame, bg="#2C3E50")
        control_frame2.pack(fill=tk.X, pady=2)
        tk.Label(control_frame2, text="Num6", font=("Times New Roman", 10, "bold"),
                 bg="#2C3E50", fg="#3498DB", width=8).pack(side=tk.LEFT)
        tk.Label(control_frame2, text="Подсказки", font=("Times New Roman", 10),
                 bg="#2C3E50", fg="#ECF0F1").pack(side=tk.LEFT, padx=3)

        separator = tk.Frame(content_frame, bg="#34495E", height=2)
        separator.pack(fill=tk.X, pady=8)

        # Действия
        tk.Label(
            content_frame,
            text="💊 ДЕЙСТВИЯ:",
            font=("Times New Roman", 11, "bold"),
            bg="#2C3E50",
            fg="#2ECC71"
        ).pack(anchor=tk.W, pady=(0, 3))

        actions = [
            ("Num1", "Таблетки ELSH (1 б)", "#27AE60"),
            ("Num2", "Таблетки Sandy (2 б)", "#27AE60"),
            ("Num4", "Вакцины ELSH (2 б)", "#2980B9"),
            ("Num5", "Вакцины Sandy (4 б)", "#2980B9"),
            ("Num7", "ПМП город (3 б)", "#E67E22"),
            ("Num8", "ПМП пригород (4 б)", "#E67E22"),
        ]

        for key, desc, color in actions:
            action_frame = tk.Frame(content_frame, bg="#2C3E50")
            action_frame.pack(fill=tk.X, pady=2)
            tk.Label(action_frame, text=key, font=("Times New Roman", 10, "bold"),
                     bg="#2C3E50", fg=color, width=8).pack(side=tk.LEFT)
            tk.Label(action_frame, text=desc, font=("Times New Roman", 9),
                     bg="#2C3E50", fg="#ECF0F1").pack(side=tk.LEFT, padx=3)

        separator2 = tk.Frame(content_frame, bg="#34495E", height=2)
        separator2.pack(fill=tk.X, pady=8)

        # Яндекс.Диск
        tk.Label(
            content_frame,
            text="📦 ЯНДЕКС.ДИСК:",
            font=("Times New Roman", 11, "bold"),
            bg="#2C3E50",
            fg="#F9A825"
        ).pack(anchor=tk.W, pady=(0, 3))

        drive_frame = tk.Frame(content_frame, bg="#2C3E50")
        drive_frame.pack(fill=tk.X, pady=2)
        tk.Label(drive_frame, text="Alt+Num1-6", font=("Times New Roman", 10, "bold"),
                 bg="#2C3E50", fg="#F9A825", width=8).pack(side=tk.LEFT)
        tk.Label(drive_frame, text="Загрузить папку", font=("Times New Roman", 9),
                 bg="#2C3E50", fg="#ECF0F1").pack(side=tk.LEFT, padx=3)

        drive_frame2 = tk.Frame(content_frame, bg="#2C3E50")
        drive_frame2.pack(fill=tk.X, pady=2)
        tk.Label(drive_frame2, text="📦 Кнопка", font=("Times New Roman", 10, "bold"),
                 bg="#2C3E50", fg="#F9A825", width=8).pack(side=tk.LEFT)
        tk.Label(drive_frame2, text="Выбрать папки", font=("Times New Roman", 9),
                 bg="#2C3E50", fg="#ECF0F1").pack(side=tk.LEFT, padx=3)

        separator3 = tk.Frame(content_frame, bg="#34495E", height=2)
        separator3.pack(fill=tk.X, pady=8)

        status_frame = tk.Frame(content_frame, bg="#34495E", relief=tk.SUNKEN, bd=1)
        status_frame.pack(fill=tk.X, pady=5)

        self.status_hint = tk.Label(
            status_frame,
            text="🟢 Логирование ВКЛ",
            font=("Times New Roman", 10, "bold"),
            bg="#34495E",
            fg="#2ECC71"
        )
        self.status_hint.pack(pady=3)

        close_btn = tk.Button(
            content_frame,
            text="✕ Закрыть",
            font=("Times New Roman", 9, "bold"),
            bg="#E74C3C",
            fg="white",
            cursor="hand2",
            command=self.hide
        )
        close_btn.pack(pady=8)

        self.window.bind('<Escape>', lambda e: self.hide())

    def update_status(self, is_running):
        if self.window:
            status_text = "🟢 Логирование ВКЛ" if is_running else "🔴 Логирование ВЫКЛ"
            status_color = "#2ECC71" if is_running else "#E74C3C"
            self.status_hint.config(text=status_text, fg=status_color)

    def toggle(self, is_running):
        if self.is_visible:
            self.hide()
        else:
            self.show(is_running)

    def show(self, is_running):
        if not self.window:
            self.create_window()
        self.update_status(is_running)
        self.window.deiconify()
        self.is_visible = True
        print("📋 Окно подсказок открыто (клики проходят сквозь окно)")

    def hide(self):
        if self.window:
            self.window.withdraw()
            self.is_visible = False
            print("📋 Окно подсказок закрыто")


class ResizableApp:
    """Класс для масштабирования интерфейса"""

    def __init__(self, root, update_callback):
        self.root = root
        self.update_callback = update_callback
        self.base_width = 550
        self.base_height = 650
        self.last_width = 550
        self.last_height = 650

        self.root.bind('<Configure>', self.on_resize)

    def on_resize(self, event):
        if event.widget == self.root:
            new_width = event.width
            new_height = event.height

            if abs(new_width - self.last_width) > 10 or abs(new_height - self.last_height) > 10:
                self.last_width = new_width
                self.last_height = new_height

                scale_w = new_width / self.base_width
                scale_h = new_height / self.base_height
                scale = min(scale_w, scale_h)
                scale = max(0.7, min(1.5, scale))

                self.update_callback(scale)


class MedicalActionLogger:
    """
    Программа для логирования медицинских действий на Majestic RP
    """

    def __init__(self):
        self.running = True
        self.screenshots_taken = 0
        self.total_points = 0
        self.current_action = None
        self.listener = None
        self.notification = NotificationWindow()
        self.hint_window = HintWindow(self)
        self.yandex_uploader = YandexDiskUploader()
        self.alt_pressed = False
        self.current_scale = 1.0

        # Очки за каждое действие
        self.action_points = {
            '1': 1,  # Таблетки ELSH
            '2': 2,  # Таблетки Sandy
            '3': 2,  # Вакцины ELSH
            '4': 4,  # Вакцины Sandy
            '5': 3,  # ПМП город
            '6': 4,  # ПМП пригород
        }

        # Счетчики для каждой папки
        self.folder_counts = {
            '01_Tab_ELSH': 0,
            '02_Tab_Sandy': 0,
            '03_Vac_ELSH': 0,
            '04_Vac_Sandy': 0,
            '05_PMP_City': 0,
            '06_PMP_Suburb': 0
        }

        # Очки для каждой папки
        self.folder_points = {
            '01_Tab_ELSH': 0,
            '02_Tab_Sandy': 0,
            '03_Vac_ELSH': 0,
            '04_Vac_Sandy': 0,
            '05_PMP_City': 0,
            '06_PMP_Suburb': 0
        }

        # Создаем главную папку по умолчанию в Документах
        documents = Path.home() / "Documents"
        self.base_folder = documents / "EMS_Logs"
        self.custom_folder = None
        self.create_folder_structure()

        # Действия и соответствующие им папки
        self.actions = {
            '1': {'name': 'Таблетки ELSH', 'folder': '01_Tab_ELSH', 'points': 1},
            '2': {'name': 'Таблетки Sandy', 'folder': '02_Tab_Sandy', 'points': 2},
            '3': {'name': 'Вакцины ELSH', 'folder': '03_Vac_ELSH', 'points': 2},
            '4': {'name': 'Вакцины Sandy', 'folder': '04_Vac_Sandy', 'points': 4},
            '5': {'name': 'ПМП город', 'folder': '05_PMP_City', 'points': 3},
            '6': {'name': 'ПМП пригород', 'folder': '06_PMP_Suburb', 'points': 4}
        }

        # Соответствие клавиш NumPad действиям
        self.numpad_to_action = {
            97: '1',  # Num1
            98: '2',  # Num2
            99: 'toggle',  # Num3
            100: '3',  # Num4
            101: '4',  # Num5
            102: 'hint',  # Num6
            103: '5',  # Num7
            104: '6',  # Num8
        }

        # Соответствие папок и их индексов
        self.folder_indices = {
            '1': '01_Tab_ELSH',
            '2': '02_Tab_Sandy',
            '3': '03_Vac_ELSH',
            '4': '04_Vac_Sandy',
            '5': '05_PMP_City',
            '6': '06_PMP_Suburb'
        }

        self.setup_gui()
        self.resizer = ResizableApp(self.root, self.update_scale)

    def update_scale(self, scale):
        """Обновление масштаба интерфейса"""
        self.current_scale = scale

        # Обновляем шрифты
        title_size = int(18 * scale)
        self.title_label.config(font=("Times New Roman", title_size, "bold"))

        status_size = int(11 * scale)
        self.status_label.config(font=("Times New Roman", status_size, "bold"))

        counter_size = int(11 * scale)
        for widget in self.counter_frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(font=("Times New Roman", counter_size, "bold"))
        self.counter_label.config(font=("Times New Roman", int(16 * scale), "bold"))

        points_size = int(11 * scale)
        self.points_label.config(font=("Times New Roman", points_size, "bold"))
        self.points_value_label.config(font=("Times New Roman", int(16 * scale), "bold"))

        section_size = int(10 * scale)
        self.actions_label.config(font=("Times New Roman", section_size, "bold"))

        # Обновляем кнопки действий и их подписи
        for item in self.action_items:
            num_label = item['num_label']
            text_label = item['text_label']
            count_label = item['count_label']
            points_display = item['points_display']

            num_label.config(font=("Times New Roman", int(10 * scale), "bold"))
            text_label.config(font=("Times New Roman", int(10 * scale), "bold"))
            count_label.config(font=("Times New Roman", int(10 * scale), "bold"))
            points_display.config(font=("Times New Roman", int(10 * scale)))

        # Обновляем большие кнопки
        self.toggle_btn.config(font=("Times New Roman", int(12 * scale), "bold"))
        self.hints_btn.config(font=("Times New Roman", int(12 * scale), "bold"))
        self.yandex_btn.config(font=("Times New Roman", int(12 * scale), "bold"))
        self.test_btn.config(font=("Times New Roman", int(12 * scale), "bold"))
        self.open_btn.config(font=("Times New Roman", int(12 * scale), "bold"))

        hint_size = int(8 * scale)
        self.toggle_hint_label.config(font=("Times New Roman", hint_size, "italic"))
        self.hints_hint_label.config(font=("Times New Roman", hint_size, "italic"))
        self.yandex_hint_label.config(font=("Times New Roman", hint_size, "italic"))

        last_size = int(9 * scale)
        self.last_action_label.config(font=("Times New Roman", last_size, "italic"))

    def create_folder_structure(self):
        """Создание структуры папок для скриншотов"""
        try:
            folders = [
                '01_Tab_ELSH',
                '02_Tab_Sandy',
                '03_Vac_ELSH',
                '04_Vac_Sandy',
                '05_PMP_City',
                '06_PMP_Suburb',
                '00_Test'
            ]

            for folder in folders:
                folder_path = self.base_folder / folder
                folder_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Папка создана: {folder_path}")

        except Exception as e:
            print(f"❌ Ошибка создания папок: {e}")
            self.base_folder = Path(__file__).parent / "EMS_Logs"
            for folder in folders:
                folder_path = self.base_folder / folder
                folder_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Папка создана (альтернативная): {folder_path}")

    def change_save_folder(self):
        """Изменение папки сохранения"""
        try:
            folder_selected = filedialog.askdirectory(
                title="Выбери папку для сохранения скриншотов",
                initialdir=str(self.base_folder.parent)
            )

            if folder_selected:
                new_folder = Path(folder_selected)

                test_file = new_folder / "test_write.txt"
                try:
                    with open(test_file, 'w', encoding='utf-8') as f:
                        f.write('test')
                    test_file.unlink()

                    self.base_folder = new_folder / "EMS_Logs"
                    self.custom_folder = self.base_folder
                    self.create_folder_structure()

                    folder_display = str(self.base_folder)
                    self.folder_value_label.config(text=folder_display)

                    self.notification.show(f"✅ Папка изменена!", 2)

                except Exception as e:
                    self.notification.show(f"❌ Нет прав на запись в эту папку", 2, is_error=True)

        except Exception as e:
            self.notification.show(f"❌ Ошибка: {str(e)}", 2, is_error=True)

    def reset_folder(self):
        """Сброс папки на стандартную (Документы)"""
        documents = Path.home() / "Documents"
        self.base_folder = documents / "EMS_Logs"
        self.custom_folder = None
        self.create_folder_structure()
        folder_display = str(self.base_folder)
        self.folder_value_label.config(text=folder_display)
        self.notification.show(f"✅ Папка сброшена на стандартную", 2)

    def toggle_logging(self):
        self.running = not self.running
        status = "ВКЛЮЧЕНО" if self.running else "ВЫКЛЮЧЕНО"
        bg_color = "#C8E6C9" if self.running else "#FFCDD2"

        print(f"🔄 Логирование {status}")

        self.status_label.config(
            text=f"{'🟢' if self.running else '🔴'} ЛОГИРОВАНИЕ {status}!",
            fg="#2E7D32" if self.running else "#B71C1C",
            bg=bg_color
        )

        self.toggle_btn.config(
            text=f"{'🔴' if self.running else '🟢'}",
            bg="#F44336" if self.running else "#4CAF50"
        )

        self.hint_window.update_status(self.running)
        self.notification.show(f"Логирование {status}!", 1)

    def toggle_hints(self):
        self.hint_window.toggle(self.running)

    def show_yandex_auth_dialog(self):
        """Показать диалог авторизации Яндекс.Диска"""
        if self.yandex_uploader.authenticated:
            self.show_yandex_upload_dialog()
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Авторизация Яндекс.Диск")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Заголовок
        tk.Label(
            dialog,
            text="📦 Подключение Яндекс.Диска",
            font=("Times New Roman", 14, "bold"),
            bg="#F9A825",
            fg="white",
            pady=10
        ).pack(fill=tk.X)

        # Фрейм с инструкцией
        frame = tk.Frame(dialog, padx=20, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # ClientID
        tk.Label(frame, text="ClientID (уже введен):", font=("Times New Roman", 10, "bold")).pack(anchor=tk.W)
        client_id_label = tk.Label(frame, text=self.yandex_uploader.client_id,
                                   font=("Times New Roman", 10), fg="#2E7D32")
        client_id_label.pack(anchor=tk.W, pady=2)

        # ClientSecret
        tk.Label(frame, text="ClientSecret:", font=("Times New Roman", 10, "bold")).pack(anchor=tk.W, pady=(10, 0))
        client_secret_entry = tk.Entry(frame, font=("Times New Roman", 10), width=50)
        add_context_menu(client_secret_entry)
        client_secret_entry.pack(fill=tk.X, pady=2)

        # Кнопка получения ссылки
        def get_auth_url():
            client_secret = client_secret_entry.get().strip()
            if not client_secret:
                self.notification.show("❌ Введите ClientSecret", 2, is_error=True)
                return
            self.yandex_uploader.client_secret = client_secret
            url = self.yandex_uploader.get_auth_url()

            dialog.clipboard_clear()
            dialog.clipboard_append(url)
            webbrowser.open(url)

            self.notification.show("🔗 Ссылка открыта в браузере и скопирована!", 2)

        tk.Button(
            frame,
            text="🔗 Открыть ссылку для авторизации",
            font=("Times New Roman", 10, "bold"),
            bg="#F9A825",
            fg="white",
            padx=10,
            pady=8,
            command=get_auth_url
        ).pack(pady=10, fill=tk.X)

        tk.Label(
            frame,
            text="Шаг 2: Перейди по ссылке, разреши доступ и скопируй код",
            font=("Times New Roman", 11, "bold"),
            anchor=tk.W
        ).pack(fill=tk.X, pady=5)

        # Код подтверждения
        tk.Label(frame, text="Код подтверждения:", font=("Times New Roman", 10, "bold")).pack(anchor=tk.W, pady=(10, 0))
        code_entry = tk.Entry(frame, font=("Times New Roman", 10), width=50)
        add_context_menu(code_entry)
        code_entry.pack(fill=tk.X, pady=2)

        # Кнопка авторизации
        def authenticate():
            code = code_entry.get().strip()
            if not code:
                self.notification.show("❌ Введите код подтверждения", 2, is_error=True)
                return

            success, result = self.yandex_uploader.exchange_code_for_token(code)
            if success:
                if self.yandex_uploader.save_token(result):
                    self.notification.show("✅ Яндекс.Диск подключен!", 2)
                    dialog.destroy()
                    self.show_yandex_upload_dialog()
                else:
                    self.notification.show("❌ Не удалось сохранить токен", 3, is_error=True)
            else:
                self.notification.show(f"❌ {result}", 3, is_error=True)

        tk.Button(
            frame,
            text="✅ Подключить",
            font=("Times New Roman", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=8,
            command=authenticate
        ).pack(pady=15, fill=tk.X)

        # Кнопка отмены
        tk.Button(
            frame,
            text="Отмена",
            font=("Times New Roman", 10),
            bg="#757575",
            fg="white",
            padx=20,
            pady=5,
            command=dialog.destroy
        ).pack()

    def show_yandex_upload_dialog(self):
        """Показать диалог выбора папок для загрузки в Яндекс.Диск"""
        if not self.yandex_uploader.authenticated:
            self.show_yandex_auth_dialog()
            return

        # Создаем диалоговое окно
        dialog = tk.Toplevel(self.root)
        dialog.title("Выгрузка в Яндекс.Диск")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Заголовок
        tk.Label(
            dialog,
            text="📦 Выберите папки для загрузки",
            font=("Times New Roman", 14, "bold"),
            bg="#F9A825",
            fg="white",
            pady=10
        ).pack(fill=tk.X)

        # Фрейм для списка папок
        list_frame = tk.Frame(dialog, padx=20, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            list_frame,
            text="Доступные папки:",
            font=("Times New Roman", 11, "bold")
        ).pack(anchor=tk.W)

        # Переменные для чекбоксов
        self.folder_vars = {}

        folder_names = {
            '01_Tab_ELSH': 'Таблетки ELSH',
            '02_Tab_Sandy': 'Таблетки Sandy',
            '03_Vac_ELSH': 'Вакцины ELSH',
            '04_Vac_Sandy': 'Вакцины Sandy',
            '05_PMP_City': 'ПМП город',
            '06_PMP_Suburb': 'ПМП пригород'
        }

        for folder_key, folder_name in folder_names.items():
            count = self.folder_counts.get(folder_key, 0)
            var = tk.BooleanVar()
            cb = tk.Checkbutton(
                list_frame,
                text=f"{folder_name} ({count} файлов)",
                variable=var,
                font=("Times New Roman", 10)
            )
            cb.pack(anchor=tk.W, pady=2)
            self.folder_vars[folder_key] = var

        # Чекбокс для создания папки с датой
        date_frame = tk.Frame(list_frame, pady=10)
        date_frame.pack(fill=tk.X)

        self.date_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            date_frame,
            text="Создать отдельную папку с датой",
            variable=self.date_var,
            font=("Times New Roman", 10, "bold")
        ).pack(anchor=tk.W)

        # Прогресс-бар
        self.upload_progress = ttk.Progressbar(dialog, length=450, mode='determinate')
        self.upload_progress.pack(pady=10)

        self.progress_label = tk.Label(
            dialog,
            text="",
            font=("Times New Roman", 9),
            fg="#666"
        )
        self.progress_label.pack()

        # Кнопки
        button_frame = tk.Frame(dialog, pady=15)
        button_frame.pack(fill=tk.X)

        tk.Button(
            button_frame,
            text="📦 Загрузить выбранные",
            font=("Times New Roman", 11, "bold"),
            bg="#F9A825",
            fg="white",
            width=20,
            height=2,
            cursor="hand2",
            command=lambda: self.upload_selected_folders(dialog)
        ).pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

        tk.Button(
            button_frame,
            text="📦 Загрузить все",
            font=("Times New Roman", 11, "bold"),
            bg="#F9A825",
            fg="white",
            width=20,
            height=2,
            cursor="hand2",
            command=lambda: self.upload_all_folders(dialog)
        ).pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

        # Отдельная строка для кнопки отмены
        cancel_frame = tk.Frame(dialog, pady=5)
        cancel_frame.pack(fill=tk.X)

        tk.Button(
            cancel_frame,
            text="Отмена",
            font=("Times New Roman", 10),
            bg="#757575",
            fg="white",
            width=10,
            height=1,
            cursor="hand2",
            command=dialog.destroy
        ).pack()

    def upload_selected_folders(self, dialog):
        """Загрузить выбранные папки"""
        selected = [key for key, var in self.folder_vars.items() if var.get()]

        if not selected:
            self.notification.show("❌ Выберите хотя бы одну папку", 2, is_error=True)
            return

        # Запускаем загрузку в отдельном потоке
        thread = threading.Thread(
            target=self.upload_folders_thread,
            args=(selected, dialog)
        )
        thread.daemon = True
        thread.start()

    def upload_all_folders(self, dialog):
        """Загрузить все папки"""
        selected = list(self.folder_vars.keys())

        # Запускаем загрузку в отдельном потоке
        thread = threading.Thread(
            target=self.upload_folders_thread,
            args=(selected, dialog)
        )
        thread.daemon = True
        thread.start()

    def upload_folders_thread(self, folder_keys, dialog):
        """Поток для загрузки папок"""
        try:
            total_files = 0
            files_to_upload = []

            # Подсчитываем общее количество файлов
            for folder_key in folder_keys:
                folder_path = self.base_folder / folder_key
                if folder_path.exists():
                    files = list(folder_path.glob('*.png'))
                    total_files += len(files)
                    files_to_upload.extend([(folder_key, f) for f in files])

            if total_files == 0:
                self.root.after(0, lambda: self.notification.show("❌ Нет файлов для загрузки", 2, is_error=True))
                self.root.after(0, dialog.destroy)
                return

            # Создаем корневую папку на Яндекс.Диске
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            root_folder_name = f"EMS_Logs_{date_str}" if self.date_var.get() else "EMS_Logs"
            root_folder_path = f"/{root_folder_name}"

            print(f"📁 Проверяю корневую папку: {root_folder_path}")

            # Проверяем и создаем корневую папку
            if not self.yandex_uploader.ensure_folder_exists(root_folder_path):
                error_msg = f"❌ Не удалось создать корневую папку {root_folder_name}"
                print(error_msg)
                self.root.after(0, lambda: self.notification.show(error_msg, 3, is_error=True))
                self.root.after(0, dialog.destroy)
                return

            # Загружаем файлы
            uploaded = 0
            failed = 0

            for folder_key, file_path in files_to_upload:
                # Обновляем прогресс
                progress = int((uploaded + failed) / total_files * 100)
                self.root.after(0, lambda p=progress: self.upload_progress.configure(value=p))
                self.root.after(0, lambda u=uploaded, f=failed, t=total_files:
                self.progress_label.configure(text=f"Загружено: {u}, Ошибок: {f} из {t}"))

                # Создаем папку для этого типа
                folder_name = folder_key
                remote_folder = f"{root_folder_path}/{folder_name}"

                # Проверяем и создаем папку
                if not self.yandex_uploader.ensure_folder_exists(remote_folder):
                    print(f"❌ Не удалось создать папку {remote_folder}")
                    failed += 1
                    continue

                # Загружаем файл
                remote_path = f"{remote_folder}/{file_path.name}"
                if self.yandex_uploader.upload_file(str(file_path), remote_path):
                    uploaded += 1
                else:
                    failed += 1

                time.sleep(0.1)

            # Финальное обновление
            self.root.after(0, lambda: self.upload_progress.configure(value=100))
            self.root.after(0, lambda u=uploaded, f=failed:
            self.progress_label.configure(text=f"✅ Загружено: {u}, Ошибок: {f}"))

            self.root.after(2000, lambda: self.notification.show(f"✅ Загружено {uploaded} файлов!", 2))
            self.root.after(2500, dialog.destroy)

        except Exception as e:
            error_msg = f"❌ Ошибка: {str(e)}"
            print(error_msg)
            self.root.after(0, lambda: self.notification.show(error_msg, 3, is_error=True))
            self.root.after(0, dialog.destroy)

    def upload_to_yandex_by_index(self, action_num):
        """Загрузка конкретной папки по индексу"""
        if not self.yandex_uploader.authenticated:
            self.show_yandex_auth_dialog()
            return

        folder_key = self.folder_indices.get(action_num)
        if not folder_key:
            self.notification.show("❌ Папка не найдена", 2, is_error=True)
            return

        folder_path = self.base_folder / folder_key
        if not folder_path.exists():
            self.notification.show("❌ Папка не существует", 2, is_error=True)
            return

        files = list(folder_path.glob('*.png'))
        if not files:
            self.notification.show(f"❌ В папке нет файлов", 2, is_error=True)
            return

        # Загружаем в отдельном потоке
        thread = threading.Thread(
            target=self.upload_single_folder_thread,
            args=(folder_key, files)
        )
        thread.daemon = True
        thread.start()

    def upload_single_folder_thread(self, folder_key, files):
        """Поток для загрузки одной папки"""
        try:
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            root_folder_name = f"EMS_Logs_{date_str}"
            root_folder_path = f"/{root_folder_name}"

            # Создаем корневую папку
            if not self.yandex_uploader.ensure_folder_exists(root_folder_path):
                self.root.after(0,
                                lambda: self.notification.show("❌ Не удалось создать корневую папку", 2, is_error=True))
                return

            # Создаем папку для типа
            folder_name = folder_key
            remote_folder = f"{root_folder_path}/{folder_name}"

            if not self.yandex_uploader.ensure_folder_exists(remote_folder):
                self.root.after(0, lambda: self.notification.show(f"❌ Не удалось создать папку {folder_name}", 2,
                                                                  is_error=True))
                return

            uploaded = 0
            failed = 0

            for file_path in files:
                remote_path = f"{remote_folder}/{file_path.name}"
                if self.yandex_uploader.upload_file(str(file_path), remote_path):
                    uploaded += 1
                else:
                    failed += 1

            self.root.after(0, lambda u=uploaded, f=failed:
            self.notification.show(f"✅ Загружено: {u}, Ошибок: {f}", 3))

        except Exception as e:
            self.root.after(0, lambda: self.notification.show(f"❌ Ошибка: {str(e)}", 3, is_error=True))

    def on_key_press(self, key):
        try:
            if key == pynput_keyboard.Key.alt_l or key == pynput_keyboard.Key.alt_r:
                self.alt_pressed = True
                return

            if hasattr(key, 'vk') and key.vk in self.numpad_to_action:
                action = self.numpad_to_action[key.vk]

                num_key = {
                    97: 'Num1', 98: 'Num2', 99: 'Num3',
                    100: 'Num4', 101: 'Num5', 102: 'Num6',
                    103: 'Num7', 104: 'Num8'
                }.get(key.vk, f'Num{key.vk - 96}')

                if action == 'toggle':
                    if self.alt_pressed:
                        print(f"🎯 Нажата Alt+{num_key} -> переключение режима")
                        self.root.after(0, self.toggle_logging)
                    else:
                        print(f"⚠️ Для переключения режима используй Alt+Num3")
                        self.root.after(0, lambda: self.notification.show(
                            "⚠️ Для переключения используй Alt+Num3", 1, is_error=True
                        ))

                elif action == 'hint':
                    if self.alt_pressed:
                        print(f"🎯 Нажата Alt+{num_key} -> показать диалог Яндекс.Диска")
                        self.root.after(0, self.show_yandex_auth_dialog)
                    else:
                        print(f"🎯 Нажата {num_key} -> показать/скрыть подсказки")
                        self.root.after(0, self.toggle_hints)

                else:
                    if self.alt_pressed:
                        print(f"🎯 Нажата Alt+{num_key} -> загрузка папки {action}")
                        self.root.after(0, lambda a=action: self.upload_to_yandex_by_index(a))
                    else:
                        if not self.running:
                            print(f"⚠️ Логирование выключено, действие {action} проигнорировано")
                            return

                        print(f"🎯 Нажата {num_key} -> действие {action}")
                        thread = threading.Thread(target=self.take_screenshot_with_action, args=(action,))
                        thread.daemon = True
                        thread.start()

        except Exception as e:
            print(f"❌ Ошибка при обработке клавиши: {e}")

    def on_key_release(self, key):
        try:
            if key == pynput_keyboard.Key.alt_l or key == pynput_keyboard.Key.alt_r:
                self.alt_pressed = False
        except Exception as e:
            print(f"❌ Ошибка: {e}")

    def start_keyboard_listener(self):
        try:
            self.listener = pynput_keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.listener.start()
            print("✅ Слушатель клавиатуры запущен")
        except Exception as e:
            print(f"❌ Ошибка запуска слушателя: {e}")
            self.notification.show("⚠️ Ошибка запуска слушателя клавиатуры", 2, is_error=True)

    def create_styled_button(self, parent, text, bg_color, command, width=3, height=1):
        """Создание стилизованной кнопки"""
        btn = tk.Button(
            parent,
            text=text,
            font=("Times New Roman", 10, "bold"),
            bg=bg_color,
            fg="white",
            width=width,
            height=height,
            cursor="hand2",
            relief=tk.FLAT,
            bd=0,
            command=command
        )

        def on_enter(e):
            btn['background'] = self.lighten_color(bg_color)

        def on_leave(e):
            btn['background'] = bg_color

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        return btn

    def create_large_button(self, parent, icon, text, bg_color, command):
        """Создание увеличенной кнопки с иконкой и текстом"""
        frame = tk.Frame(parent, bg=bg_color, relief=tk.FLAT, bd=2)

        btn = tk.Button(
            frame,
            text=f"{icon}\n{text}",
            font=("Times New Roman", 11, "bold"),
            bg=bg_color,
            fg="white",
            width=8,
            height=2,
            cursor="hand2",
            relief=tk.FLAT,
            bd=0,
            command=command
        )

        def on_enter(e):
            btn['background'] = self.lighten_color(bg_color)
            frame['background'] = self.lighten_color(bg_color)

        def on_leave(e):
            btn['background'] = bg_color
            frame['background'] = bg_color

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.pack(expand=True, fill=tk.BOTH)

        return frame

    def lighten_color(self, color):
        """Осветление цвета для эффекта наведения"""
        light_colors = {
            "#4CAF50": "#66BB6A",
            "#2196F3": "#42A5F5",
            "#FF9800": "#FFA726",
            "#F44336": "#EF5350",
            "#3498DB": "#5DADE2",
            "#9C27B0": "#AB47BC",
            "#757575": "#9E9E9E",
            "#F9A825": "#FBC02D",
            "#E74C3C": "#EF5350"
        }
        return light_colors.get(color, color)

    def update_folder_counters(self):
        """Обновление счетчиков для каждой папки и баллов"""
        self.total_points = 0

        for item in self.action_items:
            folder = item['folder']
            count = self.folder_counts.get(folder, 0)
            points = self.folder_points.get(folder, 0)

            # Форматируем с фиксированной шириной для выравнивания
            item['count_label'].config(text=f"📸 {count:3d}")
            item['points_display'].config(text=f"🏆 {points:3d}")

            self.total_points += points

        # Обновляем общий счетчик баллов
        self.points_value_label.config(text=str(self.total_points))

    def take_screenshot_with_action(self, action_num):
        print(f"\n--- Начало создания скриншота для действия {action_num} ---")

        action = self.actions.get(action_num)
        if not action:
            print(f"❌ Действие {action_num} не найдено")
            return

        try:
            self.root.after(0, lambda: self.status_label.config(
                text=f"📸 Делаю скриншот: {action['name']}...",
                fg="#FF9800"
            ))

            print(f"1. Действие: {action['name']}")
            time.sleep(0.2)

            screenshot = ImageGrab.grab()
            print(f"2. Скриншот сделан, размер: {screenshot.size}")

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            short_name = action['name'].replace(' ', '_')
            filename = f"{timestamp}_{short_name}.png"

            folder_path = self.base_folder / action['folder']
            filepath = folder_path / filename
            print(f"3. Путь: {filepath}")

            screenshot.save(filepath, "PNG", quality=95)
            print(f"4. Файл сохранен")

            # Увеличиваем общий счетчик
            self.screenshots_taken += 1

            # Увеличиваем счетчик и баллы для конкретной папки
            folder = action['folder']
            points = action['points']

            self.folder_counts[folder] = self.folder_counts.get(folder, 0) + 1
            self.folder_points[folder] = self.folder_points.get(folder, 0) + points

            print(f"5. Общий счетчик: {self.screenshots_taken}")
            print(f"6. Счетчик папки {folder}: {self.folder_counts[folder]}")
            print(f"7. Баллы за действие: +{points}")

            # Обновляем интерфейс
            self.root.after(0, self.update_ui_after_screenshot, action['name'], filepath)
            self.root.after(0, self.update_folder_counters)
            self.root.after(0, lambda: self.notification.show(f"✅ +{points} баллов! {action['name']}", 2))

            print("--- Скриншот готов ---\n")

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.root.after(0, lambda: self.notification.show(f"❌ Ошибка: {str(e)}", 2, is_error=True))

    def update_ui_after_screenshot(self, action_name, filepath):
        """Обновление интерфейса после скриншота"""
        self.counter_label.config(text=str(self.screenshots_taken))

        now = datetime.datetime.now().strftime('%H:%M:%S')
        self.last_action_label.config(
            text=f"Последнее действие: {action_name} ({now})"
        )

        self.status_label.config(
            text=f"✅ Скриншот сохранен: {filepath.name}",
            fg="#4CAF50",
            bg="#C8E6C9"
        )

    def open_folder(self):
        """Открыть папку со скриншотами"""
        try:
            if os.name == 'nt':
                os.startfile(self.base_folder)
            else:
                import subprocess
                subprocess.run(['open', self.base_folder])
        except Exception as e:
            self.notification.show("❌ Ошибка открытия папки", 2, is_error=True)

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("EMS Logger from LAPESHA")
        self.root.geometry("550x650")
        self.root.minsize(500, 600)
        self.root.resizable(True, True)

        # Главный контейнер
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Контейнер для левой части
        left_container = tk.Frame(main_container)
        left_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Заголовок
        title_frame = tk.Frame(left_container, bg="#2E7D32", height=50)
        title_frame.pack(fill=tk.X, pady=(0, 5))
        title_frame.pack_propagate(False)

        self.title_label = tk.Label(
            title_frame,
            text="🚑 EMS ЛОГГЕР от ЛЯПЕША",
            font=("Times New Roman", 16, "bold"),
            bg="#2E7D32",
            fg="white"
        )
        self.title_label.pack(expand=True)

        # Информация о папке
        info_frame = tk.Frame(left_container, bg="#E8F5E8", relief=tk.GROOVE, bd=1)
        info_frame.pack(fill=tk.X, pady=2)

        info_header = tk.Frame(info_frame, bg="#E8F5E8")
        info_header.pack(fill=tk.X, padx=5, pady=(2, 0))

        change_btn = self.create_styled_button(
            info_header,
            "📂",
            "#757575",
            self.change_save_folder,
            width=2,
            height=1
        )
        change_btn.pack(side=tk.LEFT, padx=1)

        reset_btn = self.create_styled_button(
            info_header,
            "↺",
            "#757575",
            self.reset_folder,
            width=2,
            height=1
        )
        reset_btn.pack(side=tk.LEFT, padx=1)

        tk.Label(
            info_header,
            text="📁 Папка сохранения:",
            font=("Times New Roman", 9, "bold"),
            bg="#E8F5E8"
        ).pack(side=tk.LEFT, padx=(5, 0))

        # Значение пути
        folder_display = str(self.base_folder)
        self.folder_value_label = tk.Label(
            info_header,
            text=folder_display,
            font=("Times New Roman", 8, "bold"),
            bg="#E8F5E8",
            fg="#2E7D32",
            anchor=tk.W
        )
        self.folder_value_label.pack(side=tk.LEFT, padx=(5, 5))

        # Статус
        status_frame = tk.Frame(left_container, bg="#C8E6C9" if self.running else "#FFCDD2", relief=tk.SUNKEN, bd=1)
        status_frame.pack(fill=tk.X, pady=2)

        self.status_label = tk.Label(
            status_frame,
            text="🟢 ЛОГИРОВАНИЕ ВКЛЮЧЕНО!",
            font=("Times New Roman", 11, "bold"),
            bg="#C8E6C9",
            fg="#2E7D32"
        )
        self.status_label.pack(pady=3)

        # Счетчики в одной строке
        counters_row = tk.Frame(left_container)
        counters_row.pack(fill=tk.X, pady=2)

        points_frame = tk.Frame(counters_row, bg="white", relief=tk.RAISED, bd=1)
        points_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 1))

        self.points_label = tk.Label(
            points_frame,
            text="🏆 БАЛЛЫ:",
            font=("Times New Roman", 10, "bold"),
            bg="white"
        )
        self.points_label.pack(side=tk.LEFT, padx=3, pady=3)

        self.points_value_label = tk.Label(
            points_frame,
            text="0",
            font=("Times New Roman", 14, "bold"),
            bg="white",
            fg="#FF9800"
        )
        self.points_value_label.pack(side=tk.LEFT, padx=3)

        self.counter_frame = tk.Frame(counters_row, bg="white", relief=tk.RAISED, bd=1)
        self.counter_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(1, 0))

        tk.Label(
            self.counter_frame,
            text="📸 ВСЕГО:",
            font=("Times New Roman", 10, "bold"),
            bg="white"
        ).pack(side=tk.LEFT, padx=3, pady=3)

        self.counter_label = tk.Label(
            self.counter_frame,
            text="0",
            font=("Times New Roman", 14, "bold"),
            bg="white",
            fg="#2E7D32"
        )
        self.counter_label.pack(side=tk.LEFT, padx=3)

        # Кнопки действий
        actions_frame = tk.Frame(left_container)
        actions_frame.pack(fill=tk.BOTH, expand=True, pady=3)

        # Заголовок действий с иконкой мышки
        actions_header = tk.Frame(actions_frame)
        actions_header.pack(anchor=tk.W, fill=tk.X, pady=1)

        tk.Label(
            actions_header,
            text="🖱️",
            font=("Times New Roman", 11),
            fg="#333"
        ).pack(side=tk.LEFT, padx=(0, 2))

        self.actions_label = tk.Label(
            actions_header,
            text="ДЕЙСТВИЯ:",
            font=("Times New Roman", 10, "bold")
        )
        self.actions_label.pack(side=tk.LEFT)

        buttons_container = tk.Frame(actions_frame)
        buttons_container.pack(anchor=tk.W, fill=tk.X)

        self.action_items = []

        button_configs = [
            ("Num1", "Таблетки ELSH", "#4CAF50", '1', "01_Tab_ELSH"),
            ("Num2", "Таблетки Sandy", "#4CAF50", '2', "02_Tab_Sandy"),
            ("Num4", "Вакцины ELSH", "#2196F3", '3', "03_Vac_ELSH"),
            ("Num5", "Вакцины Sandy", "#2196F3", '4', "04_Vac_Sandy"),
            ("Num7", "ПМП город", "#FF9800", '5', "05_PMP_City"),
            ("Num8", "ПМП пригород", "#FF9800", '6', "06_PMP_Suburb"),
        ]

        for key, text, color, action, folder in button_configs:
            row_frame = tk.Frame(buttons_container)
            row_frame.pack(anchor=tk.W, fill=tk.X, pady=1)

            controls_frame = tk.Frame(row_frame)
            controls_frame.pack(anchor=tk.W)

            # Номер кнопки
            num_label = tk.Label(
                controls_frame,
                text=f"[{key}]",
                font=("Times New Roman", 10, "bold"),
                fg=color,
                width=5,
                anchor=tk.W
            )
            num_label.pack(side=tk.LEFT)

            # Текст действия
            text_label = tk.Label(
                controls_frame,
                text=f"- {text}",
                font=("Times New Roman", 10, "bold"),
                fg=color,
                width=18,
                anchor=tk.W
            )
            text_label.pack(side=tk.LEFT)

            # Счетчик скриншотов
            count_label = tk.Label(
                controls_frame,
                text="📸   0",
                font=("Times New Roman", 10, "bold"),
                fg="#666",
                width=7,
                anchor=tk.W
            )
            count_label.pack(side=tk.LEFT, padx=(3, 1))

            # Счетчик баллов
            points_display = tk.Label(
                controls_frame,
                text="🏆   0",
                font=("Times New Roman", 10),
                fg="#FF9800",
                width=7,
                anchor=tk.W
            )
            points_display.pack(side=tk.LEFT)

            self.action_items.append({
                'folder': folder,
                'num_label': num_label,
                'text_label': text_label,
                'count_label': count_label,
                'points_display': points_display
            })

        # Большие кнопки управления
        big_buttons_frame = tk.Frame(left_container)
        big_buttons_frame.pack(fill=tk.X, pady=10)

        # Создаем контейнер для 5 больших кнопок
        big_buttons_container = tk.Frame(big_buttons_frame)
        big_buttons_container.pack()

        # Кнопка вкл/выкл
        toggle_frame = self.create_large_button(
            big_buttons_container,
            "🔴🟢",
            "Вкл/Выкл",
            "#F44336" if self.running else "#4CAF50",
            self.toggle_logging
        )
        toggle_frame.pack(side=tk.LEFT, padx=3)
        self.toggle_btn = toggle_frame.winfo_children()[0]

        # Кнопка подсказок
        hints_frame = self.create_large_button(
            big_buttons_container,
            "📋",
            "Подсказки",
            "#3498DB",
            self.toggle_hints
        )
        hints_frame.pack(side=tk.LEFT, padx=3)
        self.hints_btn = hints_frame.winfo_children()[0]

        # Кнопка Яндекс.Диск
        yandex_frame = self.create_large_button(
            big_buttons_container,
            "📦",
            "Яндекс",
            "#F9A825",
            self.show_yandex_auth_dialog
        )
        yandex_frame.pack(side=tk.LEFT, padx=3)
        self.yandex_btn = yandex_frame.winfo_children()[0]

        # Кнопка теста
        test_frame = self.create_large_button(
            big_buttons_container,
            "🔧",
            "Тест",
            "#9C27B0",
            self.test_screenshot
        )
        test_frame.pack(side=tk.LEFT, padx=3)
        self.test_btn = test_frame.winfo_children()[0]

        # Кнопка открыть
        open_frame = self.create_large_button(
            big_buttons_container,
            "📂",
            "Открыть",
            "#2196F3",
            self.open_folder
        )
        open_frame.pack(side=tk.LEFT, padx=3)
        self.open_btn = open_frame.winfo_children()[0]

        # Подписи с горячими клавишами
        hints_row = tk.Frame(left_container)
        hints_row.pack(fill=tk.X, pady=2)

        hint_texts = ["Alt+3", "Num6", "Alt+6", "", ""]
        for i, text in enumerate(hint_texts):
            label = tk.Label(
                hints_row,
                text=text,
                font=("Times New Roman", 7, "italic"),
                fg="#666",
                width=9
            )
            label.pack(side=tk.LEFT, padx=5, expand=True)

        # Последнее действие
        self.last_action_label = tk.Label(
            left_container,
            text="Последнее действие: —",
            font=("Times New Roman", 9, "italic"),
            fg="#666"
        )
        self.last_action_label.pack(anchor=tk.W, pady=5)

        self.start_keyboard_listener()

    def test_screenshot(self):
        try:
            print("🔍 Тест: начинаю создание тестового скриншота...")

            test_folder = self.base_folder / "00_Test"
            test_folder.mkdir(parents=True, exist_ok=True)

            screenshot = ImageGrab.grab()
            print("✅ Тест: скриншот сделан")

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            test_file = test_folder / f"test_{timestamp}.png"
            screenshot.save(test_file, "PNG")
            print(f"✅ Тест: скриншот сохранен в {test_file}")

            self.notification.show("✅ Тест успешен!", 2)

        except Exception as e:
            error_msg = f"❌ Ошибка в тесте: {str(e)}"
            print(error_msg)
            self.notification.show(f"❌ Ошибка: {str(e)}", 2, is_error=True)

    def run(self):
        """Запуск программы"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        """Обработка закрытия окна"""
        if self.hint_window:
            self.hint_window.hide()
        if self.listener:
            self.listener.stop()
        self.root.destroy()


def main():
    """Главная функция"""
    print("=" * 70)
    print("🚑 ЗАПУСК EMS ЛОГГЕРА ОТ ЛЯПЕША")
    print("=" * 70)
    print("\n✅ Программа ЗАПУЩЕНА!")
    print("📁 Скриншоты сохраняются в: Documents\\EMS_Logs\\")
    print("\n💰 СИСТЕМА БАЛЛОВ:")
    print("   Num1 → Таблетки ELSH → 1 балл")
    print("   Num2 → Таблетки Sandy → 2 балла")
    print("   Num4 → Вакцины ELSH → 2 балла")
    print("   Num5 → Вакцины Sandy → 4 балла")
    print("   Num7 → ПМП город → 3 балла")
    print("   Num8 → ПМП пригород → 4 балла")
    print("\n📦 ЯНДЕКС.ДИСК:")
    print("   📦 Кнопка → Подключить и выбрать папки")
    print("   Alt+Num1-6 → Загрузить конкретную папку")
    print("   Alt+Num6 → Подключить/выбрать папки")
    print("=" * 70)
    print("\n💡 Убедись, что Num Lock включен!")
    print("💡 ClientID уже введен, нужно только ClientSecret")
    print("💡 Можно вставлять текст через Ctrl+V или правую кнопку мыши")
    print("=" * 70)

    app = MedicalActionLogger()
    app.run()
import sys
import subprocess
import os
import json
import requests
import webbrowser
from tkinter import filedialog
from pathlib import Path


# Функция для установки пакетов
def install_package(package):
    """Установка pip пакета"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Пакет {package} успешно установлен")
        return True
    except Exception as e:
        print(f"❌ Ошибка установки {package}: {e}")
        return False


# Проверяем и устанавливаем необходимые библиотеки
required_packages = [
    'pillow',
    'pyautogui',
    'pynput',
    'requests'
]

print("🔍 Проверка установленных библиотек...")
for package in required_packages:
    try:
        __import__(package)
        print(f"✅ {package} уже установлен")
    except ImportError:
        print(f"📦 Устанавливаю {package}...")
        if not install_package(package):
            print(f"⚠️ Не удалось установить {package}")
            print("Попробуй установить вручную: pip install " + package)
            input("Нажми Enter для продолжения...")

# Теперь импортируем все библиотеки
try:
    from PIL import ImageGrab, Image
    import pyautogui
    import threading
    import time
    import datetime
    from pathlib import Path
    import tkinter as tk
    from tkinter import messagebox, ttk
    from pynput import keyboard as pynput_keyboard

except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("\nПожалуйста, выполни в терминале PyCharm команду:")
    print("pip install pillow pyautogui pynput requests")
    print("\nИли установи через настройки: File → Settings → Project → Python Interpreter → +")
    input("\nНажми Enter для выхода...")
    sys.exit(1)


class YandexDiskUploader:
    """Класс для работы с Яндекс.Диском через REST API"""

    def __init__(self):
        self.token = None
        self.authenticated = False
        self.token_file = Path(__file__).parent / 'yandex_token.json'
        self.client_id = "9bc6c562c83d4b3d8e7265cc8eb0fca2"  # Твой ClientID
        self.client_secret = ""

        # Загружаем сохраненный токен
        self.load_token()

    def load_token(self):
        """Загружает сохраненный токен"""
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'token' in data:
                        self.token = data['token']
                        # Проверяем токен
                        if self.check_token():
                            self.authenticated = True
                            print("✅ Токен Яндекс.Диска загружен")
                        else:
                            print("⚠️ Токен устарел или недействителен")
            except:
                pass

    def save_token(self, token):
        """Сохраняет токен в файл"""
        try:
            with open(self.token_file, 'w', encoding='utf-8') as f:
                json.dump({'token': token}, f, ensure_ascii=False, indent=2)
            self.token = token
            self.authenticated = True
            print("✅ Токен сохранен")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения токена: {e}")
            return False

    def check_token(self):
        """Проверяет, работает ли токен и есть ли права на запись"""
        if not self.token:
            return False
        try:
            headers = {'Authorization': f'OAuth {self.token}'}
            response = requests.get('https://cloud-api.yandex.net/v1/disk', headers=headers)

            if response.status_code == 200:
                disk_info = response.json()
                print(f"✅ Диск доступен. Всего места: {disk_info.get('total_space', 0) / 1024 ** 3:.1f} ГБ")
                return True
            else:
                print(f"❌ Ошибка проверки токена: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка при проверке токена: {e}")
            return False

    def get_auth_url(self):
        """Получить ссылку для авторизации - БЕЗ ПАРАМЕТРА SCOPE"""
        # Убираем scope полностью - будут использоваться права из настроек приложения
        return f"https://oauth.yandex.ru/authorize?response_type=code&client_id={self.client_id}"

    def exchange_code_for_token(self, code):
        """Обменять код подтверждения на токен"""
        url = "https://oauth.yandex.ru/token"
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                result = response.json()
                if 'access_token' in result:
                    return True, result['access_token']
                else:
                    return False, f"Ошибка: {result}"
            else:
                return False, f"HTTP ошибка: {response.status_code}. Возможно, код устарел или неверный."
        except Exception as e:
            return False, str(e)

    def check_folder_exists(self, folder_path):
        """Проверяет существование папки"""
        if not self.token:
            return False
        try:
            headers = {'Authorization': f'OAuth {self.token}'}
            url = 'https://cloud-api.yandex.net/v1/disk/resources'
            response = requests.get(url, headers=headers, params={'path': folder_path})
            return response.status_code == 200
        except:
            return False

    def create_folder(self, folder_path):
        """Создание папки"""
        if not self.token:
            print("❌ Нет токена")
            return False

        headers = {'Authorization': f'OAuth {self.token}'}
        url = 'https://cloud-api.yandex.net/v1/disk/resources'

        try:
            # Проверяем, существует ли папка
            if self.check_folder_exists(folder_path):
                print(f"✅ Папка уже существует: {folder_path}")
                return True

            # Создаем папку
            print(f"📁 Создаю папку: {folder_path}")
            response = requests.put(url, headers=headers, params={'path': folder_path})

            if response.status_code == 201:
                print(f"✅ Папка создана: {folder_path}")
                return True
            elif response.status_code == 202:
                print(f"⏳ Папка создается: {folder_path}")
                # Ждем немного и проверяем
                time.sleep(2)
                return self.check_folder_exists(folder_path)
            elif response.status_code == 409:
                print(f"✅ Папка уже существует (код 409): {folder_path}")
                return True
            else:
                print(f"❌ Ошибка создания папки: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Исключение при создании папки: {e}")
            return False

    def ensure_folder_exists(self, folder_path):
        """Гарантирует существование папки, создавая все промежуточные папки"""
        # Разбиваем путь на части
        parts = folder_path.strip('/').split('/')
        current_path = ""

        for part in parts:
            current_path += f"/{part}"
            if not self.check_folder_exists(current_path):
                if not self.create_folder(current_path):
                    return False
        return True

    def upload_file(self, local_path, remote_path):
        """Загрузка файла"""
        if not self.token:
            return False

        headers = {'Authorization': f'OAuth {self.token}'}

        try:
            # Получаем ссылку для загрузки
            url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
            params = {'path': remote_path, 'overwrite': 'true'}
            response = requests.get(url, headers=headers, params=params)

            if response.status_code != 200:
                print(f"❌ Ошибка получения ссылки: {response.status_code} - {response.text}")
                return False

            href = response.json().get('href')
            if not href:
                return False

            # Загружаем файл
            with open(local_path, 'rb') as f:
                upload_response = requests.put(href, files={'file': f})
                if upload_response.status_code in [201, 202]:
                    print(f"✅ Файл загружен: {remote_path}")
                    return True
                else:
                    print(f"❌ Ошибка загрузки файла: {upload_response.status_code}")
                    return False

        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return False


def add_context_menu(widget):
    """Добавляет контекстное меню для поля ввода"""
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Вставить", command=lambda: widget.event_generate("<<Paste>>"))
    menu.add_command(label="Копировать", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Вырезать", command=lambda: widget.event_generate("<<Cut>>"))

    def show_menu(event):
        menu.tk_popup(event.x_root, event.y_root)

    widget.bind("<Button-3>", show_menu)  # Правая кнопка мыши
    widget.bind("<Control-v>", lambda e: widget.event_generate("<<Paste>>"))  # Ctrl+V
    widget.bind("<Control-c>", lambda e: widget.event_generate("<<Copy>>"))  # Ctrl+C
    widget.bind("<Control-x>", lambda e: widget.event_generate("<<Cut>>"))  # Ctrl+X


class NotificationWindow:
    """Всплывающее окно уведомлений"""

    def __init__(self):
        self.window = None
        self.is_visible = False
        self.hide_after_id = None

    def show(self, message, duration=2, is_error=False):
        """Показать уведомление на заданное время"""
        if self.hide_after_id:
            try:
                self.window.after_cancel(self.hide_after_id)
            except:
                pass
        if self.window:
            try:
                self.window.destroy()
            except:
                pass

        self.window = tk.Toplevel()
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.attributes('-alpha', 0.9)

        screen_width = self.window.winfo_screenwidth()
        width = 400
        height = 60
        x = (screen_width - width) // 2
        y = 20

        self.window.geometry(f"{width}x{height}+{x}+{y}")

        bg_color = "#FF9800" if is_error else "#4CAF50"
        text_color = "white"
        self.window.configure(bg=bg_color)

        label = tk.Label(
            self.window,
            text=message,
            font=("Times New Roman", 12, "bold"),
            bg=bg_color,
            fg=text_color,
            wraplength=380
        )
        label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        self.is_visible = True
        self.hide_after_id = self.window.after(int(duration * 1000), self.hide)

    def hide(self):
        if self.window:
            try:
                self.window.destroy()
            except:
                pass
            self.window = None
            self.is_visible = False
            self.hide_after_id = None


class HintWindow:
    """Полупрозрачное окно с подсказками - кликабельно сквозь окно"""

    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.is_visible = False

    def create_window(self):
        if self.window:
            return

        self.window = tk.Toplevel()
        self.window.title("EMS Logger from LAPESHA")
        self.window.geometry("280x460")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.attributes('-alpha', 0.5)

        # ВАЖНО: Делаем окно прозрачным для событий мыши
        if os.name == 'nt':
            self.window.attributes('-transparentcolor', 'magenta')
            self.window.configure(bg='magenta')
        else:
            self.window.attributes('-alpha', 0.3)

        screen_width = self.window.winfo_screenwidth()
        x = screen_width - 290
        y = 10
        self.window.geometry(f"280x460+{x}+{y}")

        # Создаем внутренний фрейм с реальным фоном
        inner_frame = tk.Frame(self.window, bg="#2C3E50")
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        title_frame = tk.Frame(inner_frame, bg="#34495E", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="🚑 EMS ЛОГГЕР\nот ЛЯПЕША",
            font=("Times New Roman", 12, "bold"),
            bg="#34495E",
            fg="#ECF0F1"
        )
        title_label.pack(expand=True)

        content_frame = tk.Frame(inner_frame, bg="#2C3E50")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Управление
        tk.Label(
            content_frame,
            text="🔄 УПРАВЛЕНИЕ:",
            font=("Times New Roman", 11, "bold"),
            bg="#2C3E50",
            fg="#F1C40F"
        ).pack(anchor=tk.W, pady=(0, 3))

        control_frame1 = tk.Frame(content_frame, bg="#2C3E50")
        control_frame1.pack(fill=tk.X, pady=2)
        tk.Label(control_frame1, text="Alt+Num3", font=("Times New Roman", 10, "bold"),
                 bg="#2C3E50", fg="#E74C3C", width=8).pack(side=tk.LEFT)
        tk.Label(control_frame1, text="Вкл/Выкл", font=("Times New Roman", 10),
                 bg="#2C3E50", fg="#ECF0F1").pack(side=tk.LEFT, padx=3)

        control_frame2 = tk.Frame(content_frame, bg="#2C3E50")
        control_frame2.pack(fill=tk.X, pady=2)
        tk.Label(control_frame2, text="Num6", font=("Times New Roman", 10, "bold"),
                 bg="#2C3E50", fg="#3498DB", width=8).pack(side=tk.LEFT)
        tk.Label(control_frame2, text="Подсказки", font=("Times New Roman", 10),
                 bg="#2C3E50", fg="#ECF0F1").pack(side=tk.LEFT, padx=3)

        separator = tk.Frame(content_frame, bg="#34495E", height=2)
        separator.pack(fill=tk.X, pady=8)

        # Действия
        tk.Label(
            content_frame,
            text="💊 ДЕЙСТВИЯ:",
            font=("Times New Roman", 11, "bold"),
            bg="#2C3E50",
            fg="#2ECC71"
        ).pack(anchor=tk.W, pady=(0, 3))

        actions = [
            ("Num1", "Таблетки ELSH (1 б)", "#27AE60"),
            ("Num2", "Таблетки Sandy (2 б)", "#27AE60"),
            ("Num4", "Вакцины ELSH (2 б)", "#2980B9"),
            ("Num5", "Вакцины Sandy (4 б)", "#2980B9"),
            ("Num7", "ПМП город (3 б)", "#E67E22"),
            ("Num8", "ПМП пригород (4 б)", "#E67E22"),
        ]

        for key, desc, color in actions:
            action_frame = tk.Frame(content_frame, bg="#2C3E50")
            action_frame.pack(fill=tk.X, pady=2)
            tk.Label(action_frame, text=key, font=("Times New Roman", 10, "bold"),
                     bg="#2C3E50", fg=color, width=8).pack(side=tk.LEFT)
            tk.Label(action_frame, text=desc, font=("Times New Roman", 9),
                     bg="#2C3E50", fg="#ECF0F1").pack(side=tk.LEFT, padx=3)

        separator2 = tk.Frame(content_frame, bg="#34495E", height=2)
        separator2.pack(fill=tk.X, pady=8)

        # Яндекс.Диск
        tk.Label(
            content_frame,
            text="📦 ЯНДЕКС.ДИСК:",
            font=("Times New Roman", 11, "bold"),
            bg="#2C3E50",
            fg="#F9A825"
        ).pack(anchor=tk.W, pady=(0, 3))

        drive_frame = tk.Frame(content_frame, bg="#2C3E50")
        drive_frame.pack(fill=tk.X, pady=2)
        tk.Label(drive_frame, text="Alt+Num1-6", font=("Times New Roman", 10, "bold"),
                 bg="#2C3E50", fg="#F9A825", width=8).pack(side=tk.LEFT)
        tk.Label(drive_frame, text="Загрузить папку", font=("Times New Roman", 9),
                 bg="#2C3E50", fg="#ECF0F1").pack(side=tk.LEFT, padx=3)

        drive_frame2 = tk.Frame(content_frame, bg="#2C3E50")
        drive_frame2.pack(fill=tk.X, pady=2)
        tk.Label(drive_frame2, text="📦 Кнопка", font=("Times New Roman", 10, "bold"),
                 bg="#2C3E50", fg="#F9A825", width=8).pack(side=tk.LEFT)
        tk.Label(drive_frame2, text="Выбрать папки", font=("Times New Roman", 9),
                 bg="#2C3E50", fg="#ECF0F1").pack(side=tk.LEFT, padx=3)

        separator3 = tk.Frame(content_frame, bg="#34495E", height=2)
        separator3.pack(fill=tk.X, pady=8)

        status_frame = tk.Frame(content_frame, bg="#34495E", relief=tk.SUNKEN, bd=1)
        status_frame.pack(fill=tk.X, pady=5)

        self.status_hint = tk.Label(
            status_frame,
            text="🟢 Логирование ВКЛ",
            font=("Times New Roman", 10, "bold"),
            bg="#34495E",
            fg="#2ECC71"
        )
        self.status_hint.pack(pady=3)

        close_btn = tk.Button(
            content_frame,
            text="✕ Закрыть",
            font=("Times New Roman", 9, "bold"),
            bg="#E74C3C",
            fg="white",
            cursor="hand2",
            command=self.hide
        )
        close_btn.pack(pady=8)

        self.window.bind('<Escape>', lambda e: self.hide())

    def update_status(self, is_running):
        if self.window:
            status_text = "🟢 Логирование ВКЛ" if is_running else "🔴 Логирование ВЫКЛ"
            status_color = "#2ECC71" if is_running else "#E74C3C"
            self.status_hint.config(text=status_text, fg=status_color)

    def toggle(self, is_running):
        if self.is_visible:
            self.hide()
        else:
            self.show(is_running)

    def show(self, is_running):
        if not self.window:
            self.create_window()
        self.update_status(is_running)
        self.window.deiconify()
        self.is_visible = True
        print("📋 Окно подсказок открыто (клики проходят сквозь окно)")

    def hide(self):
        if self.window:
            self.window.withdraw()
            self.is_visible = False
            print("📋 Окно подсказок закрыто")


class ResizableApp:
    """Класс для масштабирования интерфейса"""

    def __init__(self, root, update_callback):
        self.root = root
        self.update_callback = update_callback
        self.base_width = 550
        self.base_height = 650
        self.last_width = 550
        self.last_height = 650

        self.root.bind('<Configure>', self.on_resize)

    def on_resize(self, event):
        if event.widget == self.root:
            new_width = event.width
            new_height = event.height

            if abs(new_width - self.last_width) > 10 or abs(new_height - self.last_height) > 10:
                self.last_width = new_width
                self.last_height = new_height

                scale_w = new_width / self.base_width
                scale_h = new_height / self.base_height
                scale = min(scale_w, scale_h)
                scale = max(0.7, min(1.5, scale))

                self.update_callback(scale)


class MedicalActionLogger:
    """
    Программа для логирования медицинских действий на Majestic RP
    """

    def __init__(self):
        self.running = True
        self.screenshots_taken = 0
        self.total_points = 0
        self.current_action = None
        self.listener = None
        self.notification = NotificationWindow()
        self.hint_window = HintWindow(self)
        self.yandex_uploader = YandexDiskUploader()
        self.alt_pressed = False
        self.current_scale = 1.0

        # Очки за каждое действие
        self.action_points = {
            '1': 1,  # Таблетки ELSH
            '2': 2,  # Таблетки Sandy
            '3': 2,  # Вакцины ELSH
            '4': 4,  # Вакцины Sandy
            '5': 3,  # ПМП город
            '6': 4,  # ПМП пригород
        }

        # Счетчики для каждой папки
        self.folder_counts = {
            '01_Tab_ELSH': 0,
            '02_Tab_Sandy': 0,
            '03_Vac_ELSH': 0,
            '04_Vac_Sandy': 0,
            '05_PMP_City': 0,
            '06_PMP_Suburb': 0
        }

        # Очки для каждой папки
        self.folder_points = {
            '01_Tab_ELSH': 0,
            '02_Tab_Sandy': 0,
            '03_Vac_ELSH': 0,
            '04_Vac_Sandy': 0,
            '05_PMP_City': 0,
            '06_PMP_Suburb': 0
        }

        # Создаем главную папку по умолчанию в Документах
        documents = Path.home() / "Documents"
        self.base_folder = documents / "EMS_Logs"
        self.custom_folder = None
        self.create_folder_structure()

        # Действия и соответствующие им папки
        self.actions = {
            '1': {'name': 'Таблетки ELSH', 'folder': '01_Tab_ELSH', 'points': 1},
            '2': {'name': 'Таблетки Sandy', 'folder': '02_Tab_Sandy', 'points': 2},
            '3': {'name': 'Вакцины ELSH', 'folder': '03_Vac_ELSH', 'points': 2},
            '4': {'name': 'Вакцины Sandy', 'folder': '04_Vac_Sandy', 'points': 4},
            '5': {'name': 'ПМП город', 'folder': '05_PMP_City', 'points': 3},
            '6': {'name': 'ПМП пригород', 'folder': '06_PMP_Suburb', 'points': 4}
        }

        # Соответствие клавиш NumPad действиям
        self.numpad_to_action = {
            97: '1',  # Num1
            98: '2',  # Num2
            99: 'toggle',  # Num3
            100: '3',  # Num4
            101: '4',  # Num5
            102: 'hint',  # Num6
            103: '5',  # Num7
            104: '6',  # Num8
        }

        # Соответствие папок и их индексов
        self.folder_indices = {
            '1': '01_Tab_ELSH',
            '2': '02_Tab_Sandy',
            '3': '03_Vac_ELSH',
            '4': '04_Vac_Sandy',
            '5': '05_PMP_City',
            '6': '06_PMP_Suburb'
        }

        self.setup_gui()
        self.resizer = ResizableApp(self.root, self.update_scale)

    def update_scale(self, scale):
        """Обновление масштаба интерфейса"""
        self.current_scale = scale

        # Обновляем шрифты
        title_size = int(18 * scale)
        self.title_label.config(font=("Times New Roman", title_size, "bold"))

        status_size = int(11 * scale)
        self.status_label.config(font=("Times New Roman", status_size, "bold"))

        counter_size = int(11 * scale)
        for widget in self.counter_frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(font=("Times New Roman", counter_size, "bold"))
        self.counter_label.config(font=("Times New Roman", int(16 * scale), "bold"))

        points_size = int(11 * scale)
        self.points_label.config(font=("Times New Roman", points_size, "bold"))
        self.points_value_label.config(font=("Times New Roman", int(16 * scale), "bold"))

        section_size = int(10 * scale)
        self.actions_label.config(font=("Times New Roman", section_size, "bold"))

        # Обновляем кнопки действий и их подписи
        for item in self.action_items:
            num_label = item['num_label']
            text_label = item['text_label']
            count_label = item['count_label']
            points_display = item['points_display']

            num_label.config(font=("Times New Roman", int(10 * scale), "bold"))
            text_label.config(font=("Times New Roman", int(10 * scale), "bold"))
            count_label.config(font=("Times New Roman", int(10 * scale), "bold"))
            points_display.config(font=("Times New Roman", int(10 * scale)))

        # Обновляем большие кнопки
        self.toggle_btn.config(font=("Times New Roman", int(12 * scale), "bold"))
        self.hints_btn.config(font=("Times New Roman", int(12 * scale), "bold"))
        self.yandex_btn.config(font=("Times New Roman", int(12 * scale), "bold"))
        self.test_btn.config(font=("Times New Roman", int(12 * scale), "bold"))
        self.open_btn.config(font=("Times New Roman", int(12 * scale), "bold"))

        hint_size = int(8 * scale)
        self.toggle_hint_label.config(font=("Times New Roman", hint_size, "italic"))
        self.hints_hint_label.config(font=("Times New Roman", hint_size, "italic"))
        self.yandex_hint_label.config(font=("Times New Roman", hint_size, "italic"))

        last_size = int(9 * scale)
        self.last_action_label.config(font=("Times New Roman", last_size, "italic"))

    def create_folder_structure(self):
        """Создание структуры папок для скриншотов"""
        try:
            folders = [
                '01_Tab_ELSH',
                '02_Tab_Sandy',
                '03_Vac_ELSH',
                '04_Vac_Sandy',
                '05_PMP_City',
                '06_PMP_Suburb',
                '00_Test'
            ]

            for folder in folders:
                folder_path = self.base_folder / folder
                folder_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Папка создана: {folder_path}")

        except Exception as e:
            print(f"❌ Ошибка создания папок: {e}")
            self.base_folder = Path(__file__).parent / "EMS_Logs"
            for folder in folders:
                folder_path = self.base_folder / folder
                folder_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Папка создана (альтернативная): {folder_path}")

    def change_save_folder(self):
        """Изменение папки сохранения"""
        try:
            folder_selected = filedialog.askdirectory(
                title="Выбери папку для сохранения скриншотов",
                initialdir=str(self.base_folder.parent)
            )

            if folder_selected:
                new_folder = Path(folder_selected)

                test_file = new_folder / "test_write.txt"
                try:
                    with open(test_file, 'w', encoding='utf-8') as f:
                        f.write('test')
                    test_file.unlink()

                    self.base_folder = new_folder / "EMS_Logs"
                    self.custom_folder = self.base_folder
                    self.create_folder_structure()

                    folder_display = str(self.base_folder)
                    self.folder_value_label.config(text=folder_display)

                    self.notification.show(f"✅ Папка изменена!", 2)

                except Exception as e:
                    self.notification.show(f"❌ Нет прав на запись в эту папку", 2, is_error=True)

        except Exception as e:
            self.notification.show(f"❌ Ошибка: {str(e)}", 2, is_error=True)

    def reset_folder(self):
        """Сброс папки на стандартную (Документы)"""
        documents = Path.home() / "Documents"
        self.base_folder = documents / "EMS_Logs"
        self.custom_folder = None
        self.create_folder_structure()
        folder_display = str(self.base_folder)
        self.folder_value_label.config(text=folder_display)
        self.notification.show(f"✅ Папка сброшена на стандартную", 2)

    def toggle_logging(self):
        self.running = not self.running
        status = "ВКЛЮЧЕНО" if self.running else "ВЫКЛЮЧЕНО"
        bg_color = "#C8E6C9" if self.running else "#FFCDD2"

        print(f"🔄 Логирование {status}")

        self.status_label.config(
            text=f"{'🟢' if self.running else '🔴'} ЛОГИРОВАНИЕ {status}!",
            fg="#2E7D32" if self.running else "#B71C1C",
            bg=bg_color
        )

        self.toggle_btn.config(
            text=f"{'🔴' if self.running else '🟢'}",
            bg="#F44336" if self.running else "#4CAF50"
        )

        self.hint_window.update_status(self.running)
        self.notification.show(f"Логирование {status}!", 1)

    def toggle_hints(self):
        self.hint_window.toggle(self.running)

    def show_yandex_auth_dialog(self):
        """Показать диалог авторизации Яндекс.Диска"""
        if self.yandex_uploader.authenticated:
            self.show_yandex_upload_dialog()
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Авторизация Яндекс.Диск")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Заголовок
        tk.Label(
            dialog,
            text="📦 Подключение Яндекс.Диска",
            font=("Times New Roman", 14, "bold"),
            bg="#F9A825",
            fg="white",
            pady=10
        ).pack(fill=tk.X)

        # Фрейм с инструкцией
        frame = tk.Frame(dialog, padx=20, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # ClientID
        tk.Label(frame, text="ClientID (уже введен):", font=("Times New Roman", 10, "bold")).pack(anchor=tk.W)
        client_id_label = tk.Label(frame, text=self.yandex_uploader.client_id,
                                   font=("Times New Roman", 10), fg="#2E7D32")
        client_id_label.pack(anchor=tk.W, pady=2)

        # ClientSecret
        tk.Label(frame, text="ClientSecret:", font=("Times New Roman", 10, "bold")).pack(anchor=tk.W, pady=(10, 0))
        client_secret_entry = tk.Entry(frame, font=("Times New Roman", 10), width=50)
        add_context_menu(client_secret_entry)
        client_secret_entry.pack(fill=tk.X, pady=2)

        # Кнопка получения ссылки
        def get_auth_url():
            client_secret = client_secret_entry.get().strip()
            if not client_secret:
                self.notification.show("❌ Введите ClientSecret", 2, is_error=True)
                return
            self.yandex_uploader.client_secret = client_secret
            url = self.yandex_uploader.get_auth_url()

            dialog.clipboard_clear()
            dialog.clipboard_append(url)
            webbrowser.open(url)

            self.notification.show("🔗 Ссылка открыта в браузере и скопирована!", 2)

        tk.Button(
            frame,
            text="🔗 Открыть ссылку для авторизации",
            font=("Times New Roman", 10, "bold"),
            bg="#F9A825",
            fg="white",
            padx=10,
            pady=8,
            command=get_auth_url
        ).pack(pady=10, fill=tk.X)

        tk.Label(
            frame,
            text="Шаг 2: Перейди по ссылке, разреши доступ и скопируй код",
            font=("Times New Roman", 11, "bold"),
            anchor=tk.W
        ).pack(fill=tk.X, pady=5)

        # Код подтверждения
        tk.Label(frame, text="Код подтверждения:", font=("Times New Roman", 10, "bold")).pack(anchor=tk.W, pady=(10, 0))
        code_entry = tk.Entry(frame, font=("Times New Roman", 10), width=50)
        add_context_menu(code_entry)
        code_entry.pack(fill=tk.X, pady=2)

        # Кнопка авторизации
        def authenticate():
            code = code_entry.get().strip()
            if not code:
                self.notification.show("❌ Введите код подтверждения", 2, is_error=True)
                return

            success, result = self.yandex_uploader.exchange_code_for_token(code)
            if success:
                if self.yandex_uploader.save_token(result):
                    self.notification.show("✅ Яндекс.Диск подключен!", 2)
                    dialog.destroy()
                    self.show_yandex_upload_dialog()
                else:
                    self.notification.show("❌ Не удалось сохранить токен", 3, is_error=True)
            else:
                self.notification.show(f"❌ {result}", 3, is_error=True)

        tk.Button(
            frame,
            text="✅ Подключить",
            font=("Times New Roman", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=8,
            command=authenticate
        ).pack(pady=15, fill=tk.X)

        # Кнопка отмены
        tk.Button(
            frame,
            text="Отмена",
            font=("Times New Roman", 10),
            bg="#757575",
            fg="white",
            padx=20,
            pady=5,
            command=dialog.destroy
        ).pack()

    def show_yandex_upload_dialog(self):
        """Показать диалог выбора папок для загрузки в Яндекс.Диск"""
        if not self.yandex_uploader.authenticated:
            self.show_yandex_auth_dialog()
            return

        # Создаем диалоговое окно
        dialog = tk.Toplevel(self.root)
        dialog.title("Выгрузка в Яндекс.Диск")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Заголовок
        tk.Label(
            dialog,
            text="📦 Выберите папки для загрузки",
            font=("Times New Roman", 14, "bold"),
            bg="#F9A825",
            fg="white",
            pady=10
        ).pack(fill=tk.X)

        # Фрейм для списка папок
        list_frame = tk.Frame(dialog, padx=20, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            list_frame,
            text="Доступные папки:",
            font=("Times New Roman", 11, "bold")
        ).pack(anchor=tk.W)

        # Переменные для чекбоксов
        self.folder_vars = {}

        folder_names = {
            '01_Tab_ELSH': 'Таблетки ELSH',
            '02_Tab_Sandy': 'Таблетки Sandy',
            '03_Vac_ELSH': 'Вакцины ELSH',
            '04_Vac_Sandy': 'Вакцины Sandy',
            '05_PMP_City': 'ПМП город',
            '06_PMP_Suburb': 'ПМП пригород'
        }

        for folder_key, folder_name in folder_names.items():
            count = self.folder_counts.get(folder_key, 0)
            var = tk.BooleanVar()
            cb = tk.Checkbutton(
                list_frame,
                text=f"{folder_name} ({count} файлов)",
                variable=var,
                font=("Times New Roman", 10)
            )
            cb.pack(anchor=tk.W, pady=2)
            self.folder_vars[folder_key] = var

        # Чекбокс для создания папки с датой
        date_frame = tk.Frame(list_frame, pady=10)
        date_frame.pack(fill=tk.X)

        self.date_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            date_frame,
            text="Создать отдельную папку с датой",
            variable=self.date_var,
            font=("Times New Roman", 10, "bold")
        ).pack(anchor=tk.W)

        # Прогресс-бар
        self.upload_progress = ttk.Progressbar(dialog, length=450, mode='determinate')
        self.upload_progress.pack(pady=10)

        self.progress_label = tk.Label(
            dialog,
            text="",
            font=("Times New Roman", 9),
            fg="#666"
        )
        self.progress_label.pack()

        # Кнопки
        button_frame = tk.Frame(dialog, pady=15)
        button_frame.pack(fill=tk.X)

        tk.Button(
            button_frame,
            text="📦 Загрузить выбранные",
            font=("Times New Roman", 11, "bold"),
            bg="#F9A825",
            fg="white",
            width=20,
            height=2,
            cursor="hand2",
            command=lambda: self.upload_selected_folders(dialog)
        ).pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

        tk.Button(
            button_frame,
            text="📦 Загрузить все",
            font=("Times New Roman", 11, "bold"),
            bg="#F9A825",
            fg="white",
            width=20,
            height=2,
            cursor="hand2",
            command=lambda: self.upload_all_folders(dialog)
        ).pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

        # Отдельная строка для кнопки отмены
        cancel_frame = tk.Frame(dialog, pady=5)
        cancel_frame.pack(fill=tk.X)

        tk.Button(
            cancel_frame,
            text="Отмена",
            font=("Times New Roman", 10),
            bg="#757575",
            fg="white",
            width=10,
            height=1,
            cursor="hand2",
            command=dialog.destroy
        ).pack()

    def upload_selected_folders(self, dialog):
        """Загрузить выбранные папки"""
        selected = [key for key, var in self.folder_vars.items() if var.get()]

        if not selected:
            self.notification.show("❌ Выберите хотя бы одну папку", 2, is_error=True)
            return

        # Запускаем загрузку в отдельном потоке
        thread = threading.Thread(
            target=self.upload_folders_thread,
            args=(selected, dialog)
        )
        thread.daemon = True
        thread.start()

    def upload_all_folders(self, dialog):
        """Загрузить все папки"""
        selected = list(self.folder_vars.keys())

        # Запускаем загрузку в отдельном потоке
        thread = threading.Thread(
            target=self.upload_folders_thread,
            args=(selected, dialog)
        )
        thread.daemon = True
        thread.start()

    def upload_folders_thread(self, folder_keys, dialog):
        """Поток для загрузки папок"""
        try:
            total_files = 0
            files_to_upload = []

            # Подсчитываем общее количество файлов
            for folder_key in folder_keys:
                folder_path = self.base_folder / folder_key
                if folder_path.exists():
                    files = list(folder_path.glob('*.png'))
                    total_files += len(files)
                    files_to_upload.extend([(folder_key, f) for f in files])

            if total_files == 0:
                self.root.after(0, lambda: self.notification.show("❌ Нет файлов для загрузки", 2, is_error=True))
                self.root.after(0, dialog.destroy)
                return

            # Создаем корневую папку на Яндекс.Диске
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            root_folder_name = f"EMS_Logs_{date_str}" if self.date_var.get() else "EMS_Logs"
            root_folder_path = f"/{root_folder_name}"

            print(f"📁 Проверяю корневую папку: {root_folder_path}")

            # Проверяем и создаем корневую папку
            if not self.yandex_uploader.ensure_folder_exists(root_folder_path):
                error_msg = f"❌ Не удалось создать корневую папку {root_folder_name}"
                print(error_msg)
                self.root.after(0, lambda: self.notification.show(error_msg, 3, is_error=True))
                self.root.after(0, dialog.destroy)
                return

            # Загружаем файлы
            uploaded = 0
            failed = 0

            for folder_key, file_path in files_to_upload:
                # Обновляем прогресс
                progress = int((uploaded + failed) / total_files * 100)
                self.root.after(0, lambda p=progress: self.upload_progress.configure(value=p))
                self.root.after(0, lambda u=uploaded, f=failed, t=total_files:
                self.progress_label.configure(text=f"Загружено: {u}, Ошибок: {f} из {t}"))

                # Создаем папку для этого типа
                folder_name = folder_key
                remote_folder = f"{root_folder_path}/{folder_name}"

                # Проверяем и создаем папку
                if not self.yandex_uploader.ensure_folder_exists(remote_folder):
                    print(f"❌ Не удалось создать папку {remote_folder}")
                    failed += 1
                    continue

                # Загружаем файл
                remote_path = f"{remote_folder}/{file_path.name}"
                if self.yandex_uploader.upload_file(str(file_path), remote_path):
                    uploaded += 1
                else:
                    failed += 1

                time.sleep(0.1)

            # Финальное обновление
            self.root.after(0, lambda: self.upload_progress.configure(value=100))
            self.root.after(0, lambda u=uploaded, f=failed:
            self.progress_label.configure(text=f"✅ Загружено: {u}, Ошибок: {f}"))

            self.root.after(2000, lambda: self.notification.show(f"✅ Загружено {uploaded} файлов!", 2))
            self.root.after(2500, dialog.destroy)

        except Exception as e:
            error_msg = f"❌ Ошибка: {str(e)}"
            print(error_msg)
            self.root.after(0, lambda: self.notification.show(error_msg, 3, is_error=True))
            self.root.after(0, dialog.destroy)

    def upload_to_yandex_by_index(self, action_num):
        """Загрузка конкретной папки по индексу"""
        if not self.yandex_uploader.authenticated:
            self.show_yandex_auth_dialog()
            return

        folder_key = self.folder_indices.get(action_num)
        if not folder_key:
            self.notification.show("❌ Папка не найдена", 2, is_error=True)
            return

        folder_path = self.base_folder / folder_key
        if not folder_path.exists():
            self.notification.show("❌ Папка не существует", 2, is_error=True)
            return

        files = list(folder_path.glob('*.png'))
        if not files:
            self.notification.show(f"❌ В папке нет файлов", 2, is_error=True)
            return

        # Загружаем в отдельном потоке
        thread = threading.Thread(
            target=self.upload_single_folder_thread,
            args=(folder_key, files)
        )
        thread.daemon = True
        thread.start()

    def upload_single_folder_thread(self, folder_key, files):
        """Поток для загрузки одной папки"""
        try:
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            root_folder_name = f"EMS_Logs_{date_str}"
            root_folder_path = f"/{root_folder_name}"

            # Создаем корневую папку
            if not self.yandex_uploader.ensure_folder_exists(root_folder_path):
                self.root.after(0,
                                lambda: self.notification.show("❌ Не удалось создать корневую папку", 2, is_error=True))
                return

            # Создаем папку для типа
            folder_name = folder_key
            remote_folder = f"{root_folder_path}/{folder_name}"

            if not self.yandex_uploader.ensure_folder_exists(remote_folder):
                self.root.after(0, lambda: self.notification.show(f"❌ Не удалось создать папку {folder_name}", 2,
                                                                  is_error=True))
                return

            uploaded = 0
            failed = 0

            for file_path in files:
                remote_path = f"{remote_folder}/{file_path.name}"
                if self.yandex_uploader.upload_file(str(file_path), remote_path):
                    uploaded += 1
                else:
                    failed += 1

            self.root.after(0, lambda u=uploaded, f=failed:
            self.notification.show(f"✅ Загружено: {u}, Ошибок: {f}", 3))

        except Exception as e:
            self.root.after(0, lambda: self.notification.show(f"❌ Ошибка: {str(e)}", 3, is_error=True))

    def on_key_press(self, key):
        try:
            if key == pynput_keyboard.Key.alt_l or key == pynput_keyboard.Key.alt_r:
                self.alt_pressed = True
                return

            if hasattr(key, 'vk') and key.vk in self.numpad_to_action:
                action = self.numpad_to_action[key.vk]

                num_key = {
                    97: 'Num1', 98: 'Num2', 99: 'Num3',
                    100: 'Num4', 101: 'Num5', 102: 'Num6',
                    103: 'Num7', 104: 'Num8'
                }.get(key.vk, f'Num{key.vk - 96}')

                if action == 'toggle':
                    if self.alt_pressed:
                        print(f"🎯 Нажата Alt+{num_key} -> переключение режима")
                        self.root.after(0, self.toggle_logging)
                    else:
                        print(f"⚠️ Для переключения режима используй Alt+Num3")
                        self.root.after(0, lambda: self.notification.show(
                            "⚠️ Для переключения используй Alt+Num3", 1, is_error=True
                        ))

                elif action == 'hint':
                    if self.alt_pressed:
                        print(f"🎯 Нажата Alt+{num_key} -> показать диалог Яндекс.Диска")
                        self.root.after(0, self.show_yandex_auth_dialog)
                    else:
                        print(f"🎯 Нажата {num_key} -> показать/скрыть подсказки")
                        self.root.after(0, self.toggle_hints)

                else:
                    if self.alt_pressed:
                        print(f"🎯 Нажата Alt+{num_key} -> загрузка папки {action}")
                        self.root.after(0, lambda a=action: self.upload_to_yandex_by_index(a))
                    else:
                        if not self.running:
                            print(f"⚠️ Логирование выключено, действие {action} проигнорировано")
                            return

                        print(f"🎯 Нажата {num_key} -> действие {action}")
                        thread = threading.Thread(target=self.take_screenshot_with_action, args=(action,))
                        thread.daemon = True
                        thread.start()

        except Exception as e:
            print(f"❌ Ошибка при обработке клавиши: {e}")

    def on_key_release(self, key):
        try:
            if key == pynput_keyboard.Key.alt_l or key == pynput_keyboard.Key.alt_r:
                self.alt_pressed = False
        except Exception as e:
            print(f"❌ Ошибка: {e}")

    def start_keyboard_listener(self):
        try:
            self.listener = pynput_keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.listener.start()
            print("✅ Слушатель клавиатуры запущен")
        except Exception as e:
            print(f"❌ Ошибка запуска слушателя: {e}")
            self.notification.show("⚠️ Ошибка запуска слушателя клавиатуры", 2, is_error=True)

    def create_styled_button(self, parent, text, bg_color, command, width=3, height=1):
        """Создание стилизованной кнопки"""
        btn = tk.Button(
            parent,
            text=text,
            font=("Times New Roman", 10, "bold"),
            bg=bg_color,
            fg="white",
            width=width,
            height=height,
            cursor="hand2",
            relief=tk.FLAT,
            bd=0,
            command=command
        )

        def on_enter(e):
            btn['background'] = self.lighten_color(bg_color)

        def on_leave(e):
            btn['background'] = bg_color

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        return btn

    def create_large_button(self, parent, icon, text, bg_color, command):
        """Создание увеличенной кнопки с иконкой и текстом"""
        frame = tk.Frame(parent, bg=bg_color, relief=tk.FLAT, bd=2)

        btn = tk.Button(
            frame,
            text=f"{icon}\n{text}",
            font=("Times New Roman", 11, "bold"),
            bg=bg_color,
            fg="white",
            width=8,
            height=2,
            cursor="hand2",
            relief=tk.FLAT,
            bd=0,
            command=command
        )

        def on_enter(e):
            btn['background'] = self.lighten_color(bg_color)
            frame['background'] = self.lighten_color(bg_color)

        def on_leave(e):
            btn['background'] = bg_color
            frame['background'] = bg_color

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.pack(expand=True, fill=tk.BOTH)

        return frame

    def lighten_color(self, color):
        """Осветление цвета для эффекта наведения"""
        light_colors = {
            "#4CAF50": "#66BB6A",
            "#2196F3": "#42A5F5",
            "#FF9800": "#FFA726",
            "#F44336": "#EF5350",
            "#3498DB": "#5DADE2",
            "#9C27B0": "#AB47BC",
            "#757575": "#9E9E9E",
            "#F9A825": "#FBC02D",
            "#E74C3C": "#EF5350"
        }
        return light_colors.get(color, color)

    def update_folder_counters(self):
        """Обновление счетчиков для каждой папки и баллов"""
        self.total_points = 0

        for item in self.action_items:
            folder = item['folder']
            count = self.folder_counts.get(folder, 0)
            points = self.folder_points.get(folder, 0)

            # Форматируем с фиксированной шириной для выравнивания
            item['count_label'].config(text=f"📸 {count:3d}")
            item['points_display'].config(text=f"🏆 {points:3d}")

            self.total_points += points

        # Обновляем общий счетчик баллов
        self.points_value_label.config(text=str(self.total_points))

    def take_screenshot_with_action(self, action_num):
        print(f"\n--- Начало создания скриншота для действия {action_num} ---")

        action = self.actions.get(action_num)
        if not action:
            print(f"❌ Действие {action_num} не найдено")
            return

        try:
            self.root.after(0, lambda: self.status_label.config(
                text=f"📸 Делаю скриншот: {action['name']}...",
                fg="#FF9800"
            ))

            print(f"1. Действие: {action['name']}")
            time.sleep(0.2)

            screenshot = ImageGrab.grab()
            print(f"2. Скриншот сделан, размер: {screenshot.size}")

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            short_name = action['name'].replace(' ', '_')
            filename = f"{timestamp}_{short_name}.png"

            folder_path = self.base_folder / action['folder']
            filepath = folder_path / filename
            print(f"3. Путь: {filepath}")

            screenshot.save(filepath, "PNG", quality=95)
            print(f"4. Файл сохранен")

            # Увеличиваем общий счетчик
            self.screenshots_taken += 1

            # Увеличиваем счетчик и баллы для конкретной папки
            folder = action['folder']
            points = action['points']

            self.folder_counts[folder] = self.folder_counts.get(folder, 0) + 1
            self.folder_points[folder] = self.folder_points.get(folder, 0) + points

            print(f"5. Общий счетчик: {self.screenshots_taken}")
            print(f"6. Счетчик папки {folder}: {self.folder_counts[folder]}")
            print(f"7. Баллы за действие: +{points}")

            # Обновляем интерфейс
            self.root.after(0, self.update_ui_after_screenshot, action['name'], filepath)
            self.root.after(0, self.update_folder_counters)
            self.root.after(0, lambda: self.notification.show(f"✅ +{points} баллов! {action['name']}", 2))

            print("--- Скриншот готов ---\n")

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.root.after(0, lambda: self.notification.show(f"❌ Ошибка: {str(e)}", 2, is_error=True))

    def update_ui_after_screenshot(self, action_name, filepath):
        """Обновление интерфейса после скриншота"""
        self.counter_label.config(text=str(self.screenshots_taken))

        now = datetime.datetime.now().strftime('%H:%M:%S')
        self.last_action_label.config(
            text=f"Последнее действие: {action_name} ({now})"
        )

        self.status_label.config(
            text=f"✅ Скриншот сохранен: {filepath.name}",
            fg="#4CAF50",
            bg="#C8E6C9"
        )

    def open_folder(self):
        """Открыть папку со скриншотами"""
        try:
            if os.name == 'nt':
                os.startfile(self.base_folder)
            else:
                import subprocess
                subprocess.run(['open', self.base_folder])
        except Exception as e:
            self.notification.show("❌ Ошибка открытия папки", 2, is_error=True)

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("EMS Logger from LAPESHA")
        self.root.geometry("550x650")
        self.root.minsize(500, 600)
        self.root.resizable(True, True)

        # Главный контейнер
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Контейнер для левой части
        left_container = tk.Frame(main_container)
        left_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Заголовок
        title_frame = tk.Frame(left_container, bg="#2E7D32", height=50)
        title_frame.pack(fill=tk.X, pady=(0, 5))
        title_frame.pack_propagate(False)

        self.title_label = tk.Label(
            title_frame,
            text="🚑 EMS ЛОГГЕР от ЛЯПЕША",
            font=("Times New Roman", 16, "bold"),
            bg="#2E7D32",
            fg="white"
        )
        self.title_label.pack(expand=True)

        # Информация о папке
        info_frame = tk.Frame(left_container, bg="#E8F5E8", relief=tk.GROOVE, bd=1)
        info_frame.pack(fill=tk.X, pady=2)

        info_header = tk.Frame(info_frame, bg="#E8F5E8")
        info_header.pack(fill=tk.X, padx=5, pady=(2, 0))

        change_btn = self.create_styled_button(
            info_header,
            "📂",
            "#757575",
            self.change_save_folder,
            width=2,
            height=1
        )
        change_btn.pack(side=tk.LEFT, padx=1)

        reset_btn = self.create_styled_button(
            info_header,
            "↺",
            "#757575",
            self.reset_folder,
            width=2,
            height=1
        )
        reset_btn.pack(side=tk.LEFT, padx=1)

        tk.Label(
            info_header,
            text="📁 Папка сохранения:",
            font=("Times New Roman", 9, "bold"),
            bg="#E8F5E8"
        ).pack(side=tk.LEFT, padx=(5, 0))

        # Значение пути
        folder_display = str(self.base_folder)
        self.folder_value_label = tk.Label(
            info_header,
            text=folder_display,
            font=("Times New Roman", 8, "bold"),
            bg="#E8F5E8",
            fg="#2E7D32",
            anchor=tk.W
        )
        self.folder_value_label.pack(side=tk.LEFT, padx=(5, 5))

        # Статус
        status_frame = tk.Frame(left_container, bg="#C8E6C9" if self.running else "#FFCDD2", relief=tk.SUNKEN, bd=1)
        status_frame.pack(fill=tk.X, pady=2)

        self.status_label = tk.Label(
            status_frame,
            text="🟢 ЛОГИРОВАНИЕ ВКЛЮЧЕНО!",
            font=("Times New Roman", 11, "bold"),
            bg="#C8E6C9",
            fg="#2E7D32"
        )
        self.status_label.pack(pady=3)

        # Счетчики в одной строке
        counters_row = tk.Frame(left_container)
        counters_row.pack(fill=tk.X, pady=2)

        points_frame = tk.Frame(counters_row, bg="white", relief=tk.RAISED, bd=1)
        points_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 1))

        self.points_label = tk.Label(
            points_frame,
            text="🏆 БАЛЛЫ:",
            font=("Times New Roman", 10, "bold"),
            bg="white"
        )
        self.points_label.pack(side=tk.LEFT, padx=3, pady=3)

        self.points_value_label = tk.Label(
            points_frame,
            text="0",
            font=("Times New Roman", 14, "bold"),
            bg="white",
            fg="#FF9800"
        )
        self.points_value_label.pack(side=tk.LEFT, padx=3)

        self.counter_frame = tk.Frame(counters_row, bg="white", relief=tk.RAISED, bd=1)
        self.counter_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(1, 0))

        tk.Label(
            self.counter_frame,
            text="📸 ВСЕГО:",
            font=("Times New Roman", 10, "bold"),
            bg="white"
        ).pack(side=tk.LEFT, padx=3, pady=3)

        self.counter_label = tk.Label(
            self.counter_frame,
            text="0",
            font=("Times New Roman", 14, "bold"),
            bg="white",
            fg="#2E7D32"
        )
        self.counter_label.pack(side=tk.LEFT, padx=3)

        # Кнопки действий
        actions_frame = tk.Frame(left_container)
        actions_frame.pack(fill=tk.BOTH, expand=True, pady=3)

        # Заголовок действий с иконкой мышки
        actions_header = tk.Frame(actions_frame)
        actions_header.pack(anchor=tk.W, fill=tk.X, pady=1)

        tk.Label(
            actions_header,
            text="🖱️",
            font=("Times New Roman", 11),
            fg="#333"
        ).pack(side=tk.LEFT, padx=(0, 2))

        self.actions_label = tk.Label(
            actions_header,
            text="ДЕЙСТВИЯ:",
            font=("Times New Roman", 10, "bold")
        )
        self.actions_label.pack(side=tk.LEFT)

        buttons_container = tk.Frame(actions_frame)
        buttons_container.pack(anchor=tk.W, fill=tk.X)

        self.action_items = []

        button_configs = [
            ("Num1", "Таблетки ELSH", "#4CAF50", '1', "01_Tab_ELSH"),
            ("Num2", "Таблетки Sandy", "#4CAF50", '2', "02_Tab_Sandy"),
            ("Num4", "Вакцины ELSH", "#2196F3", '3', "03_Vac_ELSH"),
            ("Num5", "Вакцины Sandy", "#2196F3", '4', "04_Vac_Sandy"),
            ("Num7", "ПМП город", "#FF9800", '5', "05_PMP_City"),
            ("Num8", "ПМП пригород", "#FF9800", '6', "06_PMP_Suburb"),
        ]

        for key, text, color, action, folder in button_configs:
            row_frame = tk.Frame(buttons_container)
            row_frame.pack(anchor=tk.W, fill=tk.X, pady=1)

            controls_frame = tk.Frame(row_frame)
            controls_frame.pack(anchor=tk.W)

            # Номер кнопки
            num_label = tk.Label(
                controls_frame,
                text=f"[{key}]",
                font=("Times New Roman", 10, "bold"),
                fg=color,
                width=5,
                anchor=tk.W
            )
            num_label.pack(side=tk.LEFT)

            # Текст действия
            text_label = tk.Label(
                controls_frame,
                text=f"- {text}",
                font=("Times New Roman", 10, "bold"),
                fg=color,
                width=18,
                anchor=tk.W
            )
            text_label.pack(side=tk.LEFT)

            # Счетчик скриншотов
            count_label = tk.Label(
                controls_frame,
                text="📸   0",
                font=("Times New Roman", 10, "bold"),
                fg="#666",
                width=7,
                anchor=tk.W
            )
            count_label.pack(side=tk.LEFT, padx=(3, 1))

            # Счетчик баллов
            points_display = tk.Label(
                controls_frame,
                text="🏆   0",
                font=("Times New Roman", 10),
                fg="#FF9800",
                width=7,
                anchor=tk.W
            )
            points_display.pack(side=tk.LEFT)

            self.action_items.append({
                'folder': folder,
                'num_label': num_label,
                'text_label': text_label,
                'count_label': count_label,
                'points_display': points_display
            })

        # Большие кнопки управления
        big_buttons_frame = tk.Frame(left_container)
        big_buttons_frame.pack(fill=tk.X, pady=10)

        # Создаем контейнер для 5 больших кнопок
        big_buttons_container = tk.Frame(big_buttons_frame)
        big_buttons_container.pack()

        # Кнопка вкл/выкл
        toggle_frame = self.create_large_button(
            big_buttons_container,
            "🔴🟢",
            "Вкл/Выкл",
            "#F44336" if self.running else "#4CAF50",
            self.toggle_logging
        )
        toggle_frame.pack(side=tk.LEFT, padx=3)
        self.toggle_btn = toggle_frame.winfo_children()[0]

        # Кнопка подсказок
        hints_frame = self.create_large_button(
            big_buttons_container,
            "📋",
            "Подсказки",
            "#3498DB",
            self.toggle_hints
        )
        hints_frame.pack(side=tk.LEFT, padx=3)
        self.hints_btn = hints_frame.winfo_children()[0]

        # Кнопка Яндекс.Диск
        yandex_frame = self.create_large_button(
            big_buttons_container,
            "📦",
            "Яндекс",
            "#F9A825",
            self.show_yandex_auth_dialog
        )
        yandex_frame.pack(side=tk.LEFT, padx=3)
        self.yandex_btn = yandex_frame.winfo_children()[0]

        # Кнопка теста
        test_frame = self.create_large_button(
            big_buttons_container,
            "🔧",
            "Тест",
            "#9C27B0",
            self.test_screenshot
        )
        test_frame.pack(side=tk.LEFT, padx=3)
        self.test_btn = test_frame.winfo_children()[0]

        # Кнопка открыть
        open_frame = self.create_large_button(
            big_buttons_container,
            "📂",
            "Открыть",
            "#2196F3",
            self.open_folder
        )
        open_frame.pack(side=tk.LEFT, padx=3)
        self.open_btn = open_frame.winfo_children()[0]

        # Подписи с горячими клавишами
        hints_row = tk.Frame(left_container)
        hints_row.pack(fill=tk.X, pady=2)

        hint_texts = ["Alt+3", "Num6", "Alt+6", "", ""]
        for i, text in enumerate(hint_texts):
            label = tk.Label(
                hints_row,
                text=text,
                font=("Times New Roman", 7, "italic"),
                fg="#666",
                width=9
            )
            label.pack(side=tk.LEFT, padx=5, expand=True)

        # Последнее действие
        self.last_action_label = tk.Label(
            left_container,
            text="Последнее действие: —",
            font=("Times New Roman", 9, "italic"),
            fg="#666"
        )
        self.last_action_label.pack(anchor=tk.W, pady=5)

        self.start_keyboard_listener()

    def test_screenshot(self):
        try:
            print("🔍 Тест: начинаю создание тестового скриншота...")

            test_folder = self.base_folder / "00_Test"
            test_folder.mkdir(parents=True, exist_ok=True)

            screenshot = ImageGrab.grab()
            print("✅ Тест: скриншот сделан")

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            test_file = test_folder / f"test_{timestamp}.png"
            screenshot.save(test_file, "PNG")
            print(f"✅ Тест: скриншот сохранен в {test_file}")

            self.notification.show("✅ Тест успешен!", 2)

        except Exception as e:
            error_msg = f"❌ Ошибка в тесте: {str(e)}"
            print(error_msg)
            self.notification.show(f"❌ Ошибка: {str(e)}", 2, is_error=True)

    def run(self):
        """Запуск программы"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        """Обработка закрытия окна"""
        if self.hint_window:
            self.hint_window.hide()
        if self.listener:
            self.listener.stop()
        self.root.destroy()


def main():
    """Главная функция"""
    print("=" * 70)
    print("🚑 ЗАПУСК EMS ЛОГГЕРА ОТ ЛЯПЕША")
    print("=" * 70)
    print("\n✅ Программа ЗАПУЩЕНА!")
    print("📁 Скриншоты сохраняются в: Documents\\EMS_Logs\\")
    print("\n💰 СИСТЕМА БАЛЛОВ:")
    print("   Num1 → Таблетки ELSH → 1 балл")
    print("   Num2 → Таблетки Sandy → 2 балла")
    print("   Num4 → Вакцины ELSH → 2 балла")
    print("   Num5 → Вакцины Sandy → 4 балла")
    print("   Num7 → ПМП город → 3 балла")
    print("   Num8 → ПМП пригород → 4 балла")
    print("\n📦 ЯНДЕКС.ДИСК:")
    print("   📦 Кнопка → Подключить и выбрать папки")
    print("   Alt+Num1-6 → Загрузить конкретную папку")
    print("   Alt+Num6 → Подключить/выбрать папки")
    print("=" * 70)
    print("\n💡 Убедись, что Num Lock включен!")
    print("💡 ClientID уже введен, нужно только ClientSecret")
    print("💡 Можно вставлять текст через Ctrl+V или правую кнопку мыши")
    print("=" * 70)

    app = MedicalActionLogger()
    app.run()


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()