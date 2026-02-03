import sys, os, sqlite3, subprocess, traceback, shutil
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

try:
    import minecraft_launcher_lib
except ImportError:
    print("Ошибка: Установите библиотеку: pip install minecraft-launcher-lib")

try:
    from mcstatus import JavaServer
except ImportError:
    JavaServer = None

# ==========================================
# КОНФИГ
# ==========================================
SERVER_IP = "188.127.241.8"
SERVER_PORT = 13072
SERVER_NAME = "TheWortex DivineRPG"
VERSION = "1.7.10"
# ==========================================

BD = os.path.dirname(os.path.abspath(__file__))
GD = os.path.join(BD, "GameData")
DB_PATH = os.path.join(BD, "users.db")

os.makedirs(GD, exist_ok=True)
os.makedirs(os.path.join(GD, "versions"), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS users (login TEXT UNIQUE, pass TEXT)")
    conn.commit(); conn.close()

MC_BUTTON = """
QPushButton {
    background-color: #4e7329;
    color: white;
    border: 2px solid #000;
    border-bottom: 4px solid #1a290d;
    padding: 5px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #5d8a31;
    border-color: #39ff14;
}
"""

DOWNLOAD_BTN_STYLE = """
QPushButton {
    background-color: #1a4d8b;
    color: white;
    border: 2px solid #000;
    border-bottom: 4px solid #0d2845;
    font-weight: 1000;
    font-size: 14px;
}
QPushButton:hover {
    background-color: #2664b3;
    border-color: #00dfff;
}
"""

class BaseWin(QWidget):
    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(60, 45, 35)) 
        tile = 30
        for x in range(0, self.width(), tile):
            color = QColor(75, 110, 45) if (x // tile) % 2 == 0 else QColor(60, 90, 35)
            p.fillRect(x, 0, tile, 35, color)
            p.fillRect(x, 35, tile, 5, QColor(0, 0, 0, 100))

class LoginWin(QDialog, BaseWin):
    def __init__(self):
        super().__init__()
        self.setFixedSize(450, 500); self.setWindowFlags(Qt.FramelessWindowHint); self.user_name = None
        l = QVBoxLayout(self); l.setContentsMargins(50, 80, 50, 50)
        t = QLabel("THE WORTEX"); t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet("font-size: 48px; color: #39ff14; font-weight: 1000;")
        l.addWidget(t)
        s = "padding: 15px; background: #222; border: 2px solid #444; color: white; font-size: 16px; font-weight: bold;"
        self.u = QLineEdit(); self.u.setPlaceholderText("НИКНЕЙМ"); self.u.setStyleSheet(s); l.addWidget(self.u)
        self.p = QLineEdit(); self.p.setPlaceholderText("ПАРОЛЬ"); self.p.setStyleSheet(s); self.p.setEchoMode(QLineEdit.Password); l.addWidget(self.p)
        self.btn_in = QPushButton("ВОЙТИ"); self.btn_in.setStyleSheet(MC_BUTTON); self.btn_in.setFixedHeight(60); self.btn_in.clicked.connect(self.auth); l.addWidget(self.btn_in)
        self.btn_reg = QPushButton("РЕГИСТРАЦИЯ"); self.btn_reg.setStyleSheet("color: #39ff14; border: none; font-size: 15px; font-weight: 1000;"); self.btn_reg.clicked.connect(self.reg); l.addWidget(self.btn_reg)
        self.msg = QLabel(""); self.msg.setAlignment(Qt.AlignCenter); self.msg.setStyleSheet("color: #ff5555; font-weight: bold;"); l.addWidget(self.msg)

    def auth(self):
        u, p = self.u.text(), self.p.text()
        c = sqlite3.connect(DB_PATH); r = c.execute("SELECT pass FROM users WHERE login=?", (u,)).fetchone(); c.close()
        if r and r[0] == p: self.user_name = u; self.accept()
        else: self.msg.setText("✕ ОШИБКА ДАННЫХ")

    def reg(self):
        u, p = self.u.text(), self.p.text()
        try:
            c = sqlite3.connect(DB_PATH); c.execute("INSERT INTO users VALUES (?,?)", (u, p)); c.commit(); c.close()
            self.msg.setText("✓ ГОТОВО!"); self.msg.setStyleSheet("color: #39ff14;")
        except: self.msg.setText("✕ НИК ЗАНЯТ")

    def mousePressEvent(self, e): self.oldPos = e.globalPos()
    def mouseMoveEvent(self, e):
        delta = QPoint(e.globalPos() - self.oldPos); self.move(self.x() + delta.x(), self.y() + delta.y()); self.oldPos = e.globalPos()

class MainWin(QMainWindow, BaseWin):
    def __init__(self, user):
        super().__init__(); self.user = user
        self.setFixedSize(1000, 750); self.setWindowFlags(Qt.FramelessWindowHint); self.setWindowOpacity(0.0)
        c = QWidget(); self.setCentralWidget(c)
        
        # ВЕРХНЯЯ ПАНЕЛЬ
        self.top_box = QWidget(self); self.top_box.setGeometry(650, 45, 330, 100)
        tc_lay = QVBoxLayout(self.top_box)
        btns = QHBoxLayout()
        btn_min = QPushButton("_"); btn_min.setFixedSize(35,35); btn_min.setStyleSheet(MC_BUTTON); btn_min.clicked.connect(self.showMinimized)
        btn_cls = QPushButton("✕"); btn_cls.setFixedSize(35,35); btn_cls.setStyleSheet(MC_BUTTON.replace("#4e7329", "#992222")); btn_cls.clicked.connect(sys.exit)
        btns.addStretch(); btns.addWidget(btn_min); btns.addWidget(btn_cls); tc_lay.addLayout(btns)
        
        user_row = QHBoxLayout()
        self.lbl_u = QLabel(f"ИГРОК: {self.user}"); self.lbl_u.setStyleSheet("color: white; font-weight: 1000; font-size: 18px;")
        self.set_btn = QPushButton("⚙"); self.set_btn.setFixedSize(45, 45); self.set_btn.setStyleSheet(MC_BUTTON)
        m = QMenu(self); m.setStyleSheet("background: #222; color: white; border: 1px solid #39ff14;")
        m.addAction("Очистить папку GameData").triggered.connect(self.clean_data)
        self.set_btn.setMenu(m); user_row.addStretch(); user_row.addWidget(self.lbl_u); user_row.addWidget(self.set_btn); tc_lay.addLayout(user_row)

        self.logo = QLabel("THE WORTEX", self); self.logo.setGeometry(0, 100, 1000, 100); self.logo.setAlignment(Qt.AlignCenter)
        self.logo.setStyleSheet("font-size: 85px; color: #39ff14; font-weight: 1000; letter-spacing: 12px;")

        # ЛОГИ
        self.log_area = QTextEdit(self); self.log_area.setGeometry(50, 220, 900, 220); self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background: rgba(0, 0, 0, 200); border: 1px solid #39ff14; color: #39ff14; font-family: 'Consolas'; font-size: 11px;")
        
        # ПАНЕЛЬ СЛЕВА (ОЗУ + СКАЧАТЬ)
        self.left_panel = QWidget(self); self.left_panel.setGeometry(50, 460, 250, 250)
        lpl = QVBoxLayout(self.left_panel)
        
        lpl.addWidget(QLabel("ВЫДЕЛЕНИЕ ОЗУ:", styleSheet="color: #eee; font-weight: bold;"))
        self.ram = QComboBox(); self.ram.setFixedSize(220, 45); self.ram.addItems(["1024 MB", "2048 MB", "4096 MB", "8192 MB"]); self.ram.setCurrentIndex(2)
        self.ram.setStyleSheet("background: #111; color: #39ff14; border: 2px solid #39ff14; font-weight: 1000;"); lpl.addWidget(self.ram)
        
        lpl.addSpacing(20)
        
        self.btn_download = QPushButton("СКАЧАТЬ ВСЕ ФАЙЛЫ"); self.btn_download.setFixedSize(220, 60)
        self.btn_download.setStyleSheet(DOWNLOAD_BTN_STYLE); self.btn_download.clicked.connect(lambda: self.start_process(only_download=True))
        lpl.addWidget(self.btn_download)

        # ПАНЕЛЬ СПРАВА (СЕРВЕР + ИГРАТЬ)
        self.bot_right = QWidget(self); self.bot_right.setGeometry(650, 460, 330, 250); brl = QVBoxLayout(self.bot_right)
        self.srv_l = QLabel(SERVER_NAME); self.srv_l.setStyleSheet("font-size: 28px; color: #39ff14; font-weight: 1000;"); self.srv_l.setAlignment(Qt.AlignRight)
        self.on_l = QLabel("ПРОВЕРКА..."); self.on_l.setStyleSheet("color: #ccc; font-weight: bold;"); self.on_l.setAlignment(Qt.AlignRight)
        self.btn_go = QPushButton("ИГРАТЬ!"); self.btn_go.setFixedSize(300, 100); self.btn_go.setStyleSheet(MC_BUTTON.replace("font-weight: bold;", "font-size: 42px; font-weight: 1000; background: #39ff14; color: black;")); self.btn_go.clicked.connect(lambda: self.start_process(only_download=False))
        brl.addWidget(self.srv_l); brl.addWidget(self.on_l); brl.addWidget(self.btn_go)

        self.anim_fade = QPropertyAnimation(self, b"windowOpacity"); self.anim_fade.setDuration(800); self.anim_fade.setStartValue(0.0); self.anim_fade.setEndValue(1.0); self.anim_fade.start()
        self.timer = QTimer(); self.timer.timeout.connect(self.upd_srv); self.timer.start(10000); self.upd_srv()
        self.log_msg("Лаунчер готов. Нажмите 'СКАЧАТЬ ВСЕ ФАЙЛЫ', если запускаете впервые.")

    def log_msg(self, msg):
        self.log_area.append(f"> {msg}"); self.log_area.ensureCursorVisible(); QCoreApplication.processEvents()

    def upd_srv(self):
        if JavaServer:
            try:
                s = JavaServer.lookup(f"{SERVER_IP}:{SERVER_PORT}").status()
                self.on_l.setText(f"ОНЛАЙН: {s.players.online}/{s.players.max}")
                self.on_l.setStyleSheet("color: #39ff14; font-weight: bold;")
            except: self.on_l.setText("СЕРВЕР ВЫКЛЮЧЕН"); self.on_l.setStyleSheet("color: #ff4d4d; font-weight: bold;")

    def clean_data(self):
        if os.path.exists(GD):
            shutil.rmtree(GD); os.makedirs(GD); os.makedirs(os.path.join(GD, "versions"))
            self.log_msg("Папка GameData очищена.")

    def start_process(self, only_download=False):
        self.btn_go.setEnabled(False); self.btn_download.setEnabled(False)
        QTimer.singleShot(100, lambda: self.run_task(only_download))

    def run_task(self, only_download):
        try:
            self.log_msg("--- НАЧАЛО ПРОЦЕССА ---")
            v_path = os.path.join(GD, "versions")
            
            # 1. Скачивание Minecraft
            self.log_msg(f"Проверка клиента Minecraft {VERSION}...")
            minecraft_launcher_lib.install.install_minecraft_version(VERSION, GD)
            
            # 2. Установка Forge
            self.log_msg("Проверка и установка Forge (это может занять время)...")
            fv = minecraft_launcher_lib.forge.find_forge_version(VERSION)
            if not fv:
                self.log_msg("Ошибка: Forge не найден для 1.7.10")
                self.reset_btns(); return
            
            minecraft_launcher_lib.forge.install_forge_version(fv, GD)
            
            # 3. Поиск установленной версии
            final_v = None
            for root, dirs, files in os.walk(v_path):
                for file in files:
                    if file.endswith(".json") and "forge" in file.lower():
                        final_v = os.path.splitext(file)[0]; break
            
            if not final_v:
                self.log_msg("Ошибка: Не удалось найти JSON Forge.")
                self.reset_btns(); return

            self.log_msg("Проверка файлов успешно завершена!")

            if only_download:
                self.log_msg("Все файлы готовы к запуску. Теперь можно нажать 'ИГРАТЬ'.")
                self.reset_btns()
                return

            # 4. Запуск игры
            ram = self.ram.currentText().split(" ")[0]
            options = {
                "username": self.user,
                "server": SERVER_IP,
                "port": str(SERVER_PORT),
                "jvmArguments": [f"-Xmx{ram}M"]
            }
            
            self.log_msg(f"Запуск {final_v} с {ram}MB ОЗУ...")
            command = minecraft_launcher_lib.command.get_minecraft_command(final_v, GD, options)
            subprocess.Popen(command)
            self.log_msg("Игра запускается. Лаунчер закроется через 5 секунд.")
            QTimer.singleShot(5000, sys.exit)
            
        except Exception as e:
            self.log_msg(f"КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
            self.reset_btns()

    def reset_btns(self):
        self.btn_go.setEnabled(True); self.btn_download.setEnabled(True)

    def mousePressEvent(self, e): self.oldPos = e.globalPos()
    def mouseMoveEvent(self, e):
        delta = QPoint(e.globalPos() - self.oldPos); self.move(self.x() + delta.x(), self.y() + delta.y()); self.oldPos = e.globalPos()

if __name__ == "__main__":
    init_db(); a = QApplication(sys.argv)
    l = LoginWin()
    if l.exec_() == QDialog.Accepted:
        w = MainWin(l.user_name); w.show(); sys.exit(a.exec_())