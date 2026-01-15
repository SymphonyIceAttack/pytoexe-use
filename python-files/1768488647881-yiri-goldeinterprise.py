import sys, os, hashlib, platform, psutil, uuid, webbrowser, logging
import pyqtgraph as pg
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# ==========================================
# FIXÁLT ÜZLETI ADATOK (MAJSAI ISTVÁN)
# ==========================================
DEV_NAME = "Majsai István"
CONTACT_EMAIL = "istvanmajsai70@gmail.com"
CONTACT_PHONE = "06306260688"
IBAN_NUMBER = "HU37 1177 3195 0317 0124 0000 0000"
STRIPE_LINK = "https://buy.stripe.com/your_live_link_here" # IDE MÁSOLD A VALÓDI LINKET!

# ==========================================
# BIZTONSÁGI SZÁL (OPTIMALIZÁLT)
# ==========================================
class DataWorker(QThread):
    data_sig = pyqtSignal(float, float)
    def run(self):
        while not self.isInterruptionRequested():
            try:
                # Interval=0.1 a simább grafikonért
                cpu = psutil.cpu_percent(interval=0.1)
                ram = psutil.virtual_memory().percent
                self.data_sig.emit(cpu, ram)
                self.msleep(500) # Fél másodpercenkénti frissítés
            except:
                pass

# ==========================================
# PRÉMIUM GUI KERETRENDSZER
# ==========================================
class TitaniumFinal(QMainWindow):
    def __init__(self):
        super().__init__()
        # Egyedi HWID generálás
        raw_hwid = f"{uuid.getnode()}-{platform.processor()}-2026"
        self.hwid = hashlib.sha256(raw_hwid.encode()).hexdigest()[:16].upper()
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"Tolna Enterprise Ultimate - Gold Edition | ID: {self.hwid}")
        self.setMinimumSize(1100, 750)
        
        # Sötét téma alapok
        self.setStyleSheet("""
            QMainWindow { background-color: #05070a; }
            #Sidebar { background-color: #0b0e14; border-right: 1px solid #1c222d; min-width: 240px; }
            QPushButton { 
                background-color: #0078d4; color: white; border-radius: 5px; 
                padding: 12px; font-weight: bold; font-family: 'Segoe UI'; border: none;
            }
            QPushButton:hover { background-color: #005a9e; }
            QLabel { color: #cbd5e1; font-family: 'Segoe UI'; }
            #Header { font-size: 20px; font-weight: bold; color: white; padding: 20px; }
        """)

        # Fő elrendezés
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # 1. SIDEBAR
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        s_layout = QVBoxLayout(sidebar)
        
        logo = QLabel("TOLNA MI\nENTERPRISE")
        logo.setObjectName("Header")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s_layout.addWidget(logo)

        btns = [("📊 DASHBOARD", 0), ("💳 AKTIVÁLÁS", 1), ("📞 ÜGYFÉLSZOLGÁLAT", 2)]
        for text, idx in btns:
            b = QPushButton(text)
            b.clicked.connect(lambda _, i=idx: self.pages.setCurrentIndex(i))
            s_layout.addWidget(b)

        s_layout.addStretch()
        s_layout.addWidget(QLabel(f"Hardware ID:\n{self.hwid}"))
        layout.addWidget(sidebar)

        # 2. CONTENT AREA
        self.pages = QStackedWidget()
        layout.addWidget(self.pages)

        self.setup_dashboard()
        self.setup_payment()
        self.setup_contact()

        # Adatgyűjtés indítása
        self.worker = DataWorker()
        self.worker.data_sig.connect(self.refresh_stats)
        self.worker.start()

    def setup_dashboard(self):
        p = QWidget()
        l = QVBoxLayout(p)
        l.addWidget(QLabel("<h1>Rendszeranalitika</h1>"))
        
        self.plot = pg.PlotWidget()
        self.plot.setBackground('#0b0e14')
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        self.curve = self.plot.plot(pen=pg.mkPen('#0078d4', width=3))
        self.history = []
        
        l.addWidget(self.plot)
        self.pages.addWidget(p)

    def setup_payment(self):
        p = QWidget()
        l = QVBoxLayout(p)
        l.addWidget(QLabel("<h1>Licenc Vásárlás</h1>"))
        
        box = QFrame()
        box.setStyleSheet("background: #0f172a; border-radius: 10px; padding: 30px;")
        bl = QVBoxLayout(box)
        bl.addWidget(QLabel(f"<b>Kedvezményezett:</b> {DEV_NAME}"))
        bl.addWidget(QLabel(f"<b>Számlaszám (IBAN):</b><br><span style='font-size:18px; color:#3b82f6;'>{IBAN_NUMBER}</span>"))
        bl.addWidget(QLabel(f"<b>Közlemény:</b> LICENCE-{self.hwid}"))
        l.addWidget(box)
        
        stripe = QPushButton("Fizetés Bankkártyával (Stripe)")
        stripe.setCursor(Qt.CursorShape.PointingHandCursor)
        stripe.clicked.connect(lambda: webbrowser.open(f"{STRIPE_LINK}?client_id={self.hwid}"))
        l.addWidget(stripe)
        l.addStretch()
        self.pages.addWidget(p)

    def setup_contact(self):
        p = QWidget()
        l = QVBoxLayout(p)
        l.addWidget(QLabel("<h1>Technikai Támogatás</h1>"))
        l.addWidget(QLabel(f"<b>Email:</b> {CONTACT_EMAIL}"))
        l.addWidget(QLabel(f"<b>Mobil:</b> {CONTACT_PHONE}"))
        l.addWidget(QLabel("<br>Minden licencvásárlás után 1 évig ingyenes frissítést biztosítunk."))
        l.addStretch()
        self.pages.addWidget(p)

    def refresh_stats(self, cpu, ram):
        self.history.append(cpu)
        if len(self.history) > 100: self.history.pop(0)
        self.curve.setData(self.history)
        self.statusBar().showMessage(f"CPU: {cpu}% | RAM: {ram}% | Rendszerállapot: Biztonságos")

    def closeEvent(self, event):
        self.worker.requestInterruption()
        self.worker.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = TitaniumFinal()
    win.show()
    sys.exit(app.exec())
