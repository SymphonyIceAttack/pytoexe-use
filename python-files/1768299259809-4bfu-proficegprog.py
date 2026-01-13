import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QMessageBox

# --- Modulok import ---
from db import setup_database
from license_manager import check_license
from admin_panel import AdminPanel
from ai_module import AIModule
from security_vpn import SecurityVPN
from payment_manager import create_card_payment, create_revolut_payment, new_bank_payment

# --- Adatbázis létrehozása ---
setup_database()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Profi Céges Program - DEMO/PRO")
        self.resize(900, 550)

        layout = QVBoxLayout()
        self.label = QLabel("Üdv a Profi Céges Programban!")
        layout.addWidget(self.label)

        # Fizetési gombok
        self.pay_stripe_btn = QPushButton("Fizetés Stripe kártyával")
        self.pay_stripe_btn.clicked.connect(self.pay_stripe)
        layout.addWidget(self.pay_stripe_btn)

        self.pay_revolut_btn = QPushButton("Fizetés Revolut")
        self.pay_revolut_btn.clicked.connect(self.pay_revolut)
        layout.addWidget(self.pay_revolut_btn)

        self.pay_bank_btn = QPushButton("Fizetés banki átutalással")
        self.pay_bank_btn.clicked.connect(self.pay_bank)
        layout.addWidget(self.pay_bank_btn)

        # Modulok gombjai
        self.admin_btn = QPushButton("Admin Panel")
        self.admin_btn.clicked.connect(self.show_admin)
        layout.addWidget(self.admin_btn)

        self.ai_btn = QPushButton("AI Asszisztens")
        self.ai_btn.clicked.connect(self.show_ai)
        layout.addWidget(self.ai_btn)

        self.vpn_btn = QPushButton("VPN & Biztonság")
        self.vpn_btn.clicked.connect(self.show_vpn)
        layout.addWidget(self.vpn_btn)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # DEMO/PRO ellenőrzés
        status = check_license("demo@user")
        if status == "PRO":
            self.label.setText("PRO verzió aktiválva!")
        elif status == "EXPIRED":
            self.label.setText("DEMO lejárt. Vásárolj PRO-t!")
        else:
            self.label.setText("DEMO mód fut.")

    # --- Fizetés modulok ---
    def pay_stripe(self):
        url = create_card_payment("demo@user", 9.99)
        QMessageBox.information(self, "Stripe Fizetés", f"Kattints a linkre a fizetéshez:\n{url}")

    def pay_revolut(self):
        url = create_revolut_payment("demo@user", 9.99)
        QMessageBox.information(self, "Revolut Fizetés", f"Kattints a linkre a fizetéshez:\n{url}")

    def pay_bank(self):
        ref = new_bank_payment("demo@user", 9.99)
        QMessageBox.information(self, "Banki átutalás", f"Használd ezt a REF kódot az utalásnál:\n{ref}")

    # --- Modulok ablakai ---
    def show_admin(self):
        status = check_license("demo@user")
        if status != "PRO":
            QMessageBox.warning(self, "Admin", "Csak PRO felhasználóknak!")
            return
        self.admin_window = AdminPanel()
        self.admin_window.show()

    def show_ai(self):
        self.ai_window = AIModule()
        self.ai_window.show()

    def show_vpn(self):
        self.vpn_window = SecurityVPN()
        self.vpn_window.show()


app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())