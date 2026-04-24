#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
纯本地离线音视频播放器 - 基于 PyQt5 + QtMultimedia
无广告、不联网、纯桌面程序
支持格式：MP4, AVI, MKV, MOV, MP3, WAV, FLAC, AAC 等（依赖系统解码器）
"""

import sys
import os
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFileDialog, QStyle, QMessageBox,
    QComboBox
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget


class AudioPlaceholder(QWidget):
    """纯音频播放时的占位界面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        label = QLabel("🎵 正在播放音频\n无视频画面")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: #888; padding: 50px;")
        layout.addWidget(label)


class Player(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("极简播放器")
        self.setMinimumSize(800, 600)
        self.resize(1024, 720)

        # 核心组件
        self.player = QMediaPlayer(self)
        self.video_widget = QVideoWidget()
        self.player.setVideoOutput(self.video_widget)

        # 音频占位
        self.audio_placeholder = AudioPlaceholder()
        self.audio_placeholder.hide()

        # 堆叠布局：视频/音频自动切换
        self.central_stack = QWidget()
        self.stack_layout = QVBoxLayout(self.central_stack)
        self.stack_layout.setContentsMargins(0, 0, 0, 0)
        self.stack_layout.addWidget(self.video_widget)
        self.stack_layout.addWidget(self.audio_placeholder)
        self.setCentralWidget(self.central_stack)

        # 控制栏
        self.setup_controls()
        # 菜单栏
        self.setup_menu()

        # 状态变量
        self.current_file = None
        self.is_looping = False
        self.is_muted = False
        self.slider_pressed = False

        # 信号连接
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.player.stateChanged.connect(self.update_play_button)
        self.player.mediaStatusChanged.connect(self.handle_media_end)
        self.player.error.connect(self.handle_error)

        # 定时刷新进度条（解决拖动时卡顿）
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_slider)
        self.timer.start(100)

        # 支持拖拽文件
        self.setAcceptDrops(True)

    # ---------- 界面构建 ----------
    def setup_controls(self):
        """底部控制栏"""
        ctrl_widget = QWidget()
        layout = QHBoxLayout(ctrl_widget)
        layout.setContentsMargins(10, 5, 10, 5)

        # 播放/暂停
        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_btn.setToolTip("播放/暂停 (Space)")
        self.play_btn.clicked.connect(self.toggle_play)
        layout.addWidget(self.play_btn)

        # 停止
        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_btn.setToolTip("停止 (Esc)")
        self.stop_btn.clicked.connect(self.player.stop)
        layout.addWidget(self.stop_btn)

        # 音量滑块
        layout.addWidget(QLabel("🔊"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setToolTip("音量")
        self.volume_slider.valueChanged.connect(self.set_volume)
        layout.addWidget(self.volume_slider)

        # 静音按钮
        self.mute_btn = QPushButton("🔊")
        self.mute_btn.setFixedWidth(40)
        self.mute_btn.setToolTip("静音 (M)")
        self.mute_btn.clicked.connect(self.toggle_mute)
        layout.addWidget(self.mute_btn)

        # 时间标签
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setMinimumWidth(100)
        layout.addWidget(self.time_label)

        # 进度条
        self.progress = QSlider(Qt.Horizontal)
        self.progress.setRange(0, 1000)
        self.progress.setToolTip("进度条")
        self.progress.sliderPressed.connect(lambda: setattr(self, 'slider_pressed', True))
        self.progress.sliderReleased.connect(self.seek)
        self.progress.sliderMoved.connect(self.update_time_label_on_drag)
        layout.addWidget(self.progress, 1)

        # 倍速选择
        self.speed_combo = QComboBox()
        for sp in ["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"]:
            self.speed_combo.addItem(sp)
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.currentTextChanged.connect(self.change_speed)
        layout.addWidget(QLabel("倍速"))
        layout.addWidget(self.speed_combo)

        # 循环按钮
        self.loop_btn = QPushButton("🔂")
        self.loop_btn.setToolTip("循环播放")
        self.loop_btn.setCheckable(True)
        self.loop_btn.clicked.connect(self.toggle_loop)
        layout.addWidget(self.loop_btn)

        # 全屏按钮
        self.full_btn = QPushButton("⤢")
        self.full_btn.setToolTip("全屏 (F)")
        self.full_btn.clicked.connect(self.toggle_fullscreen)
        layout.addWidget(self.full_btn)

        # 打开文件
        open_btn = QPushButton("📁")
        open_btn.setToolTip("打开文件 (Ctrl+O)")
        open_btn.clicked.connect(self.open_file)
        layout.addWidget(open_btn)

        self.statusBar().addWidget(ctrl_widget)

    def setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件(&F)")
        open_action = QAction("打开文件(&O)", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        play_menu = menubar.addMenu("播放(&P)")
        self.loop_action = QAction("循环播放(&L)", self, checkable=True)
        self.loop_action.triggered.connect(self.toggle_loop)
        play_menu.addAction(self.loop_action)

        help_menu = menubar.addMenu("帮助(&H)")
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    # ---------- 核心功能 ----------
    def open_file(self, path=None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(
                self, "选择媒体文件", "",
                "媒体文件 (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.mp3 *.wav *.flac *.aac *.m4a *.ogg);;所有文件 (*.*)"
            )
            if not path:
                return
        self.current_file = path
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
        # 自动区分视频/音频
        ext = os.path.splitext(path)[1].lower()
        audio_exts = {".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg", ".opus"}
        if ext in audio_exts:
            self.video_widget.hide()
            self.audio_placeholder.show()
        else:
            self.audio_placeholder.hide()
            self.video_widget.show()
        self.setWindowTitle(f"极简播放器 - {os.path.basename(path)}")
        self.player.play()

    def toggle_play(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def set_volume(self, val):
        self.player.setVolume(val)
        if val == 0:
            self.mute_btn.setText("🔇")
            self.is_muted = True
        else:
            self.mute_btn.setText("🔊")
            self.is_muted = False

    def toggle_mute(self):
        if self.is_muted:
            self.volume_slider.setValue(50)
        else:
            self.volume_slider.setValue(0)

    def change_speed(self, text):
        rate = float(text.rstrip('x'))
        self.player.setPlaybackRate(rate)

    def toggle_loop(self, checked):
        self.is_looping = checked
        self.loop_btn.setChecked(checked)
        self.loop_action.setChecked(checked)
        self.loop_btn.setText("🔁" if checked else "🔂")

    # ---------- 进度条与时间 ----------
    def update_position(self, pos):
        if not self.slider_pressed:
            self.update_slider(pos)

    def refresh_slider(self):
        if not self.slider_pressed:
            self.update_slider(self.player.position())

    def update_slider(self, pos):
        dur = self.player.duration()
        if dur > 0:
            self.progress.setValue(int(pos / dur * 1000))
            self.update_time_label(pos, dur)

    def update_duration(self, dur):
        self.update_time_label(self.player.position(), dur)

    def update_time_label(self, pos, dur):
        self.time_label.setText(f"{self.format_time(pos)} / {self.format_time(dur)}")

    def update_time_label_on_drag(self, value):
        dur = self.player.duration()
        if dur > 0:
            pos = int(value / 1000 * dur)
            self.time_label.setText(f"{self.format_time(pos)} / {self.format_time(dur)}")

    def format_time(self, ms):
        s = ms // 1000
        if s >= 3600:
            return f"{s // 3600}:{(s % 3600) // 60:02d}:{s % 60:02d}"
        return f"{s // 60:02d}:{s % 60:02d}"

    def seek(self):
        self.slider_pressed = False
        dur = self.player.duration()
        if dur > 0:
            pos = int(self.progress.value() / 1000 * dur)
            self.player.setPosition(pos)

    # ---------- 其他信号处理 ----------
    def update_play_button(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def handle_media_end(self, status):
        if status == QMediaPlayer.EndOfMedia and self.is_looping and self.current_file:
            self.player.setPosition(0)
            self.player.play()

    def handle_error(self, error):
        if error != QMediaPlayer.NoError:
            QMessageBox.warning(self, "播放错误", "无法播放此文件，可能格式不支持或解码器缺失")

    # ---------- 全屏 ----------
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.full_btn.setText("⤢")
            self.menuBar().show()
            self.statusBar().show()
        else:
            self.showFullScreen()
            self.full_btn.setText("✖")
            self.menuBar().hide()
            self.statusBar().hide()

    # ---------- 键盘快捷键 ----------
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.toggle_play()
        elif event.key() == Qt.Key_Escape:
            if self.isFullScreen():
                self.toggle_fullscreen()
            else:
                self.player.stop()
        elif event.key() == Qt.Key_F:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_M:
            self.toggle_mute()
        else:
            super().keyPressEvent(event)

    # ---------- 拖拽文件 ----------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path:
                self.open_file(path)
                break

    def show_about(self):
        QMessageBox.about(self, "关于极简播放器",
            "极简播放器\n"
            "基于 PyQt5 + QtMultimedia\n"
            "完全本地离线，无任何网络连接\n\n"
            "快捷键:\n"
            "  Space  播放/暂停\n"
            "  F      全屏\n"
            "  Esc    停止/退出全屏\n"
            "  M      静音\n"
            "  Ctrl+O 打开文件\n\n"
            "支持格式: 主流音视频格式 (需系统解码器)")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("极简播放器")
    window = Player()
    # 支持命令行传参（文件关联）
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        window.open_file(sys.argv[1])
    window.show()
    sys.exit(app.exec_())