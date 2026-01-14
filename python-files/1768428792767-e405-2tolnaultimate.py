import sys, os, hashlib, platform, uuid, webbrowser, logging, json, datetime
import pyqtgraph as pg
import psutil, requests
from pathlib import Path
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# ============================================================
# 1. ÜZLETI ÉS LICENC ADATOK - MAJSAI ISTVÁN
# ============================================================
DEV_NAME = "Majsai István"
CONTACT_EMAIL = "istvanmajsai70@gmail.com"
CONTACT_PHONE = "06306260688"
IBAN_NUMBER = "HU37 1177 3195 0317 0124 0000 0000"
VERSION = "4.0.0-GOLD"

# ============================================================
# 2. INTELLIGENS MODULOK (AI & LOGISZTIKA)
# ============================================================
class SystemAI:
    def __init__(self):
        self.cpu_hist = []
    def update(self, cpu):
        self.cpu_hist.append(cpu)
        if len(self.cpu_hist) > 50: self.cpu_hist.pop(0)
    def diagnose(self):
        if not self.cpu_hist: return "Elemzés..."
        avg = sum(self.cpu_hist) / len(self.cpu_hist)
        if avg > 85: return "⚠ KRITIKUS: CPU túlterhelés!"
        if avg > 50: return "⚡ Rendszer leterhelt"
        return "✅ Optimális működés"

class SystemLogistics:
    def __init__(self):
        self.f = Path("enterprise_log.json")
        if not self.f.exists(): self.save([])
    def save(self, d):
        with open(self.f, "w") as f: json.dump(d, f, indent=2)
    def log_event(self, d):
        try:
            with open(self.f, "r") as f: logs = json.load(f)
            d['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logs.append(d)
            self.save(logs[-100:]) 
        except: pass

# ============================================================
# 3. ADATGYŰJTŐ MOTOR (HÁTTÉRSZÁL)
# ============================================================
class DataEngine(QThread):
    stats_signal = pyqtSignal(dict)
    def run(self):
        while not self.isInterruptionRequested():
            try:
                data = {
                    'cpu': psutil.cpu_percent(interval=0.5),
                    'ram': psutil.virtual_memory().percent,
                    'disk': psutil.disk_usage('/').percent
                }
                self.stats_signal.emit(data)
            except: pass
            self.msleep(500)

# ============================================================
# 4. PRÉMIUM FELÜLET (GUI)
# ============================================================
class TitaniumApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Egyedi Hardver ID generálás
        raw_id = f"{uuid.getnode()}{platform.machine()}{os.getlogin()}"
        self.hwid = hashlib.sha256(raw_id.encode()).hexdigest()[:16].upper()
        
        self.system_ai = SystemAI()
        self.logistics = SystemLogistics()
        self.init_ui()
        self.start_engine()

    def init_ui(self):
        self.setWindowTitle(f"Tolna Enterprise Gold - {VERSION} | ID: {self.hwid}")
        self.setMinimumSize(1100, 750)
        
        # Sötét Modern Stílus
        self.setStyleSheet("""
            QMainWindow { background-color: #05070a; }
            #Sidebar { background-color: #0b0e14; border-right: 1px solid #1c222d; min-width: 260px; }
            QPushButton { 
                background-color: #0078d4; color: white; border-radius: 6px; 
                padding: 12px; font-weight: bold; border: none; margin: 5px; 
                text-align: left; padding-left: 20px; 
            }
            QPushButton:hover { background-color: #005a9e; }
            QLabel { color: #e2e8f0; font-family: 'Segoe UI'; }
            QStatusBar { background-color: #0b0e14; color: #64748b; border-top: 1px solid #1c222d; }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0,0,0,0)

        # OLDALSÁV (Sidebar)
        sidebar = QFrame(); sidebar.setObjectName("Sidebar")
        s_layout = QVBoxLayout(sidebar)
        
        logo = QLabel("TOLNA MI\nULTIMATE"); logo.setStyleSheet("font-size: 20px; font-weight: 900; color: #0078d4; margin: 20px 0;"); logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s_layout.addWidget(logo)

        self.btn_dash = QPushButton("📊 Dashboard")
        self.btn_pay = QPushButton("💳 Aktiválás")
        self.btn_supp = QPushButton("📞 Kapcsolat")
        
        for b in [self.btn_dash, self.btn_pay, self.btn_supp]: s_layout.addWidget(b)
        s_layout.addStretch()
        s_layout.addWidget(QLabel(f"Hardware ID:\n{self.hwid}"))
        layout.addWidget(sidebar)

        # TARTALOM (Pages)
        self.pages = QStackedWidget()
        layout.addWidget(self.pages)
        self.init_pages()

        self.btn_dash.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        self.btn_pay.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        self.btn_supp.clicked.connect(lambda: self.pages.setCurrentIndex(2))

    def init_pages(self):
        # Dashboard Oldal
        p1 = QWidget(); l1 = QVBoxLayout(p1)
        l1.addWidget(QLabel("<h1>Rendszeranalitika</h1>"))
        self.plot = pg.PlotWidget(); self.plot.setBackground('#0b0e14')
        self.plot.setYRange(0, 100); self.curve = self.plot.plot(pen=pg.mkPen('#0078d4', width=3))
        self.history = []
        l1.addWidget(self.plot)
        self.ai_label = QLabel("AI STATUS: Elemzés..."); self.ai_label.setStyleSheet("color: #10b981; font-weight: bold; background: #0f172a; padding: 10px; border-radius: 5px;")
        l1.addWidget(self.ai_label)
        self.pages.addWidget(p1)

        # Fizetés Oldal
        p2 = QWidget(); l2 = QVBoxLayout(p2)
        l2.addWidget(QLabel("<h1>Aktiválás és Fizetés</h1>"))
        info = QFrame(); info.setStyleSheet("background: #0f172a; border-radius: 12px; padding: 25px;"); il = QVBoxLayout(info)
        il.addWidget(QLabel(f"<b>Kedvezményezett:</b> {DEV_NAME}"))
        il.addWidget(QLabel(f"<b>IBAN utalás:</b><br><span style='color:#3b82f6; font-size:22px;'>{IBAN_NUMBER}</span>"))
        il.addWidget(QLabel(f"<b>Közlemény (HWID):</b> {self.hwid}"))
        l2.addWidget(info)
        btn_stripe = QPushButton("💳 Stripe Fizetés"); btn_stripe.setStyleSheet("background: #059669; text-align: center;")
        btn_stripe.clicked.connect(lambda: webbrowser.open(f"https://stripe.com/?client_id={self.hwid}"))
        l2.addWidget(btn_stripe); l2.addStretch(); self.pages.addWidget(p2)

        # Kapcsolat Oldal
        p3 = QWidget(); l3 = QVBoxLayout(p3)
        l3.addWidget(QLabel(f"<h1>Support</h1><p>Email: {CONTACT_EMAIL}</p><p>Tel: {CONTACT_PHONE}</p>"))
        l3.addStretch(); self.pages.addWidget(p3)

    def start_engine(self):
        self.engine = DataEngine()
        self.engine.stats_signal.connect(self.update_ui)
        self.engine.start()

    def update_ui(self, data):
        self.history.append(data['cpu'])
        if len(self.history) > 60: self.history.pop(0)
        self.curve.setData(self.history)
        self.statusBar().showMessage(f"CPU: {data['cpu']}% | RAM: {data['ram']}% | DISK: {data['disk']}%")
        self.system_ai.update(data['cpu'])
        self.ai_label.setText(f"AI STATUS: {self.system_ai.diagnose()}")
        self.logistics.log_event(data)

    def closeEvent(self, event):
        self.engine.requestInterruption(); self.engine.wait(); event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setStyle("Fusion")
    dark_p = QPalette()
    dark_p.setColor(QPalette.ColorRole.Window, QColor(5, 7, 10))
    dark_p.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    app.setPalette(dark_p)
    main_win = TitaniumApp(); main_win.show()
    sys.exit(app.exec())
