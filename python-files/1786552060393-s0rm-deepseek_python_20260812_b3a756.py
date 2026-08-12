"""
小米 MiMo-TTS 语音朗读器 - Windows 桌面版
需要安装: pip install PyQt5 requests pygame
打包命令: pyinstaller --onefile --windowed --name="小米语音朗读器" --icon=app.ico tts_gui.py
"""

import sys
import os
import json
import tempfile
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QComboBox, QLabel, QStatusBar,
    QSlider, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
import requests
import pygame

# ========== 配置 ==========
API_KEY = "sk-c17vbkhiq2law889uiyvlns99ci0sxd17htu7ramntidp60v"
API_BASE = "https://api.xiaomimimo.com/v1"
MODEL = "mimo-v2.5-tts"

# ========== 工作线程 ==========
class TTSWorker(QThread):
    finished = pyqtSignal(str)  # 成功返回文件路径
    error = pyqtSignal(str)     # 错误消息
    status = pyqtSignal(str)    # 状态更新

    def __init__(self, text, voice, volume):
        super().__init__()
        self.text = text
        self.voice = voice
        self.volume = volume

    def run(self):
        try:
            self.status.emit("⏳ 正在请求小米 TTS...")

            # 尝试多种格式
            formats = ['mp3', 'wav', 'pcm']
            for fmt in formats:
                try:
                    self.status.emit(f"⏳ 尝试格式: {fmt}")
                    payload = {
                        "model": MODEL,
                        "messages": [
                            {"role": "user", "content": ""},
                            {"role": "assistant", "content": self.text}
                        ],
                        "audio": {
                            "format": fmt,
                            "voice": self.voice
                        }
                    }

                    resp = requests.post(
                        f"{API_BASE}/chat/completions",
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {API_KEY}"
                        },
                        json=payload,
                        timeout=30
                    )

                    if resp.status_code != 200:
                        err_msg = resp.text
                        try:
                            err_json = resp.json()
                            if 'error' in err_json and 'message' in err_json['error']:
                                err_msg = err_json['error']['message']
                        except:
                            pass
                        self.status.emit(f"⚠️ 格式 {fmt} 失败: HTTP {resp.status_code}")
                        continue

                    # 保存临时文件
                    ext = 'mp3' if fmt == 'mp3' else 'wav'
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{ext}')
                    tmp.write(resp.content)
                    tmp.close()

                    # 验证文件大小
                    if os.path.getsize(tmp.name) < 1000:
                        os.unlink(tmp.name)
                        self.status.emit(f"⚠️ 格式 {fmt} 返回数据过小")
                        continue

                    self.finished.emit(tmp.name)
                    return

                except requests.exceptions.Timeout:
                    self.status.emit(f"⚠️ 格式 {fmt} 超时")
                except Exception as e:
                    self.status.emit(f"⚠️ 格式 {fmt} 异常: {str(e)}")

            self.error.emit("所有音频格式均失败，请检查网络和API Key")

        except Exception as e:
            self.error.emit(f"请求失败: {str(e)}")

# ========== 主窗口 ==========
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("小米语音朗读器")
        self.setFixedSize(700, 500)

        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background: #f6f9fc;
            }
            QTextEdit {
                border: 2px solid #dde3ed;
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
                background: #fafcff;
                font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
            }
            QTextEdit:focus {
                border-color: #ff6b35;
            }
            QPushButton {
                border-radius: 20px;
                padding: 8px 24px;
                font-size: 14px;
                font-weight: 600;
                border: none;
            }
            QPushButton#speakBtn {
                background: #ff6b35;
                color: white;
            }
            QPushButton#speakBtn:hover {
                background: #e85a2a;
            }
            QPushButton#speakBtn:disabled {
                background: #ccc;
                color: #888;
            }
            QPushButton#stopBtn {
                background: #eef2f7;
                color: #1f3a5f;
                border: 2px solid #c8d7e9;
            }
            QPushButton#stopBtn:hover {
                background: #dce5ef;
            }
            QComboBox {
                border-radius: 20px;
                padding: 6px 16px;
                border: 2px solid #cbd8e8;
                background: white;
                font-size: 13px;
                min-width: 120px;
            }
            QComboBox:focus {
                border-color: #ff6b35;
            }
            QGroupBox {
                border: none;
                margin-top: 10px;
                font-weight: 600;
                font-size: 13px;
                color: #1f3a5f;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #dde3ed;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ff6b35;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QStatusBar {
                background: transparent;
                color: #4a5b6f;
                font-size: 13px;
            }
            QLabel#statusLabel {
                color: #4a5b6f;
                font-size: 13px;
                padding: 4px 12px;
                background: #eef4fa;
                border-radius: 16px;
            }
        """)

        # 中央控件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        # 标题
        title = QLabel("🔊 小米语音朗读器")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #0b1e33;")
        layout.addWidget(title)

        subtitle = QLabel("粘贴文本，选择音色，点击朗读 — 基于小米 MiMo-TTS")
        subtitle.setStyleSheet("color: #4a5b6f; font-size: 13px; border-left: 4px solid #ff6b35; padding-left: 12px; background: #f0f5fa; border-radius: 0 8px 8px 0;")
        layout.addWidget(subtitle)

        # 文本框
        self.textEdit = QTextEdit()
        self.textEdit.setPlaceholderText("在此粘贴要朗读的文本...")
        self.textEdit.setText("在苍茫的大海上，狂风卷集着乌云。在乌云和大海之间，海燕像黑色的闪电，在高傲地飞翔。")
        layout.addWidget(self.textEdit)

        # 控制栏
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(12)

        # 音色选择
        voice_group = QWidget()
        voice_group.setStyleSheet("background: #f2f6fc; border-radius: 30px; padding: 4px 16px;")
        vg_layout = QHBoxLayout(voice_group)
        vg_layout.setContentsMargins(0, 0, 0, 0)
        vg_layout.addWidget(QLabel("🎤 音色"))
        self.voiceCombo = QComboBox()
        self.voiceCombo.addItems(["茉莉", "冰糖", "苏打", "白桦", "mimo_default"])
        self.voiceCombo.setCurrentText("冰糖")
        vg_layout.addWidget(self.voiceCombo)
        ctrl_layout.addWidget(voice_group)

        # 音量
        vol_group = QWidget()
        vol_group.setStyleSheet("background: #f2f6fc; border-radius: 30px; padding: 4px 16px;")
        vol_layout = QHBoxLayout(vol_group)
        vol_layout.setContentsMargins(0, 0, 0, 0)
        vol_layout.addWidget(QLabel("🔊"))
        self.volumeSlider = QSlider(Qt.Horizontal)
        self.volumeSlider.setRange(0, 100)
        self.volumeSlider.setValue(80)
        self.volumeSlider.setFixedWidth(80)
        vol_layout.addWidget(self.volumeSlider)
        ctrl_layout.addWidget(vol_group)

        ctrl_layout.addStretch()

        # 按钮
        self.speakBtn = QPushButton("▶ 朗读")
        self.speakBtn.setObjectName("speakBtn")
        self.speakBtn.clicked.connect(self.onSpeak)
        self.speakBtn.setFixedHeight(40)
        ctrl_layout.addWidget(self.speakBtn)

        self.stopBtn = QPushButton("⏹ 停止")
        self.stopBtn.setObjectName("stopBtn")
        self.stopBtn.clicked.connect(self.onStop)
        self.stopBtn.setFixedHeight(40)
        ctrl_layout.addWidget(self.stopBtn)

        # 字符数
        self.charLabel = QLabel("0 字符")
        self.charLabel.setStyleSheet("background: #eef4fa; border-radius: 16px; padding: 4px 12px; color: #59748f; font-size: 13px;")
        ctrl_layout.addWidget(self.charLabel)

        layout.addLayout(ctrl_layout)

        # 状态栏
        status_layout = QHBoxLayout()
        self.statusLabel = QLabel("就绪，粘贴文本后点击朗读")
        self.statusLabel.setObjectName("statusLabel")
        status_layout.addWidget(self.statusLabel)
        status_layout.addStretch()
        status_layout.addWidget(QLabel("MiMo-TTS · Key 已集成"))
        layout.addLayout(status_layout)

        # 提示
        footer = QLabel("⚡ 点击「朗读」后请稍等，音频生成需要几秒钟")
        footer.setStyleSheet("background: #f2f7fc; border-radius: 20px; padding: 6px 16px; color: #6b7f96; font-size: 12px;")
        layout.addWidget(footer)

        # 状态变量
        self.worker = None
        self.audio_file = None
        self.is_playing = False

        # 更新字符数
        self.textEdit.textChanged.connect(self.updateCharCount)
        self.updateCharCount()

    def updateCharCount(self):
        count = len(self.textEdit.toPlainText())
        self.charLabel.setText(f"{count} 字符")

    def onSpeak(self):
        text = self.textEdit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请先输入要朗读的文本")
            return
        if len(text) > 1200:
            QMessageBox.warning(self, "提示", "文本超过 1200 字符，请缩短")
            return

        # 停止当前播放
        self.onStop()

        voice = self.voiceCombo.currentText()
        volume = self.volumeSlider.value()

        self.speakBtn.setEnabled(False)
        self.speakBtn.setText("⏳ 生成中...")

        self.worker = TTSWorker(text, voice, volume)
        self.worker.status.connect(self.updateStatus)
        self.worker.finished.connect(self.onTTSFinished)
        self.worker.error.connect(self.onTTSError)
        self.worker.start()

    def onTTSFinished(self, filepath):
        self.audio_file = filepath
        self.speakBtn.setEnabled(False)
        self.speakBtn.setText("▶ 播放中...")
        self.is_playing = True
        self.updateStatus("🔊 正在播放...")

        # 用 pygame 播放
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.set_volume(self.volumeSlider.value() / 100)
            pygame.mixer.music.play()

            # 定时检查播放状态
            self.play_timer = QTimer()
            self.play_timer.timeout.connect(self.checkPlayback)
            self.play_timer.start(500)

        except Exception as e:
            self.onTTSError(f"播放失败: {str(e)}")

    def checkPlayback(self):
        if not pygame.mixer.music.get_busy():
            self.play_timer.stop()
            self.is_playing = False
            self.speakBtn.setEnabled(True)
            self.speakBtn.setText("▶ 朗读")
            self.updateStatus("✅ 播放完成")
            # 清理临时文件
            if self.audio_file and os.path.exists(self.audio_file):
                try:
                    os.unlink(self.audio_file)
                except:
                    pass
                self.audio_file = None

    def onTTSError(self, msg):
        self.speakBtn.setEnabled(True)
        self.speakBtn.setText("▶ 朗读")
        self.updateStatus(f"❌ {msg}")
        QMessageBox.critical(self, "错误", msg)

    def onStop(self):
        self.play_timer.stop() if hasattr(self, 'play_timer') and self.play_timer.isActive() else None
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        self.is_playing = False
        self.speakBtn.setEnabled(True)
        self.speakBtn.setText("▶ 朗读")
        self.updateStatus("已停止")

        # 清理临时文件
        if self.audio_file and os.path.exists(self.audio_file):
            try:
                os.unlink(self.audio_file)
            except:
                pass
            self.audio_file = None

        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()

    def updateStatus(self, msg):
        self.statusLabel.setText(msg)

    def closeEvent(self, event):
        self.onStop()
        event.accept()

# ========== 启动 ==========
if __name__ == "__main__":
    # 初始化 pygame 混音器
    try:
        pygame.mixer.init()
    except:
        pass

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # 设置字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())