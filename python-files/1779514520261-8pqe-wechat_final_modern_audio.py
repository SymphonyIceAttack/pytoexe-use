import sys, ctypes
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer

ACC = "11451419188.@weixin.com"
PWD = "114514"
CODE = "114514"
GREEN = "#07C160"
DARK_MODE = False

ctypes.windll.kernel32.SetConsoleTitleW("WeChat.exe")

def enable_blur(hwnd):
    ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 4, ctypes.byref(ctypes.c_int(1)), 4)

class Login(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(380, 520)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.count = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)

        box = QFrame(self)
        box.setStyleSheet("background:white;border-radius:8px;")
        layout = QVBoxLayout(box)

        title = QLabel("微信")
        title.setFont(QFont("Microsoft YaHei", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color:{GREEN};")

        self.u = QLineEdit()
        self.p = QLineEdit()
        self.c = QLineEdit()

        self.u.setPlaceholderText("账号")
        self.p.setPlaceholderText("密码")
        self.c.setPlaceholderText("验证码")
        self.p.setEchoMode(QLineEdit.Password)

        self.code_btn = QPushButton("发送验证码")
        self.code_btn.setFixedHeight(34)
        self.code_btn.clicked.connect(self.send_code)

        code_row = QHBoxLayout()
        code_row.addWidget(self.c)
        code_row.addWidget(self.code_btn)

        btn = QPushButton("登录")
        btn.setFixedHeight(38)
        btn.setStyleSheet(f"QPushButton{{background:{GREEN};color:white;border-radius:4px;}}")
        btn.clicked.connect(self.login)

        layout.addWidget(title)
        layout.addSpacing(30)
        layout.addWidget(self.u)
        layout.addWidget(self.p)
        layout.addLayout(code_row)
        layout.addSpacing(20)
        layout.addWidget(btn)

        main = QVBoxLayout(self)
        main.setContentsMargins(20, 20, 20, 20)
        main.addWidget(box)

    def send_code(self):
        self.count = 11
        self.code_btn.setEnabled(False)
        self.code_btn.setText("11 秒后重试")
        self.timer.start(1000)

    def tick(self):
        self.count -= 1
        if self.count <= 0:
            self.code_btn.setEnabled(True)
            self.code_btn.setText("发送验证码")
            self.timer.stop()
        else:
            self.code_btn.setText(f"{self.count} 秒后重试")

    def login(self):
        if self.u.text() != ACC or self.p.text() != PWD:
            QMessageBox.warning(self, "错误", "账号或密码错误")
            return
        if self.c.text() != CODE:
            QMessageBox.warning(self, "错误", "验证码错误")
            return
        self.main = Main()
        self.main.show()
        self.close()

class Bubble(QWidget):
    def __init__(self, text, me=True):
        super().__init__()
        self.me = me
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setMaximumWidth(260)
        self.update_style()

        (layout.addWidget if me else layout.addStretch)()
        layout.addWidget(self.label)
        (layout.addStretch if me else layout.addWidget)(None)

    def update_style(self):
        bg = "#2A2A2A" if DARK_MODE else "white"
        fg = "white" if self.me else ("white" if DARK_MODE else "black")
        self.label.setStyleSheet(
            f"padding:8px 12px;border-radius:6px;"
            f"background:{'#057C53' if self.me else bg};color:{fg};"
        )

class Avatar(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.lbl = QLabel("bb")
        self.lbl.setFixedSize(64, 64)
        self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setStyleSheet("background:#07C160;color:white;border-radius:32px;font-size:20px;")
        layout.addWidget(self.lbl, alignment=Qt.AlignHCenter)

    def mouseDoubleClickEvent(self, e):
        QMessageBox.information(self, "拍一拍", "你拍了拍 bb")

class Main(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(940, 660)
        enable_blur(int(self.winId()))

        self.stack = QStackedWidget()
        self.stack.addWidget(self.chat_page())
        self.stack.addWidget(QWidget())
        self.stack.addWidget(QWidget())
        self.stack.addWidget(self.me_page())

        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)
        layout.addWidget(self.bottom_bar())

        self._pos = None

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._pos = e.globalPos()

    def mouseMoveEvent(self, e):
        if self._pos:
            self.move(self.pos() + e.globalPos() - self._pos)
            self._pos = e.globalPos()

    def chat_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        top = QFrame()
        top.setFixedHeight(46)
        top.setStyleSheet("border-bottom:1px solid #444;" if DARK_MODE else "border-bottom:1px solid #ddd;")

        h = QHBoxLayout(top)
        h.addStretch()

        for t in ["📞", "📹", "🧧", "💳", "🌙"]:
            b = QPushButton(t)
            b.setFlat(True)
            b.setFixedSize(36, 36)
            h.addWidget(b)

        chat_area = QVBoxLayout()
        chat_area.addWidget(Bubble("在吗？", False))

        send_btn = QPushButton("发送")
        send_btn.clicked.connect(lambda: chat_area.addWidget(Bubble("好的", True)))

        layout.addWidget(top)
        layout.addLayout(chat_area)
        layout.addWidget(send_btn)
        return page

    def me_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(Avatar(), alignment=Qt.AlignHCenter)
        layout.addWidget(QLabel("bb"), alignment=Qt.AlignHCenter)
        layout.addStretch()
        return w

    def bottom_bar(self):
        bar = QFrame()
        bar.setFixedHeight(46)
        bar.setStyleSheet("background:#FAFAFA;border-top:1px solid #ddd;")
        h = QHBoxLayout(bar)
        for i, n in enumerate(["微信", "通讯录", "发现", "我"]):
            b = QPushButton(n)
            b.setFlat(True)
            b.clicked.connect(lambda _, x=i: self.stack.setCurrentIndex(x))
            h.addWidget(b)
        return bar

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 9))
    Login().show()
    sys.exit(app.exec_())
