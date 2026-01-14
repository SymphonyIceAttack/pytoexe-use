import sys, hashlib, uuid, os, time, logging, winreg
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIcon, QAction, QSystemTrayIcon, QMenu
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# --- RENDSZERSZINTŰ SZERVIZ MODUL (Windows fókusz) ---
class SystemService:
    @staticmethod
    def set_autostart(enabled=True):
        """Bejegyzi a programot a Windows Registry-be az automatikus indításhoz."""
        app_name = "ProBizOS2026"
        file_path = os.path.realpath(sys.argv[0])
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if enabled:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, file_path)
                logging.info("Auto-start sikeresen aktiválva a Registry-ben.")
            else:
                winreg.DeleteValue(key, app_name)
            winreg.CloseKey(key)
        except Exception as e:
            logging.error(f"Registry hiba: {e}")

class BackgroundWatcher(QThread):
    """Folyamatos háttérfigyelő szerviz (pl. gyanús folyamatok ellen)."""
    alert = pyqtSignal(str)

    def run(self):
        while True:
            # Itt lehetne figyelni a processzeket (pl. psutil-al)
            # Ha gyanús tevékenységet észlelünk, jelezzük a főprogramnak
            time.sleep(10) 

# --- FŐ OS-SZINTŰ ALKALMAZÁS ---
class ProBizOS(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_system_integration()
        self.init_ui()

    def init_system_integration(self):
        # 1. Automatikus indítás beállítása
        SystemService.set_autostart(True)
        
        # 2. Tálca ikon (System Tray) beállítása
        self.tray_icon = QSystemTrayIcon(self)
        # Itt egy valódi .ico fájl elérési útja kellene
        self.tray_icon.setIcon(QIcon("logo.png")) 
        
        # Tálca menü
        tray_menu = QMenu()
        show_action = QAction("Megnyitás", self)
        show_action.triggered.connect(self.showNormal)
        quit_action = QAction("Kilépés", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # 3. Háttérszerviz indítása
        self.watcher = BackgroundWatcher()
        self.watcher.alert.connect(self.handle_security_alert)
        self.watcher.start()

    def handle_security_alert(self, msg):
        self.tray_icon.showMessage("Biztonsági Figyelmeztetés", msg, QSystemTrayIcon.MessageIcon.Warning)

    def closeEvent(self, event):
        """Bezáráskor nem lép ki, csak a tálcára kicsinyít."""
        if self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage("ProBiz OS", "A rendszer a háttérben tovább fut.", QSystemTrayIcon.MessageIcon.Information)
            event.ignore()

    def init_ui(self):
        self.setWindowTitle("ProBiz OS - System Service Level")
        self.setFixedSize(1200, 800)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel("<h1>ProBiz Rendszerszintű Vezérlőpult</h1>"))
        layout.addWidget(QLabel(f"Rendszer állapot: <b>AKTÍV</b><br>HWID: {hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:12].upper()}"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Biztosítjuk, hogy ne lépjen ki az utolsó ablak bezárásakor (mert a tálcán fut tovább)
    app.setQuitOnLastWindowClosed(False)
    window = ProBizOS()
    window.show()
    sys.exit(app.exec())
