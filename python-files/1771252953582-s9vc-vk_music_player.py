import sys
import json
import os
import threading
import time
import vk_api
from vk_api.audio import VkAudio
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QListWidget, QListWidgetItem,
                             QLabel, QLineEdit, QMessageBox, QSystemTrayIcon, QMenu,
                             QSlider, QStyle, QFrame)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QUrl, QThread
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.Qt import QShortcut
import keyboard
import requests
from io import BytesIO

class VKAuthThread(QThread):
    """Поток для аутентификации ВКонтакте"""
    auth_complete = pyqtSignal(object)
    auth_error = pyqtSignal(str)
    
    def __init__(self, login, password):
        super().__init__()
        self.login = login
        self.password = password
        
    def run(self):
        try:
            vk_session = vk_api.VkApi(login=self.login, password=self.password)
            vk_session.auth()
            vk = vk_session.get_api()
            vk_audio = VkAudio(vk_session)
            self.auth_complete.emit(vk_audio)
        except Exception as e:
            self.auth_error.emit(str(e))

class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.vk_audio = None
        self.audio_list = []
        self.current_track_index = -1
        self.is_playing = False
        self.hotkeys_enabled = True
        self.init_ui()
        self.init_player()
        self.load_settings()
        self.setup_hotkeys()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("VK Music Player")
        self.setGeometry(300, 300, 600, 500)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Панель авторизации
        auth_frame = QFrame()
        auth_frame.setFrameStyle(QFrame.Box)
        auth_layout = QHBoxLayout(auth_frame)
        
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Телефон или email")
        auth_layout.addWidget(QLabel("Логин:"))
        auth_layout.addWidget(self.login_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        auth_layout.addWidget(QLabel("Пароль:"))
        auth_layout.addWidget(self.password_input)
        
        self.auth_btn = QPushButton("Войти")
        self.auth_btn.clicked.connect(self.login_vk)
        auth_layout.addWidget(self.auth_btn)
        
        layout.addWidget(auth_frame)
        
        # Панель поиска
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск музыки...")
        self.search_btn = QPushButton("Найти")
        self.search_btn.clicked.connect(self.search_music)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)
        
        # Список треков
        self.tracks_list = QListWidget()
        self.tracks_list.itemDoubleClicked.connect(self.play_selected_track)
        layout.addWidget(self.tracks_list)
        
        # Панель управления
        controls_frame = QFrame()
        controls_frame.setFrameStyle(QFrame.Box)
        controls_layout = QHBoxLayout(controls_frame)
        
        # Кнопки управления
        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_btn.clicked.connect(self.toggle_play)
        controls_layout.addWidget(self.play_btn)
        
        self.prev_btn = QPushButton()
        self.prev_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        self.prev_btn.clicked.connect(self.play_previous)
        controls_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton()
        self.next_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipForward))
        self.next_btn.clicked.connect(self.play_next)
        controls_layout.addWidget(self.next_btn)
        
        # Слайдер громкости
        controls_layout.addWidget(QLabel("Громкость:"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.change_volume)
        controls_layout.addWidget(self.volume_slider)
        
        layout.addWidget(controls_frame)
        
        # Информация о текущем треке
        self.current_track_label = QLabel("Не выбран трек")
        layout.addWidget(self.current_track_label)
        
        # Статус горячих клавиш
        self.hotkeys_label = QLabel("Горячие клавиши: ВКЛ (F5-F8)")
        layout.addWidget(self.hotkeys_label)
        
        # Создаем иконку в трее
        self.setup_tray_icon()
        
    def init_player(self):
        """Инициализация медиаплеера"""
        self.player = QMediaPlayer()
        self.player.mediaStatusChanged.connect(self.handle_media_status)
        self.player.stateChanged.connect(self.handle_player_state)
        
        # Таймер для обновления позиции (если нужно)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_position)
        
    def setup_hotkeys(self):
        """Настройка глобальных горячих клавиш"""
        try:
            # F5 - Play/Pause
            keyboard.add_hotkey('f5', self.toggle_play_hotkey)
            # F6 - Next track
            keyboard.add_hotkey('f6', self.play_next_hotkey)
            # F7 - Previous track
            keyboard.add_hotkey('f7', self.play_previous_hotkey)
            # F8 - Volume up (можно добавить)
            keyboard.add_hotkey('f8', self.volume_up)
            # Shift+F8 - Volume down
            keyboard.add_hotkey('shift+f8', self.volume_down)
            
            print("Горячие клавиши настроены")
        except Exception as e:
            print(f"Ошибка настройки горячих клавиш: {e}")
            
    def toggle_play_hotkey(self):
        """Обработчик горячей клавиши play/pause"""
        if self.hotkeys_enabled:
            self.toggle_play()
            
    def play_next_hotkey(self):
        """Обработчик горячей клавиши next track"""
        if self.hotkeys_enabled:
            self.play_next()
            
    def play_previous_hotkey(self):
        """Обработчик горячей клавиши previous track"""
        if self.hotkeys_enabled:
            self.play_previous()
            
    def volume_up(self):
        """Увеличение громкости"""
        if self.hotkeys_enabled:
            current = self.volume_slider.value()
            self.volume_slider.setValue(min(100, current + 10))
            
    def volume_down(self):
        """Уменьшение громкости"""
        if self.hotkeys_enabled:
            current = self.volume_slider.value()
            self.volume_slider.setValue(max(0, current - 10))
            
    def setup_tray_icon(self):
        """Настройка иконки в системном трее"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Показать")
        show_action.triggered.connect(self.show)
        quit_action = tray_menu.addAction("Выход")
        quit_action.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
    def login_vk(self):
        """Авторизация ВКонтакте"""
        login = self.login_input.text()
        password = self.password_input.text()
        
        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return
            
        self.auth_btn.setEnabled(False)
        self.auth_btn.setText("Вход...")
        
        # Запускаем аутентификацию в отдельном потоке
        self.auth_thread = VKAuthThread(login, password)
        self.auth_thread.auth_complete.connect(self.on_auth_success)
        self.auth_thread.auth_error.connect(self.on_auth_error)
        self.auth_thread.start()
        
    def on_auth_success(self, vk_audio):
        """Успешная авторизация"""
        self.vk_audio = vk_audio
        self.auth_btn.setEnabled(True)
        self.auth_btn.setText("Войти")
        
        # Сохраняем настройки
        self.save_settings()
        
        # Загружаем аудиозаписи
        self.load_my_music()
        
        QMessageBox.information(self, "Успех", "Авторизация прошла успешно!")
        
    def on_auth_error(self, error):
        """Ошибка авторизации"""
        self.auth_btn.setEnabled(True)
        self.auth_btn.setText("Войти")
        QMessageBox.critical(self, "Ошибка авторизации", str(error))
        
    def load_my_music(self):
        """Загрузка аудиозаписей пользователя"""
        if not self.vk_audio:
            return
            
        try:
            self.tracks_list.clear()
            self.audio_list = []
            
            # Получаем аудиозаписи
            audio_items = list(self.vk_audio.get())
            
            for audio in audio_items:
                self.audio_list.append(audio)
                item_text = f"{audio.get('artist', 'Unknown')} - {audio.get('title', 'Unknown')}"
                item = QListWidgetItem(item_text)
                self.tracks_list.addItem(item)
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить музыку: {e}")
            
    def search_music(self):
        """Поиск музыки"""
        if not self.vk_audio:
            QMessageBox.warning(self, "Ошибка", "Сначала выполните вход")
            return
            
        query = self.search_input.text()
        if not query:
            self.load_my_music()
            return
            
        try:
            self.tracks_list.clear()
            self.audio_list = []
            
            # Поиск аудиозаписей
            search_results = list(self.vk_audio.search(q=query, count=50))
            
            for audio in search_results:
                self.audio_list.append(audio)
                item_text = f"{audio.get('artist', 'Unknown')} - {audio.get('title', 'Unknown')}"
                item = QListWidgetItem(item_text)
                self.tracks_list.addItem(item)
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка поиска: {e}")
            
    def play_selected_track(self):
        """Воспроизведение выбранного трека"""
        current_row = self.tracks_list.currentRow()
        if current_row >= 0 and current_row < len(self.audio_list):
            self.current_track_index = current_row
            self.play_current_track()
            
    def play_current_track(self):
        """Воспроизведение текущего трека"""
        if self.current_track_index < 0 or self.current_track_index >= len(self.audio_list):
            return
            
        track = self.audio_list[self.current_track_index]
        url = track.get('url')
        
        if url:
            # Обновляем информацию о треке
            track_info = f"{track.get('artist', 'Unknown')} - {track.get('title', 'Unknown')}"
            self.current_track_label.setText(track_info)
            
            # Воспроизводим
            media_content = QMediaContent(QUrl(url))
            self.player.setMedia(media_content)
            self.player.play()
            self.is_playing = True
            self.update_play_button()
            
    def toggle_play(self):
        """Воспроизведение/пауза"""
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            if self.current_track_index >= 0:
                self.player.play()
            else:
                # Если нет выбранного трека, выбираем первый
                if self.audio_list:
                    self.current_track_index = 0
                    self.play_current_track()
                    
    def play_next(self):
        """Следующий трек"""
        if self.audio_list and self.current_track_index < len(self.audio_list) - 1:
            self.current_track_index += 1
            self.play_current_track()
            
    def play_previous(self):
        """Предыдущий трек"""
        if self.audio_list and self.current_track_index > 0:
            self.current_track_index -= 1
            self.play_current_track()
            
    def change_volume(self, value):
        """Изменение громкости"""
        self.player.setVolume(value)
        
    def handle_media_status(self, status):
        """Обработка статуса медиа"""
        if status == QMediaPlayer.EndOfMedia:
            self.play_next()
            
    def handle_player_state(self, state):
        """Обработка состояния плеера"""
        self.is_playing = (state == QMediaPlayer.PlayingState)
        self.update_play_button()
        
    def update_play_button(self):
        """Обновление иконки кнопки воспроизведения"""
        if self.is_playing:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            
    def update_position(self):
        """Обновление позиции воспроизведения (можно реализовать прогресс-бар)"""
        pass
        
    def save_settings(self):
        """Сохранение настроек"""
        settings = {
            'login': self.login_input.text(),
            'hotkeys_enabled': self.hotkeys_enabled
        }
        try:
            with open('vk_music_settings.json', 'w') as f:
                json.dump(settings, f)
        except:
            pass
            
    def load_settings(self):
        """Загрузка настроек"""
        try:
            with open('vk_music_settings.json', 'r') as f:
                settings = json.load(f)
                self.login_input.setText(settings.get('login', ''))
                self.hotkeys_enabled = settings.get('hotkeys_enabled', True)
        except:
            pass
            
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "VK Music Player",
            "Приложение свернуто в трей",
            QSystemTrayIcon.Information,
            2000
        )
        
    def quit_app(self):
        """Выход из приложения"""
        self.save_settings()
        # Удаляем горячие клавиши
        keyboard.unhook_all()
        QApplication.quit()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    player = MusicPlayer()
    player.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()