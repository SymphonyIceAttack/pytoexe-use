import sys, os, base64, psutil, sqlite3, hashlib, math, random, string, time, ctypes
from datetime import datetime
from collections import Counter
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTextEdit, QStackedWidget, QProgressBar,
    QFrame, QListWidget, QMessageBox, QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import pyqtgraph as pg

# ===============================
# SECURITY MODULE
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
        conn.execute("CREATE TABLE IF NOT EXISTS credentials (id INTEGER PRIMARY KEY, site TEXT, user TEXT, pass TEXT)")
        conn.close()

    def initialize_cipher(self, password):
        if not os.path.exists(self.salt_file):
            with open(self.salt_file, "wb") as f:
                f.write(os.urandom(16))
        with open(self.salt_file, "rb") as f:
            salt = f.read()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(), length=32, salt=salt,
            iterations=480000, backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.cipher = Fernet(key)

    def log_event(self, text):
        if not self.cipher: return
        entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {text}"
        with open(self.log_file, "ab") as f:
            f.write(self.cipher.encrypt(entry.encode()) + b"\n")

    def get_logs(self):
        if not os.path.exists(self.log_file) or not self.cipher: return []
        logs = []
        with open(self.log_file, "rb") as f:
            for line in f:
                try: logs.append(self.cipher.decrypt(line.strip()).decode())
                except: pass
        return logs[-15:]

    def generate_password(self, length=20):
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(random.choice(chars) for _ in range(length))

    def encrypt_file(self, path):
        try:
            with open(path, "rb") as f: data = f.read()
            with open(path + ".titan", "wb") as f: f.write(self.cipher.encrypt(data))
            return True
        except: return False

    def decrypt_file(self, path):
        try:
            with open(path, "rb") as f: data = f.read()
            out = path.replace(".titan", "")
            with open(out, "wb") as f: f.write(self.cipher.decrypt(data))
            return True
        except: return False

# ===============================
# THREADS: SCANNER & GUARD
# ===============================
class ScannerThread(QThread):
    progress = pyqtSignal(int); found = pyqtSignal(str); finished = pyqtSignal(int)
    def entropy(self, data):
        if not data: return 0
        probs = [float(data.count(b))/len(data) for b in set(data)]
        return -sum(p*math.log2(p) for p in probs)
    def run(self):
        threats=0
        path = os.path.expanduser("~/Downloads")
        if not os.path.exists(path): self.finished.emit(0); return
        files = [os.path.join(path,f) for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))]
        for i,f_p in enumerate(files):
            self.progress.emit(int((i+1)/len(files)*100))
            try:
                with open(f_p,"rb") as f: data=f.read()
                if self.entropy(data) > 7.5:
                    self.found.emit(f"⚠️ HIGH ENTROPY: {os.path.basename(f_p)}")
                    threats +=1
            except: pass
            self.msleep(30)
        self.finished.emit(threats)

class BackgroundGuard(QThread):
    alert = pyqtSignal(str)
    def run(self):
        while True:
            if psutil.cpu_percent(interval=1) > 95: self.alert.emit("CPU OVERLOAD!")
            self.msleep(10000)

# ===============================
# AI RISK ENGINE
# ===============================
class RiskEngine:
    def __init__(self): self.score=0
    def add(self,value): self.score=min(100,self.score+value)
    def reset(self): self.score=0

# ===============================
# MAIN UI
# ===============================
class TitaniumOmega(QWidget):
    def __init__(self):
        super().__init__()
        self.security=SecurityModule()
        self.authenticate()
        self.init_ui()
        self.net_data=[0]*60
        self.last_io=psutil.net_io_counters().bytes_recv
        self.timer=QTimer(); self.timer.timeout.connect(self.update_telemetry); self.timer.start(1000)
        self.guard=BackgroundGuard(); self.guard.alert.connect(self.trigger_alert); self.guard.start()
        self.risk=RiskEngine()
        self.security.log_event("System started.")

    def authenticate(self):
        pw, ok = QInputDialog.getText(self, "Omega Auth","Master password:",QLineEdit.EchoMode.Password)
        if not ok or len(pw)<8: sys.exit()
        self.security.initialize_cipher(pw)

    def init_ui(self):
        self.setWindowTitle("TITANIUM OMEGA 2026")
        self.resize(1200,800)
        self.setStyleSheet("QWidget { background:#0d1117; color:#58a6ff; font-family:Consolas; } QPushButton { background:#21262d; border:1px solid #30363d; padding:10px; border-radius:5px; } QPushButton:hover { background:#30363d; }")
        layout=QHBoxLayout(self)
        sidebar=QFrame(); sidebar.setFixedWidth(200); sl=QVBoxLayout(sidebar)
        self.stack=QStackedWidget()
        pages=["Dashboard","Scanner","Network","Vault","Passwords","Logs"]
        for i,name in enumerate(pages):
            btn=QPushButton(name); btn.clicked.connect(lambda _,x=i:self.stack.setCurrentIndex(x)); sl.addWidget(btn)
        sl.addStretch(); panic=QPushButton("⚠️ PANIC"); panic.setStyleSheet("background:#8b0000;color:white;"); panic.clicked.connect(sys.exit); sl.addWidget(panic)
        # Dashboard
        dash=QWidget(); dl=QVBoxLayout(dash); self.status_lbl=QLabel("STATUS: SECURE ✅"); self.status_lbl.setStyleSheet("font-size:30px;"); dl.addWidget(self.status_lbl); self.stack.addWidget(dash)
        # Scanner
        scan_w=QWidget(); scl=QVBoxLayout(scan_w); self.scan_list=QListWidget(); self.pbar=QProgressBar(); s_btn=QPushButton("Scan"); s_btn.clicked.connect(self.start_scan); scl.addWidget(self.scan_list); scl.addWidget(self.pbar); scl.addWidget(s_btn); self.stack.addWidget(scan_w)
        # Network
        net_w=QWidget(); nl=QVBoxLayout(net_w); self.plot=pg.PlotWidget(); self.curve=self.plot.plot(pen='c'); nl.addWidget(self.plot); self.stack.addWidget(net_w)
        # Vault
        v_w=QWidget(); vl=QVBoxLayout(v_w); eb=QPushButton("Encrypt"); db=QPushButton("Decrypt"); eb.clicked.connect(self.enc_ui); db.clicked.connect(self.dec_ui); vl.addWidget(eb); vl.addWidget(db); self.stack.addWidget(v_w)
        # Passwords
        p_w=QWidget(); pl=QVBoxLayout(p_w); self.p_list=QListWidget(); ab=QPushButton("Add/Gen Password"); ab.clicked.connect(self.add_pw_ui); pl.addWidget(self.p_list); pl.addWidget(ab); self.stack.addWidget(p_w)
        # Logs
        l_w=QWidget(); ll=QVBoxLayout(l_w); self.log_list=QListWidget(); ll.addWidget(QLabel("Encrypted Logs")); ll.addWidget(self.log_list); self.stack.addWidget(l_w)
        layout.addWidget(sidebar); layout.addWidget(self.stack)

    def update_telemetry(self):
        io=psutil.net_io_counters().bytes_recv
        self.net_data=self.net_data[1:] + [(io-self.last_io)/1024]; self.last_io=io
        self.curve.setData(self.net_data)
        if self.stack.currentIndex()==5:
            self.log_list.clear(); self.log_list.addItems(self.security.get_logs())

    def trigger_alert(self,msg):
        self.status_lbl.setText("ALERT ⚠️"); self.status_lbl.setStyleSheet("color:#f85149;font-size:30px;"); self.security.log_event(msg)
        self.risk.add(20)

    def start_scan(self):
        self.scan_list.clear(); self.worker=ScannerThread(); self.worker.progress.connect(self.pbar.setValue); self.worker.found.connect(self.scan_list.addItem); self.worker.finished.connect(lambda x:self.security.log_event(f"Scan complete: {x} hits")); self.worker.start()

    def enc_ui(self):
        f,_=QFileDialog.getOpenFileName(self,"Encrypt")
        if f and self.security.encrypt_file(f): self.security.log_event(f"Encrypted: {f}")

    def dec_ui(self):
        f,_=QFileDialog.getOpenFileName(self,"Decrypt","","Titan (*.titan)")
        if f and self.security.decrypt_file(f): self.security.log_event(f"Decrypted: {f}")

    def add_pw_ui(self):
        gen=self.security.generate_password()
        s,ok1=QInputDialog.getText(self,"Site","Webpage:")
        p,ok2=QInputDialog.getText(self,"Password","Password (generated suggested):",text=gen)
        if ok1 and ok2:
            conn=sqlite3.connect(self.security.db_path)
            conn.execute("INSERT INTO credentials (site,user,pass) VALUES (?,?,?)",(s,"user",self.security.cipher.encrypt(p.encode()).decode()))
            conn.commit(); conn.close(); self.refresh_pws(); self.security.log_event(f"New password added: {s}")

    def refresh_pws(self):
        self.p_list.clear()
        conn=sqlite3.connect(self.security.db_path)
        for r in conn.execute("SELECT site,user,pass FROM credentials").fetchall():
            try: pw=self.security.cipher.decrypt(r[2].encode()).decode()
            except: pw="***"
            self.p_list.addItem(f"{r[0]} | {r[1]} | {pw}")
        conn.close()

if __name__=="__main__":
    app=QApplication(sys.argv); w=TitaniumOmega(); w.show(); sys.exit(app.exec())