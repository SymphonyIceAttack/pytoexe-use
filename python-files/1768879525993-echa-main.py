import sys
import os
import sqlite3
import threading
import time
import math
import wave
import struct
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QListWidget, QLineEdit, 
                             QLabel, QMessageBox, QSpinBox, QComboBox, QCheckBox,
                             QGroupBox, QFormLayout, QTabWidget, QScrollArea, QFileDialog)
from PyQt5.QtCore import QTimer, QSettings
from PyQt5.QtMultimedia import QSound
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ==================== НАСТРОЙКИ ====================
YOUTUBE_API_KEY = "AIzaSyDtF1i4GWo4Ty9eYB9xnenGskFgFH7garw"  # ЗАМЕНИТЕ НА РЕАЛЬНЫЙ КЛЮЧ

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== БАЗА ДАННЫХ ====================
def init_db():
    """Создаёт базу данных, если её нет"""
    conn = sqlite3.connect('youtube_channels.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            chat_id INTEGER,
            channel_id TEXT,
            channel_name TEXT,
            last_video_id TEXT,
            PRIMARY KEY (chat_id, channel_id)
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")

def add_channel(chat_id, channel_id, channel_name):
    """Добавляет канал в отслеживание"""
    conn = sqlite3.connect('youtube_channels.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO channels (chat_id, channel_id, channel_name, last_video_id) VALUES (?, ?, ?, ?)",
            (chat_id, channel_id, channel_name, "")
        )
        conn.commit()
        logger.info(f"Канал '{channel_name}' (ID: {channel_id}) добавлен")
        return True
    except sqlite3.IntegrityError:
        logger.warning(f"Канал {channel_id} уже отслеживается")
        return False
    finally:
        conn.close()

def get_user_channels(chat_id):
    """Возвращает список каналов пользователя"""
    conn = sqlite3.connect('youtube_channels.db')
    cursor = conn.cursor()
    cursor.execute("SELECT channel_id, channel_name FROM channels WHERE chat_id = ?", (chat_id,))
    channels = cursor.fetchall()
    conn.close()
    return channels

def remove_channel(chat_id, channel_id):
    """Удаляет канал из отслеживания"""
    conn = sqlite3.connect('youtube_channels.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM channels WHERE chat_id = ? AND channel_id = ?", (chat_id, channel_id))
    conn.commit()
    conn.close()
    logger.info(f"Канал {channel_id} удалён")

def get_all_channels():
    """Возвращает все каналы для проверки"""
    conn = sqlite3.connect('youtube_channels.db')
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, channel_id, channel_name, last_video_id FROM channels")
    channels = cursor.fetchall()
    conn.close()
    return channels

def update_last_video(chat_id, channel_id, video_id):
    """Обновляет ID последнего видео"""
    conn = sqlite3.connect('youtube_channels.db')
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE channels SET last_video_id = ? WHERE chat_id = ? AND channel_id = ?",
        (video_id, chat_id, channel_id)
    )
    conn.commit()
    conn.close()
    logger.info(f"Обновлён ID последнего видео для канала {channel_id}")

# ==================== YOUTUBE API ====================
def get_channel_id_by_username(youtube, username):
    """Получает ID канала по имени пользователя"""
    try:
        request = youtube.channels().list(part="id", forUsername=username)
        response = request.execute()
        if response["items"]:
            return response["items"][0]["id"]
        return None
    except Exception as e:
        logger.error(f"Ошибка get_channel_id_by_username: {e}")
        return None

def get_latest_video(youtube, channel_id):
    """Получает последнее видео с канала"""
    try:
        request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            order="date",
            maxResults=1,
            type="video"
        )
        response = request.execute()
        if response["items"]:
            video = response["items"][0]
            return {
                "id": video["id"]["videoId"],
                "title": video["snippet"]["title"],
                "url": f"https://www.youtube.com/watch?v={video['id']['videoId']}"
            }
        return None
    except Exception as e:
        logger.error(f"Ошибка get_latest_video: {e}")
        return None

def extract_channel_id(self, input_text):
    """Извлекает ID канала из разных форматов"""
    
    # 1. Прямой ID (например, UC7xAi2uRaJuba47-a6Wawyg)
    if len(input_text) == 24 and input_text.startswith("UC"):
        return input_text
    
    # 2. URL канала (https://www.youtube.com/channel/UC7xAi2uRaJuba47-a6Wawyg)
    if "youtube.com/channel/" in input_text:
        parts = input_text.split("/channel/")
        if len(parts) > 1:
            channel_id = parts[1].split("/")[0]
            if len(channel_id) == 24 and channel_id.startswith("UC"):
                return channel_id
    
    # 3. Username (например, @username или просто username)
    if input_text.startswith("@"):
        username = input_text[1:]
    else:
        username = input_text
    
    # Пытаемся получить ID по username через API
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY, cache_discovery=False)
        request = youtube.channels().list(part="id", forUsername=username)
        response = request.execute()
        
        if response["items"]:
            return response["items"][0]["id"]
    except:
        pass
    
    # Если не получилось, попробуем найти по поиску
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY, cache_discovery=False)
        request = youtube.search().list(
            part="snippet",
            q=username,
            type="channel",
            maxResults=1
        )
        response = request.execute()
        
        if response["items"]:
            return response["items"][0]["id"]["channelId"]
    except:
        pass
    
    return None

# ==================== УПРАВЛЕНИЕ ЗВУКОМ ====================
class SoundNotifier:
    """Управление звуковыми оповещениями"""
    
    def __init__(self, settings_manager):
        self.settings = settings_manager
        self.sound = None
        self.sound_path = None
        self.load_sound()
        
    def load_sound(self):
        """Загружает звуковой файл"""
        try:
            sound_path = self.settings.get_sound_file()
            
            # Проверяем, существует ли файл
            if not os.path.exists(sound_path):
                # Создаём папку sounds и умолчательный файл
                sounds_dir = os.path.join(os.path.dirname(__file__), "sounds")
                os.makedirs(sounds_dir, exist_ok=True)
                
                # Создаём простой WAV файл
                self.create_default_sound(sounds_dir)
                sound_path = os.path.join(sounds_dir, "notification.wav")
            
            self.sound_path = sound_path
            self.sound = QSound(sound_path)
            
        except Exception as e:
            logger.error(f"Ошибка загрузки звука: {e}")
            self.sound = None
    
    def create_default_sound(self, sounds_dir):
        """Создаёт простой звуковой файл"""
        filename = os.path.join(sounds_dir, "notification.wav")
        
        # Параметры WAV файла
        sample_rate = 44100
        duration = 0.3
        frequency = 1000
        amplitude = 32767
        
        # Создаём WAV файл
        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            
            # Генерируем синусоиду
            for i in range(int(sample_rate * duration)):
                value = int(amplitude * 0.5 * math.sin(2 * math.pi * frequency * i / sample_rate))
                wav_file.writeframes(struct.pack('h', value))
    
    def play(self):
        """Воспроизводит звук"""
        if self.sound and self.settings.get_sound_enabled():
            try:
                volume = self.settings.get_volume() / 100.0
                self.sound.setVolume(volume)
                self.sound.play()
                logger.info("Звук воспроизведён")
            except Exception as e:
                logger.error(f"Ошибка воспроизведения звука: {e}")
    
    def test(self):
        """Тестовое воспроизведение"""
        self.play()

# ==================== УПРАВЛЕНИЕ НАСТРОЙКАМИ ====================
class SettingsManager:
    """Управление настройками приложения"""
    
    def __init__(self):
        self.settings = QSettings("YouTube Notifier", "Settings")
        
    def get_check_interval(self):
        """Возвращает интервал проверки в минутах"""
        return self.settings.value("check_interval", 10, type=int)
    
    def set_check_interval(self, minutes):
        """Устанавливает интервал проверки"""
        self.settings.setValue("check_interval", minutes)
        
    def get_sound_enabled(self):
        """Возвращает, включены ли звуковые оповещения"""
        return self.settings.value("sound_enabled", True, type=bool)
    
    def set_sound_enabled(self, enabled):
        """Включает/выключает звуковые оповещения"""
        self.settings.setValue("sound_enabled", enabled)
        
    def get_sound_file(self):
        """Возвращает путь к звуковому файлу"""
        default_sound = os.path.join(os.path.dirname(__file__), "sounds", "notification.wav")
        return self.settings.value("sound_file", default_sound, type=str)
    
    def set_sound_file(self, file_path):
        """Устанавливает путь к звуковому файлу"""
        self.settings.setValue("sound_file", file_path)
    
    def get_volume(self):
        """Возвращает громкость (0-100)"""
        return self.settings.value("volume", 80, type=int)
    
    def set_volume(self, volume):
        """Устанавливает громкость"""
        self.settings.setValue("volume", volume)
    
    def get_minimize_to_tray(self):
        """Возвращает, сворачивать ли в трей"""
        return self.settings.value("minimize_to_tray", True, type=bool)
    
    def set_minimize_to_tray(self, enabled):
        """Устанавливает сворачивание в трей"""
        self.settings.setValue("minimize_to_tray", enabled)
    
    def get_auto_start(self):
        """Возвращает, запускаться ли при старте Windows"""
        return self.settings.value("auto_start", False, type=bool)
    
    def set_auto_start(self, enabled):
        """Устанавливает автозапуск"""
        self.settings.setValue("auto_start", enabled)
        self.update_auto_start_registry(enabled)
    
    def update_auto_start_registry(self, enabled):
        """Обновляет автозапуск в реестре Windows"""
        try:
            import winreg
            
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "YouTube Notifier"
            exe_path = os.path.abspath(sys.executable)
            
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            if enabled:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            logger.error(f"Ошибка обновления реестра: {e}")
    
    def get_all_settings(self):
        """Возвращает все настройки"""
        return {
            "check_interval": self.get_check_interval(),
            "sound_enabled": self.get_sound_enabled(),
            "sound_file": self.get_sound_file(),
            "volume": self.get_volume(),
            "minimize_to_tray": self.get_minimize_to_tray(),
            "auto_start": self.get_auto_start(),
        }

# ==================== ГЛАВНОЕ ОКНО ====================
class YouTubeNotifierApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Инициализация менеджеров
        self.settings_manager = SettingsManager()
        self.sound_notifier = SoundNotifier(self.settings_manager)
        
        # Инициализация UI
        self.init_ui()
        
        # Инициализация таймера
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_videos)
        self.timer.start(self.settings_manager.get_check_interval() * 60 * 1000)
        
        # Настройка сворачивания в трей
        self.setup_tray()
        
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle("YouTube Notifier")
        self.setGeometry(100, 100, 600, 500)
        
        # Создаём вкладки
        self.tabs = QTabWidget()
        
        # Вкладка 1: Основная
        main_tab = QWidget()
        self.setup_main_tab(main_tab)
        self.tabs.addTab(main_tab, "Основное")
        
        # Вкладка 2: Настройки
        settings_tab = QWidget()
        self.setup_settings_tab(settings_tab)
        self.tabs.addTab(settings_tab, "Настройки")
        
        # Устанавливаем вкладки как центральный виджет
        self.setCentralWidget(self.tabs)
        
    def setup_main_tab(self, tab):
        """Настройка основной вкладки"""
        layout = QVBoxLayout(tab)
        
        # Добавление канала
        add_layout = QHBoxLayout()
        self.channel_input = QLineEdit()
        self.channel_input.setPlaceholderText("Введите ID канала или URL...")
        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.add_channel)
        add_layout.addWidget(self.channel_input)
        add_layout.addWidget(add_button)
        layout.addLayout(add_layout)
        
        # Список каналов
        layout.addWidget(QLabel("Отслеживаемые каналы:"))
        self.channel_list = QListWidget()
        layout.addWidget(self.channel_list)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        remove_btn = QPushButton("Удалить")
        remove_btn.clicked.connect(self.remove_channel)
        check_btn = QPushButton("Проверить сейчас")
        check_btn.clicked.connect(self.check_videos)
        test_sound_btn = QPushButton("Тест звука")
        test_sound_btn.clicked.connect(self.test_sound)
        btn_layout.addWidget(remove_btn)
        btn_layout.addWidget(check_btn)
        btn_layout.addWidget(test_sound_btn)
        layout.addLayout(btn_layout)
        
        # Статус
        self.status_label = QLabel("Готов к работе")
        layout.addWidget(self.status_label)
        
        self.refresh_list()
        
    def setup_settings_tab(self, tab):
        """Настройка вкладки настроек"""
        layout = QVBoxLayout(tab)
        
        # Группа настроек проверки
        check_group = QGroupBox("Настройки проверки")
        check_layout = QFormLayout()
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1440)  # 1 минута - 24 часа
        self.interval_spin.setValue(self.settings_manager.get_check_interval())
        self.interval_spin.valueChanged.connect(self.on_interval_changed)
        check_layout.addRow("Интервал (минуты):", self.interval_spin)
        
        self.auto_check_cb = QCheckBox("Автоматическая проверка")
        self.auto_check_cb.setChecked(True)
        self.auto_check_cb.stateChanged.connect(self.on_auto_check_changed)
        check_layout.addRow(self.auto_check_cb)
        
        check_group.setLayout(check_layout)
        layout.addWidget(check_group)
        
        # Группа звуковых оповещений
        sound_group = QGroupBox("Звуковые оповещения")
        sound_layout = QFormLayout()
        
        self.sound_enabled_cb = QCheckBox("Включить звуковые оповещения")
        self.sound_enabled_cb.setChecked(self.settings_manager.get_sound_enabled())
        self.sound_enabled_cb.stateChanged.connect(self.on_sound_enabled_changed)
        sound_layout.addRow(self.sound_enabled_cb)
        
        self.volume_spin = QSpinBox()
        self.volume_spin.setRange(0, 100)
        self.volume_spin.setValue(self.settings_manager.get_volume())
        self.volume_spin.valueChanged.connect(self.on_volume_changed)
        sound_layout.addRow("Громкость (%):", self.volume_spin)
        
        self.sound_file_input = QLineEdit()
        self.sound_file_input.setText(self.settings_manager.get_sound_file())
        self.sound_file_input.setReadOnly(True)
        sound_layout.addRow("Файл звука:", self.sound_file_input)
        
        select_sound_btn = QPushButton("Выбрать файл")
        select_sound_btn.clicked.connect(self.select_sound_file)
        sound_layout.addRow(select_sound_btn)
        
        test_sound_btn = QPushButton("Тест звука")
        test_sound_btn.clicked.connect(self.test_sound)
        sound_layout.addRow(test_sound_btn)
        
        sound_group.setLayout(sound_layout)
        layout.addWidget(sound_group)
        
        # Группа общих настроек
        general_group = QGroupBox("Общие настройки")
        general_layout = QFormLayout()
        
        self.minimize_to_tray_cb = QCheckBox("Сворачивать в трей")
        self.minimize_to_tray_cb.setChecked(self.settings_manager.get_minimize_to_tray())
        self.minimize_to_tray_cb.stateChanged.connect(self.on_minimize_to_tray_changed)
        general_layout.addRow(self.minimize_to_tray_cb)
        
        self.auto_start_cb = QCheckBox("Автозапуск при старте Windows")
        self.auto_start_cb.setChecked(self.settings_manager.get_auto_start())
        self.auto_start_cb.stateChanged.connect(self.on_auto_start_changed)
        general_layout.addRow(self.auto_start_cb)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # Кнопки сохранения
        save_btn = QPushButton("Сохранить настройки")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        
    def setup_tray(self):
        """Настройка трей"""
        from PyQt5.QtWidgets import QSystemTrayIcon, QMenu
        from PyQt5.QtGui import QIcon
        
        self.tray_icon = QSystemTrayIcon(self)
        
        # Попытка загрузить иконку
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "icons", "youtube.png")
            if os.path.exists(icon_path):
                self.tray_icon.setIcon(QIcon(icon_path))
            else:
                self.tray_icon.setIcon(QIcon.fromTheme("video-x-generic"))
        except:
            self.tray_icon.setIcon(QIcon.fromTheme("video-x-generic"))
        
        # Меню трея
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Показать")
        show_action.triggered.connect(self.show)
        
        check_action = tray_menu.addAction("Проверить сейчас")
        check_action.triggered.connect(self.check_videos)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("Выход")
        quit_action.triggered.connect(QApplication.quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Сигнал для сворачивания
        self.tray_icon.activated.connect(self.on_tray_activated)
        
    def on_tray_activated(self, reason):
        """Обработка клика по иконке трея"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            
    def closeEvent(self, event):
        """Перехват закрытия окна"""
        if self.settings_manager.get_minimize_to_tray():
            self.hide()
            event.ignore()
        else:
            event.accept()
            
    def on_interval_changed(self, value):
        """Изменение интервала проверки"""
        self.settings_manager.set_check_interval(value)
        self.timer.setInterval(value * 60 * 1000)
        
    def on_auto_check_changed(self, state):
        """Изменение автоматической проверки"""
        if state:
            self.timer.start()
        else:
            self.timer.stop()
            
    def on_sound_enabled_changed(self, state):
        """Изменение включения звука"""
        self.settings_manager.set_sound_enabled(state)
        
    def on_volume_changed(self, value):
        """Изменение громкости"""
        self.settings_manager.set_volume(value)
        
    def on_minimize_to_tray_changed(self, state):
        """Изменение сворачивания в трей"""
        self.settings_manager.set_minimize_to_tray(state)
        
    def on_auto_start_changed(self, state):
        """Изменение автозапуска"""
        self.settings_manager.set_auto_start(state)
        
    def select_sound_file(self):
        """Выбор звукового файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите звуковой файл",
            "",
            "Звуковые файлы (*.wav *.mp3 *.ogg)"
        )
        
        if file_path:
            self.settings_manager.set_sound_file(file_path)
            self.sound_file_input.setText(file_path)
            
    def test_sound(self):
        """Тест звука"""
        self.sound_notifier.play()
        
    def save_settings(self):
        """Сохранение настроек"""
        QMessageBox.information(self, "Сохранение", "Настройки сохранены!")
        
    def extract_channel_id(self, input_text):
        """Извлекает ID канала из разных форматов"""
        
        # 1. Прямой ID (например, UC7xAi2uRaJuba47-a6Wawyg)
        if len(input_text) == 24 and input_text.startswith("UC"):
            return input_text
        
        # 2. URL канала (https://www.youtube.com/channel/UC7xAi2uRaJuba47-a6Wawyg)
        if "youtube.com/channel/" in input_text:
            parts = input_text.split("/channel/")
            if len(parts) > 1:
                channel_id = parts[1].split("/")[0]
                if len(channel_id) == 24 and channel_id.startswith("UC"):
                    return channel_id
        
        # 3. Username (например, @username или просто username)
        if input_text.startswith("@"):
            username = input_text[1:]
        else:
            username = input_text
        
        # Пытаемся получить ID по username через API
        try:
            youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY, cache_discovery=False)
            request = youtube.channels().list(part="id", forUsername=username)
            response = request.execute()
            
            if response["items"]:
                return response["items"][0]["id"]
        except:
            pass
        
        # Если не получилось, попробуем найти по поиску
        try:
            youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY, cache_discovery=False)
            request = youtube.search().list(
                part="snippet",
                q=username,
                type="channel",
                maxResults=1
            )
            response = request.execute()
            
            if response["items"]:
                return response["items"][0]["id"]["channelId"]
        except:
            pass
        
        return None
    
    def add_channel(self):
        """Добавление канала"""
        channel_input = self.channel_input.text().strip()
        
        if not channel_input:
            QMessageBox.warning(self, "Ошибка", "Введите ID канала или URL!")
            return
        
        # Извлекаем ID из разных форматов
        channel_id = self.extract_channel_id(channel_input)
        
        if not channel_id:
            QMessageBox.warning(self, "Ошибка", "Неверный формат канала!")
            return
        
        try:
            youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY, cache_discovery=False)
            
            # Проверяем канал
            request = youtube.channels().list(part="snippet", id=channel_id)
            response = request.execute()
            
            if not response["items"]:
                QMessageBox.warning(self, "Ошибка", "Канал не найден!")
                return
            
            real_name = response["items"][0]["snippet"]["title"]
            
            if add_channel(0, channel_id, real_name):
                QMessageBox.information(self, "Успех", f"Канал '{real_name}' добавлен!")
                self.channel_input.clear()
                self.refresh_list()
            else:
                QMessageBox.warning(self, "Внимание", "Канал уже отслеживается!")
                
        except HttpError as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка YouTube API: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {e}")
            
    def remove_channel(self):
        """Удаление канала"""
        current_item = self.channel_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Ошибка", "Выберите канал для удаления!")
            return
            
        # Извлекаем ID из строки
        text = current_item.text()
        channel_id = text.split("ID: ")[1]
        
        remove_channel(0, channel_id)
        self.refresh_list()
        
    def refresh_list(self):
        """Обновление списка каналов"""
        self.channel_list.clear()
        channels = get_user_channels(0)
        for channel_id, channel_name in channels:
            self.channel_list.addItem(f"{channel_name}\nID: {channel_id}")
            
    def check_videos(self):
        """Проверка новых видео в фоновом потоке"""
        def check():
            try:
                youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY, cache_discovery=False)
                channels = get_all_channels()
                
                new_videos_count = 0
                for chat_id, channel_id, channel_name, last_video_id in channels:
                    latest = get_latest_video(youtube, channel_id)
                    if latest and latest["id"] != last_video_id:
                        update_last_video(chat_id, channel_id, latest["id"])
                        
                        # Показываем системное уведомление
                        from plyer import notification
                        notification.notify(
                            title="Новое видео на YouTube!",
                            message=f"{channel_name}\n{latest['title']}",
                            app_name="YouTube Notifier",
                            timeout=10
                        )
                        
                        # Воспроизводим звук
                        self.sound_notifier.play()
                        new_videos_count += 1
                        
                if new_videos_count > 0:
                    self.status_label.setText(f"Найдено новых видео: {new_videos_count}")
                else:
                    self.status_label.setText("Новых видео нет")
                    
            except Exception as e:
                logger.error(f"Ошибка при проверке видео: {e}")
                self.status_label.setText(f"Ошибка: {e}")
        
        thread = threading.Thread(target=check)
        thread.start()
        self.status_label.setText("Проверка...")
        
        # Обновляем статус через 2 секунды
        QTimer.singleShot(2000, lambda: self.status_label.setText("Готов к работе"))
        
    def test_sound(self):
        """Тест звука"""
        self.sound_notifier.play()

# ==================== ЗАПУСК ====================
def main():
    init_db()
    
    # Создаём папку для звуков, если её нет
    sounds_dir = os.path.join(os.path.dirname(__file__), "sounds")
    os.makedirs(sounds_dir, exist_ok=True)
    
    app = QApplication(sys.argv)
    window = YouTubeNotifierApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()