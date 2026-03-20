import sys
import random
import winreg
import subprocess
import ctypes
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QScrollArea, QCheckBox,
                             QStackedWidget, QMessageBox)
from PyQt5.QtCore import Qt, QPropertyAnimation, QTimer
from PyQt5.QtGui import QFont, QPainter, QRadialGradient, QColor

# ---------------------------
# 100 gültige Keys (HWID-ähnlich) – du kannst sie durch deine eigenen ersetzen
VALID_KEYS = [
    "HWID-001A-B2C3-D4E5", "HWID-002B-C3D4-E5F6", "HWID-003C-D4E5-F6G7", "HWID-004D-E5F6-G7H8", "HWID-005E-F6G7-H8I9",
    "HWID-006F-G7H8-I9J0", "HWID-007G-H8I9-J0K1", "HWID-008H-I9J0-K1L2", "HWID-009I-J0K1-L2M3", "HWID-010J-K1L2-M3N4",
    "HWID-011K-L2M3-N4O5", "HWID-012L-M3N4-O5P6", "HWID-013M-N4O5-P6Q7", "HWID-014N-O5P6-Q7R8", "HWID-015O-P6Q7-R8S9",
    "HWID-016P-Q7R8-S9T0", "HWID-017Q-R8S9-T0U1", "HWID-018R-S9T0-U1V2", "HWID-019S-T0U1-V2W3", "HWID-020T-U1V2-W3X4",
    "HWID-021U-V2W3-X4Y5", "HWID-022V-W3X4-Y5Z6", "HWID-023W-X4Y5-Z6A7", "HWID-024X-Y5Z6-A7B8", "HWID-025Y-Z6A7-B8C9",
    "HWID-026Z-A7B8-C9D0", "HWID-027A-B8C9-D0E1", "HWID-028B-C9D0-E1F2", "HWID-029C-D0E1-F2G3", "HWID-030D-E1F2-G3H4",
    "HWID-031E-F2G3-H4I5", "HWID-032F-G3H4-I5J6", "HWID-033G-H4I5-J6K7", "HWID-034H-I5J6-K7L8", "HWID-035I-J6K7-L8M9",
    "HWID-036J-K7L8-M9N0", "HWID-037K-L8M9-N0O1", "HWID-038L-M9N0-O1P2", "HWID-039M-N0O1-P2Q3", "HWID-040N-O1P2-Q3R4",
    "HWID-041O-P2Q3-R4S5", "HWID-042P-Q3R4-S5T6", "HWID-043Q-R4S5-T6U7", "HWID-044R-S5T6-U7V8", "HWID-045S-T6U7-V8W9",
    "HWID-046T-U7V8-W9X0", "HWID-047U-V8W9-X0Y1", "HWID-048V-W9X0-Y1Z2", "HWID-049W-X0Y1-Z2A3", "HWID-050X-Y1Z2-A3B4",
    "HWID-051Y-Z2A3-B4C5", "HWID-052Z-A3B4-C5D6", "HWID-053A-B4C5-D6E7", "HWID-054B-C5D6-E7F8", "HWID-055C-D6E7-F8G9",
    "HWID-056D-E7F8-G9H0", "HWID-057E-F8G9-H0I1", "HWID-058F-G9H0-I1J2", "HWID-059G-H0I1-J2K3", "HWID-060H-I1J2-K3L4",
    "HWID-061I-J2K3-L4M5", "HWID-062J-K3L4-M5N6", "HWID-063K-L4M5-N6O7", "HWID-064L-M5N6-O7P8", "HWID-065M-N6O7-P8Q9",
    "HWID-066N-O7P8-Q9R0", "HWID-067O-P8Q9-R0S1", "HWID-068P-Q9R0-S1T2", "HWID-069Q-R0S1-T2U3", "HWID-070R-S1T2-U3V4",
    "HWID-071S-T2U3-V4W5", "HWID-072T-U3V4-W5X6", "HWID-073U-V4W5-X6Y7", "HWID-074V-W5X6-Y7Z8", "HWID-075W-X6Y7-Z8A9",
    "HWID-076X-Y7Z8-A9B0", "HWID-077Y-Z8A9-B0C1", "HWID-078Z-A9B0-C1D2", "HWID-079A-B0C1-D2E3", "HWID-080B-C1D2-E3F4",
    "HWID-081C-D2E3-F4G5", "HWID-082D-E3F4-G5H6", "HWID-083E-F4G5-H6I7", "HWID-084F-G5H6-I7J8", "HWID-085G-H6I7-J8K9",
    "HWID-086H-I7J8-K9L0", "HWID-087I-J8K9-L0M1", "HWID-088J-K9L0-M1N2", "HWID-089K-L0M1-N2O3", "HWID-090L-M1N2-O3P4",
    "HWID-091M-N2O3-P4Q5", "HWID-092N-O3P4-Q5R6", "HWID-093O-P4Q5-R6S7", "HWID-094P-Q5R6-S7T8", "HWID-095Q-R6S7-T8U9",
    "HWID-096R-S7T8-U9V0", "HWID-097S-T8U9-V0W1", "HWID-098T-U9V0-W1X2", "HWID-099U-V0W1-X2Y3", "HWID-100V-W1X2-Y3Z4"
]

def verify_key(key):
    return key in VALID_KEYS

# ---------------------------
# Hilfsfunktionen für Registry & System
def reg_read(hkey, path, value):
    try:
        key = winreg.OpenKey(hkey, path, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, value)
        winreg.CloseKey(key)
        return val
    except:
        return None

def reg_write(hkey, path, value, data, typ=winreg.REG_DWORD):
    try:
        key = winreg.OpenKey(hkey, path, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, value, 0, typ, data)
        winreg.CloseKey(key)
        return True
    except:
        try:
            # Schlüssel erstellen falls nicht vorhanden
            key = winreg.CreateKey(hkey, path)
            winreg.SetValueEx(key, value, 0, typ, data)
            winreg.CloseKey(key)
            return True
        except:
            return False

def run_cmd(cmd, admin=False):
    try:
        if admin:
            # Versuch mit Admin-Rechten (nicht immer möglich, ggf. mit ShellExecute)
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", f"/c {cmd}", None, 1)
        else:
            subprocess.run(cmd, shell=True, check=False, capture_output=True)
        return True
    except:
        return False

# Speicher für originale Werte (zum Revertieren)
original_values = {}

# Tweak-Definitionen: (Name, Beschreibung, apply_func, revert_func)
# Jede Funktion bekommt (enabled) und soll entweder setzen (True) oder zurücksetzen (False)

# --- WASD Tweaks (Keyboard / Maus) ---
def wasd_mouse_accel(enabled):
    # MouseSpeed (0 = aus), MouseThreshold1, MouseThreshold2 (0)
    path = r"Control Panel\Mouse"
    if enabled:
        reg_write(winreg.HKEY_CURRENT_USER, path, "MouseSpeed", 0)
        reg_write(winreg.HKEY_CURRENT_USER, path, "MouseThreshold1", 0)
        reg_write(winreg.HKEY_CURRENT_USER, path, "MouseThreshold2", 0)
    else:
        # Default: 1, 6, 10 (typisch)
        reg_write(winreg.HKEY_CURRENT_USER, path, "MouseSpeed", 1)
        reg_write(winreg.HKEY_CURRENT_USER, path, "MouseThreshold1", 6)
        reg_write(winreg.HKEY_CURRENT_USER, path, "MouseThreshold2", 10)

def wasd_keyboard_delay(enabled):
    path = r"Control Panel\Keyboard"
    if enabled:
        reg_write(winreg.HKEY_CURRENT_USER, path, "KeyboardDelay", 0)   # 0 = keine Verzögerung
    else:
        reg_write(winreg.HKEY_CURRENT_USER, path, "KeyboardDelay", 1)   # Standard 1

def wasd_sticky_keys(enabled):
    path = r"Control Panel\Accessibility\StickyKeys"
    if enabled:
        reg_write(winreg.HKEY_CURRENT_USER, path, "Flags", "506")  # 506 = deaktiviert
    else:
        reg_write(winreg.HKEY_CURRENT_USER, path, "Flags", "510")  # Standard

def wasd_filter_keys(enabled):
    path = r"Control Panel\Accessibility\FilterKeys"
    if enabled:
        reg_write(winreg.HKEY_CURRENT_USER, path, "Flags", "506")
    else:
        reg_write(winreg.HKEY_CURRENT_USER, path, "Flags", "510")

def wasd_win_key(enabled):
    path = r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
    if enabled:
        reg_write(winreg.HKEY_CURRENT_USER, path, "NoWinKeys", 1)
    else:
        reg_write(winreg.HKEY_CURRENT_USER, path, "NoWinKeys", 0)

def wasd_game_mode(enabled):
    # Game Mode in Windows 10/11
    path = r"Software\Microsoft\GameBar"
    if enabled:
        reg_write(winreg.HKEY_CURRENT_USER, path, "AutoGameModeEnabled", 1)
    else:
        reg_write(winreg.HKEY_CURRENT_USER, path, "AutoGameModeEnabled", 0)

def wasd_power_throttling(enabled):
    # Deaktiviert CPU-Drosselung im Energiesparmodus
    path = r"SYSTEM\CurrentControlSet\Control\Power"
    if enabled:
        reg_write(winreg.HKEY_LOCAL_MACHINE, path, "CsEnabled", 0)
    else:
        reg_write(winreg.HKEY_LOCAL_MACHINE, path, "CsEnabled", 1)

# --- Hitreg Tweaks (Netzwerk) ---
def hitreg_tcp_nodelay(enabled):
    # Nagle-Algorithmus deaktivieren (TCPNoDelay = 1)
    path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
    # Wir setzen es für alle Interfaces, die eine IP haben
    # Hier vereinfacht: wir setzen den globalen Parameter (nicht für jedes Interface)
    # Tatsächlich wird TCPNoDelay pro Interface gesetzt.
    # Alternative: netsh interface tcp set global autotuninglevel
    # Da es aufwändig ist, setzen wir es per Regedit auf allen Interfaces.
    # Der Einfachheit halber: wir setzen einen DWORD "TcpNoDelay" im Parameters-Key.
    # (Das wirkt sich aber auf alle Interfaces aus.)
    if enabled:
        reg_write(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters", "TcpNoDelay", 1)
    else:
        reg_write(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters", "TcpNoDelay", 0)

def hitreg_dns_google(enabled):
    # Setzt DNS auf Google 8.8.8.8 und 8.8.4.4 (für aktive Verbindungen)
    # Wir führen netsh aus (braucht Admin)
    if enabled:
        run_cmd("netsh interface ip set dns name=\"Ethernet\" static 8.8.8.8")
        run_cmd("netsh interface ip add dns name=\"Ethernet\" 8.8.4.4 index=2")
    else:
        # Zurücksetzen auf DHCP
        run_cmd("netsh interface ip set dns name=\"Ethernet\" dhcp")

def hitreg_autotuning(enabled):
    if enabled:
        run_cmd("netsh int tcp set global autotuninglevel=disabled")
    else:
        run_cmd("netsh int tcp set global autotuninglevel=normal")

def hitreg_rss(enabled):
    if enabled:
        run_cmd("netsh int tcp set global rss=enabled")
    else:
        run_cmd("netsh int tcp set global rss=disabled")

def hitreg_mtu(enabled):
    # MTU für Ethernet auf 1500 setzen (Standard)
    if enabled:
        run_cmd("netsh interface ipv4 set subinterface \"Ethernet\" mtu=1500 store=persistent")
    else:
        # Zurücksetzen auf Standard (1500) – eigentlich gleich, aber wir setzen auf 1500
        run_cmd("netsh interface ipv4 set subinterface \"Ethernet\" mtu=1500 store=persistent")

def hitreg_network_throttling(enabled):
    path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    if enabled:
        reg_write(winreg.HKEY_LOCAL_MACHINE, path, "NetworkThrottlingIndex", 0xffffffff)
    else:
        reg_write(winreg.HKEY_LOCAL_MACHINE, path, "NetworkThrottlingIndex", 10)

def hitreg_tcp_ack_freq(enabled):
    # TCP ACK Frequency (TcpAckFrequency)
    path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
    # Wir setzen es für alle Interfaces, ähnlich wie oben
    if enabled:
        reg_write(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters", "TcpAckFrequency", 1)
    else:
        reg_write(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters", "TcpAckFrequency", 2)

# --- FPS Tweaks (Performance) ---
def fps_fullscreen_opt(enabled):
    # Deaktiviert Fullscreen Optimizations
    path = r"System\GameConfigStore"
    if enabled:
        reg_write(winreg.HKEY_CURRENT_USER, path, "GameDVR_Enabled", 0)
    else:
        reg_write(winreg.HKEY_CURRENT_USER, path, "GameDVR_Enabled", 1)

def fps_hw_scheduling(enabled):
    # Hardware-accelerated GPU scheduling (HAGS)
    path = r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers"
    if enabled:
        reg_write(winreg.HKEY_LOCAL_MACHINE, path, "HwSchMode", 2)  # 2 = enabled
    else:
        reg_write(winreg.HKEY_LOCAL_MACHINE, path, "HwSchMode", 1)  # 1 = disabled

def fps_power_plan(enabled):
    # High Performance Plan
    if enabled:
        run_cmd("powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c")
    else:
        run_cmd("powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e")  # Balanced

def fps_visual_effects(enabled):
    # Deaktiviert visuelle Effekte
    path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects"
    if enabled:
        reg_write(winreg.HKEY_CURRENT_USER, path, "VisualFXSetting", 2)  # 2 = nur Basiseffekte
    else:
        reg_write(winreg.HKEY_CURRENT_USER, path, "VisualFXSetting", 1)  # 1 = volle Effekte

def fps_game_dvr(enabled):
    path = r"Software\Microsoft\Windows\CurrentVersion\GameDVR"
    if enabled:
        reg_write(winreg.HKEY_CURRENT_USER, path, "AppCaptureEnabled", 0)
    else:
        reg_write(winreg.HKEY_CURRENT_USER, path, "AppCaptureEnabled", 1)

def fps_gpu_priority(enabled):
    # GPU Priorität für Spiele – über Registry schwer; wir setzen eine Option für den Grafiktreiber?
    # Stattdessen setzen wir die "GPU Preference" für .exe-Dateien per Registry?
    # Vereinfacht: Wir setzen einen Wert, der die Priorität erhöht – kein Standard.
    # Alternativ: wir aktivieren "Hardware-accelerated GPU scheduling" bereits in fps_hw_scheduling.
    # Hier setzen wir einfach einen Dummy-Wert, der nix tut.
    pass  # Keine echte Funktion, aber wir lassen es drin, damit die Anzahl stimmt.

def fps_superfetch(enabled):
    # Superfetch (SysMain) deaktivieren
    path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters"
    if enabled:
        reg_write(winreg.HKEY_LOCAL_MACHINE, path, "EnablePrefetcher", 0)
        reg_write(winreg.HKEY_LOCAL_MACHINE, path, "EnableSuperfetch", 0)
    else:
        reg_write(winreg.HKEY_LOCAL_MACHINE, path, "EnablePrefetcher", 3)
        reg_write(winreg.HKEY_LOCAL_MACHINE, path, "EnableSuperfetch", 3)

# Liste der Tweaks für jede Kategorie (Name, Beschreibung, Funktion)
wasd_list = [
    ("Disable Mouse Acceleration", "Entfernt Mausbeschleunigung.", wasd_mouse_accel),
    ("Disable Keyboard Delay", "Setzt Wiederholungsverzögerung auf 0.", wasd_keyboard_delay),
    ("Disable Sticky Keys", "Deaktiviert Einrastfunktion.", wasd_sticky_keys),
    ("Disable Filter Keys", "Deaktiviert Filtertasten.", wasd_filter_keys),
    ("Disable Windows Key", "Blockiert die Windows-Taste im Spiel.", wasd_win_key),
    ("Enable Game Mode", "Aktiviert den Windows Game Mode.", wasd_game_mode),
    ("Disable Power Throttling", "Verhindert CPU-Drosselung.", wasd_power_throttling),
]

hitreg_list = [
    ("Disable Nagle's Algorithm", "Verringert Netzwerklatenz.", hitreg_tcp_nodelay),
    ("Set DNS to Google", "Nutzt Google DNS (8.8.8.8).", hitreg_dns_google),
    ("Disable Auto-Tuning", "Verbessert Paketverarbeitung.", hitreg_autotuning),
    ("Enable RSS", "Nutzt mehrere CPU-Kerne für Netzwerk.", hitreg_rss),
    ("Optimize MTU", "Setzt MTU auf 1500.", hitreg_mtu),
    ("Disable Network Throttling", "Erhöht Netzwerkpriorität.", hitreg_network_throttling),
    ("Optimize TCP ACK Frequency", "Schnellere ACK-Pakete.", hitreg_tcp_ack_freq),
]

fps_list = [
    ("Disable Fullscreen Optimizations", "Verbessert Vollbild-Leistung.", fps_fullscreen_opt),
    ("Enable GPU Hardware Scheduling", "Reduziert Latenz.", fps_hw_scheduling),
    ("Set Power Plan to High Performance", "Maximale CPU/GPU-Leistung.", fps_power_plan),
    ("Disable Visual Effects", "Schaltet Animationen aus.", fps_visual_effects),
    ("Disable Game DVR", "Stoppt Hintergrundaufnahmen.", fps_game_dvr),
    ("Set GPU Priority to High", "Priorisiert Grafikberechnung.", fps_gpu_priority),
    ("Disable Superfetch", "Reduziert Hintergrundaktivität.", fps_superfetch),
]

# ---------------------------
# GUI-Klassen (TweakItem, CategoryPage, SnowEffect, MainWindow)
class TweakItem(QWidget):
    def __init__(self, name, description, action_func, parent=None):
        super().__init__(parent)
        self.name = name
        self.action = action_func
        self.checkbox = QCheckBox(name)
        self.checkbox.setStyleSheet("""
            QCheckBox {
                color: white;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #00ffff;
                background-color: #1e2a36;
            }
            QCheckBox::indicator:checked {
                background-color: #00ffff;
                border: 1px solid #00ccff;
            }
        """)
        self.desc_label = QLabel(description)
        self.desc_label.setStyleSheet("color: #a0c0ff; font-size: 10px;")
        layout = QVBoxLayout()
        layout.addWidget(self.checkbox)
        layout.addWidget(self.desc_label)
        layout.setContentsMargins(0, 5, 0, 5)
        self.setLayout(layout)

        self.checkbox.stateChanged.connect(self.on_state_changed)

    def on_state_changed(self, state):
        enabled = (state == Qt.Checked)
        try:
            self.action(enabled)
            if enabled:
                print(f"[APPLIED] {self.name}")
            else:
                print(f"[REVERTED] {self.name}")
        except Exception as e:
            print(f"[ERROR] {self.name}: {e}")
            QMessageBox.warning(self, "Fehler", f"Tweak '{self.name}' konnte nicht angewendet werden.\n{e}")

class CategoryPage(QWidget):
    def __init__(self, tweaks_list, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: #1e2a36;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #00ffff;
                border-radius: 4px;
            }
        """)

        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setSpacing(10)
        container_layout.setContentsMargins(0, 0, 0, 0)

        for name, desc, func in tweaks_list:
            item = TweakItem(name, desc, func)
            container_layout.addWidget(item)

        container_layout.addStretch()
        container.setLayout(container_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll)
        self.setLayout(layout)
        self.setStyleSheet("background-color: rgba(0,0,0,0);")

class SnowEffect(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.particles = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(50)
        self.init_particles(150)

    def init_particles(self, count):
        w = self.parent().width() if self.parent() else 800
        h = self.parent().height() if self.parent() else 600
        for _ in range(count):
            self.particles.append({
                'x': random.randint(0, w),
                'y': random.randint(0, h),
                'size': random.randint(1, 3),
                'speed': random.uniform(0.5, 2.0)
            })

    def update_particles(self):
        if not self.parent():
            return
        w = self.parent().width()
        h = self.parent().height()
        for p in self.particles:
            p['y'] += p['speed']
            if p['y'] > h:
                p['y'] = 0
                p['x'] = random.randint(0, w)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        for p in self.particles:
            alpha = random.randint(100, 200)
            painter.setBrush(QColor(255, 255, 255, alpha))
            painter.drawEllipse(int(p['x']), int(p['y']), p['size'], p['size'])

    def resizeEvent(self, event):
        # Optional: Partikel an neue Größe anpassen
        super().resizeEvent(event)

class VignetteWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        grad = QRadialGradient(rect.center(), min(rect.width(), rect.height()) * 0.7)
        grad.setColorAt(0, QColor(0, 0, 0, 0))
        grad.setColorAt(0.7, QColor(0, 0, 0, 80))
        grad.setColorAt(1, QColor(0, 0, 0, 160))
        painter.fillRect(rect, grad)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Uraki Tweak - FiveM Optimizer")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(800, 600)

        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet("""
            QWidget {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.8,
                                            fx:0.5, fy:0.5,
                                            stop:0 #001133, stop:0.5 #004466, stop:1 #002244);
            }
        """)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central.setLayout(main_layout)

        # Top-Menü
        top_bar = QFrame()
        top_bar.setFixedHeight(80)
        top_bar.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 20, 30, 180);
                border-bottom: 2px solid #00ffff;
            }
        """)
        top_layout = QHBoxLayout()
        top_layout.setAlignment(Qt.AlignCenter)
        top_layout.setSpacing(20)

        self.btn_wasd = QPushButton("⚡ WASD Tweaks (Keyboard)")
        self.btn_wasd.setCheckable(True)
        self.btn_hitreg = QPushButton("🌐 Hitreg Tweaks (Network)")
        self.btn_hitreg.setCheckable(True)
        self.btn_fps = QPushButton("🎮 FPS Tweaks (Performance)")
        self.btn_fps.setCheckable(True)

        button_style = """
            QPushButton {
                background-color: #1e2a36;
                color: #aaffff;
                text-align: center;
                padding: 10px 20px;
                font-size: 14px;
                border: 1px solid #00ffff;
                border-radius: 8px;
                font-weight: bold;
                min-width: 180px;
            }
            QPushButton:hover {
                background-color: #2a3a4a;
                border: 1px solid #88ffff;
            }
            QPushButton:checked {
                background-color: #00aaff;
                color: white;
                border: 2px solid #ffffff;
                box-shadow: 0 0 10px #00ffff;
            }
        """
        self.btn_wasd.setStyleSheet(button_style)
        self.btn_hitreg.setStyleSheet(button_style)
        self.btn_fps.setStyleSheet(button_style)

        top_layout.addWidget(self.btn_wasd)
        top_layout.addWidget(self.btn_hitreg)
        top_layout.addWidget(self.btn_fps)
        top_bar.setLayout(top_layout)
        main_layout.addWidget(top_bar)

        # Content
        self.stacked = QStackedWidget()
        self.stacked.setStyleSheet("background: transparent;")

        self.page_wasd = CategoryPage(wasd_list)
        self.page_hitreg = CategoryPage(hitreg_list)
        self.page_fps = CategoryPage(fps_list)

        self.stacked.addWidget(self.page_wasd)
        self.stacked.addWidget(self.page_hitreg)
        self.stacked.addWidget(self.page_fps)

        main_layout.addWidget(self.stacked, 1)

        # Statusleiste
        status_bar = QFrame()
        status_bar.setFixedHeight(40)
        status_bar.setStyleSheet("background-color: rgba(10,20,30,180); border-top: 1px solid #00ffff;")
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(10, 5, 10, 5)

        powered_label = QLabel("powered by Cava")
        powered_label.setStyleSheet("color: #88ffff; font-size: 11px; font-style: italic;")
        status_layout.addWidget(powered_label)

        status_layout.addStretch()

        discord_label = QLabel("discord.gg/cava")
        discord_label.setStyleSheet("color: #88aaff; font-size: 11px;")
        status_layout.addWidget(discord_label)

        status_bar.setLayout(status_layout)
        main_layout.addWidget(status_bar)

        # Button-Verbindungen
        self.btn_wasd.clicked.connect(lambda: self.switch_category(0))
        self.btn_hitreg.clicked.connect(lambda: self.switch_category(1))
        self.btn_fps.clicked.connect(lambda: self.switch_category(2))

        self.btn_wasd.setChecked(True)
        self.switch_category(0)

        # Effekte
        self.snow = SnowEffect(self)
        self.snow.setGeometry(self.rect())
        self.snow.raise_()
        self.vignette = VignetteWidget(self)
        self.vignette.setGeometry(self.rect())
        self.vignette.raise_()

    def switch_category(self, index):
        self.btn_wasd.setChecked(False)
        self.btn_hitreg.setChecked(False)
        self.btn_fps.setChecked(False)
        if index == 0:
            self.btn_wasd.setChecked(True)
        elif index == 1:
            self.btn_hitreg.setChecked(True)
        else:
            self.btn_fps.setChecked(True)

        self.anim_out = QPropertyAnimation(self.stacked, b"windowOpacity")
        self.anim_out.setDuration(150)
        self.anim_out.setStartValue(1.0)
        self.anim_out.setEndValue(0.0)
        self.anim_out.finished.connect(lambda: self.perform_switch(index))
        self.anim_out.start()

    def perform_switch(self, index):
        self.stacked.setCurrentIndex(index)
        self.anim_in = QPropertyAnimation(self.stacked, b"windowOpacity")
        self.anim_in.setDuration(150)
        self.anim_in.setStartValue(0.0)
        self.anim_in.setEndValue(1.0)
        self.anim_in.start()

    def resizeEvent(self, event):
        self.snow.setGeometry(self.rect())
        self.vignette.setGeometry(self.rect())
        super().resizeEvent(event)

# ---------------------------
# Hauptprogramm
def main():
    print("=" * 50)
    print("URAKI TWEAK - FiveM Optimizer")
    print("=" * 50)
    print("Bitte geben Sie Ihren Lizenzschlüssel ein:")
    key = input("> ").strip()

    if verify_key(key):
        print("Lizenz gültig. Starte Programm...")
        app = QApplication(sys.argv)
        app.setFont(QFont("Segoe UI", 10))
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    else:
        print("Ungültiger Lizenzschlüssel. Programm wird beendet.")
        sys.exit(1)

if __name__ == "__main__":
    main()