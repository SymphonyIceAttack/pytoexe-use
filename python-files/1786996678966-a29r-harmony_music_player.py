"""Harmony Music Player

Build on Windows with:
    python -m pip install -r requirements.txt
    pyinstaller --noconfirm --clean --windowed --name HarmonyMusicPlayer harmony_music_player.py
"""

from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path
from typing import Any

from mutagen.flac import FLAC
from mutagen.id3 import ID3, APIC
from mutagen.mp3 import MP3
from PyQt5.QtCore import Qt, QTime, QUrl
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSlider,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


APP_NAME = "Harmony Music Player"
SUPPORTED_EXTENSIONS = {".mp3", ".flac", ".wav", ".ogg", ".m4a"}
FAVORITES = "Favorites"

DARK_STYLESHEET = """
QMainWindow, QWidget { background: #121212; color: #ffffff; font-family: "Segoe UI"; }
QWidget#topBar, QWidget#bottomBar { background: #0a0a0a; }
QLabel { color: #ffffff; }
QPushButton { background: transparent; border: none; color: #ffffff; padding: 8px 12px; }
QPushButton:hover { background: rgba(255,255,255,0.1); border-radius: 4px; }
QPushButton#primary { background: #1DB954; border-radius: 4px; font-weight: bold; }
QPushButton#primary:hover { background: #1ed760; }
QPushButton#danger { background: #e74c3c; border-radius: 4px; font-weight: bold; }
QPushButton#danger:hover { background: #c0392b; }
QPushButton#play { background: #1DB954; border-radius: 30px; font-size: 18px; min-width: 56px; min-height: 56px; }
QPushButton#play:hover { background: #1ed760; }
QPushButton#control { color: #b3b3b3; font-size: 16px; min-width: 36px; min-height: 36px; }
QLineEdit, QComboBox { background: #282828; border: none; border-radius: 18px; color: #ffffff; padding: 9px 14px; }
QListWidget, QTableWidget { background: #181818; border: none; border-radius: 6px; color: #ffffff; }
QListWidget::item { padding: 8px; border-radius: 4px; }
QListWidget::item:selected, QTableWidget::item:selected { background: #1DB954; }
QListWidget::item:hover, QTableWidget::item:hover { background: #282828; }
QHeaderView::section { background: #181818; color: #b3b3b3; padding: 8px; border: none; }
QSlider::groove:horizontal { height: 4px; background: #404040; border-radius: 2px; }
QSlider::handle:horizontal { background: #1DB954; width: 12px; margin: -4px 0; border-radius: 6px; }
QSlider::sub-page:horizontal { background: #1DB954; border-radius: 2px; }
"""


def app_data_file() -> Path:
    """Return a writable per-user data location on Windows and other systems."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    folder = base / "HarmonyMusicPlayer"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "music_player_data.json"


class MusicPlayer(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1400, 800)
        self.setMinimumSize(1000, 650)

        self.player = QMediaPlayer()
        self.all_songs: list[str] = []
        self.song_metadata: dict[str, dict[str, Any]] = {}
        self.playlists: dict[str, list[str]] = {}
        self.playlist_covers: dict[str, str | None] = {}
        self.favorites: list[str] = []
        self.current_playlist_songs: list[str] = []
        self.current_playlist_name = ""
        self.current_index = -1
        self.shuffle_mode = False
        self.repeat_mode = 0  # 0 off, 1 all, 2 one
        self.volume_before_mute = 70
        self.data_path = app_data_file()

        self.load_data()
        self.init_ui()
        self.connect_player_signals()
        self.player.setVolume(70)
        self.setStyleSheet(DARK_STYLESHEET)

        if FAVORITES not in self.playlists:
            self.playlists[FAVORITES] = []
            self.playlist_covers[FAVORITES] = None
        self.refresh_all_views()

    def connect_player_signals(self) -> None:
        self.player.mediaStatusChanged.connect(self.handle_media_status)
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.player.stateChanged.connect(self.update_play_button)
        self.player.error.connect(self.handle_player_error)

    def init_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self.create_top_bar())
        self.screen_stack = QStackedWidget()
        self.library_screen = self.create_library_screen()
        self.now_playing_screen = self.create_now_playing_screen()
        self.screen_stack.addWidget(self.library_screen)
        self.screen_stack.addWidget(self.now_playing_screen)
        root.addWidget(self.screen_stack, 1)
        root.addWidget(self.create_bottom_bar())

    def create_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("topBar")
        bar.setFixedHeight(58)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 20, 0)

        logo = QLabel("Harmony")
        logo.setStyleSheet("font-size: 22px; font-weight: bold; color: #1DB954;")
        layout.addWidget(logo)

        self.library_btn = QPushButton("Library")
        self.library_btn.setObjectName("primary")
        self.library_btn.clicked.connect(self.show_library)
        layout.addWidget(self.library_btn)

        self.now_playing_btn = QPushButton("Now Playing")
        self.now_playing_btn.clicked.connect(self.show_now_playing)
        layout.addWidget(self.now_playing_btn)
        layout.addStretch()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search songs...")
        self.search_bar.setFixedWidth(280)
        self.search_bar.textChanged.connect(self.search_songs)
        layout.addWidget(self.search_bar)
        return bar

    def create_library_screen(self) -> QWidget:
        screen = QWidget()
        layout = QHBoxLayout(screen)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        left = QWidget()
        left.setFixedWidth(260)
        left_layout = QVBoxLayout(left)
        header = QHBoxLayout()
        title = QLabel("Playlists")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        add_playlist = QPushButton("+")
        add_playlist.setObjectName("primary")
        add_playlist.setFixedSize(32, 32)
        add_playlist.clicked.connect(self.create_playlist)
        header.addWidget(add_playlist)
        left_layout.addLayout(header)

        self.playlist_list = QListWidget()
        self.playlist_list.itemDoubleClicked.connect(self.load_playlist)
        left_layout.addWidget(self.playlist_list)

        import_m3u = QPushButton("Import M3U")
        import_m3u.clicked.connect(self.import_m3u)
        left_layout.addWidget(import_m3u)
        fav_title = QLabel("Favorites")
        fav_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        left_layout.addWidget(fav_title)
        self.favorites_list = QListWidget()
        self.favorites_list.itemDoubleClicked.connect(self.play_favorite)
        left_layout.addWidget(self.favorites_list)
        layout.addWidget(left)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        actions = QHBoxLayout()
        all_songs = QLabel("All Songs")
        all_songs.setStyleSheet("font-size: 16px; font-weight: bold;")
        actions.addWidget(all_songs)
        actions.addStretch()
        add_files = QPushButton("Add Music")
        add_files.setObjectName("primary")
        add_files.clicked.connect(self.add_music_files)
        actions.addWidget(add_files)
        add_folder = QPushButton("Add Folder")
        add_folder.setObjectName("primary")
        add_folder.clicked.connect(self.add_folder_to_library)
        actions.addWidget(add_folder)
        self.remove_selected_btn = QPushButton("Remove Selected")
        self.remove_selected_btn.setObjectName("danger")
        self.remove_selected_btn.setEnabled(False)
        self.remove_selected_btn.clicked.connect(self.remove_selected_songs)
        actions.addWidget(self.remove_selected_btn)
        center_layout.addLayout(actions)

        self.library_table = QTableWidget(0, 4)
        self.library_table.setHorizontalHeaderLabels(["Title", "Artist", "Album", "Year"])
        self.library_table.horizontalHeader().setStretchLastSection(True)
        self.library_table.verticalHeader().setVisible(False)
        self.library_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.library_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.library_table.itemDoubleClicked.connect(self.play_from_library)
        self.library_table.itemSelectionChanged.connect(self.on_selection_changed)
        center_layout.addWidget(self.library_table)

        bottom = QHBoxLayout()
        bottom.addWidget(QLabel("Add to playlist"))
        self.playlist_combo = QComboBox()
        self.playlist_combo.currentIndexChanged.connect(self.update_add_button_state)
        bottom.addWidget(self.playlist_combo)
        self.add_to_playlist_btn = QPushButton("Add Selected")
        self.add_to_playlist_btn.setObjectName("primary")
        self.add_to_playlist_btn.setEnabled(False)
        self.add_to_playlist_btn.clicked.connect(self.add_selected_to_playlist)
        bottom.addWidget(self.add_to_playlist_btn)
        bottom.addStretch()
        self.selection_label = QLabel("0 selected")
        self.selection_label.setStyleSheet("color: #b3b3b3;")
        bottom.addWidget(self.selection_label)
        center_layout.addLayout(bottom)
        layout.addWidget(center, 1)
        return screen

    def create_now_playing_screen(self) -> QWidget:
        screen = QWidget()
        layout = QHBoxLayout(screen)
        layout.setContentsMargins(40, 25, 40, 25)
        layout.setSpacing(40)

        left = QWidget()
        left.setFixedWidth(420)
        left_layout = QVBoxLayout(left)
        left_layout.setAlignment(Qt.AlignCenter)

        self.now_playing_art = QLabel("No Album Art")
        self.now_playing_art.setFixedSize(360, 360)
        self.now_playing_art.setAlignment(Qt.AlignCenter)
        self.now_playing_art.setStyleSheet("background: #181818; border-radius: 18px; color: #666;")
        left_layout.addWidget(self.now_playing_art, alignment=Qt.AlignCenter)

        self.now_playing_title = QLabel("No song playing")
        self.now_playing_title.setAlignment(Qt.AlignCenter)
        self.now_playing_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        left_layout.addWidget(self.now_playing_title)
        self.now_playing_artist = QLabel("")
        self.now_playing_artist.setAlignment(Qt.AlignCenter)
        self.now_playing_artist.setStyleSheet("font-size: 16px; color: #b3b3b3;")
        left_layout.addWidget(self.now_playing_artist)

        progress = QHBoxLayout()
        self.np_current_time = QLabel("0:00")
        self.np_progress_slider = QSlider(Qt.Horizontal)
        self.np_progress_slider.sliderMoved.connect(self.set_position)
        self.np_total_time = QLabel("0:00")
        progress.addWidget(self.np_current_time)
        progress.addWidget(self.np_progress_slider)
        progress.addWidget(self.np_total_time)
        left_layout.addLayout(progress)

        controls = QHBoxLayout()
        controls.setAlignment(Qt.AlignCenter)
        self.np_shuffle_btn = QPushButton("Shuffle")
        self.np_shuffle_btn.setObjectName("control")
        self.np_shuffle_btn.clicked.connect(self.toggle_shuffle)
        controls.addWidget(self.np_shuffle_btn)
        prev = QPushButton("Previous")
        prev.setObjectName("control")
        prev.clicked.connect(self.previous_song)
        controls.addWidget(prev)
        self.np_play_btn = QPushButton("Play")
        self.np_play_btn.setObjectName("play")
        self.np_play_btn.clicked.connect(self.toggle_play)
        controls.addWidget(self.np_play_btn)
        nxt = QPushButton("Next")
        nxt.setObjectName("control")
        nxt.clicked.connect(self.next_song)
        controls.addWidget(nxt)
        self.np_repeat_btn = QPushButton("Repeat")
        self.np_repeat_btn.setObjectName("control")
        self.np_repeat_btn.clicked.connect(self.toggle_repeat)
        controls.addWidget(self.np_repeat_btn)
        left_layout.addLayout(controls)
        layout.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        queue_title = QLabel("Queue")
        queue_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        right_layout.addWidget(queue_title)
        self.np_queue_list = QListWidget()
        self.np_queue_list.itemDoubleClicked.connect(self.play_from_queue)
        right_layout.addWidget(self.np_queue_list)
        self.np_playlist_name_label = QLabel("")
        self.np_playlist_name_label.setStyleSheet("color: #b3b3b3;")
        right_layout.addWidget(self.np_playlist_name_label)
        layout.addWidget(right, 1)
        return screen

    def create_bottom_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("bottomBar")
        bar.setFixedHeight(62)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 8, 20, 8)
        self.volume_icon = QPushButton("Volume")
        self.volume_icon.clicked.connect(self.toggle_mute)
        layout.addWidget(self.volume_icon)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(140)
        self.volume_slider.valueChanged.connect(self.set_volume)
        layout.addWidget(self.volume_slider)
        layout.addStretch()
        self.bottom_now_playing = QLabel("Ready")
        self.bottom_now_playing.setStyleSheet("color: #b3b3b3;")
        layout.addWidget(self.bottom_now_playing)
        return bar

    # Navigation
    def show_library(self) -> None:
        self.screen_stack.setCurrentWidget(self.library_screen)
        self.library_btn.setObjectName("primary")
        self.now_playing_btn.setObjectName("")
        self.style().unpolish(self.library_btn)
        self.style().polish(self.library_btn)

    def show_now_playing(self) -> None:
        self.screen_stack.setCurrentWidget(self.now_playing_screen)
        self.update_queue()

    # Metadata and library
    def is_music_file(self, path: str) -> bool:
        return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS

    def extract_metadata(self, path: str) -> dict[str, Any]:
        if path in self.song_metadata:
            return self.song_metadata[path]
        meta: dict[str, Any] = {
            "title": Path(path).stem,
            "artist": "",
            "album": "",
            "year": "",
            "album_art": None,
        }
        try:
            if path.lower().endswith(".mp3"):
                audio = MP3(path)
                tags = audio.tags or ID3()
                meta["title"] = str(tags.get("TIT2", meta["title"]))
                meta["artist"] = str(tags.get("TPE1", ""))
                meta["album"] = str(tags.get("TALB", ""))
                meta["year"] = str(tags.get("TDRC", ""))
                for tag in tags.values():
                    if isinstance(tag, APIC):
                        pixmap = QPixmap()
                        pixmap.loadFromData(tag.data)
                        if not pixmap.isNull():
                            meta["album_art"] = pixmap
                            break
            elif path.lower().endswith(".flac"):
                audio = FLAC(path)
                meta["title"] = audio.get("title", [meta["title"]])[0]
                meta["artist"] = audio.get("artist", [""])[0]
                meta["album"] = audio.get("album", [""])[0]
                meta["year"] = audio.get("date", [""])[0]
                if audio.pictures:
                    pixmap = QPixmap()
                    pixmap.loadFromData(audio.pictures[0].data)
                    if not pixmap.isNull():
                        meta["album_art"] = pixmap
        except Exception:
            pass
        self.song_metadata[path] = meta
        return meta

    def scan_folder(self, folder: str) -> list[str]:
        return [
            str(path)
            for path in Path(folder).rglob("*")
            if path.is_file() and self.is_music_file(str(path))
        ]

    def add_music_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Music Files", "", "Music Files (*.mp3 *.flac *.wav *.ogg *.m4a)"
        )
        self.add_files_to_library(files)

    def add_folder_to_library(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Folder with Music")
        if not folder:
            return
        progress = QProgressDialog("Scanning folder...", "Cancel", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        files = self.scan_folder(folder)
        progress.close()
        self.add_files_to_library(files)

    def add_files_to_library(self, files: list[str]) -> None:
        added = 0
        for path in files:
            path = os.path.abspath(path)
            if path not in self.all_songs and self.is_music_file(path):
                self.all_songs.append(path)
                self.extract_metadata(path)
                added += 1
        self.refresh_all_views()
        if files:
            QMessageBox.information(self, "Library Updated", f"Added {added} music file(s).")

    def remove_selected_songs(self) -> None:
        rows = sorted({item.row() for item in self.library_table.selectedItems()}, reverse=True)
        if not rows:
            return
        if QMessageBox.question(
            self, "Remove Songs", f"Remove {len(rows)} song(s) from the library?",
            QMessageBox.Yes | QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        paths = [self.library_table.item(row, 0).data(Qt.UserRole) for row in rows]
        for path in paths:
            if path in self.all_songs:
                self.all_songs.remove(path)
            self.song_metadata.pop(path, None)
            if path in self.favorites:
                self.favorites.remove(path)
            for playlist in self.playlists.values():
                if path in playlist:
                    playlist.remove(path)
        self.refresh_all_views()

    def search_songs(self, text: str) -> None:
        needle = text.lower().strip()
        for row in range(self.library_table.rowCount()):
            item = self.library_table.item(row, 0)
            visible = not needle or (item is not None and needle in item.text().lower())
            self.library_table.setRowHidden(row, not visible)

    # Playlists
    def create_playlist(self) -> None:
        name, ok = QInputDialog.getText(self, "Create Playlist", "Playlist name:")
        name = name.strip()
        if ok and name:
            if name in self.playlists:
                QMessageBox.warning(self, "Playlist", "That playlist already exists.")
                return
            self.playlists[name] = []
            self.playlist_covers[name] = None
            self.refresh_all_views()

    def add_selected_to_playlist(self) -> None:
        name = self.playlist_combo.currentText()
        if name not in self.playlists:
            return
        rows = {item.row() for item in self.library_table.selectedItems()}
        added = 0
        for row in rows:
            path = self.library_table.item(row, 0).data(Qt.UserRole)
            if path not in self.playlists[name]:
                self.playlists[name].append(path)
                added += 1
        self.save_data()
        QMessageBox.information(self, "Playlist Updated", f"Added {added} song(s) to {name}.")
        self.library_table.clearSelection()
        self.update_queue()

    def load_playlist(self, item: QListWidgetItem) -> None:
        name = item.text()
        songs = self.playlists.get(name, [])
        if songs:
            self.current_playlist_name = name
            self.current_playlist_songs = [path for path in songs if os.path.exists(path)]
            self.current_index = 0
            self.play_current()
            self.show_now_playing()

    def play_favorite(self, item: QListWidgetItem) -> None:
        path = self.favorites[self.favorites_list.row(item)]
        self.current_playlist_name = FAVORITES
        self.current_playlist_songs = [path]
        self.current_index = 0
        self.play_current()
        self.show_now_playing()

    def import_m3u(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select M3U File", "", "M3U Files (*.m3u *.m3u8)")
        if not path:
            return
        name = Path(path).stem
        self.playlists.setdefault(name, [])
        self.playlist_covers.setdefault(name, None)
        try:
            lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    candidate = Path(line)
                    if not candidate.is_absolute():
                        candidate = Path(path).parent / candidate
                    candidate = candidate.resolve()
                    if candidate.exists() and self.is_music_file(str(candidate)):
                        value = str(candidate)
                        if value not in self.playlists[name]:
                            self.playlists[name].append(value)
                        if value not in self.all_songs:
                            self.all_songs.append(value)
                            self.extract_metadata(value)
            self.refresh_all_views()
        except OSError as exc:
            QMessageBox.critical(self, "Import Error", str(exc))

    # Playback
    def play_from_library(self, item: QTableWidgetItem) -> None:
        path = item.data(Qt.UserRole)
        if path and os.path.exists(path):
            self.current_playlist_songs = [path]
            self.current_playlist_name = "Now Playing"
            self.current_index = 0
            self.play_current()
            self.show_now_playing()
        else:
            QMessageBox.warning(self, "File Missing", "That music file could not be found.")

    def play_from_queue(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.UserRole)
        if path in self.current_playlist_songs:
            self.current_index = self.current_playlist_songs.index(path)
            self.play_current()

    def play_current(self) -> None:
        if not (0 <= self.current_index < len(self.current_playlist_songs)):
            return
        path = self.current_playlist_songs[self.current_index]
        if not os.path.exists(path):
            self.next_song()
            return
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
        self.player.play()
        self.update_song_info(path)
        self.bottom_now_playing.setText(Path(path).name)
        self.update_queue()

    def toggle_play(self) -> None:
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        elif self.player.state() == QMediaPlayer.PausedState:
            self.player.play()
        elif self.current_playlist_songs:
            self.play_current()
        elif self.all_songs:
            self.current_playlist_songs = [self.all_songs[0]]
            self.current_playlist_name = "Now Playing"
            self.current_index = 0
            self.play_current()

    def next_song(self) -> None:
        if not self.current_playlist_songs:
            return
        if self.repeat_mode == 2:
            self.play_current()
        elif self.shuffle_mode and len(self.current_playlist_songs) > 1:
            choices = [i for i in range(len(self.current_playlist_songs)) if i != self.current_index]
            self.current_index = random.choice(choices)
            self.play_current()
        elif self.current_index < len(self.current_playlist_songs) - 1:
            self.current_index += 1
            self.play_current()
        elif self.repeat_mode == 1:
            self.current_index = 0
            self.play_current()
        else:
            self.player.stop()
            self.bottom_now_playing.setText("Playback finished")

    def previous_song(self) -> None:
        if self.current_playlist_songs and self.current_index > 0:
            self.current_index -= 1
            self.play_current()

    def toggle_shuffle(self) -> None:
        self.shuffle_mode = not self.shuffle_mode
        self.np_shuffle_btn.setStyleSheet("color: #1DB954;" if self.shuffle_mode else "")

    def toggle_repeat(self) -> None:
        self.repeat_mode = (self.repeat_mode + 1) % 3
        labels = ["Repeat", "Repeat All", "Repeat One"]
        self.np_repeat_btn.setText(labels[self.repeat_mode])

    def set_volume(self, volume: int) -> None:
        self.player.setVolume(volume)
        self.volume_icon.setText("Muted" if volume == 0 else f"Volume {volume}%")

    def toggle_mute(self) -> None:
        if self.player.volume() == 0:
            self.set_volume(self.volume_before_mute)
            self.volume_slider.setValue(self.volume_before_mute)
        else:
            self.volume_before_mute = self.player.volume()
            self.set_volume(0)
            self.volume_slider.setValue(0)

    def set_position(self, position: int) -> None:
        self.player.setPosition(position)

    def update_position(self, position: int) -> None:
        self.np_progress_slider.setValue(position)
        self.np_current_time.setText(format_time(position))

    def update_duration(self, duration: int) -> None:
        self.np_progress_slider.setRange(0, max(0, duration))
        self.np_total_time.setText(format_time(duration))

    def update_play_button(self, state: QMediaPlayer.State) -> None:
        self.np_play_btn.setText("Pause" if state == QMediaPlayer.PlayingState else "Play")

    def handle_media_status(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.EndOfMedia:
            self.next_song()

    def handle_player_error(self, _error: QMediaPlayer.Error) -> None:
        message = self.player.errorString()
        if message:
            QMessageBox.warning(self, "Playback Error", message)

    def update_song_info(self, path: str) -> None:
        meta = self.extract_metadata(path)
        self.now_playing_title.setText(str(meta["title"]))
        details = " • ".join(value for value in (meta["artist"], meta["year"]) if value)
        self.now_playing_artist.setText(details)
        art = meta.get("album_art")
        if isinstance(art, QPixmap):
            self.now_playing_art.setPixmap(art.scaled(360, 360, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.now_playing_art.setText("")
        else:
            self.now_playing_art.setPixmap(QPixmap())
            self.now_playing_art.setText("No Album Art")

    # Views and persistence
    def update_library_table(self) -> None:
        self.library_table.setRowCount(len(self.all_songs))
        for row, path in enumerate(self.all_songs):
            meta = self.extract_metadata(path)
            title = QTableWidgetItem(str(meta["title"]))
            title.setData(Qt.UserRole, path)
            self.library_table.setItem(row, 0, title)
            for col, key in enumerate(("artist", "album", "year"), start=1):
                self.library_table.setItem(row, col, QTableWidgetItem(str(meta[key])))

    def update_playlist_views(self) -> None:
        self.playlist_list.clear()
        for name in sorted(self.playlists):
            self.playlist_list.addItem(name)
        self.favorites_list.clear()
        for path in self.favorites:
            self.favorites_list.addItem(Path(path).name)
        current = self.playlist_combo.currentText()
        self.playlist_combo.clear()
        self.playlist_combo.addItem("Select playlist...")
        self.playlist_combo.addItems(sorted(self.playlists))
        if current:
            index = self.playlist_combo.findText(current)
            if index >= 0:
                self.playlist_combo.setCurrentIndex(index)

    def update_queue(self) -> None:
        self.np_queue_list.clear()
        self.np_playlist_name_label.setText(
            f"Playlist: {self.current_playlist_name}" if self.current_playlist_name else "No songs in queue"
        )
        for index, path in enumerate(self.current_playlist_songs, start=1):
            item = QListWidgetItem(f"{index}. {self.extract_metadata(path)['title']}")
            item.setData(Qt.UserRole, path)
            self.np_queue_list.addItem(item)

    def on_selection_changed(self) -> None:
        rows = {item.row() for item in self.library_table.selectedItems()}
        self.selection_label.setText(f"{len(rows)} selected")
        enabled = bool(rows)
        self.remove_selected_btn.setEnabled(enabled)
        self.add_to_playlist_btn.setEnabled(enabled and self.playlist_combo.currentIndex() > 0)

    def update_add_button_state(self) -> None:
        self.on_selection_changed()

    def refresh_all_views(self) -> None:
        self.update_library_table()
        self.update_playlist_views()
        self.update_queue()
        self.save_data()

    def load_data(self) -> None:
        try:
            data = json.loads(self.data_path.read_text(encoding="utf-8"))
            self.favorites = data.get("favorites", [])
            self.playlists = data.get("playlists", {})
            self.playlist_covers = data.get("playlist_covers", {})
            self.all_songs = data.get("all_songs", [])
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self.favorites = []
            self.playlists = {}
            self.playlist_covers = {}
            self.all_songs = []

    def save_data(self) -> None:
        data = {
            "favorites": self.favorites,
            "playlists": self.playlists,
            "playlist_covers": self.playlist_covers,
            "all_songs": self.all_songs,
        }
        try:
            self.data_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            pass


def format_time(milliseconds: int) -> str:
    seconds = max(0, milliseconds // 1000)
    return f"{seconds // 60}:{seconds % 60:02d}"


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = MusicPlayer()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()