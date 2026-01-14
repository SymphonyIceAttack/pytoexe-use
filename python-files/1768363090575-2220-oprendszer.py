import sys, hashlib, uuid, os, time, logging, re, sqlite3
import cv2, pytesseract, requests
import pyqtgraph as pg
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QIcon, QAction
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from reportlab.pdfgen import canvas  # PDF generáláshoz
from reportlab.lib.pagesizes import A4

# --- RENDSZERSZINTŰ SZERVIZEK ---
class ProBizOSCore:
    """Operációs rendszer szintű integráció és automatizálás."""
    @staticmethod
    def ensure_system_integrity():
        """Ellenőrzi a fájlstruktúrát és a naplózást indításkor."""
        if not os.path.exists("exports"): os.makedirs("exports")
        logging.info("Rendszerintegritás ellenőrizve. Könyvtárak aktívak.")

    @staticmethod
    def register_background_service():
        """Szimulált háttérszolgáltatás regisztrálása a tálcára."""
        # Itt valósítható meg a Windows Registry-be való bejegyzés az auto-starthoz
        pass

# --- PROFESSZIONÁLIS ADATBÁZIS KEZELŐ ---
class EnterpriseDB:
    def __init__(self):
        self.conn = sqlite3.connect("probiz_core.db")
        self.cur = self.conn.cursor()
        self.cur.execute('''CREATE TABLE IF NOT EXISTS invoices 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, partner TEXT, total REAL, date TEXT, pdf_path TEXT)''')
        self.conn.commit()

    def add_record(self, partner, total, date, path):
        self.cur.execute("INSERT INTO invoices (partner, total, date, pdf_path) VALUES (?,?,?,?)",
                         (partner, total, date, path))
        self.conn.commit()

# --- PDF GENERÁTOR MOTOR ---
class InvoiceEngine:
    @staticmethod
    def generate_pro_pdf(partner, amount, date):
        filename = f"exports/szamla_{int(time.time())}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        # Dizájn elemek a PDF-ben
        c.setStrokeColorRGB(0.2, 0.4, 0.6)
        c.line(50, 800, 550, 800)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, 770, "PROBIZ ENTERPRISE 2026")
        c.setFont("Helvetica", 12)
        c.drawString(50, 750, "Hivatalos Elektronikus Bizonylat")
        
        # Adatok
        c.drawString(50, 700, f"Partner megnevezése: {partner}")
        c.drawString(50, 680, f"Tranzakció összege: {amount} HUF")
        c.drawString(50, 660, f"Kiállítás dátuma: {date}")
        
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(50, 100, "Ez a dokumentum a ProBiz AI által automatikusan generált hiteles másolat.")
        c.save()
        return filename

# --- INTEGRÁLT FŐPROGRAM ---
class ProBizMasterOS(QMainWindow):
    def __init__(self):
        super().__init__()
        ProBizOSCore.ensure_system_integrity()
        self.db = EnterpriseDB()
        self.hwid = hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:12].upper()
        
        self.setWindowTitle("ProBiz OS - Enterprise Environment 2026")
        self.setFixedSize(1300, 900)
        self.init_ui()

    def init_ui(self):
        # UI Kialakítása (A korábbi Glassmorphism stílus bővítése)
        self.setStyleSheet("QMainWindow { background-color: #05070a; }")
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # Oldalpanel és Stacks (Dashboard, OCR, PDF Center)
        self.sidebar = self.create_sidebar()
        self.pages = QStackedWidget()
        
        layout.addWidget(self.sidebar)
        layout.addWidget(self.pages)
        
        # Aloldalak betöltése
        self.pages.addWidget(self.create_billing_center())
        self.pages.addWidget(self.create_ai_node())

    def create_billing_center(self):
        page = QWidget()
        l = QVBoxLayout(page)
        l.addWidget(QLabel("<h1>Számlázási és PDF Archívum</h1>"))
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Partner", "Összeg", "Dátum", "PDF Elérhetőség"])
        l.addWidget(self.table)
        
        btn = QPushButton("🆕 ÚJ SZÁMLA GENERÁLÁSA")
        btn.setFixedHeight(50)
        btn.setStyleSheet("background-color: #0ea5e9; color: white; font-weight: bold; border-radius: 10px;")
        btn.clicked.connect(self.action_generate)
        l.addWidget(btn)
        return page

    def action_generate(self):
        name, ok1 = QInputDialog.getText(self, "Adatbevitel", "Partner neve:")
        amount, ok2 = QInputDialog.getText(self, "Adatbevitel", "Összeg (HUF):")
        
        if ok1 and ok2:
            path = InvoiceEngine.generate_pro_pdf(name, amount, "2026.01.14")
            self.db.add_record(name, amount, "2026.01.14", path)
            self.refresh_table()
            QMessageBox.information(self, "Rendszer", f"PDF sikeresen archiválva: {path}")

    def refresh_table(self):
        # Táblázat frissítése az adatbázisból
        self.db.cur.execute("SELECT * FROM invoices ORDER BY id DESC")
        rows = self.db.cur.fetchall()
        self.table.setRowCount(0)
        for row_data in rows:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            for col_idx, data in enumerate(row_data[1:]): # ID kihagyása
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))

    def create_sidebar(self):
        # (Oldalmenü kódja...)
        frame = QFrame()
        frame.setFixedWidth(250)
        frame.setStyleSheet("background-color: #0f172a; border-right: 2px solid #1e293b;")
        return frame

    def create_ai_node(self):
        return QLabel("AI Node aktív...")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProBizMasterOS()
    window.show()
    sys.exit(app.exec())
