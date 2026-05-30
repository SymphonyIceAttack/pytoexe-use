import sys
import random
import requests
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

API_URL = "http://61kl.jiangxx.tbit.xin/61/get.php"


def log(msg):
    """强制终端输出"""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ================= 关闭按钮 =================
class CloseButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("✕", parent)
        self.setFixedSize(48, 48)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background: rgba(255, 50, 50, 230);
                color: white;
                font-size: 24px;
                font-weight: bold;
                border-radius: 24px;
            }
            QPushButton:hover {
                background: rgba(255, 0, 0, 255);
            }
        """)


# ================= 主窗口 =================
class DanmuWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.raw_list = []
        self.play_queue = []
        self.shown_ids = set()
        self.screen_danmus = []

        log("🎈 六一弹幕程序启动")
        self.init_ui()
        self.init_timers()
        self.load_data()

    def init_ui(self):
        self.setWindowTitle("六一弹幕")
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(QApplication.primaryScreen().geometry())

        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.close_btn = CloseButton(self)
        self.close_btn.move(self.width() - 65, 10)
        self.close_btn.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.close_btn.clicked.connect(self.close_app)

        self.colors = [
            QColor("#FF69B4"),
            QColor("#4169E1"),
            QColor("#32CD32"),
            QColor("#FF4500"),
            QColor("#9370DB"),
            QColor("#00CED1"),
        ]

        log("✅ UI 初始化完成")

    def load_data(self):
        log("📥 正在拉取弹幕数据...")
        try:
            r = requests.get(API_URL, timeout=5).json()
            if r.get("code") != 0:
                log("❌ API 返回错误")
                return

            for item in reversed(r.get("data", [])):
                uid = f"{item['nickname']}|{item['content']}|{item['time']}"
                if uid in self.shown_ids:
                    continue

                self.raw_list.insert(0, item)
                self.shown_ids.add(uid)

            self.play_queue = self.raw_list.copy()
            log(f"✅ 共加载 {len(self.raw_list)} 条弹幕（最新优先）")

        except Exception as e:
            log(f"❌ 加载失败: {e}")
            if not self.raw_list:
                self.raw_list = [
                    {"nickname": "系统", "content": "六一快乐 🎈", "time": "00:00"},
                    {"nickname": "管理员", "content": "终端测试弹幕", "time": "00:01"},
                ]
                self.play_queue = self.raw_list.copy()
                log("⚠️ 使用本地测试数据")

    def init_timers(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(60)

        self.reload = QTimer(self)
        self.reload.timeout.connect(self.load_data)
        self.reload.start(4000)

        log("⏱ 定时器已启动")

    def tick(self):
        if not self.play_queue:
            log("🔄 弹幕播放完毕，重新循环")
            self.play_queue = self.raw_list.copy()

        if self.play_queue and random.random() < 0.35:
            item = self.play_queue.pop(0)
            text = f"{item['nickname']}：{item['content']}"

            self.screen_danmus.append({
                "x": self.width(),
                "y": random.randint(80, self.height() - 120),
                "text": text,
                "speed": random.uniform(2.2, 5.2),
                "color": random.choice(self.colors),
                "size": random.randint(18, 26),
                "alpha": 255
            })

        for d in self.screen_danmus:
            d["x"] -= d["speed"]
            if d["x"] < -400:
                d["alpha"] = max(0, d["alpha"] - 6)

        self.screen_danmus = [d for d in self.screen_danmus if d["alpha"] > 0]
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)

        for d in self.screen_danmus:
            c = QColor(d["color"])
            c.setAlpha(d["alpha"])
            p.setPen(c)
            p.setFont(QFont("Microsoft YaHei", d["size"], QFont.Bold))
            p.drawText(int(d["x"]), int(d["y"]), d["text"])

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close_app()

    def resizeEvent(self, e):
        self.close_btn.move(self.width() - 65, 10)

    def close_app(self):
        log("🛑 弹幕程序已关闭")
        QApplication.quit()


# ================= main =================
if __name__ == "__main__":
    log("🚀 Python 弹幕程序开始执行")
    app = QApplication(sys.argv)
    win = DanmuWindow()
    win.showFullScreen()
    sys.exit(app.exec_())