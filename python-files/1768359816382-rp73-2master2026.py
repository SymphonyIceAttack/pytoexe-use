import sys, hashlib, uuid, os, time, logging, re
import cv2, pytesseract, psutil, requests
import pyqtgraph as pg
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QColor, QIcon, QAction
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from reportlab.pdfgen import canvas

# --- KONFIGURÁCIÓ & BIZTONSÁG ---
SALT = "PROBIZ_ENTERPRISE_2026_SECURE_V1"
logging.basicConfig(filename='audit_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

class ProBizMaster(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProBiz Ultimate Suite 2026 - Enterprise Edition")
        self.setFixedSize(1200, 850)
        self.hwid = hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:12].upper()
        self.is_active = False
        self.init_ui()

    def init_ui(self):
        # Professzionális Sötét Vállalati Dizájn (Glassmorphism hatás)
        self.setStyleSheet("""
            QMainWindow { background-color: #0b0f19; }
            QFrame#Sidebar { background-color: #161b22; border-right: 1px solid #30363d; }
            QPushButton { 
                background-color: transparent; color: #8b949e; 
                text-align: left; padding: 15px; border: none; font-size: 14px;
            }
            QPushButton:hover { background-color: #21262d; color: #58a6ff; }
            QPushButton#ActiveBtn { background-color: #238636; color: white; border-radius: 5px; font-weight: bold; }
            QLabel { color: #e6edf3; }
            QTableWidget { background-color: #0d1117; color: white; gridline-color: #30363d; }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0,0,0,0)

        # --- OLDALSÓ MENÜ ---
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(250)
        side_layout = QVBoxLayout(sidebar)
        
        logo = QLabel("PROBIZ 2026")
        logo.setFont(QFont("Impact", 24))
        logo.setStyleSheet("color: #58a6ff; margin-bottom: 20px;")
        side_layout.addWidget(logo)

        self.menu_btns = {}
        menu_items = [
            ("📊 Dashboard", 0), ("🧠 AI Genius", 1), 
            ("📄 OCR Számlázó", 2), ("🛡️ Cyber Shield", 3), ("⚙️ Beállítások", 4)
        ]

        for text, idx in menu_items:
            btn = QPushButton(text)
            btn.clicked.connect(lambda _, i=idx: self.stack.setCurrentIndex(i))
            side_layout.addWidget(btn)
            self.menu_btns[idx] = btn

        side_layout.addStretch()
        
        self.act_btn = QPushButton("🔑 AKTIVÁLÁS")
        self.act_btn.setObjectName("ActiveBtn")
        self.act_btn.clicked.connect(self.show_activation)
        side_layout.addWidget(self.act_btn)
        
        main_layout.addWidget(sidebar)

        # --- TÖBBRÉTEGŰ TARTALOM (Stacked Widget) ---
        self.stack = QStackedWidget()
        
        # 1. Oldal: Dashboard
        self.stack.addWidget(self.create_dashboard())
        # 2. Oldal: AI
        self.stack.addWidget(self.create_ai_panel())
        # 3. Oldal: OCR/Számlázó
        self.stack.addWidget(self.create_ocr_billing())
        # 4. Oldal: Cyber Shield
        self.stack.addWidget(self.create_security_center())
        
        main_layout.addWidget(self.stack)

    # --- MODULOK LÉTREHOZÁSA ---
    
    def create_dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("<h1>Vállalati Analitika</h1>"))
        
        # Grafikon integráció
        graph = pg.PlotWidget()
        graph.setBackground('#0d1117')
        graph.plot([1,2,3,4,5], [10,25,18,35,42], pen=pg.mkPen(color='#58a6ff', width=3))
        layout.addWidget(graph)
        return page

    def create_ai_panel(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("<h1>Business Genius AI</h1>"))
        self.ai_output = QTextEdit()
        self.ai_output.setReadOnly(True)
        self.ai_output.setStyleSheet("background: #0d1117; border: 1px solid #30363d;")
        layout.addWidget(self.ai_output)
        
        entry = QLineEdit()
        entry.setPlaceholderText("Kérdezzen az üzleti stratégiáról...")
        layout.addWidget(entry)
        return page

    def create_ocr_billing(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("<h1>Intelligens Számlafeldolgozás</h1>"))
        btn = QPushButton("📁 SZÁMLA BEOLVASÁSA (OCR)")
        btn.setStyleSheet("background: #38bdf8; color: black; font-weight: bold;")
        layout.addWidget(btn)
        
        table = QTableWidget(5, 3)
        table.setHorizontalHeaderLabels(["Partner", "Összeg", "Dátum"])
        layout.addWidget(table)
        return page

    def create_security_center(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("<h1>Active Cyber Shield</h1>"))
        log = QListWidget()
        log.addItem("🛡️ Rendszerfigyelő aktív...")
        log.addItem("✅ Tűzfal állapota: OK")
        layout.addWidget(log)
        return page

    # --- LOGIKA ---
    
    def show_activation(self):
        correct_key = hashlib.md5((self.hwid + SALT).encode()).hexdigest()[:10].upper()
        key, ok = QInputDialog.getText(self, "Licenc", f"HWID: {self.hwid}\nKulcs:")
        if ok and key.upper() == correct_key:
            QMessageBox.information(self, "Siker", "Enterprise Licenc Aktiválva!")
            self.act_btn.hide()
            logging.info("Szoftver sikeresen aktiválva.")

# --- INDÍTÁS ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProBizMaster()
    window.show()
    sys.exit(app.exec())
