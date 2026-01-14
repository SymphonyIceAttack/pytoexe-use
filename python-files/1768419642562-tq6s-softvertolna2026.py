import sys, os, hashlib, platform, json, webbrowser, io, sqlite3, psutil
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import qrcode
from reportlab.pdfgen import canvas

# ==========================================
# BIZTONSÁGI MAG (HWID & ENCRYPTION)
# ==========================================
class SecurityCore:
    @staticmethod
    def get_hwid():
        unique_str = platform.node() + platform.processor() + platform.machine()
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16].upper()

# ==========================================
# ALKALMAZÁSOK (APPS)
# ==========================================

class WalletApp(QWidget):
    def __init__(self, hwid):
        super().__init__()
        l = QVBoxLayout(self)
        self.setStyleSheet("background: #0b0e14; color: white;")
        
        qr = qrcode.make(f"bitcoin:bc1q_WALLET_CIM?amount=0.01&label={hwid}")
        buf = io.BytesIO()
        qr.save(buf, format="PNG")
        qimg = QImage.fromData(buf.getvalue())
        
        qr_label = QLabel()
        qr_label.setPixmap(QPixmap.fromImage(qimg).scaled(200, 200))
        qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        l.addWidget(QLabel(f"<b>Pénztárca - ID: {hwid}</b>"))
        l.addWidget(qr_label)
        l.addWidget(QLabel("Egyenleg: 150.000 Ft"))
        
        btn_stripe = QPushButton("💳 Kártyás fizetés (Stripe)")
        btn_stripe.setStyleSheet("background: #6772e5; padding: 10px;")
        l.addWidget(btn_stripe)

class ExplorerApp(QWidget):
    def __init__(self):
        super().__init__()
        l = QVBoxLayout(self)
        self.list = QListWidget()
        self.list.setStyleSheet("background: #05070a; color: #00ff00;")
        path = os.path.join(os.getcwd(), "Enterprise_Files")
        if not os.path.exists(path): os.makedirs(path)
        for f in os.listdir(path): self.list.addItem(f"📄 {f}")
        l.addWidget(QLabel("Munkakönyvtár: /Enterprise_Files"))
        l.addWidget(self.list)

class TaskManagerApp(QWidget):
    def __init__(self):
        super().__init__()
        l = QVBoxLayout(self)
        self.cpu = QProgressBar()
        self.ram = QProgressBar()
        l.addWidget(QLabel("CPU Terhelés:"))
        l.addWidget(self.cpu)
        l.addWidget(QLabel("RAM Használat:"))
        l.addWidget(self.ram)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

    def refresh(self):
        self.cpu.setValue(int(psutil.cpu_percent()))
        self.ram.setValue(int(psutil.virtual_memory().percent))

# ==========================================
# FŐ OPERÁCIÓS RENDSZER (MINI OS)
# ==========================================
class EnterpriseOS(QMainWindow):
    def __init__(self):
        super().__init__()
        self.hwid = SecurityCore.get_hwid()
        self.setWindowTitle("Tolna MI - Enterprise OS v2.0")
        self.showFullScreen()
        
        self.mdi = QMdiArea()
        self.mdi.setBackground(QBrush(QColor("#05070a")))
        self.setCentralWidget(self.mdi)
        
        self.init_desktop()
        self.init_taskbar()

    def init_desktop(self):
        icon_cont = QWidget(self.mdi)
        layout = QVBoxLayout(icon_cont)
        
        apps = [
            ("Pénztárca", self.open_wallet),
            ("Fájlkezelő", self.open_explorer),
            ("Rendszer", self.open_taskmgr),
            ("Riport (PDF)", self.gen_pdf)
        ]
        
        for name, func in apps:
            btn = QToolButton()
            btn.setText(name)
            btn.setFixedSize(80, 80)
            btn.clicked.connect(func)
            btn.setStyleSheet("color: white; font-weight: bold; border: 1px solid #1c222d;")
            layout.addWidget(btn)
            
        icon_cont.adjustSize()
        icon_cont.move(20, 20)

    def init_taskbar(self):
        tb = QToolBar("Taskbar")
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, tb)
        tb.setStyleSheet("background: #151921; border-top: 1px solid #333;")
        tb.addWidget(QPushButton(" 🚀 START "))
        
        self.time_lbl = QLabel()
        self.time_lbl.setStyleSheet("color: white; padding-right: 20px;")
        tb.addSeparator()
        tb.addWidget(self.time_lbl)
        
        t = QTimer(self)
        t.timeout.connect(lambda: self.time_lbl.setText(datetime.now().strftime(" %H:%M:%S ")))
        t.start(1000)

    def open_window(self, title, widget):
        sub = QMdiSubWindow()
        sub.setWidget(widget)
        sub.setWindowTitle(title)
        self.mdi.addSubWindow(sub)
        sub.show()

    def open_wallet(self): self.open_window("Wallet & QR", WalletApp(self.hwid))
    def open_explorer(self): self.open_window("Explorer", ExplorerApp())
    def open_taskmgr(self): self.open_window("Task Manager", TaskManagerApp())
    
    def gen_pdf(self):
        fname = f"Riport_{self.hwid}.pdf"
        c = canvas.Canvas(fname)
        c.drawString(100, 750, f"ENTERPRISE REPORT - {datetime.now()}")
        c.drawString(100, 730, f"HWID: {self.hwid}")
        c.save()
        QMessageBox.information(self, "Siker", f"Riport legenerálva: {fname}")

# ==========================================
# BELÉPŐ PANEL (LOGIN)
# ==========================================
class LoginScreen(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Biztonsági Belépés")
        self.setFixedSize(350, 250)
        self.setStyleSheet("background: #0b0e14; color: white;")
        l = QVBoxLayout(self)
        
        l.addWidget(QLabel("<b>ENTERPRISE LICENC ELLENŐRZÉS</b>"))
        self.key = QLineEdit()
        self.key.setPlaceholderText("Licenc kulcs...")
        self.key.setStyleSheet("padding: 8px; background: #1c222d; color: white;")
        l.addWidget(self.key)
        
        btn = QPushButton("BELÉPÉS")
        btn.setStyleSheet("background: #0078d4; padding: 10px; font-weight: bold;")
        btn.clicked.connect(self.check)
        l.addWidget(btn)
        
        self.hwid_lbl = QLabel(f"ID: {SecurityCore.get_hwid()}")
        self.hwid_lbl.setStyleSheet("font-size: 9px; color: #555;")
        l.addWidget(self.hwid_lbl)

    def check(self):
        if len(self.key.text()) > 5: self.accept() # Itt jönne a szerver kérés
        else: QMessageBox.warning(self, "Hiba", "Érvénytelen kulcs!")

# ==========================================
# INDÍTÁS
# ==========================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    login = LoginScreen()
    if login.exec() == QDialog.DialogCode.Accepted:
        window = EnterpriseOS()
        window.show()
        sys.exit(app.exec())
