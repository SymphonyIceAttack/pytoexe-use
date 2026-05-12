#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频壁纸软件 - 超简稳定版
只使用 PyQt5 基础组件，兼容性最好
"""

import sys
import os
import json
import ctypes
from pathlib import Path

# 日志记录
LOG_FILE = str(Path.home() / ".video_wallpaper.log")

def log(msg):
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{msg}\n")
    except:
        pass

log("=" * 50)
log("程序启动")

# 导入 PyQt5
try:
    from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                                 QPushButton, QLabel, QFileDialog, QSystemTrayIcon,
                                 QMenu, QAction, QSlider, QMainWindow)
    from PyQt5.QtCore import Qt, QTimer, QUrl
    from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor
    from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
    from PyQt5.QtMultimediaWidgets import QVideoWidget
    log("PyQt5 导入成功")
except Exception as e:
    log(f"导入错误: {e}")
    sys.exit(1)


class WallpaperWidget(QWidget):
    """壁纸窗口"""
    
    def __init__(self):
        super().__init__()
        log("创建壁纸窗口")
        
        # 全屏无边框
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnBottomHint |
            Qt.Tool
        )
        
        # 视频播放
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_widget = QVideoWidget()
        layout.addWidget(self.video_widget)
        
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video_widget)
        self.player.setVolume(0)
        
        # 嵌入桌面
        self.embed_to_desktop()
        self.show()
        log("壁纸窗口显示")
    
    def embed_to_desktop(self):
        """嵌入Windows桌面"""
        try:
            progman = ctypes.windll.user32.FindWindowW("Progman", None)
            if progman:
                ctypes.windll.user32.SendMessageTimeoutW(progman, 0x052C, 0, 0, 0x0, 1000, None)
                workerw = ctypes.windll.user32.FindWindowExW(0, 0, "WorkerW", None)
                if workerw:
                    ctypes.windll.user32.SetParent(int(self.winId()), workerw)
                    log("已嵌入桌面")
        except Exception as e:
            log(f"嵌入失败: {e}")
    
    def play(self, path):
        """播放视频"""
        try:
            url = QUrl.fromLocalFile(path)
            self.player.setMedia(QMediaContent(url))
            self.player.play()
            log(f"播放: {path}")
        except Exception as e:
            log(f"播放失败: {e}")
    
    def stop(self):
        self.player.stop()
    
    def set_volume(self, v):
        self.player.setVolume(v)


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, wallpaper):
        super().__init__()
        self.wallpaper = wallpaper
        self.config_file = Path.home() / ".video_wallpaper.json"
        self.video_path = None
        
        self.setWindowTitle("视频壁纸")
        self.setFixedSize(350, 250)
        
        # 界面
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题
        title = QLabel("视频壁纸设置")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 视频选择
        hbox = QHBoxLayout()
        self.path_label = QLabel("未选择视频")
        self.path_label.setStyleSheet("color: gray;")
        hbox.addWidget(self.path_label)
        
        btn = QPushButton("浏览...")
        btn.clicked.connect(self.select_video)
        hbox.addWidget(btn)
        layout.addLayout(hbox)
        
        # 音量
        hbox2 = QHBoxLayout()
        hbox2.addWidget(QLabel("音量:"))
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.volume_changed)
        hbox2.addWidget(self.slider)
        self.vol_label = QLabel("0%")
        hbox2.addWidget(self.vol_label)
        layout.addLayout(hbox2)
        
        # 按钮
        hbox3 = QHBoxLayout()
        self.play_btn = QPushButton("播放")
        self.play_btn.clicked.connect(self.play)
        self.play_btn.setEnabled(False)
        hbox3.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop)
        hbox3.addWidget(self.stop_btn)
        layout.addLayout(hbox3)
        
        # 状态
        self.status = QLabel("就绪")
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)
        
        layout.addStretch()
        
        # 加载配置
        self.load_config()
    
    def select_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择视频", "", "视频 (*.mp4 *.avi *.mkv)")
        if path:
            self.video_path = path
            self.path_label.setText(Path(path).name)
            self.path_label.setStyleSheet("color: black;")
            self.play_btn.setEnabled(True)
            self.save_config()
    
    def play(self):
        if self.video_path:
            self.wallpaper.play(self.video_path)
            self.status.setText(f"播放中: {Path(self.video_path).name}")
            self.save_config()
    
    def stop(self):
        self.wallpaper.stop()
        self.status.setText("已停止")
    
    def volume_changed(self, v):
        self.vol_label.setText(f"{v}%")
        self.wallpaper.set_volume(v)
    
    def save_config(self):
        try:
            cfg = {"path": self.video_path, "vol": self.slider.value()}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(cfg, f)
        except:
            pass
    
    def load_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                path = cfg.get("path")
                if path and os.path.exists(path):
                    self.video_path = path
                    self.path_label.setText(Path(path).name)
                    self.path_label.setStyleSheet("color: black;")
                    self.play_btn.setEnabled(True)
                    self.slider.setValue(cfg.get("vol", 0))
                    # 自动播放
                    QTimer.singleShot(500, self.play)
        except:
            pass


class App(QApplication):
    """应用"""
    
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)
        
        # 创建壁纸窗口
        self.wallpaper = WallpaperWidget()
        
        # 创建主窗口
        self.window = MainWindow(self.wallpaper)
        self.window.show()
        
        # 系统托盘
        self.setup_tray()
    
    def setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        
        # 简单图标
        pm = QPixmap(16, 16)
        pm.fill(QColor(0, 120, 215))
        self.tray.setIcon(QIcon(pm))
        
        menu = QMenu()
        menu.addAction("设置", self.window.show)
        menu.addSeparator()
        menu.addAction("退出", self.quit)
        
        self.tray.setContextMenu(menu)
        self.tray.show()


def main():
    # DPI
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    app = App(sys.argv)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
