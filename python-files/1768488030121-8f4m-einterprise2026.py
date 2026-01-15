import sys, os, sqlite3, hashlib, platform, requests, json, qrcode, io, webbrowser, stripe, logging, shutil
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from reportlab.pdfgen import canvas

# ==========================================
# 1. SZERVER OLDALI LOGIKA (Flask Backend)
# ==========================================
# (Ezt VPS szerveren futtasd külön)
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_PATH = 'enterprise_pro.db'

def db_query(query, params=(), fetch=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, params)
    res = cursor.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return res

@app.route('/verify', methods=['GET'])
def verify():
    hwid = request.args.get('hwid')
    res = db_query("SELECT status, expiry FROM licenses WHERE hwid=?", (hwid,), True)
    if res:
        return jsonify({"access": "GRANTED", "expiry": res[0][1]})
    return jsonify({"access": "DENIED"})

@app.route('/api/wallet/redeem', methods=['POST'])
def redeem():
    data = request.json
    hwid, code = data['hwid'], data['code'].upper()
    coupon = db_query("SELECT reward FROM coupons WHERE code=? AND active=1", (code,), True)
    if coupon:
        db_query("UPDATE coupons SET active=0 WHERE code=?", (code,))
        db_query("UPDATE wallets SET balance = balance + ? WHERE hwid=?", (coupon[0][0], hwid))
        return jsonify({"status": "success", "reward": coupon[0][0]})
    return jsonify({"status": "error"}), 400

# ==========================================
# 2. BIZTONSÁGI ÉS VPN MODUL (Kliens)
# ==========================================
class SecuritySystem:
    def __init__(self, hwid):
        self.hwid = hwid
        self.key = Fernet.generate_key() # Szimulált VPN kulcs
        self.cipher = Fernet(self.key)

    @staticmethod
    def get_hwid():
        unique_str = platform.node() + platform.processor() + platform.machine()
        return hashlib.sha256(unique_str.encode()).hexdigest()[:12].upper()

    def self_destruct(self):
        """Önmegsemmisítő: Törli a helyi adatokat és kilép"""
        print("ATTACK DETECTED - SELF DESTRUCT INITIATED")
        if os.path.exists('app_activity.log'): os.remove('app_activity.log')
        os._exit(1)

# ==========================================
# 3. FIZETÉSI KÖZPONT (Wallet & QR & Stripe)
# ==========================================
class PaymentHub(QDialog):
    def __init__(self, hwid):
        super().__init__()
        self.hwid = hwid
        self.setWindowTitle("Tolna MI - Pénztárca és Fizetés")
        self.setFixedSize(450, 600)
        self.setStyleSheet("background-color: #0b0e14; color: white;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # QR Kód szekció
        btc_addr = "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
        qr = qrcode.make(f"bitcoin:{btc_addr}")
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        qimg = QImage.fromData(buffer.getvalue())
        
        qr_label = QLabel()
        qr_label.setPixmap(QPixmap.fromImage(qimg).scaled(200, 200))
        qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(QLabel("BTC Befizetés (Automata):"))
        layout.addWidget(qr_label)

        # Stripe gomb
        btn_stripe = QPushButton("Fizetés Bankkártyával (Stripe)")
        btn_stripe.setStyleSheet("background-color: #6772e5; padding: 10px; font-weight: bold;")
        btn_stripe.clicked.connect(lambda: webbrowser.open("https://stripe.com/checkout"))
        layout.addWidget(btn_stripe)

        # IBAN adatok
        bank_info = QLabel(f"Revolut IBAN: LT81 3250 0757 5026 3901\nKözlemény: {self.hwid}")
        bank_info.setStyleSheet("color: #0078d4; font-size: 14px;")
        layout.addWidget(bank_info)

# ==========================================
# 4. FŐ ALKALMAZÁS (Enterprise UI)
# ==========================================
class EnterpriseMain(QMainWindow):
    def __init__(self):
        super().__init__()
        self.hwid = SecuritySystem.get_hwid()
        self.security = SecuritySystem(self.hwid)
        
        self.setWindowTitle(f"Tolna MI Enterprise Core - ID: {self.hwid}")
        self.resize(1100, 800)
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("background-color: #151921;")
        side_layout = QVBoxLayout(sidebar)
        
        btn_wallet = QPushButton("Pénztárca / PRO")
        btn_wallet.clicked.connect(self.open_wallet)
        side_layout.addWidget(btn_wallet)
        
        side_layout.addStretch()
        layout.addWidget(sidebar)

        # Konténer a logoknak és adatoknak
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_dashboard(), "Műszerfal")
        self.tabs.addTab(self.create_log_monitor(), "Tűzfal & Logok")
        layout.addWidget(self.tabs)

    def create_dashboard(self):
        page = QWidget()
        l = QVBoxLayout(page)
        l.addWidget(QLabel(f"Üdvözöljük! Gép azonosító: {self.hwid}"))
        
        # Statisztikai kártya szimuláció
        card = QFrame()
        card.setStyleSheet("background-color: #1c222d; border-radius: 10px; padding: 20px;")
        cl = QVBoxLayout(card)
        cl.addWidget(QLabel("Rendszer Állapot: ONLINE (VPN AKTÍV)"))
        l.addWidget(card)
        
        return page

    def create_log_monitor(self):
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("background: black; color: #00ff00; font-family: Consolas;")
        return self.log_view

    def open_wallet(self):
        self.pay_win = PaymentHub(self.hwid)
        self.pay_win.exec()

# ==========================================
# 5. AUTOMATA TELEPÍTŐ (Incializálás)
# ==========================================
def first_time_setup():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("CREATE TABLE licenses (hwid TEXT PRIMARY KEY, status TEXT, expiry TEXT)")
        c.execute("CREATE TABLE wallets (hwid TEXT PRIMARY KEY, balance REAL)")
        c.execute("CREATE TABLE coupons (code TEXT PRIMARY KEY, reward REAL, active INTEGER)")
        c.execute("INSERT INTO coupons VALUES ('TOLNA2026', 150000, 1)")
        conn.commit()
        conn.close()
        print("[!] Rendszer inicializálva. 'TOLNA2026' kupon aktív.")

# ==========================================
# FUTTATÁS
# ==========================================
if __name__ == "__main__":
    first_time_setup()
    # Megjegyzés: A Flask szervert külön szálon vagy folyamatban kellene indítani
    # Itt most csak a GUI-t indítjuk
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Sötét téma beállítása globálisan
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(11, 14, 20))
    app.setPalette(palette)
    
    window = EnterpriseMain()
    window.show()
    sys.exit(app.exec())
