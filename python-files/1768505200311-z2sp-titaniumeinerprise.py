import sys, os, hashlib, platform, psutil, uuid, webbrowser, logging
import pyqtgraph as pg
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from reportlab.pdfgen import canvas

# ==========================================
# ELÉRHETŐSÉGEK ÉS ÜZLETI ADATOK
# ==========================================
DEVELOPER_NAME = "Majsai István"
CONTACT_EMAIL = "istvanmajsai70@gmail.com"
CONTACT_PHONE = "06306260688"
IBAN_NUMBER = "HU37 1177 3195 0317 0124 0000 0000" # Ellenőrizd a pontosságot!
STRIPE_LINK = f"https://buy.stripe.com/test_id?client_reference_id="

# ==========================================
# MODERN TITANIUM STÍLUS (QSS)
# ==========================================
STYLE_SHEET = """
    QMainWindow { background-color: #05070a; }
    #Sidebar { background-color: #0b0e14; border-right: 1px solid #1c222d; min-width: 250px; }
    #ContentArea { background-color: #05070a; border-radius: 15px; margin: 10px; }
    QLabel { color: #e2e8f0; font-family: 'Segoe UI'; }
    QPushButton { 
        background-color: #0078d4; color: white; border-radius: 6px; 
        padding: 12px; font-weight: bold; border: none; margin: 5px;
    }
    QPushButton:hover { background-color: #005a9e; }
    #Header { font-size: 24px; font-weight: bold; color: white; margin-bottom: 20px; }
"""

# ==========================================
# RENDSZERMAG (SECURITY & DATA)
# ==========================================
class SecurityShield:
    @staticmethod
    def get_ultra_hwid():
        # Kombinált azonosító a biztonságért
        raw = f"{uuid.getnode()}-{platform.processor()}-MAJSAI_SECURE_2026"
        return hashlib.sha256(raw.encode()).hexdigest()[:20].upper()

class DataWorker(QThread):
    data_sig = pyqtSignal(float, float)
    def run(self):
        while not self.isInterruptionRequested():
            cpu = psutil.cpu_percent(interval=0.8)
            ram = psutil.virtual_memory().percent
            self.data_sig.emit(cpu, ram)

# ==========================================
# FŐ ALKALMAZÁS KERET
# ==========================================
class UltimateEnterprise(QMainWindow):
    def __init__(self):
        super().__init__()
        self.hwid = SecurityShield.get_ultra_hwid()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"Tolna Enterprise Ultimate v3.0 | Licensed to: {self.hwid}")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(STYLE_SHEET)

        main_widget = QWidget()
        self.main_layout = QHBoxLayout(main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(main_widget)

        self.setup_sidebar()
        
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("ContentArea")
        self.main_layout.addWidget(self.content_stack)

        self.init_pages()

    def setup_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        l = QVBoxLayout(sidebar)
        
        logo = QLabel("TOLNA ENTERPRISE\nULTIMATE")
        logo.setStyleSheet("font-size: 18px; font-weight: bold; color: #0078d4; padding: 30px 10px; text-align: center;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(logo)

        menus = [
            ("📊 DASHBOARD", 0),
            ("💳 LICENC VÁSÁRLÁS", 1),
            ("📞 TÁMOGATÁS", 2)
        ]

        for name, idx in menus:
            btn = QPushButton(name)
            btn.clicked.connect(lambda _, i=idx: self.content_stack.setCurrentIndex(i))
            l.addWidget(btn)

        l.addStretch()
        
        id_box = QLabel(f"DEVICE ID:\n{self.hwid}")
        id_box.setStyleSheet("font-size: 10px; color: #475569; padding: 10px;")
        l.addWidget(id_box)

        self.main_layout.addWidget(sidebar)

    def init_pages(self):
        # 0. PAGE: Dashboard (Élő grafikon)
        dash = QWidget()
        dl = QVBoxLayout(dash)
        dl.addWidget(QLabel("<h1>Rendszeranalitika</h1>"))
        
        self.plot = pg.PlotWidget()
        self.plot.setBackground('#0b0e14')
        self.plot.showGrid(x=True, y=True)
        self.curve = self.plot.plot(pen=pg.mkPen('#0078d4', width=3))
        self.history = []
        
        dl.addWidget(self.plot)
        self.content_stack.addWidget(dash)

        # 1. PAGE: Fizetési információk
        pay = QWidget()
        pl = QVBoxLayout(pay)
        pl.addWidget(QLabel("<h1>Szoftver Aktiválása</h1>"))
        
        info_box = QFrame()
        info_box.setStyleSheet("background: #0b0e14; border: 1px solid #1c222d; border-radius: 10px; padding: 20px;")
        il = QVBoxLayout(info_box)
        il.addWidget(QLabel(f"<b>Banki átutalás (IBAN):</b><br><span style='font-size:18px; color:#0078d4;'>{IBAN_NUMBER}</span>"))
        il.addWidget(QLabel("<br><b>Kedvezményezett:</b> " + DEVELOPER_NAME))
        il.addWidget(QLabel(f"<b>Közlemény:</b> LICENCE-{self.hwid}"))
        pl.addWidget(info_box)
        
        stripe_btn = QPushButton("Fizetés Bankkártyával (Stripe)")
        stripe_btn.setFixedHeight(50)
        stripe_btn.clicked.connect(lambda: webbrowser.open(f"{STRIPE_LINK}{self.hwid}"))
        pl.addWidget(stripe_btn)
        pl.addStretch()
        self.content_stack.addWidget(pay)

        # 2. PAGE: Kapcsolat
        supp = QWidget()
        sl = QVBoxLayout(supp)
        sl.addWidget(QLabel("<h1>Kapcsolat és Support</h1>"))
        
        contact_box = QFrame()
        contact_box.setStyleSheet("background: #0b0e14; border-radius: 10px; padding: 20px;")
        cl = QVBoxLayout(contact_box)
        cl.addWidget(QLabel(f"<b>Fejlesztő:</b> {DEVELOPER_NAME}"))
        cl.addWidget(QLabel(f"<b>E-mail:</b> {CONTACT_EMAIL}"))
        cl.addWidget(QLabel(f"<b>Telefon:</b> {CONTACT_PHONE}"))
        sl.addWidget(contact_box)
        
        sl.addWidget(QLabel("<br>Bármilyen technikai kérdés esetén forduljon hozzánk bizalommal!"))
        sl.addStretch()
        self.content_stack.addWidget(supp)

        # Monitor szál indítása
        self.worker = DataWorker()
        self.worker.data_sig.connect(self.update_ui_stats)
        self.worker.start()

    def update_ui_stats(self, cpu, ram):
        self.history.append(cpu)
        if len(self.history) > 60: self.history.pop(0)
        self.curve.setData(self.history)
        self.statusBar().showMessage(f"CPU: {cpu}% | RAM: {ram}% | Biztonságos Kapcsolat Aktív")

    def closeEvent(self, event):
        self.worker.requestInterruption()
        self.worker.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Sötét mód paletta
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(5, 7, 10))
    p.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    app.setPalette(p)
    
    win = UltimateEnterprise()
    win.show()
    sys.exit(app.exec())
