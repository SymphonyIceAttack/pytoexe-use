import os, sys, base64, platform, requests, psutil, threading, time
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
from PyQt6.QtGui import QFont

# --- KONFIG ---
SERVER_URL = "http://127.0.0.1:5000/api/activate"  # VPS-re cseréld
LICENSE_FILE = os.path.join(os.getenv('APPDATA', '.'), 'TMI2026.lic')
CURRENT_VERSION = "1.0.0"
UPDATE_URL = "http://127.0.0.1:5000/latest_version.exe"

# --- HWID ---
def get_machine_id():
    info = f"{platform.node()}-{platform.processor()}-{platform.system()}"
    return base64.b64encode(info.encode()).decode()[:20]

# --- Licenc kezelés ---
def save_license(license_key):
    encrypted = base64.b64encode(f"{license_key}|{get_machine_id()}".encode()).decode()
    with open(LICENSE_FILE, "w") as f:
        f.write(encrypted)

def check_local():
    if not os.path.exists(LICENSE_FILE):
        return False
    try:
        decoded = base64.b64decode(open(LICENSE_FILE).read().encode()).decode().split('|')
        return decoded[1] == get_machine_id()
    except:
        return False

def activate_online(license_key):
    try:
        r = requests.post(SERVER_URL, json={
            "license_key": license_key,
            "hwid": get_machine_id()
        })
        data = r.json()
        if data.get("valid"):
            save_license(license_key)
            return True, "Sikeres aktiválás!"
        return False, data.get("error", "Ismeretlen hiba")
    except Exception as e:
        return False, str(e)

# --- Anti-Tamper ---
class AntiTamper(threading.Thread):
    def __init__(self, callback):
        super().__init__()
        self.protected_files = ["TolnaMI2026_Pro_Full.exe", "TMI2026.lic"]
        self.forbidden_procs = ["cheatengine", "processhacker", "wireshark"]
        self.callback = callback
        self.daemon = True

    def run(self):
        while True:
            for f in self.protected_files:
                if not os.path.exists(f):
                    self.callback(f"KRITIKUS HIBA: {f} hiányzik!")
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and proc.info['name'].lower() in self.forbidden_procs:
                    self.callback(f"BIZTONSÁGI VESZÉLY: {proc.info['name']} észlelve!")
            time.sleep(3)

# --- Updater ---
def check_update():
    try:
        r = requests.get("http://127.0.0.1:5000/version.txt")
        latest = r.text.strip()
        if latest != CURRENT_VERSION:
            r2 = requests.get(UPDATE_URL)
            with open("TolnaMI2026_Pro_new.exe", "wb") as f:
                f.write(r2.content)
            print("Új verzió letöltve. Indítsd újra a programot!")
    except:
        pass

# --- GUI ---
class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tolna MI 2026 Professional")
        self.resize(500, 250)

        self.label = QLabel("✔ Aktiválva! Tolna MI 2026 fut")
        self.label.setFont(QFont("Segoe UI", 12))
        self.label.setStyleSheet("color: green;")

        self.mi_info = QLabel("\n[MI] Motor indul...")
        self.mi_info.setFont(QFont("Segoe UI", 10))

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.mi_info)
        self.setLayout(layout)

        # Anti-Tamper indítása
        self.shield = AntiTamper(self.alert)
        self.shield.start()

        # Frissítés ellenőrzés
        threading.Thread(target=check_update, daemon=True).start()

        # <<< IDE JÖN A TE MI KÓDOD >>>
        print("[MI] Betöltés... kész.")

    def alert(self, msg):
        QMessageBox.critical(self, "Anti-Tamper", msg)

class ActivationApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tolna MI 2026 - Aktiválás")
        self.resize(400, 200)

        self.label = QLabel(f"Gép ID: {get_machine_id()}")
        self.label.setFont(QFont("Segoe UI", 10))

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Licenc kulcs")

        self.btn = QPushButton("Aktiválás")
        self.btn.clicked.connect(self.do_activate)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.key_input)
        layout.addWidget(self.btn)
        self.setLayout(layout)

    def do_activate(self):
        key = self.key_input.text().strip()
        ok, msg = activate_online(key)
        QMessageBox.information(self, "Aktiválás", msg)
        if ok:
            self.close()
            launch_main()

def launch_main():
    app2 = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app2.exec())

def main():
    if check_local():
        launch_main()
    else:
        app = QApplication(sys.argv)
        win = ActivationApp()
        win.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main()