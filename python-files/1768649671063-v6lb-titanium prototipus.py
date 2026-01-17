# ===============================
# TITANIUM ENTERPRISE 2026 PROTOTÍPUS
# Teljes integrált verzió – Python + PyQt6
# Demo modulok: VPN, Antivirus, Browser, Cloud, AI
# Licenc + 14 napos trial + fizetés backend demo
# ===============================

import sys
import random
import requests
from datetime import datetime

# PyQt6 GUI
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox

# -------------------------------
# CONFIG
# -------------------------------
API_URL = "https://titanium-backend.com"  # cseréld a valós FastAPI szerverre
USER_ID = "user-1234"
LICENSE_KEY = "TITANIUM-2026-XXXX-XXXX"

# -------------------------------
# LICENSE MANAGER
# -------------------------------
class LicenseManager:
    def __init__(self):
        self.user_id = USER_ID
        self.license_key = LICENSE_KEY

    def start_trial(self):
        try:
            r = requests.post(f"{API_URL}/trial_start/", params={"user_id": self.user_id})
            return r.json()
        except:
            return {"active": False, "expires_at": None}

    def check_trial(self):
        try:
            r = requests.get(f"{API_URL}/check_trial/", params={"user_id": self.user_id})
            return r.json()
        except:
            return {"days_left": 0, "active": False}

    def check_license(self):
        try:
            r = requests.get(f"{API_URL}/check_license/", params={"license_key": self.license_key})
            return r.json()
        except:
            return {"active": False, "expires_at": None}

# -------------------------------
# VPN MODULE (Demo)
# -------------------------------
class VPNModule:
    def __init__(self):
        self.connected = False
        self.ip = "Not connected"

    def connect(self):
        self.connected = True
        self.ip = "192.168.10.10"
        return self.ip

    def disconnect(self):
        self.connected = False
        self.ip = "Not connected"

# -------------------------------
# ANTIVIRUS MODULE (Demo)
# -------------------------------
class Antivirus:
    def scan_system(self):
        issues = random.randint(0, 5)
        if issues == 0:
            return "No threats found"
        return f"{issues} potential threats found!"

# -------------------------------
# BROWSER MODULE (Demo)
# -------------------------------
class Browser:
    def open_page(self, url):
        return f"Opening {url} in built-in browser"

    def open_wallet(self):
        return "Opening Titanium integrated wallet"

# -------------------------------
# CLOUD DRIVE MODULE (Demo)
# -------------------------------
class CloudDrive:
    def __init__(self):
        self.files = ["report.pdf", "invoice.xlsx"]

    def list_files(self):
        return self.files

    def upload_file(self, filename):
        self.files.append(filename)
        return f"{filename} uploaded"

# -------------------------------
# AI ASSISTANT MODULE (Demo)
# -------------------------------
class AIAssistant:
    def analyze_system(self):
        return "AI checked system: no critical issues"

    def chat(self, message):
        return f"AI response to '{message}'"

# -------------------------------
# DASHBOARD GUI
# -------------------------------
class Dashboard(QWidget):
    def __init__(self, license_manager, vpn, antivirus, browser, cloud, ai):
        super().__init__()
        self.license_manager = license_manager
        self.vpn = vpn
        self.antivirus = antivirus
        self.browser = browser
        self.cloud = cloud
        self.ai = ai
        self.setWindowTitle("Titanium Enterprise 2026")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Licenc státusz
        trial_status = self.license_manager.check_trial()
        license_status = self.license_manager.check_license()
        layout.addWidget(QLabel(f"Trial active: {trial_status['active']} - {trial_status.get('days_left',0)} days left"))
        layout.addWidget(QLabel(f"License active: {license_status['active']}"))

        # VPN gomb
        vpn_btn = QPushButton("Connect VPN")
        vpn_btn.clicked.connect(lambda: layout.addWidget(QLabel(f"VPN IP: {self.vpn.connect()}")))
        layout.addWidget(vpn_btn)

        # Antivirus gomb
        av_btn = QPushButton("Scan System")
        av_btn.clicked.connect(lambda: layout.addWidget(QLabel(self.antivirus.scan_system())))
        layout.addWidget(av_btn)

        # Browser gomb
        browser_btn = QPushButton("Open Browser")
        browser_btn.clicked.connect(lambda: layout.addWidget(QLabel(self.browser.open_page("https://example.com"))))
        layout.addWidget(browser_btn)

        # Cloud gomb
        cloud_btn = QPushButton("List Cloud Files")
        cloud_btn.clicked.connect(lambda: layout.addWidget(QLabel(str(self.cloud.list_files()))))
        layout.addWidget(cloud_btn)

        # AI gomb
        ai_btn = QPushButton("AI Chat")
        ai_btn.clicked.connect(lambda: layout.addWidget(QLabel(self.ai.chat("Hello Titanium"))))
        layout.addWidget(ai_btn)

        self.setLayout(layout)

# -------------------------------
# FORBIDDEN OPTIONS CHECK
# -------------------------------
FORBIDDEN_OPTIONS = ["clags", "optimize_debug", "dev_mode"]

def check_forbidden_opts(args):
    for arg in args:
        if arg.lower() in FORBIDDEN_OPTIONS:
            raise RuntimeError(f"Forbidden option detected: {arg}. Program will exit!")

# -------------------------------
# MAIN PROGRAM
# -------------------------------
def main():
    # Ellenőrizzük tiltott opciókat
    try:
        check_forbidden_opts(sys.argv[1:])
    except RuntimeError as e:
        print(e)
        sys.exit(1)

    # Inicializáljuk modulokat
    license_manager = LicenseManager()
    vpn = VPNModule()
    antivirus = Antivirus()
    browser = Browser()
    cloud = CloudDrive()
    ai = AIAssistant()

    # GUI indítása
    app = QApplication(sys.argv)

    # Licenc / trial ellenőrzés
    trial = license_manager.check_trial()
    lic = license_manager.check_license()
    msg = QMessageBox()
    if lic['active'] or (trial['active']):
        msg.setText("Program elindulhat!")
        msg.setIcon(QMessageBox.Icon.Information)
    else:
        msg.setText("Licenc szükséges a további használathoz!")
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.exec()
        sys.exit(1)
    msg.exec()

    dashboard = Dashboard(license_manager, vpn, antivirus, browser, cloud, ai)
    dashboard.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()