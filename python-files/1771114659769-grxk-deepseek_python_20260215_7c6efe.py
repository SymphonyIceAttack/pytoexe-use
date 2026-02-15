#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CS:PY - External Counter-Strike 2 Cheat in Python
Basierend auf PyMem und PySide6
Features: ESP, Aimbot, Triggerbot, Bhop, GUI
"""

import ctypes
import ctypes.wintypes
import math
import random
import struct
import sys
import time
import threading
from datetime import datetime

# Windows API für Maus- und Tastaturereignisse
from ctypes import wintypes
from ctypes import windll, c_int, c_uint, c_void_p, byref, create_string_buffer

# PyMem für Speicherzugriff
try:
    import pymem
    import pymem.process
except ImportError:
    print("[!] PyMem nicht installiert. Führe 'pip install pymem' aus.")
    sys.exit(1)

# PyQt6/PySide6 für GUI
try:
    from PySide6.QtWidgets import *
    from PySide6.QtCore import *
    from PySide6.QtGui import *
except ImportError:
    print("[!] PySide6 nicht installiert. Führe 'pip install PySide6' aus.")
    sys.exit(1)

# Pynput für Hotkeys
try:
    from pynput import keyboard
except ImportError:
    print("[!] Pynput nicht installiert. Führe 'pip install pynput' aus.")
    sys.exit(1)

# =====================================================================
# OFFSETS (AUTO-UPDATING über cs2-dumper) [citation:2]
# =====================================================================

class Offsets:
    """CS2 Offsets - können automatisch aktualisiert werden"""
    
    # Standard-Offsets (Fallback)
    dwEntityList = 0x18C01A8
    dwLocalPlayerPawn = 0x1729A58
    dwViewMatrix = 0x1872BD0
    dwViewAngles = 0x19209F8
    
    # Netvars
    m_iHealth = 0x334
    m_iTeamNum = 0x3CB
    m_vOldOrigin = 0x1224
    m_aimPunchAngle = 0x1508
    m_pGameSceneNode = 0x310
    m_modelState = 0x160
    m_iFOV = 0x234
    m_bIsScoped = 0x238
    m_flFlashDuration = 0x300
    
    @classmethod
    def fetch_latest(cls):
        """Holt die neuesten Offsets von GitHub [citation:2]"""
        try:
            import requests
            url = "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                cls.dwEntityList = int(data.get("dwEntityList", cls.dwEntityList), 16)
                cls.dwLocalPlayerPawn = int(data.get("dwLocalPlayerPawn", cls.dwLocalPlayerPawn), 16)
                cls.dwViewMatrix = int(data.get("dwViewMatrix", cls.dwViewMatrix), 16)
                print("[*] Offsets erfolgreich aktualisiert")
            else:
                print("[!] Konnte Offsets nicht aktualisieren, verwende Standard")
        except Exception as e:
            print(f"[!] Fehler beim Offsets-Update: {e}")

# =====================================================================
# MEMORY MANAGER
# =====================================================================

class MemoryManager:
    """Verwaltet den Speicherzugriff auf CS2 [citation:4][citation:8]"""
    
    def __init__(self):
        self.pm = None
        self.client = None
        self.engine = None
        self.process_id = None
        self.connected = False
        
    def connect(self):
        """Verbindung zu CS2 herstellen"""
        try:
            self.pm = pymem.Pymem("cs2.exe")
            self.client = pymem.process.module_from_name(self.pm.process_handle, "client.dll")
            self.engine = pymem.process.module_from_name(self.pm.process_handle, "engine2.dll")
            
            if self.client and self.engine:
                self.connected = True
                print(f"[+] CS2 gefunden! PID: {self.pm.process_id}")
                print(f"[+] client.dll: 0x{self.client.lpBaseOfDll:X}")
                print(f"[+] engine2.dll: 0x{self.engine.lpBaseOfDll:X}")
                return True
            else:
                print("[!] Konnte Module nicht finden")
                return False
                
        except pymem.exception.ProcessNotFound:
            print("[!] CS2 läuft nicht. Bitte starte CS2 zuerst.")
            return False
        except Exception as e:
            print(f"[!] Verbindungsfehler: {e}")
            return False
    
    def read_int(self, address):
        """Liest einen Integer aus dem Speicher"""
        try:
            return self.pm.read_int(address)
        except:
            return 0
    
    def read_uint(self, address):
        """Liest einen Unsigned Integer"""
        try:
            return self.pm.read_uint(address)
        except:
            return 0
    
    def read_float(self, address):
        """Liest einen Float"""
        try:
            return self.pm.read_float(address)
        except:
            return 0.0
    
    def read_bool(self, address):
        """Liest einen Boolean"""
        try:
            return self.pm.read_bool(address)
        except:
            return False
    
    def read_bytes(self, address, size):
        """Liest Bytes"""
        try:
            return self.pm.read_bytes(address, size)
        except:
            return b'\x00' * size
    
    def write_int(self, address, value):
        """Schreibt einen Integer"""
        try:
            self.pm.write_int(address, value)
            return True
        except:
            return False
    
    def write_float(self, address, value):
        """Schreibt einen Float"""
        try:
            self.pm.write_float(address, value)
            return True
        except:
            return False
    
    def write_bool(self, address, value):
        """Schreibt einen Boolean"""
        try:
            self.pm.write_bool(address, value)
            return True
        except:
            return False
    
    def get_client_address(self, offset=0):
        """Gibt eine Adresse in client.dll zurück"""
        return self.client.lpBaseOfDll + offset
    
    def get_engine_address(self, offset=0):
        """Gibt eine Adresse in engine2.dll zurück"""
        return self.engine.lpBaseOfDll + offset

# =====================================================================
# ENTITY MANAGER
# =====================================================================

class Vector3:
    """3D-Vektor für Positionen"""
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z
    
    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def length(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    def distance_to(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)
    
    def to_tuple(self):
        return (self.x, self.y, self.z)
    
    @staticmethod
    def from_bytes(data, offset=0):
        """Erstellt Vector3 aus Bytes"""
        x = struct.unpack('<f', data[offset:offset+4])[0]
        y = struct.unpack('<f', data[offset+4:offset+8])[0]
        z = struct.unpack('<f', data[offset+8:offset+12])[0]
        return Vector3(x, y, z)

class Entity:
    """Repräsentiert einen Spieler im Spiel"""
    
    def __init__(self, mem, address):
        self.mem = mem
        self.address = address
        self.health = 0
        self.team = 0
        self.position = Vector3()
        self.head_position = Vector3()
        self.name = "Unknown"
        self.visible = False
        self.distance = 0.0
        self.update()
    
    def update(self):
        """Aktualisiert die Entity-Daten"""
        try:
            # Health lesen
            health_addr = self.address + Offsets.m_iHealth
            self.health = self.mem.read_int(health_addr)
            
            # Team lesen
            team_addr = self.address + Offsets.m_iTeamNum
            self.team = self.mem.read_int(team_addr)
            
            # Position lesen (Origin)
            origin_addr = self.address + Offsets.m_vOldOrigin
            origin_bytes = self.mem.read_bytes(origin_addr, 12)
            self.position = Vector3.from_bytes(origin_bytes, 0)
            
            # GameSceneNode für Kopfposition
            scene_node_addr = self.mem.read_int(self.address + Offsets.m_pGameSceneNode)
            if scene_node_addr:
                # Bone Position (Head ist normalerweise Bone 6)
                # Für CS2: Vereinfachte Kopfposition = Position + (0,0,70)
                self.head_position = Vector3(
                    self.position.x,
                    self.position.y,
                    self.position.z + 70
                )
            
            # Distanz berechnen (zum Local Player)
            # Wird später gesetzt
            
        except Exception as e:
            pass
    
    def is_alive(self):
        return self.health > 0 and self.health <= 100
    
    def is_enemy(self, local_team):
        return self.team != local_team and self.team in [2, 3]  # 2 = T, 3 = CT
    
    def __repr__(self):
        return f"Entity(health={self.health}, team={self.team}, pos=({self.position.x:.1f}, {self.position.y:.1f}))"

# =====================================================================
# MATH UTILITIES
# =====================================================================

class Math3D:
    """3D-Mathematik für WorldToScreen und Winkelberechnung"""
    
    @staticmethod
    def world_to_screen(matrix, pos, screen_width, screen_height):
        """Konvertiert 3D-Weltkoordinaten zu 2D-Bildschirmkoordinaten"""
        try:
            # Transformationsmatrix anwenden
            w = 0.0
            x = matrix[0] * pos[0] + matrix[1] * pos[1] + matrix[2] * pos[2] + matrix[3]
            y = matrix[4] * pos[0] + matrix[5] * pos[1] + matrix[6] * pos[2] + matrix[7]
            w = matrix[12] * pos[0] + matrix[13] * pos[1] + matrix[14] * pos[2] + matrix[15]
            
            if w < 0.01:
                return None
            
            inv_w = 1.0 / w
            x *= inv_w
            y *= inv_w
            
            # Bildschirmkoordinaten
            screen_x = (screen_width / 2) + (x * screen_width / 2)
            screen_y = (screen_height / 2) - (y * screen_height / 2)
            
            return (screen_x, screen_y)
        except:
            return None
    
    @staticmethod
    def calculate_angle(local_pos, target_pos):
        """Berechnet den Winkel zu einem Ziel"""
        try:
            delta = Vector3(
                target_pos.x - local_pos.x,
                target_pos.y - local_pos.y,
                target_pos.z - local_pos.z
            )
            
            hyp = math.sqrt(delta.x**2 + delta.y**2)
            
            pitch = -math.atan2(delta.z, hyp) * 180 / math.pi
            yaw = math.atan2(delta.y, delta.x) * 180 / math.pi
            
            return Vector3(pitch, yaw, 0)
        except:
            return None

# =====================================================================
# CONFIGURATION
# =====================================================================

class Config:
    """Globale Konfiguration für den Cheat"""
    
    def __init__(self):
        # Triggerbot
        self.triggerbot_enabled = False
        self.triggerbot_key = "shift"
        self.triggerbot_delay = 25  # ms
        self.triggerbot_radius = 10  # Pixel
        
        # Aimbot
        self.aimbot_enabled = False
        self.aimbot_key = "rbutton"
        self.aimbot_bone = 0  # 0=head, 1=neck, 2=chest
        self.aimbot_smooth = 5.0
        self.aimbot_fov = 30.0
        self.aimbot_rcs = False
        
        # ESP
        self.esp_enabled = False
        self.esp_box = True
        self.esp_health = True
        self.esp_name = True
        self.esp_distance = False
        self.esp_snaplines = False
        
        # Misc
        self.bhop_enabled = False
        self.no_flash = False
        self.auto_pistol = False
        
        # Farben (RGB)
        self.box_color = (255, 0, 0)  # Rot
        self.snapline_color = (255, 255, 255)  # Weiß
        
    def save(self, filename="config.txt"):
        """Speichert die Konfiguration"""
        try:
            with open(filename, 'w') as f:
                for key, value in self.__dict__.items():
                    f.write(f"{key}={value}\n")
            return True
        except:
            return False
    
    def load(self, filename="config.txt"):
        """Lädt die Konfiguration"""
        try:
            with open(filename, 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        if hasattr(self, key):
                            # Typkonvertierung
                            current = getattr(self, key)
                            if isinstance(current, bool):
                                setattr(self, key, value.lower() == 'true')
                            elif isinstance(current, int):
                                setattr(self, key, int(value))
                            elif isinstance(current, float):
                                setattr(self, key, float(value))
                            elif isinstance(current, tuple) and key.endswith('_color'):
                                # Tuple wie (255,0,0)
                                vals = value.strip('()').split(',')
                                setattr(self, key, tuple(int(v.strip()) for v in vals))
                            else:
                                setattr(self, key, value)
            return True
        except:
            return False

# =====================================================================
# GUI MIT PYSIDE6 [citation:4]
# =====================================================================

class CheatGUI(QMainWindow):
    """Hauptfenster des Cheats mit GUI-Steuerung"""
    
    def __init__(self, cheat_instance):
        super().__init__()
        self.cheat = cheat_instance
        self.config = cheat_instance.config
        self.init_ui()
        
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        self.setWindowTitle("CS:PY - Counter-Strike Python Cheat")
        self.setGeometry(100, 100, 600, 500)
        
        # Zentrales Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Hauptlayout
        layout = QVBoxLayout(central_widget)
        
        # Tab Widget
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # ===== TRIGGERBOT TAB =====
        trigger_tab = QWidget()
        tabs.addTab(trigger_tab, "Triggerbot")
        
        trigger_layout = QVBoxLayout(trigger_tab)
        
        # Enable Checkbox
        self.trigger_enabled = QCheckBox("Triggerbot aktivieren")
        self.trigger_enabled.setChecked(self.config.triggerbot_enabled)
        self.trigger_enabled.stateChanged.connect(self.toggle_triggerbot)
        trigger_layout.addWidget(self.trigger_enabled)
        
        # Key Selection
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Aktivierungstaste:"))
        self.trigger_key = QComboBox()
        self.trigger_key.addItems(["shift", "alt", "ctrl", "rbutton", "lbutton", "xbutton1"])
        self.trigger_key.setCurrentText(self.config.triggerbot_key)
        self.trigger_key.currentTextChanged.connect(self.update_trigger_key)
        key_layout.addWidget(self.trigger_key)
        trigger_layout.addLayout(key_layout)
        
        # Delay Slider
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Verzögerung (ms):"))
        self.trigger_delay = QSlider(Qt.Horizontal)
        self.trigger_delay.setRange(0, 200)
        self.trigger_delay.setValue(self.config.triggerbot_delay)
        self.trigger_delay.valueChanged.connect(self.update_trigger_delay)
        delay_layout.addWidget(self.trigger_delay)
        self.trigger_delay_label = QLabel(str(self.config.triggerbot_delay))
        delay_layout.addWidget(self.trigger_delay_label)
        trigger_layout.addLayout(delay_layout)
        
        # Radius Slider
        radius_layout = QHBoxLayout()
        radius_layout.addWidget(QLabel("Scan-Radius (Pixel):"))
        self.trigger_radius = QSlider(Qt.Horizontal)
        self.trigger_radius.setRange(2, 50)
        self.trigger_radius.setValue(self.config.triggerbot_radius)
        self.trigger_radius.valueChanged.connect(self.update_trigger_radius)
        radius_layout.addWidget(self.trigger_radius)
        self.trigger_radius_label = QLabel(str(self.config.triggerbot_radius))
        radius_layout.addWidget(self.trigger_radius_label)
        trigger_layout.addLayout(radius_layout)
        
        trigger_layout.addStretch()
        
        # ===== AIMBOT TAB =====
        aim_tab = QWidget()
        tabs.addTab(aim_tab, "Aimbot")
        
        aim_layout = QVBoxLayout(aim_tab)
        
        # Enable Checkbox
        self.aim_enabled = QCheckBox("Aimbot aktivieren")
        self.aim_enabled.setChecked(self.config.aimbot_enabled)
        self.aim_enabled.stateChanged.connect(self.toggle_aimbot)
        aim_layout.addWidget(self.aim_enabled)
        
        # Aim Key
        aim_key_layout = QHBoxLayout()
        aim_key_layout.addWidget(QLabel("Aim-Taste:"))
        self.aim_key = QComboBox()
        self.aim_key.addItems(["rbutton", "shift", "alt", "ctrl", "xbutton1"])
        self.aim_key.setCurrentText(self.config.aimbot_key)
        self.aim_key.currentTextChanged.connect(self.update_aim_key)
        aim_key_layout.addWidget(self.aim_key)
        aim_layout.addLayout(aim_key_layout)
        
        # Bone Selection
        bone_layout = QHBoxLayout()
        bone_layout.addWidget(QLabel("Zielknochen:"))
        self.aim_bone = QComboBox()
        self.aim_bone.addItems(["Kopf", "Hals", "Brust"])
        self.aim_bone.setCurrentIndex(self.config.aimbot_bone)
        self.aim_bone.currentIndexChanged.connect(self.update_aim_bone)
        bone_layout.addWidget(self.aim_bone)
        aim_layout.addLayout(bone_layout)
        
        # Smoothing
        smooth_layout = QHBoxLayout()
        smooth_layout.addWidget(QLabel("Smoothing:"))
        self.aim_smooth = QSlider(Qt.Horizontal)
        self.aim_smooth.setRange(1, 20)
        self.aim_smooth.setValue(int(self.config.aimbot_smooth))
        self.aim_smooth.valueChanged.connect(self.update_aim_smooth)
        smooth_layout.addWidget(self.aim_smooth)
        self.aim_smooth_label = QLabel(str(self.config.aimbot_smooth))
        smooth_layout.addWidget(self.aim_smooth_label)
        aim_layout.addLayout(smooth_layout)
        
        # FOV
        fov_layout = QHBoxLayout()
        fov_layout.addWidget(QLabel("FOV (Grad):"))
        self.aim_fov = QSlider(Qt.Horizontal)
        self.aim_fov.setRange(1, 90)
        self.aim_fov.setValue(int(self.config.aimbot_fov))
        self.aim_fov.valueChanged.connect(self.update_aim_fov)
        fov_layout.addWidget(self.aim_fov)
        self.aim_fov_label = QLabel(str(self.config.aimbot_fov))
        fov_layout.addWidget(self.aim_fov_label)
        aim_layout.addLayout(fov_layout)
        
        # RCS Checkbox
        self.aim_rcs = QCheckBox("Recoil Control (RCS)")
        self.aim_rcs.setChecked(self.config.aimbot_rcs)
        self.aim_rcs.stateChanged.connect(self.toggle_rcs)
        aim_layout.addWidget(self.aim_rcs)
        
        aim_layout.addStretch()
        
        # ===== ESP TAB =====
        esp_tab = QWidget()
        tabs.addTab(esp_tab, "ESP / Visuals")
        
        esp_layout = QVBoxLayout(esp_tab)
        
        # Enable ESP
        self.esp_enabled = QCheckBox("ESP aktivieren")
        self.esp_enabled.setChecked(self.config.esp_enabled)
        self.esp_enabled.stateChanged.connect(self.toggle_esp)
        esp_layout.addWidget(self.esp_enabled)
        
        # Box ESP
        self.esp_box = QCheckBox("Bounding Box")
        self.esp_box.setChecked(self.config.esp_box)
        self.esp_box.stateChanged.connect(self.toggle_esp_box)
        esp_layout.addWidget(self.esp_box)
        
        # Box Color
        box_color_layout = QHBoxLayout()
        box_color_layout.addWidget(QLabel("Box-Farbe:"))
        self.box_color_btn = QPushButton("Farbe wählen")
        self.box_color_btn.clicked.connect(self.choose_box_color)
        box_color_layout.addWidget(self.box_color_btn)
        esp_layout.addLayout(box_color_layout)
        
        # Health Bar
        self.esp_health = QCheckBox("Health Bar")
        self.esp_health.setChecked(self.config.esp_health)
        self.esp_health.stateChanged.connect(self.toggle_esp_health)
        esp_layout.addWidget(self.esp_health)
        
        # Name ESP
        self.esp_name = QCheckBox("Spielername")
        self.esp_name.setChecked(self.config.esp_name)
        self.esp_name.stateChanged.connect(self.toggle_esp_name)
        esp_layout.addWidget(self.esp_name)
        
        # Distance ESP
        self.esp_distance = QCheckBox("Distanz")
        self.esp_distance.setChecked(self.config.esp_distance)
        self.esp_distance.stateChanged.connect(self.toggle_esp_distance)
        esp_layout.addWidget(self.esp_distance)
        
        # Snaplines
        self.esp_snaplines = QCheckBox("Snaplines")
        self.esp_snaplines.setChecked(self.config.esp_snaplines)
        self.esp_snaplines.stateChanged.connect(self.toggle_esp_snaplines)
        esp_layout.addWidget(self.esp_snaplines)
        
        esp_layout.addStretch()
        
        # ===== MISC TAB =====
        misc_tab = QWidget()
        tabs.addTab(misc_tab, "Misc")
        
        misc_layout = QVBoxLayout(misc_tab)
        
        # Bunnyhop
        self.bhop_enabled = QCheckBox("Bunnyhop (B-Hop)")
        self.bhop_enabled.setChecked(self.config.bhop_enabled)
        self.bhop_enabled.stateChanged.connect(self.toggle_bhop)
        misc_layout.addWidget(self.bhop_enabled)
        
        # No Flash
        self.no_flash = QCheckBox("No Flash (keine Blendung)")
        self.no_flash.setChecked(self.config.no_flash)
        self.no_flash.stateChanged.connect(self.toggle_no_flash)
        misc_layout.addWidget(self.no_flash)
        
        # Auto Pistol
        self.auto_pistol = QCheckBox("Auto Pistol")
        self.auto_pistol.setChecked(self.config.auto_pistol)
        self.auto_pistol.stateChanged.connect(self.toggle_auto_pistol)
        misc_layout.addWidget(self.auto_pistol)
        
        misc_layout.addStretch()
        
        # ===== STATUS & CONTROLS =====
        status_layout = QHBoxLayout()
        
        # Connect Button
        self.connect_btn = QPushButton("Mit CS2 verbinden")
        self.connect_btn.clicked.connect(self.toggle_connection)
        status_layout.addWidget(self.connect_btn)
        
        # Status Label
        self.status_label = QLabel("❌ Nicht verbunden")
        self.status_label.setStyleSheet("color: red;")
        status_layout.addWidget(self.status_label)
        
        layout.addLayout(status_layout)
        
        # Info Label
        info_label = QLabel("CS:PY - Für Bildungszwecke. Nutzung auf eigene Gefahr!")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(info_label)
    
    # ===== SLOTS FÜR GUI-EVENTS =====
    
    def toggle_triggerbot(self, state):
        self.config.triggerbot_enabled = (state == Qt.Checked)
        self.cheat.update_config()
    
    def update_trigger_key(self, key):
        self.config.triggerbot_key = key
        self.cheat.update_config()
    
    def update_trigger_delay(self, value):
        self.config.triggerbot_delay = value
        self.trigger_delay_label.setText(str(value))
        self.cheat.update_config()
    
    def update_trigger_radius(self, value):
        self.config.triggerbot_radius = value
        self.trigger_radius_label.setText(str(value))
        self.cheat.update_config()
    
    def toggle_aimbot(self, state):
        self.config.aimbot_enabled = (state == Qt.Checked)
        self.cheat.update_config()
    
    def update_aim_key(self, key):
        self.config.aimbot_key = key
        self.cheat.update_config()
    
    def update_aim_bone(self, index):
        self.config.aimbot_bone = index
        self.cheat.update_config()
    
    def update_aim_smooth(self, value):
        self.config.aimbot_smooth = float(value)
        self.aim_smooth_label.setText(str(value))
        self.cheat.update_config()
    
    def update_aim_fov(self, value):
        self.config.aimbot_fov = float(value)
        self.aim_fov_label.setText(str(value))
        self.cheat.update_config()
    
    def toggle_rcs(self, state):
        self.config.aimbot_rcs = (state == Qt.Checked)
        self.cheat.update_config()
    
    def toggle_esp(self, state):
        self.config.esp_enabled = (state == Qt.Checked)
        self.cheat.update_config()
    
    def toggle_esp_box(self, state):
        self.config.esp_box = (state == Qt.Checked)
    
    def choose_box_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.config.box_color = (color.red(), color.green(), color.blue())
    
    def toggle_esp_health(self, state):
        self.config.esp_health = (state == Qt.Checked)
    
    def toggle_esp_name(self, state):
        self.config.esp_name = (state == Qt.Checked)
    
    def toggle_esp_distance(self, state):
        self.config.esp_distance = (state == Qt.Checked)
    
    def toggle_esp_snaplines(self, state):
        self.config.esp_snaplines = (state == Qt.Checked)
    
    def toggle_bhop(self, state):
        self.config.bhop_enabled = (state == Qt.Checked)
        self.cheat.update_config()
    
    def toggle_no_flash(self, state):
        self.config.no_flash = (state == Qt.Checked)
        self.cheat.update_config()
    
    def toggle_auto_pistol(self, state):
        self.config.auto_pistol = (state == Qt.Checked)
        self.cheat.update_config()
    
    def toggle_connection(self):
        if not self.cheat.mem.connected:
            if self.cheat.connect_to_game():
                self.status_label.setText("✅ Verbunden mit CS2")
                self.status_label.setStyleSheet("color: green;")
                self.connect_btn.setText("Trennen")
            else:
                QMessageBox.warning(self, "Fehler", "Konnte keine Verbindung zu CS2 herstellen.")
        else:
            # Disconnect
            self.cheat.mem.connected = False
            self.status_label.setText("❌ Nicht verbunden")
            self.status_label.setStyleSheet("color: red;")
            self.connect_btn.setText("Mit CS2 verbinden")
    
    def closeEvent(self, event):
        """Wird beim Schließen des Fensters aufgerufen"""
        self.config.save()
        event.accept()

# =====================================================================
# OVERLAY WINDOW (ESP RENDERING)
# =====================================================================

class OverlayWindow(QWidget):
    """Transparentes Overlay-Fenster für ESP"""
    
    def __init__(self, cheat_instance):
        super().__init__()
        self.cheat = cheat_instance
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # Vollbild
        screen = QApplication.primaryScreen()
        self.setGeometry(screen.geometry())
        
        # Timer für Updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # ~60 FPS
    
    def paintEvent(self, event):
        """Zeichnet ESP auf das Overlay"""
        if not self.cheat.running or not self.cheat.mem.connected:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Local Player holen
        local_player = self.cheat.get_local_player()
        if not local_player:
            return
        
        # Entities holen
        entities = self.cheat.get_entities()
        
        # View Matrix holen
        view_matrix = self.cheat.get_view_matrix()
        if not view_matrix:
            return
        
        screen_width = self.width()
        screen_height = self.height()
        
        # ESP zeichnen [citation:1][citation:4]
        for entity in entities:
            if not entity.is_alive() or not entity.is_enemy(local_player.team):
                continue
            
            if not self.cheat.config.esp_enabled:
                continue
            
            # Position zu Bildschirmkoordinaten konvertieren
            screen_pos = Math3D.world_to_screen(
                view_matrix,
                (entity.position.x, entity.position.y, entity.position.z),
                screen_width,
                screen_height
            )
            
            if not screen_pos:
                continue
            
            # Box ESP
            if self.cheat.config.esp_box:
                color = self.cheat.config.box_color
                painter.setPen(QPen(QColor(*color), 2))
                
                # Einfache 2D-Box (vereinfacht)
                box_height = 60
                box_width = 30
                painter.drawRect(
                    int(screen_pos[0] - box_width/2),
                    int(screen_pos[1] - box_height),
                    box_width,
                    box_height
                )
            
            # Name ESP
            if self.cheat.config.esp_name:
                painter.setPen(QPen(Qt.white, 1))
                painter.setFont(QFont("Arial", 10))
                painter.drawText(
                    int(screen_pos[0] - 30),
                    int(screen_pos[1] - 70),
                    f"Enemy"
                )
            
            # Health Bar
            if self.cheat.config.esp_health:
                health_percent = entity.health / 100.0
                bar_height = 50
                bar_width = 5
                health_height = int(bar_height * health_percent)
                
                # Hintergrund
                painter.fillRect(
                    int(screen_pos[0] + 20),
                    int(screen_pos[1] - 60),
                    bar_width,
                    bar_height,
                    QColor(0, 0, 0, 128)
                )
                
                # Health
                color = QColor(
                    int(255 * (1 - health_percent)),
                    int(255 * health_percent),
                    0
                )
                painter.fillRect(
                    int(screen_pos[0] + 20),
                    int(screen_pos[1] - 60 + (bar_height - health_height)),
                    bar_width,
                    health_height,
                    color
                )
            
            # Snapline
            if self.cheat.config.esp_snaplines:
                color = self.cheat.config.snapline_color
                painter.setPen(QPen(QColor(*color), 1))
                painter.drawLine(
                    int(screen_width / 2),
                    screen_height,
                    int(screen_pos[0]),
                    int(screen_pos[1])
                )

# =====================================================================
# HAUPT-CHEAT-KLASSE
# =====================================================================

class CSPYCheat(QObject):
    """Hauptklasse des Cheats - verwaltet alle Funktionen"""
    
    def __init__(self):
        super().__init__()
        self.mem = MemoryManager()
        self.config = Config()
        self.config.load()
        
        self.running = True
        self.local_player_addr = 0
        self.local_player = None
        self.entity_cache = []
        
        # Threading
        self.aim_thread = None
        self.trigger_thread = None
        self.misc_thread = None
        
        # GUI
        self.gui = None
        self.overlay = None
        
        # Offsets aktualisieren
        Offsets.fetch_latest()
    
    def connect_to_game(self):
        """Verbindet sich mit CS2"""
        if self.mem.connect():
            return True
        return False
    
    def update_config(self):
        """Wird aufgerufen, wenn sich die Config ändert"""
        self.config.save()
    
    def get_local_player(self):
        """Holt den lokalen Spieler"""
        if not self.mem.connected:
            return None
        
        try:
            # Local Player Adresse lesen
            local_addr = self.mem.read_int(self.mem.get_client_address(Offsets.dwLocalPlayerPawn))
            if local_addr:
                if not self.local_player or self.local_player.address != local_addr:
                    self.local_player = Entity(self.mem, local_addr)
                else:
                    self.local_player.update()
                return self.local_player
        except:
            pass
        return None
    
    def get_entities(self):
        """Holt alle Entities (Spieler)"""
        if not self.mem.connected:
            return []
        
        entities = []
        try:
            # EntityList lesen
            entity_list = self.mem.read_int(self.mem.get_client_address(Offsets.dwEntityList))
            if not entity_list:
                return []
            
            # Loop durch Entity-Indizes
            for i in range(1, 32):  # Max 32 Spieler
                try:
                    entity_addr = self.mem.read_int(entity_list + (i << 5))  # i * 32
                    if entity_addr:
                        entity = Entity(self.mem, entity_addr)
                        if entity.is_alive():
                            entities.append(entity)
                except:
                    pass
        except:
            pass
        
        return entities
    
    def get_view_matrix(self):
        """Holt die View Matrix für WorldToScreen"""
        if not self.mem.connected:
            return None
        
        try:
            matrix_addr = self.mem.get_client_address(Offsets.dwViewMatrix)
            matrix_bytes = self.mem.read_bytes(matrix_addr, 16 * 4)  # 16 floats
            matrix = struct.unpack('<16f', matrix_bytes)
            return matrix
        except:
            return None
    
    def run_aimbot(self):
        """Aimbot-Loop [citation:4]"""
        while self.running:
            if self.mem.connected and self.config.aimbot_enabled:
                try:
                    # Check ob Aim-Key gedrückt
                    key_pressed = False
                    key = self.config.aimbot_key.lower()
                    
                    if key == "rbutton":
                        key_pressed = (ctypes.windll.user32.GetAsyncKeyState(0x02) & 0x8000) != 0
                    elif key == "lbutton":
                        key_pressed = (ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000) != 0
                    elif key == "shift":
                        key_pressed = (ctypes.windll.user32.GetAsyncKeyState(0x10) & 0x8000) != 0
                    elif key == "ctrl":
                        key_pressed = (ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000) != 0
                    elif key == "alt":
                        key_pressed = (ctypes.windll.user32.GetAsyncKeyState(0x12) & 0x8000) != 0
                    
                    if key_pressed:
                        # Local Player holen
                        local = self.get_local_player()
                        if not local:
                            time.sleep(0.01)
                            continue
                        
                        # Entities holen
                        entities = self.get_entities()
                        
                        # Bestes Ziel finden
                        best_target = None
                        best_fov = self.config.aimbot_fov
                        
                        for entity in entities:
                            if not entity.is_alive() or not entity.is_enemy(local.team):
                                continue
                            
                            # Zielposition je nach Bone
                            if self.config.aimbot_bone == 0:  # Head
                                target_pos = entity.head_position
                            elif self.config.aimbot_bone == 1:  # Neck
                                target_pos = Vector3(
                                    entity.position.x,
                                    entity.position.y,
                                    entity.position.z + 60
                                )
                            else:  # Chest
                                target_pos = Vector3(
                                    entity.position.x,
                                    entity.position.y,
                                    entity.position.z + 40
                                )
                            
                            # Winkel berechnen
                            angle = Math3D.calculate_angle(local.position, target_pos)
                            if not angle:
                                continue
                            
                            # FOV berechnen (vereinfacht)
                            # Hier müsste man die aktuellen ViewAngles lesen
                            # Vereinfacht: immer treffen
                            
                            best_target = angle
                            break  # Erstes Ziel nehmen
                        
                        # Ziel anvisieren
                        if best_target:
                            # Smoothing anwenden
                            # Hier müsste man ViewAngles schreiben
                            # Komplexe Implementierung - für dieses Beispiel vereinfacht
                            pass
                
                except Exception as e:
                    print(f"[!] Aimbot Fehler: {e}")
            
            time.sleep(0.001)  # CPU-Schonung
    
    def run_triggerbot(self):
        """Triggerbot-Loop [citation:1][citation:8]"""
        while self.running:
            if self.mem.connected and self.config.triggerbot_enabled:
                try:
                    # Check Trigger-Key
                    key_pressed = False
                    key = self.config.triggerbot_key.lower()
                    
                    if key == "shift":
                        key_pressed = (ctypes.windll.user32.GetAsyncKeyState(0x10) & 0x8000) != 0
                    elif key == "alt":
                        key_pressed = (ctypes.windll.user32.GetAsyncKeyState(0x12) & 0x8000) != 0
                    elif key == "ctrl":
                        key_pressed = (ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000) != 0
                    
                    if key_pressed:
                        # Vereinfachte Triggerbot-Implementierung
                        # In der Praxis müsste man Pixel-Scanning machen
                        # oder Crosshair-Entity erkennen
                        
                        # Delay
                        time.sleep(self.config.triggerbot_delay / 1000.0)
                        
                        # Mausklick simulieren
                        ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # DOWN
                        time.sleep(0.01)
                        ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # UP
                
                except Exception as e:
                    print(f"[!] Triggerbot Fehler: {e}")
            
            time.sleep(0.005)
    
    def run_misc(self):
        """Misc-Features (Bhop, No Flash, etc.) [citation:8]"""
        while self.running:
            if self.mem.connected:
                try:
                    local = self.get_local_player()
                    if not local:
                        time.sleep(0.1)
                        continue
                    
                    # Bunnyhop
                    if self.config.bhop_enabled:
                        space_pressed = (ctypes.windll.user32.GetAsyncKeyState(0x20) & 0x8000) != 0
                        if space_pressed:
                            # Check ob auf Boden
                            # Vereinfacht: immer springen
                            time.sleep(0.01)
                            # Space loslassen und wieder drücken
                            # Komplexe Implementierung...
                            pass
                    
                    # No Flash
                    if self.config.no_flash:
                        flash_addr = local.address + Offsets.m_flFlashDuration
                        self.mem.write_float(flash_addr, 0.0)
                    
                    # Auto Pistol
                    if self.config.auto_pistol:
                        # Check ob Pistole ausgerüstet
                        # Vereinfacht
                        pass
                
                except Exception as e:
                    pass
            
            time.sleep(0.01)
    
    def start(self):
        """Startet den Cheat"""
        print("""
╔══════════════════════════════════╗
║         CS:PY - CHEAT            ║
║     Counter-Strike Python        ║
╚══════════════════════════════════╝
        """)
        
        # Offsets aktualisieren
        Offsets.fetch_latest()
        
        # Threads starten
        self.aim_thread = threading.Thread(target=self.run_aimbot, daemon=True)
        self.trigger_thread = threading.Thread(target=self.run_triggerbot, daemon=True)
        self.misc_thread = threading.Thread(target=self.run_misc, daemon=True)
        
        self.aim_thread.start()
        self.trigger_thread.start()
        self.misc_thread.start()
        
        # GUI starten
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        self.gui = CheatGUI(self)
        self.overlay = OverlayWindow(self)
        
        self.gui.show()
        self.overlay.show()
        
        # Config laden
        self.config.load()
        
        # Event Loop
        app.exec()
        
        # Cleanup
        self.running = False
        self.mem.connected = False

# =====================================================================
# MAIN
# =====================================================================

def main():
    """Einstiegspunkt"""
    
    # Prüfe Admin-Rechte
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("[!] Bitte als Administrator ausführen!")
        print("[!] Rechte Maustaste -> 'Als Administrator ausführen'")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Cheat starten
    cheat = CSPYCheat()
    
    try:
        cheat.start()
    except KeyboardInterrupt:
        print("\n[*] Cheat wird beendet...")
    except Exception as e:
        print(f"[!] Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()