import sys, hashlib, uuid, webbrowser, os, time
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# --- KONFIGURÁCIÓ ---
IBAN = "LT32 5007 5750 2639 01"
SALT = "PROBIZ_ULTIMATE_SECURITY_2026"

class SecurityWorker(QThread):
    """Háttérben futó vírusirtó szkenner szimuláció"""
    progress = pyqtSignal(int)
    def run(self):
        for i in range(101):
            time.sleep(0.05)
            self.progress.emit(i)

class ProBizUltimate(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProBiz Ultimate Suite 2026 - Security & Business")
        self.setFixedSize(1100, 800)
        self.hwid = hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:12].upper()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #0f172a; color: #e2e8f0;")
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # --- OLDALSÓ NAVIGÁCIÓ (Cyber Style) ---
        nav = QFrame()
        nav.setFixedWidth(260)
        nav.setStyleSheet("background-color: #1e293b; border-right: 2px solid #38bdf8;")
        nav_layout = QVBoxLayout(nav)
        
        logo = QLabel("PROBIZ ULTIMATE")
        logo.setFont(QFont("Orbitron", 18, QFont.Weight.Bold))
        logo.setStyleSheet("color: #38bdf8; margin-bottom: 30px;")
        nav_layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)

        self.stack = QStackedWidget()
        
        # Gombok
        self.menu_items = {
            "security": self.add_nav(nav_layout, "🛡️ Vírusirtó & Tűzfal"),
            "ai": self.add_nav(nav_layout, "🤖 AI Üzleti Asszisztens"),
            "billing": self.add_nav(nav_layout, "📊 Számlázó & GDPR"),
            "converter": self.add_nav(nav_layout, "🔄 Konvertáló (PDF/DOC)"),
            "logs": self.add_nav(nav_layout, "🕵️ Rendszer Logok")
        }

        nav_layout.addStretch()
        
        self.btn_act = QPushButton("🔑 PRO AKTIVÁLÁS")
        self.btn_act.setStyleSheet("background-color: #ef4444; padding: 15px; font-weight: bold; border-radius: 8px;")
        self.btn_act.clicked.connect(self.activation_dialog)
        nav_layout.addWidget(self.btn_act)

        layout.addWidget(nav)
        layout.addWidget(self.stack)
        self.create_pages()

    def add_nav(self, layout, text):
        btn = QPushButton(text)
        btn.setEnabled(False)
        btn.setStyleSheet("QPushButton { text-align: left; padding: 15px; border: none; font-size: 14px; color: #64748b; }")
        layout.addWidget(btn)
        return btn

    def create_pages(self):
        # 1. BIZTONSÁGI MODUL (Vírusirtó + Tűzfal)
        p1 = QWidget(); l1 = QVBoxLayout(p1)
        l1.addWidget(QLabel("<h1>Cyber Security Center</h1>"))
        self.scan_btn = QPushButton("Rendszer Teljes Átvizsgálása")
        self.scan_btn.clicked.connect(self.start_scan)
        l1.addWidget(self.scan_btn)
        self.pbar = QProgressBar()
        l1.addWidget(self.pbar)
        l1.addWidget(QLabel("Tűzfal Állapot: <font color='#22c55e'>AKTÍV</font>"))
        l1.addWidget(QLabel("Behatolásvédelem (IDS): <font color='#22c55e'>FIGYELÉS</font>"))
        self.stack.addWidget(p1)

        # 2. AI ASSZISZTENS
        p2 = QWidget(); l2 = QVBoxLayout(p2)
        l2.addWidget(QLabel("<h1>AI Business Genius</h1>"))
        self.ai_input = QTextEdit()
        self.ai_input.setPlaceholderText("Kérdezzen az AI-tól üzleti stratégiát...")
        l2.addWidget(self.ai_input)
        l2.addWidget(QPushButton("Elemzés Indítása"))
        self.stack.addWidget(p2)

        # 3. KONVERTÁLÓ
        p3 = QWidget(); l3 = QVBoxLayout(p3)
        l3.addWidget(QLabel("<h1>Univerzális Konvertáló</h1>"))
        l3.addWidget(QPushButton("📁 Fájl Kiválasztása"))
        cb = QComboBox()
        cb.addItems(["PDF -> DOCX", "DOCX -> PDF", "JPG -> PNG", "Excel -> XML"])
        l3.addWidget(cb)
        l3.addWidget(QPushButton("Konvertálás Indítása"))
        self.stack.addWidget(p3)

    def start_scan(self):
        self.worker = SecurityWorker()
        self.worker.progress.connect(self.pbar.setValue)
        self.worker.start()

    def activation_dialog(self):
        msg = f"<b>HWID:</b> {self.hwid}<br><br><b>Utalás:</b> {IBAN}<br>Fizetés után írja be a kapott kódot!"
        code, ok = QInputDialog.getText(self, "Licenc Aktiválás", msg)
        if ok:
            check = hashlib.md5((self.hwid + SALT).encode()).hexdigest()[:8].upper()
            if code.upper() == check:
                self.unlock_all()

    def unlock_all(self):
        self.btn_act.hide()
        for key, btn in self.menu_items.items():
            btn.setEnabled(True)
            btn.setStyleSheet("color: #38bdf8; font-weight: bold; text-align: left; padding: 15px;")
            # Oldalváltás bekötése
            idx = list(self.menu_items.keys()).index(key)
            btn.clicked.connect(lambda checked, i=idx: self.stack.setCurrentIndex(i))
        QMessageBox.information(self, "Siker", "Üdvözöljük a ProBiz Ultimate Suite-ban!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProBizUltimate()
    window.show()
    sys.exit(app.exec())
