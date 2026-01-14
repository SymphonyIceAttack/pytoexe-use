import sys
import os
import requests
import hashlib
import platform
from datetime import datetime
from reportlab.pdfgen import canvas # PDF-hez: pip install reportlab
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# --- KONFIGURÁCIÓ ---
VERSION = "1.0.2"
SERVER_URL = "http://your-vps-ip:5000" # Ide írd a szervered címét

class UpdateThread(QThread):
    """C FÁZIS: Automata frissítés ellenőrző modul"""
    update_found = pyqtSignal(str)

    def run(self):
        try:
            # Szimulált verzió ellenőrzés a szerveren
            response = requests.get(f"{SERVER_URL}/api/version", timeout=5)
            server_version = response.json().get("version")
            if server_version > VERSION:
                self.update_found.emit(server_version)
        except:
            pass

class EnterpriseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Tolna MI Enterprise - v{VERSION}")
        self.resize(1100, 750)
        self.init_styles()
        
        # UI Felépítése
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        self.sidebar = self.create_sidebar()
        layout.addWidget(self.sidebar)

        # Tartalom
        self.stack = QStackedWidget()
        self.stack.addWidget(self.create_data_page())
        layout.addWidget(self.stack)

        # Indításkor frissítés ellenőrzés (C fázis)
        self.updater = UpdateThread()
        self.updater.update_found.connect(self.show_update_dialog)
        self.updater.start()

    def init_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0b0e14; }
            #Sidebar { background-color: #151921; min-width: 220px; border-right: 2px solid #0078d4; }
            QLabel { color: white; font-family: 'Segoe UI'; }
            QPushButton { 
                background-color: transparent; color: #a0a0a0; padding: 12px; 
                text-align: left; border: none; font-size: 14px;
            }
            QPushButton:hover { background-color: #1c222d; color: #0078d4; }
            QTableWidget { 
                background-color: #151921; color: white; border-radius: 10px; 
                gridline-color: #2a2f3a; selection-background-color: #0078d4;
            }
        """)

    def create_sidebar(self):
        frame = QWidget()
        frame.setObjectName("Sidebar")
        layout = QVBoxLayout(frame)
        
        logo = QLabel("TOLNA MI 2026")
        logo.setStyleSheet("font-size: 20px; font-weight: bold; color: #0078d4; margin: 20px;")
        layout.addWidget(logo)

        for text in ["Műszerfal", "Adatbázis", "Riportok", "Beállítások"]:
            btn = QPushButton(f"  {text}")
            layout.addWidget(btn)
        
        layout.addStretch()
        return frame

    def create_data_page(self):
        """A & B FÁZIS: Adatkezelés és PDF funkció"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Vállalati Adatbázis és Riportok")
        title.setStyleSheet("font-size: 26px; margin-bottom: 20px;")
        layout.addWidget(title)

        self.table = QTableWidget(5, 3)
        self.table.setHorizontalHeaderLabels(["Partner", "Projekt", "Állapot"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Példa adatok (A fázisban itt requests.get lenne a szerverről)
        sample_data = [("OTP Bank", "MI Integráció", "Folyamatban"), ("MOL Nyrt.", "Adatvédelem", "Kész")]
        for i, (p, pr, s) in enumerate(sample_data):
            self.table.setItem(i, 0, QTableWidgetItem(p))
            self.table.setItem(i, 1, QTableWidgetItem(pr))
            self.table.setItem(i, 2, QTableWidgetItem(s))
        
        layout.addWidget(self.table)

        # B FÁZIS: PDF Generálás gomb
        pdf_btn = QPushButton("  PROFI PDF RIPORT GENERÁLÁSA")
        pdf_btn.setStyleSheet("background-color: #0078d4; color: white; font-weight: bold; border-radius: 5px;")
        pdf_btn.clicked.connect(self.generate_report)
        layout.addWidget(pdf_btn)

        return page

    def generate_report(self):
        """PDF generáló logika"""
        filename = f"Riport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        try:
            c = canvas.Canvas(filename)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, 800, "TOLNA MI - HIVATALOS ÜZLETI RIPORT")
            c.setFont("Helvetica", 12)
            c.drawString(100, 780, f"Dátum: {datetime.now()}")
            c.line(100, 770, 500, 770)
            
            c.drawString(100, 740, "A rendszer által elemzett legfrissebb adatok...")
            # Ide jöhetne a táblázat tartalma
            c.save()
            QMessageBox.information(self, "Siker", f"A riport elkészült: {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Hiba", f"PDF hiba: {str(e)}")

    def show_update_dialog(self, new_ver):
        QMessageBox.information(self, "Frissítés elérhető", f"Új verzió található: v{new_ver}\nKérjük, töltse le a frissítést!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EnterpriseApp()
    window.show()
    sys.exit(app.exec())
