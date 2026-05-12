#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量级视频壁纸软件 - 主程序
支持播放 MP4 格式的视频壁纸
"""

import sys
import os
import ctypes
import json
from pathlib import Path

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFileDialog,
                             QSystemTrayIcon, QMenu, QAction, QMessageBox,
                             QSlider, QCheckBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont

# 导入视频播放器模块
try:
    from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
    from PyQt5.QtMultimediaWidgets import QVideoWidget
    USE_QT_MEDIA = True
except ImportError:
    USE_QT_MEDIA = False
    print("警告: QtMultimedia 不可用，尝试使用 VLC")


class WallpaperWindow(QWidget):
    """壁纸窗口 - 嵌入到桌面"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Wallpaper")
        self.setup_ui()
        self.embed_to_desktop()
        
    def setup_ui(self):
        """设置UI"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        if USE_QT_MEDIA:
            # 使用 Qt 内置播放器
            self.video_widget = QVideoWidget()
            self.layout.addWidget(self.video_widget)
            
            self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
            self.media_player.setVideoOutput(self.video_widget)
            self.media_player.setVolume(0)  # 默认静音
        else:
            # 使用 QLabel 作为占位符
            self.label = QLabel("视频加载中...")
            self.label.setAlignment(Qt.AlignCenter)
            self.label.setStyleSheet("color: white; font-size: 24px;")
            self.layout.addWidget(self.label)
            self.media_player = None
            
    def embed_to_desktop(self):
        """将窗口嵌入到桌面背景层"""
        # 获取屏幕尺寸
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        # 设置窗口属性
        self.setWindowFlags(
            Qt.FramelessWindowHint |      # 无边框
            Qt.WindowStaysOnBottomHint |  # 保持在最底层
            Qt.Tool |                      # 不在任务栏显示
            Qt.WindowDoesNotAcceptFocus    # 不获取焦点
        )
        
        # Windows 特定: 嵌入到桌面
        if sys.platform == 'win32':
            self._embed_to_desktop_windows()
            
        self.show()
        
    def _embed_to_desktop_windows(self):
        """Windows 平台: 将窗口嵌入到桌面图标层下方"""
        # 获取 WorkerW 窗口
        progman = ctypes.windll.user32.FindWindowW("Progman", None)
        
        if progman:
            # 发送消息让系统创建 WorkerW 窗口
            ctypes.windll.user32.SendMessageTimeoutW(
                progman, 0x052C, 0, 0, 0x0, 1000, None
            )
            
            # 查找 WorkerW 窗口
            def enum_windows_callback(hwnd, extra):
                shell_dll = ctypes.windll.user32.FindWindowExW(hwnd, 0, "SHELLDLL_DefView", None)
                if shell_dll:
                    workerw = ctypes.windll.user32.FindWindowExW(0, hwnd, "WorkerW", None)
                    extra.append(workerw)
                return True
            
            worker_windows = []
            ctypes.windll.user32.EnumWindows(
                ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.POINTER(ctypes.py_object))(enum_windows_callback),
                ctypes.py_object(worker_windows)
            )
            
            # 设置父窗口
            if worker_windows and worker_windows[0]:
                ctypes.windll.user32.SetParent(int(self.winId()), worker_windows[0])
                
    def play_video(self, video_path):
        """播放视频"""
        if self.media_player and USE_QT_MEDIA:
            self.media_player.setMedia(QMediaContent.fromLocalFile(video_path))
            self.media_player.setPlaybackRate(1.0)
            self.media_player.play()
            # 循环播放
            self.media_player.mediaStatusChanged.connect(self._loop_video)
            
    def _loop_video(self, status):
        """视频循环播放"""
        if status == QMediaPlayer.EndOfMedia:
            self.media_player.setPosition(0)
            self.media_player.play()
            
    def set_volume(self, volume):
        """设置音量 (0-100)"""
        if self.media_player and USE_QT_MEDIA:
            self.media_player.setVolume(volume)
            
    def stop(self):
        """停止播放"""
        if self.media_player and USE_QT_MEDIA:
            self.media_player.stop()


class SettingsWindow(QMainWindow):
    """设置窗口"""
    
    def __init__(self, wallpaper_window):
        super().__init__()
        self.wallpaper_window = wallpaper_window
        self.config_file = Path.home() / ".video_wallpaper_config.json"
        self.current_video = None
        
        self.setWindowTitle("视频壁纸设置")
        self.setFixedSize(400, 300)
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        """设置UI"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("🎬 视频壁纸设置")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 视频选择
        video_layout = QHBoxLayout()
        self.video_label = QLabel("未选择视频")
        self.video_label.setStyleSheet("color: gray;")
        video_layout.addWidget(self.video_label)
        
        select_btn = QPushButton("选择视频")
        select_btn.clicked.connect(self.select_video)
        video_layout.addWidget(select_btn)
        layout.addLayout(video_layout)
        
        # 音量控制
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("音量:"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(0)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        volume_layout.addWidget(self.volume_slider)
        self.volume_value = QLabel("0%")
        volume_layout.addWidget(self.volume_value)
        layout.addLayout(volume_layout)
        
        # 开机自启
        self.autostart_checkbox = QCheckBox("开机自动启动")
        self.autostart_checkbox.stateChanged.connect(self.on_autostart_changed)
        layout.addWidget(self.autostart_checkbox)
        
        # 控制按钮
        btn_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶ 播放")
        self.play_btn.clicked.connect(self.play_video)
        self.play_btn.setEnabled(False)
        btn_layout.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.clicked.connect(self.stop_video)
        btn_layout.addWidget(self.stop_btn)
        
        layout.addLayout(btn_layout)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: green;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # 说明
        info = QLabel("提示: 关闭此窗口后，软件将在系统托盘继续运行")
        info.setStyleSheet("color: gray; font-size: 11px;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
    def select_video(self):
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.avi *.mkv *.mov);;所有文件 (*.*)"
        )
        if file_path:
            self.current_video = file_path
            self.video_label.setText(Path(file_path).name)
            self.video_label.setStyleSheet("color: black;")
            self.play_btn.setEnabled(True)
            self.save_config()
            
    def play_video(self):
        """播放视频"""
        if self.current_video and os.path.exists(self.current_video):
            self.wallpaper_window.play_video(self.current_video)
            self.status_label.setText("正在播放: " + Path(self.current_video).name)
            self.status_label.setStyleSheet("color: green;")
            self.save_config()
            
    def stop_video(self):
        """停止播放"""
        self.wallpaper_window.stop()
        self.status_label.setText("已停止")
        self.status_label.setStyleSheet("color: orange;")
        
    def on_volume_changed(self, value):
        """音量改变"""
        self.volume_value.setText(f"{value}%")
        self.wallpaper_window.set_volume(value)
        
    def on_autostart_changed(self, state):
        """开机自启设置改变"""
        self.set_autostart(state == Qt.Checked)
        self.save_config()
        
    def set_autostart(self, enable):
        """设置开机自启"""
        if sys.platform == 'win32':
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "VideoWallpaper"
            app_path = sys.executable + " " + os.path.abspath(__file__)
            
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                if enable:
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
                else:
                    try:
                        winreg.DeleteValue(key, app_name)
                    except:
                        pass
                winreg.CloseKey(key)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"设置开机自启失败: {e}")
                
    def save_config(self):
        """保存配置"""
        config = {
            "video_path": self.current_video,
            "volume": self.volume_slider.value(),
            "autostart": self.autostart_checkbox.isChecked()
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except:
            pass
            
    def load_config(self):
        """加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                video_path = config.get("video_path")
                if video_path and os.path.exists(video_path):
                    self.current_video = video_path
                    self.video_label.setText(Path(video_path).name)
                    self.video_label.setStyleSheet("color: black;")
                    self.play_btn.setEnabled(True)
                    
                self.volume_slider.setValue(config.get("volume", 0))
                self.autostart_checkbox.setChecked(config.get("autostart", False))
                
                # 如果有视频配置，自动播放
                if self.current_video:
                    QTimer.singleShot(1000, self.play_video)
                    
        except:
            pass


class VideoWallpaperApp(QApplication):
    """应用程序主类"""
    
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)
        
        # 创建壁纸窗口
        self.wallpaper_window = WallpaperWindow()
        
        # 创建设置窗口
        self.settings_window = SettingsWindow(self.wallpaper_window)
        
        # 创建系统托盘
        self.setup_tray()
        
        # 显示设置窗口
        self.settings_window.show()
        
    def setup_tray(self):
        """设置系统托盘"""
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        # 使用默认图标（如果没有自定义图标）
        # 这里使用一个简单的彩色图标
        from PyQt5.QtGui import QPixmap, QPainter, QColor
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 120, 215))
        self.tray_icon.setIcon(QIcon(pixmap))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction("打开设置", self)
        show_action.triggered.connect(self.settings_window.show)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        play_action = QAction("播放", self)
        play_action.triggered.connect(self.settings_window.play_video)
        tray_menu.addAction(play_action)
        
        stop_action = QAction("停止", self)
        stop_action.triggered.connect(self.settings_window.stop_video)
        tray_menu.addAction(stop_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("视频壁纸")
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()
        
    def on_tray_activated(self, reason):
        """托盘图标被激活"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.settings_window.show()
            
    def quit_app(self):
        """退出应用"""
        self.wallpaper_window.stop()
        self.wallpaper_window.close()
        self.quit()


def main():
    """主函数"""
    # 设置 DPI 感知
    if sys.platform == 'win32':
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
            
    app = VideoWallpaperApp(sys.argv)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
