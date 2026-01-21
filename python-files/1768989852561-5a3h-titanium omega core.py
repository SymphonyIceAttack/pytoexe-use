import sys, os, base64, psutil, sqlite3, hashlib, math, random, string
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import pyqtgraph as pg

# ===============================
# SECURITY & LOGGING MODULE
# ===============================
class SecurityModule:
    def __init__(self):
        self.cipher = None
        self.salt_file = "vault.salt"
        self.db_path = "vault.db"
        self.log_file = "omega.log"
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY,
                site TEXT,
                user TEXT,
                password TEXT
            )
        """)
        conn.close()

    def initialize_cipher(self, password):
        if not os.path.exists(self.salt_file):
            with open(self.salt_file, "wb") as f:
                f.write(os.urandom(16))
        salt = open(self.salt_file, "rb").read()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.cipher = Fernet(key)

    def log_event(self, text):
        if not self.cipher: return
        entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {text}"
        with open(self.log_file, "ab") as f:
            f.write(self.cipher.encrypt(entry.encode()) + b"\n")

    def get_logs(self):
        if not os.path.exists(self.log_file) or not self.cipher:
            return []
        logs = []
        for line in open(self.log_file, "rb"):
            try:
                logs.append(self.cipher.decrypt(line.strip()).decode())
            except:
                pass
        return logs[-20:]

    def generate_password(self, length=20):
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(random.choice(chars) for _ in range(length))

    def encrypt_file(self, path):
        try:
            data = open(path, "rb").read()
            open(path + ".titan", "wb").write(self.cipher.encrypt(data))
            return True
        except:
            return False

    def decrypt_file(self, path):
        try:
            data = open(path, "rb").read()
            open(path.replace(".titan", ""), "wb").write(self.cipher.decrypt(data))
            return True
        except:
            return False

# ===============================
# THREADS
# ===============================
class ScannerThread(QThread):
    progress = pyqtSignal(int)
    found = pyqtSignal(str)
    finished = pyqtSignal(int)

    def entropy(self, data):
        if not data: return 0
        probs = [data.count(b) / len(data) for b in set(data)]
        return -sum(p * math.log2(p) for p in probs)

    def run(self):
        base = os.path.expanduser("~/Downloads")
        if not os.path.exists(base):
            self.finished.emit(0)
            return

        files = [os.path.join(base, f) for f in os.listdir(base)]
        threats = 0
        for i, fp in enumerate(files):
            self.progress.emit(int((i+1)/len(files)*100))
            try:
                data = open(fp, "rb").read()
                if self.entropy(data) > 7.5:
                    self.found.emit(f"⚠️ MAGAS ENTRÓPIA: {os.path.basename(fp)}")
                    threats += 1
            except:
                pass
            self.msleep(25)
        self.finished.emit(threats)

class BackgroundGuard(QThread):
    alert = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        while self.running:
            if psutil.cpu_percent(interval=1) > 95:
                self.alert.emit("Kritikus CPU terhelés!")
            self.msleep(8000)

    def stop(self):
        self.running = False

# ===============================
# MAIN UI
# ===============================
class TitaniumOmega(QWidget):
    def __init__(self):
        super().__init__()
        self.security = SecurityModule()
        self.authenticate()
        self.init_ui()

        self.guard = BackgroundGuard()
        self.guard.alert.connect(self.trigger_alert)
        self.guard.start()

        self.net_data = [0]*60
        self.last_io = psutil.net_io_counters().bytes_recv
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_telemetry)
        self.timer.start(1000)

        self.security.log_event("Rendszer elindítva")

    def closeEvent(self, event):
        self.guard.stop()
        event.accept()

    def authenticate(self):
        pw, ok = QInputDialog.getText(self, "Omega Auth", "Mesterjelszó:", QLineEdit.EchoMode.Password)
        if not ok or len(pw) < 8:
            sys.exit()
        self.security.initialize_cipher(pw)

    def init_ui(self):
        self.setWindowTitle("TITANIUM OMEGA 2026 – APEX")
        self.resize(1200, 800)

        layout = QHBoxLayout(self)
        sidebar = QVBoxLayout()
        self.stack = QStackedWidget()

        for i, name in enumerate(["Dashboard","Scanner","Network","Vault","Passwords","Logs"]):
            b = QPushButton(name)
            b.clicked.connect(lambda _, x=i: self.switch_page(x))
            sidebar.addWidget(b)

        layout.addLayout(sidebar)
        layout.addWidget(self.stack)

        self.status = QLabel("ÁLLAPOT: VÉDETT ✅")
        self.stack.addWidget(self.status)

        self.scan_list = QListWidget()
        self.pbar = QProgressBar()
        sb = QPushButton("Scan"); sb.clicked.connect(self.start_scan)
        w = QWidget(); l = QVBoxLayout(w)
        l.addWidget(self.scan_list); l.addWidget(self.pbar); l.addWidget(sb)
        self.stack.addWidget(w)

        self.plot = pg.PlotWidget(); self.curve = self.plot.plot()
        self.stack.addWidget(self.plot)

        v = QWidget(); vl = QVBoxLayout(v)
        eb = QPushButton("Encrypt"); db = QPushButton("Decrypt")
        eb.clicked.connect(self.enc_ui); db.clicked.connect(self.dec_ui)
        vl.addWidget(eb); vl.addWidget(db)
        self.stack.addWidget(v)

        self.p_list = QListWidget()
        ab = QPushButton("Add Password"); ab.clicked.connect(self.add_pw_ui)
        pw = QWidget(); pl = QVBoxLayout(pw)
        pl.addWidget(self.p_list); pl.addWidget(ab)
        self.stack.addWidget(pw)

        self.log_list = QListWidget()
        self.stack.addWidget(self.log_list)

    def switch_page(self, i):
        self.stack.setCurrentIndex(i)
        if i == 4:
            self.refresh_pws()
        if i == 5:
            self.log_list.clear()
            self.log_list.addItems(self.security.get_logs())

    def update_telemetry(self):
        io = psutil.net_io_counters().bytes_recv
        self.net_data = self.net_data[1:] + [(io - self.last_io)/1024]
        self.last_io = io
        self.curve.setData(self.net_data)

    def trigger_alert(self, msg):
        self.status.setText("VESZÉLY ⚠️")
        self.security.log_event(msg)

    def start_scan(self):
        self.scan_list.clear()
        self.worker = ScannerThread()
        self.worker.progress.connect(self.pbar.setValue)
        self.worker.found.connect(self.scan_list.addItem)
        self.worker.finished.connect(lambda x: self.security.log_event(f"Scan kész: {x}"))
        self.worker.start()

    def enc_ui(self):
        f,_ = QFileDialog.getOpenFileName(self,"Encrypt")
        if f and self.security.encrypt_file(f):
            self.security.log_event(f"Titkosítva: {f}")

    def dec_ui(self):
        f,_ = QFileDialog.getOpenFileName(self,"Decrypt","","Titan (*.titan)")
        if f and self.security.decrypt_file(f):
            self.security.log_event(f"Visszafejtve: {f}")

    def add_pw_ui(self):
        site,ok = QInputDialog.getText(self,"Site","Weboldal:")
        pwd = self.security.generate_password()
        if ok:
            conn = sqlite3.connect(self.security.db_path)
            conn.execute(
                "INSERT INTO credentials (site,user,password) VALUES (?,?,?)",
                (site,"user",self.security.cipher.encrypt(pwd.encode()).decode())
            )
            conn.commit(); conn.close()
            self.refresh_pws()
            self.security.log_event(f"Új jelszó: {site}")

    def refresh_pws(self):
        self.p_list.clear()
        conn = sqlite3.connect(self.security.db_path)
        for s,u,p in conn.execute("SELECT site,user,password FROM credentials"):
            try: pw = self.security.cipher.decrypt(p.encode()).decode()
            except: pw = "***"
            self.p_list.addItem(f"{s} | {u} | {pw}")
        conn.close()

# ===============================
# ENTRY POINT
# ===============================
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    w = TitaniumOmega()
    w.show()
    sys.exit(app.exec())