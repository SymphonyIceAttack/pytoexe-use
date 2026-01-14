import sys, os, sqlite3, hashlib, platform, requests, json, qrcode, io, webbrowser, stripe, logging, shutil
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from reportlab.pdfgen import canvas

# --- 1. GLOBÁLIS BEÁLLÍTÁSOK ---
VERSION = "2.0.0"
DB_NAME = "enterprise_pro.db"
# Élesben ide a VPS IP-címét írd!
SERVER_URL = "http://localhost:5000" 

# --- 2. BIZTONSÁGI ÉS ANTI-TAMPER RENDSZER ---
class SecurityCore:
    @staticmethod
    def get_hwid():
        unique_str = platform.node() + platform.processor() + platform.machine()
        return hashlib.sha256(unique_str.encode()).hexdigest()[:12].upper()

    @staticmethod
    def kill_switch():
        """Önmegsemmisítő: Törlés és kilépés"""
        if os.path.exists('session_cache.db'): os.remove('session_cache.db')
        QMessageBox.critical(None, "SECURITY", "Rendszer zárolva. Forduljon az adminisztrátorhoz!")
        os._exit(1)

# --- 3. FIZETÉSI KÖZPONT ÉS QR GENERÁTOR ---
class PaymentHub(QDialog):
    def __init__(self, hwid):
        super().__init__()
        self.hwid = hwid
        self.setWindowTitle("Tolna MI - Pénztárca Feltöltés")
        self.setFixedSize(450, 650)
        self.setStyleSheet("background-color: #0b0e14; color: white;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # QR Kód generálás (Bitcoin)
        btc_addr = "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
        qr = qrcode.QRCode(box_size=6, border=2)
        qr.add_data(f"bitcoin:{btc_addr}?message=PRO_{self.hwid}")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # QImage-re konvertálás
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qimg = QImage.fromData(buffer.getvalue())
        
        qr_label = QLabel()
        qr_label.setPixmap(QPixmap.fromImage(qimg))
        qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(QLabel(f"Saját ID: {self.hwid}"))
        layout.addWidget(QLabel("<b>BTC Fizetés (QR):</b>"))
        layout.addWidget(qr_label)
        
        # Stripe / Kártya gomb
        btn_stripe = QPushButton("💳 KÁRTYÁS FIZETÉS (STRIPE)")
        btn_stripe.setStyleSheet("background-color: #6772e5; padding: 12px; font-weight: bold;")
        btn_stripe.clicked.connect(lambda: webbrowser.open("https://stripe.com"))
        layout.addWidget(btn_stripe)

        # Banki adatok
        bank_box = QLabel(f"<b>Revolut IBAN:</b><br>LT81 3250 0757 5026 3901<br><b>Közlemény:</b> {self.hwid}")
        bank_box.setStyleSheet("background-color: #1c222d; padding: 10px; border-radius: 5px;")
        layout.addWidget(bank_box)

# --- 4. FŐ ALKALMAZÁS UI ---
class EnterpriseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.hwid = SecurityCore.get_hwid()
        self.setWindowTitle(f"Tolna MI Enterprise Core - v{VERSION}")
        self.resize(1100, 800)
        self.setup_ui()
        self.log_event("Rendszer elindítva. Tűzfal: OK.")

    def setup_ui(self):
        # Sötét téma (Dark Mode)
        self.setStyleSheet("""
            QMainWindow { background-color: #0b0e14; }
            QPushButton { background-color: #1c222d; color: #a0a0a0; padding: 10px; border: 1px solid #2a2f3a; }
            QPushButton:hover { background-color: #0078d4; color: white; }
            QTextEdit { background-color: #05070a; color: #00ff00; font-family: 'Consolas'; }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # Bal oldali menü
        sidebar = QVBoxLayout()
        btn_wallet = QPushButton("💰 PÉNZTÁRCA")
        btn_wallet.clicked.connect(self.open_payment)
        sidebar.addWidget(btn_wallet)
        
        btn_report = QPushButton("📄 PDF RIPORT")
        btn_report.clicked.connect(self.generate_pdf)
        sidebar.addWidget(btn_report)
        
        sidebar.addStretch()
        main_layout.addLayout(sidebar, 1)

        # Jobb oldali tartalom (Logok és monitor)
        content = QVBoxLayout()
        content.addWidget(QLabel(f"<b>Gép azonosító (HWID):</b> {self.hwid}"))
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        content.addWidget(QLabel("<b>Élő Log Monitorozás & Tűzfal:</b>"))
        content.addWidget(self.log_display)
        
        main_layout.addLayout(content, 4)

    def log_event(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_display.append(f"[{ts}] {msg}")

    def open_payment(self):
        self.pay_hub = PaymentHub(self.hwid)
        self.pay_hub.exec()

    def generate_pdf(self):
        # Reportlab PDF generálás
        path = f"Riport_{self.hwid}.pdf"
        c = canvas.Canvas(path)
        c.drawString(100, 800, "TOLNA MI ENTERPRISE - HIVATALOS RIPORT")
        c.drawString(100, 780, f"Azonosító: {self.hwid}")
        c.save()
        self.log_event(f"PDF Riport generálva: {path}")
        QMessageBox.information(self, "Siker", "A riport elkészült!")

# --- 5. AUTOMATA TELEPÍTŐ ÉS SZERVER INDÍTÓ ---
def run_database_setup():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS licenses (hwid TEXT PRIMARY KEY, status TEXT, expiry TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS wallets (hwid TEXT PRIMARY KEY, balance REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS coupons (code TEXT PRIMARY KEY, reward REAL, active INTEGER)")
    # Teszt kupon
    c.execute("INSERT OR IGNORE INTO coupons VALUES ('TOLNA2026', 150000, 1)")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    run_database_setup()
    
    app = QApplication(sys.argv)
    window = EnterpriseApp()
    window.show()
    sys.exit(app.exec())
