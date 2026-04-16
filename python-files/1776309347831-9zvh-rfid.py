"""
BoxRFID Manager for QIDI Box
RFID tag writer/reader for 3D printer filament spools

Credits:
- Original RFID communication logic based on MIFARE Classic implementation
- CustomTKinter library for modern GUI
- QIDI 3D for filament specifications

License: MIT
"""

import customtkinter as ctk
from tkinter import messagebox
from smartcard.System import readers
import threading
import time
import os
import sys
import configparser
from pathlib import Path
from datetime import datetime

# ================================
# VERSION & METADATA
# ================================
APP_NAME = "BoxRFID Manager"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Open Source Community"

# ================================
# CONFIGURATION MANAGER
# ================================
class ConfigManager:
    """Handles configuration file operations"""
    
    def __init__(self):
        self.config_path = self._get_config_path()
        self.manufacturers = {}
        self.materials = {}
        self._load_or_create_config()
    
    def _get_config_path(self):
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, 'config.ini')
    
    def _get_default_manufacturers(self):
        return {
            0: {"de": "Generic", "en": "Generic", "ru": "Generic"},
            1: {"de": "QIDI", "en": "QIDI", "ru": "QIDI"},
            2: {"de": "eSun", "en": "eSun", "ru": "eSun"},
            3: {"de": "Bestfilament", "en": "Bestfilament", "ru": "Bestfilament"},
            4: {"de": "Creality", "en": "Creality", "ru": "Creality"},
            5: {"de": "Plastikoff", "en": "Plastikoff", "ru": "Plastikoff"},
            6: {"de": "KingRoon", "en": "KingRoon", "ru": "KingRoon"},
            7: {"de": "BambuLab", "en": "BambuLab", "ru": "BambuLab"},
            8: {"de": "REC", "en": "REC", "ru": "REC"},
            9: {"de": "Filamentarno!", "en": "Filamentarno!", "ru": "Filamentarno!"},
            10: {"de": "NIT", "en": "NIT", "ru": "NIT"},
            11: {"de": "Alfa filament", "en": "Alfa filament", "ru": "Alfa filament"},
            12: {"de": "Creality", "en": "Creality", "ru": "Creality"},
            13: {"de": "Polymaker", "en": "Polymaker", "ru": "Polymaker"},
            14: {"de": "Elegoo", "en": "Elegoo", "ru": "Elegoo"},
            15: {"de": "Anycubic", "en": "Anycubic", "ru": "Anycubic"},
            16: {"de": "Sunlu", "en": "Sunlu", "ru": "Sunlu"},
            17: {"de": "Unknown", "en": "Unknown", "ru": "Неизвестно"},
            18: {"de": "Unknown", "en": "Unknown", "ru": "Неизвестно"},
            19: {"de": "Unknown", "en": "Unknown", "ru": "Неизвестно"},
            20: {"de": "Unknown", "en": "Unknown", "ru": "Неизвестно"}
        }
    
    def _get_default_materials(self):
        return {
            "PLA": 1, "PLA Matte": 2, "PLA Metal": 3, "PLA Silk": 4,
            "PLA-CF": 5, "PLA-Wood": 6, "PLA Basic": 7, "PLA Matte Basic": 8,
            "ABS": 11, "ABS-GF": 12, "ABS-Metal": 13, "ABS-Odorless": 14,
            "ASA": 18, "ASA-AERO": 19, "UltraPA": 24, "PA12-CF": 25,
            "UltraPA-CF25": 26, "PAHT-CF": 30, "PAHT-GF": 31,
            "Support For PAHT": 32, "Support For PET/PA": 33, "PC/ABS-FR": 34,
            "PET-CF": 37, "PET-GF": 38, "PETG Basic": 39, "PETG-Though": 40,
            "PETG": 41, "PPS-CF": 44, "PETG Translucent": 45, "PVA": 47,
            "TPU-AERO": 49, "TPU": 50
        }
    
    def _load_or_create_config(self):
        config = configparser.ConfigParser()
        
        if not os.path.exists(self.config_path):
            self._create_default_config(config)
        else:
            self._load_existing_config(config)
    
    def _create_default_config(self, config):
        config['Manufacturers'] = {}
        for key, value in self._get_default_manufacturers().items():
            config['Manufacturers'][str(key)] = f"{value['de']}|{value['en']}|{value['ru']}"
        
        config['Materials'] = {}
        for name, code in self._get_default_materials().items():
            config['Materials'][str(code)] = name
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            config.write(f)
        
        self.manufacturers = self._get_default_manufacturers()
        self.materials = self._get_default_materials()
    
    def _load_existing_config(self, config):
        try:
            config.read(self.config_path, encoding='utf-8')
            
            # Load manufacturers
            self.manufacturers = {}
            if 'Manufacturers' in config:
                for key, value in config['Manufacturers'].items():
                    parts = value.split('|')
                    if len(parts) == 3:
                        self.manufacturers[int(key)] = {
                            "de": parts[0], "en": parts[1], "ru": parts[2]
                        }
            
            # Fill missing manufacturers
            defaults = self._get_default_manufacturers()
            for i in range(21):
                if i not in self.manufacturers:
                    self.manufacturers[i] = defaults[i]
            
            # Load materials
            self.materials = {}
            if 'Materials' in config:
                for code, name in config['Materials'].items():
                    self.materials[name] = int(code)
            
            if not self.materials:
                self.materials = self._get_default_materials()
                
        except Exception as e:
            print(f"Config error: {e}")
            self.manufacturers = self._get_default_manufacturers()
            self.materials = self._get_default_materials()

# ================================
# COLOR PALETTE
# ================================
class ColorPalette:
    """Beautiful color definitions for UI and RFID"""
    
    # RFID color codes
    RFID_COLORS = {
        "#FAFAFA": {"de": "Weiß", "en": "White", "ru": "Белый", "code": 1},
        "#060606": {"de": "Schwarz", "en": "Black", "ru": "Черный", "code": 2},
        "#D9E3ED": {"de": "Grau", "en": "Gray", "ru": "Серый", "code": 3},
        "#5CF30F": {"de": "Hellgrün", "en": "Light Green", "ru": "Светло-зеленый", "code": 4},
        "#63E492": {"de": "Mint", "en": "Mint", "ru": "Мятный", "code": 5},
        "#2850FF": {"de": "Blau", "en": "Blue", "ru": "Синий", "code": 6},
        "#FE98FE": {"de": "Pink", "en": "Pink", "ru": "Розовый", "code": 7},
        "#DFD628": {"de": "Gelb", "en": "Yellow", "ru": "Желтый", "code": 8},
        "#228332": {"de": "Grün", "en": "Green", "ru": "Зеленый", "code": 9},
        "#99DEFF": {"de": "Hellblau", "en": "Light Blue", "ru": "Голубой", "code": 10},
        "#1714B0": {"de": "Dunkelblau", "en": "Dark Blue", "ru": "Темно-синий", "code": 11},
        "#CEC0FE": {"de": "Lavendel", "en": "Lavender", "ru": "Лавандовый", "code": 12},
        "#CADE4B": {"de": "Lime", "en": "Lime", "ru": "Лаймовый", "code": 13},
        "#1353AB": {"de": "Royalblau", "en": "Royal Blue", "ru": "Королевский синий", "code": 14},
        "#5EA9FD": {"de": "Himmelblau", "en": "Sky Blue", "ru": "Небесно-голубой", "code": 15},
        "#A878FF": {"de": "Violett", "en": "Violet", "ru": "Фиолетовый", "code": 16},
        "#FE717A": {"de": "Rosa", "en": "Rose", "ru": "Розовый", "code": 17},
        "#FF362D": {"de": "Rot", "en": "Red", "ru": "Красный", "code": 18},
        "#E2DFCD": {"de": "Beige", "en": "Beige", "ru": "Бежевый", "code": 19},
        "#898F9B": {"de": "Silber", "en": "Silver", "ru": "Серебряный", "code": 20},
        "#6E3812": {"de": "Braun", "en": "Brown", "ru": "Коричневый", "code": 21},
        "#CAC59F": {"de": "Khaki", "en": "Khaki", "ru": "Хаки", "code": 22},
        "#F28636": {"de": "Orange", "en": "Orange", "ru": "Оранжевый", "code": 23},
        "#B87F2B": {"de": "Bronze", "en": "Bronze", "ru": "Бронзовый", "code": 24},
    }
    
    @classmethod
    def get_color_name(cls, code, lang):
        for hex_code, info in cls.RFID_COLORS.items():
            if info["code"] == code:
                return hex_code, info[lang]
        return "#FFFFFF", "Unknown"
    
    @classmethod
    def get_color_code(cls, hex_code):
        return cls.RFID_COLORS.get(hex_code, {}).get("code", 0)

# ================================
# LANGUAGE MANAGER
# ================================
class LanguageManager:
    """Manages multilingual UI text"""
    
    TRANSLATIONS = {
        "ru": {
            "title": "BoxRFID Менеджер",
            "subtitle": "Управление RFID метками для QIDI Box",
            "manufacturer": "Производитель",
            "material": "Материал",
            "color": "Цвет",
            "write": "📝 ЗАПИСАТЬ МЕТКУ",
            "read": "🔍 СЧИТАТЬ МЕТКУ",
            "auto": "🤖 АВТО-ОБНАРУЖЕНИЕ",
            "auto_on": "🔴 АВТО-ОБНАРУЖЕНИЕ АКТИВНО",
            "auto_off": "⭕ АВТО-ОБНАРУЖЕНИЕ",
            "info": "📋 ИНФОРМАЦИЯ О МЕТКЕ",
            "empty": "❌ ПУСТАЯ МЕТКА",
            "ready": "✅ RFID РИДЕР ГОТОВ",
            "not_ready": "⚠️ RFID РИДЕР НЕ НАЙДЕН",
            "tag_placed": "🏷️ Метка обнаружена",
            "tag_removed": "🗑️ Метка удалена",
            "error": "Ошибка",
            "success": "Успех",
            "write_success": "Метка успешно записана!",
            "no_reader": "RFID ридер не подключен",
            "no_manufacturer": "Выберите производителя",
            "no_material": "Выберите материал",
            "no_color": "Выберите цвет",
            "auth_failed": "Ошибка аутентификации",
            "write_failed": "Ошибка записи",
            "read_failed": "Ошибка чтения"
        },
        "en": {
            "title": "BoxRFID Manager",
            "subtitle": "RFID Tag Manager for QIDI Box",
            "manufacturer": "Manufacturer",
            "material": "Material",
            "color": "Color",
            "write": "📝 WRITE TAG",
            "read": "🔍 READ TAG",
            "auto": "🤖 AUTO DETECTION",
            "auto_on": "🔴 AUTO DETECTION ACTIVE",
            "auto_off": "⭕ AUTO DETECTION",
            "info": "📋 TAG INFORMATION",
            "empty": "❌ EMPTY TAG",
            "ready": "✅ RFID READER READY",
            "not_ready": "⚠️ RFID READER NOT FOUND",
            "tag_placed": "🏷️ Tag detected",
            "tag_removed": "🗑️ Tag removed",
            "error": "Error",
            "success": "Success",
            "write_success": "Tag written successfully!",
            "no_reader": "RFID reader not connected",
            "no_manufacturer": "Select manufacturer",
            "no_material": "Select material",
            "no_color": "Select color",
            "auth_failed": "Authentication failed",
            "write_failed": "Write failed",
            "read_failed": "Read failed"
        },
        "de": {
            "title": "BoxRFID Manager",
            "subtitle": "RFID Tag Manager für QIDI Box",
            "manufacturer": "Hersteller",
            "material": "Material",
            "color": "Farbe",
            "write": "📝 TAG SCHREIBEN",
            "read": "🔍 TAG LESEN",
            "auto": "🤖 AUTO-ERKENNUNG",
            "auto_on": "🔴 AUTO-ERKENNUNG AKTIV",
            "auto_off": "⭕ AUTO-ERKENNUNG",
            "info": "📋 TAG INFORMATIONEN",
            "empty": "❌ LEERER TAG",
            "ready": "✅ RFID LESER BEREIT",
            "not_ready": "⚠️ RFID LESER NICHT GEFUNDEN",
            "tag_placed": "🏷️ Tag erkannt",
            "tag_removed": "🗑️ Tag entfernt",
            "error": "Fehler",
            "success": "Erfolg",
            "write_success": "Tag erfolgreich geschrieben!",
            "no_reader": "RFID Leser nicht verbunden",
            "no_manufacturer": "Wählen Sie Hersteller",
            "no_material": "Wählen Sie Material",
            "no_color": "Wählen Sie Farbe",
            "auth_failed": "Authentifizierung fehlgeschlagen",
            "write_failed": "Schreiben fehlgeschlagen",
            "read_failed": "Lesen fehlgeschlagen"
        }
    }
    
    def __init__(self, default_lang="ru"):
        self.current_lang = default_lang
    
    def get(self, key):
        return self.TRANSLATIONS[self.current_lang].get(key, key)
    
    def switch(self):
        langs = ["ru", "en", "de"]
        current_index = langs.index(self.current_lang)
        self.current_lang = langs[(current_index + 1) % len(langs)]
        return self.current_lang

# ================================
# RFID CONTROLLER
# ================================
class RFIDController:
    """Handles all RFID operations"""
    
    DATA_BLOCK = 4
    KEYS = [
        [0xD3, 0xF7, 0xD3, 0xF7, 0xD3, 0xF7],
        [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    ]
    
    def __init__(self, status_callback=None):
        self.status_callback = status_callback
        self.reader_available = False
        self._check_reader()
    
    def _check_reader(self):
        try:
            r = readers()
            self.reader_available = bool(r and len(r) > 0)
        except:
            self.reader_available = False
        return self.reader_available
    
    def _get_connection(self):
        if not self.reader_available:
            raise Exception("no_reader")
        r = readers()
        conn = r[0].createConnection()
        conn.connect()
        return conn
    
    def _load_key(self, conn, key):
        cmd = [0xFF, 0x82, 0x00, 0x00, 0x06] + key
        _, sw1, sw2 = conn.transmit(cmd)
        return sw1 == 0x90 and sw2 == 0x00
    
    def _authenticate(self, conn, block):
        cmd = [0xFF, 0x86, 0x00, 0x00, 0x05, 0x01, 0x00, block, 0x60, 0x00]
        _, sw1, sw2 = conn.transmit(cmd)
        return sw1 == 0x90 and sw2 == 0x00
    
    def _find_key(self, conn):
        for key in self.KEYS:
            if self._load_key(conn, key) and self._authenticate(conn, self.DATA_BLOCK):
                return key
        raise Exception("no_key")
    
    def write_tag(self, material_code, color_code, manufacturer_code):
        """Write data to RFID tag"""
        if not self.reader_available:
            raise Exception("no_reader")
        
        conn = None
        try:
            conn = self._get_connection()
            self._find_key(conn)
            
            data = [material_code, color_code, manufacturer_code, 1] + [0] * 12
            cmd = [0xFF, 0xD6, 0x00, self.DATA_BLOCK, 0x10] + data
            _, sw1, sw2 = conn.transmit(cmd)
            
            if sw1 != 0x90 or sw2 != 0x00:
                raise Exception("write_failed")
            
            return True
            
        finally:
            if conn:
                try:
                    conn.disconnect()
                except:
                    pass
    
    def read_tag(self):
        """Read data from RFID tag"""
        if not self.reader_available:
            raise Exception("no_reader")
        
        conn = None
        try:
            conn = self._get_connection()
            self._find_key(conn)
            
            cmd = [0xFF, 0xB0, 0x00, self.DATA_BLOCK, 0x10]
            data, sw1, sw2 = conn.transmit(cmd)
            
            if sw1 != 0x90 or sw2 != 0x00:
                raise Exception("read_failed")
            
            return {
                "material": data[0],
                "color": data[1],
                "manufacturer": data[2] if len(data) > 2 else 0
            }
            
        finally:
            if conn:
                try:
                    conn.disconnect()
                except:
                    pass
    
    def check_presence(self):
        """Quick check if tag is present"""
        if not self.reader_available:
            return False
        try:
            conn = self._get_connection()
            conn.disconnect()
            return True
        except:
            return False

# ================================
# MODERN GUI APPLICATION
# ================================
class ModernRFIDApp:
    """Main application class with modern UI"""
    
    def __init__(self):
        # Initialize components
        self.config = ConfigManager()
        self.lang = LanguageManager()
        self.rfid = RFIDController(status_callback=self.update_status)
        
        # Application state
        self.auto_detect_active = False
        self.auto_detect_thread = None
        
        # Setup GUI
        self.setup_window()
        self.create_widgets()
        self.start_periodic_check()
        
    def setup_window(self):
        """Configure main window"""
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("520x920")
        self.root.minsize(480, 800)
        
        # Set window icon if available
        try:
            self.root.iconbitmap(default="icon.ico")
        except:
            pass
    
    def create_widgets(self):
        """Create all UI elements"""
        # Main container with gradient-like background
        self.main_container = ctk.CTkFrame(self.root, fg_color="white")
        self.main_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Header section
        self.create_header()
        
        # Status section
        self.create_status_section()
        
        # Selection section
        self.create_selection_section()
        
        # Action buttons
        self.create_action_buttons()
        
        # Info section
        self.create_info_section()
        
        # Footer
        self.create_footer()
    
    def create_header(self):
        """Create stylish header"""
        header = ctk.CTkFrame(self.main_container, fg_color="white", height=70)
        header.pack(fill="x", padx=20, pady=(10, 5))
        
        # Title
        title = ctk.CTkLabel(
            header, 
            text=self.lang.get("title"),
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#1a1a2e"
        )
        title.pack(side="left", padx=10)
        
        # Language button with stylish design
        self.lang_btn = ctk.CTkButton(
            header,
            text="🌐",
            width=40,
            height=40,
            corner_radius=20,
            fg_color="#e0e0e0",
            hover_color="#d0d0d0",
            text_color="#1a1a2e",
            font=ctk.CTkFont(size=16),
            command=self.toggle_language
        )
        self.lang_btn.pack(side="right", padx=10)
        
        # Subtitle
        subtitle = ctk.CTkLabel(
            self.main_container,
            text=self.lang.get("subtitle"),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#666666"
        )
        subtitle.pack(pady=(0, 15))
    
    def create_status_section(self):
        """Create status indicator section"""
        self.status_frame = ctk.CTkFrame(self.main_container, fg_color="#f8f9fa", corner_radius=10)
        self.status_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # Reader status
        self.status_icon = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=ctk.CTkFont(size=14)
        )
        self.status_icon.pack(side="left", padx=15, pady=10)
        
        self.status_text = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        )
        self.status_text.pack(side="left", pady=10)
        
        # Config indicator
        config_indicator = ctk.CTkLabel(
            self.status_frame,
            text="⚙️ config.ini",
            font=ctk.CTkFont(size=10),
            text_color="#888888"
        )
        config_indicator.pack(side="right", padx=15, pady=10)
        
        self.update_reader_status()
    
    def create_selection_section(self):
        """Create selection controls"""
        # Manufacturer selection
        self.create_combo_box(
            self.lang.get("manufacturer"),
            self.get_manufacturer_list(),
            self.on_manufacturer_change
        )
        
        # Material selection
        self.create_combo_box(
            self.lang.get("material"),
            list(self.config.materials.keys()),
            self.on_material_change
        )
        
        # Color selection
        color_label = ctk.CTkLabel(
            self.main_container,
            text=self.lang.get("color"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#1a1a2e"
        )
        color_label.pack(pady=(15, 5))
        
        # Color preview
        self.color_preview = ctk.CTkLabel(
            self.main_container,
            text=self.lang.get("no_color"),
            width=200,
            height=45,
            corner_radius=10,
            fg_color="#e0e0e0",
            text_color="#1a1a2e",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        self.color_preview.pack(pady=(5, 10))
        
        # Color grid
        self.create_color_grid()
    
    def create_combo_box(self, label_text, values, command):
        """Create styled combobox with label"""
        label = ctk.CTkLabel(
            self.main_container,
            text=label_text,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#1a1a2e"
        )
        label.pack(pady=(15, 5))
        
        combo = ctk.CTkOptionMenu(
            self.main_container,
            values=values,
            fg_color="#f0f0f0",
            button_color="#e0e0e0",
            button_hover_color="#d0d0d0",
            text_color="#1a1a2e",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12),
            width=250,
            height=40,
            corner_radius=10,
            command=command
        )
        combo.pack(pady=(5, 0))
        
        if "manufacturer" in label_text.lower():
            self.manufacturer_combo = combo
        else:
            self.material_combo = combo
        
        return combo
    
    def create_color_grid(self):
        """Create beautiful color grid"""
        colors_frame = ctk.CTkFrame(self.main_container, fg_color="white")
        colors_frame.pack(pady=10)
        
        row, col = 0, 0
        for hex_code, info in ColorPalette.RFID_COLORS.items():
            btn = ctk.CTkButton(
                colors_frame,
                text="",
                width=42,
                height=42,
                fg_color=hex_code,
                hover_color=hex_code,
                corner_radius=8,
                command=lambda h=hex_code, i=info: self.select_color(h, i[self.lang.current_lang])
            )
            btn.grid(row=row, column=col, padx=3, pady=3)
            
            col += 1
            if col >= 8:
                col = 0
                row += 1
    
    def create_action_buttons(self):
        """Create main action buttons"""
        # Write button
        self.write_btn = ctk.CTkButton(
            self.main_container,
            text=self.lang.get("write"),
            command=self.write_tag,
            fg_color="#28a745",
            hover_color="#218838",
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            corner_radius=12,
            height=50
        )
        self.write_btn.pack(pady=(20, 10), fill="x", padx=40)
        
        # Read button
        self.read_btn = ctk.CTkButton(
            self.main_container,
            text=self.lang.get("read"),
            command=self.read_tag,
            fg_color="#007bff",
            hover_color="#0069d9",
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            corner_radius=12,
            height=50
        )
        self.read_btn.pack(pady=(0, 10), fill="x", padx=40)
        
        # Auto detect button
        self.auto_btn = ctk.CTkButton(
            self.main_container,
            text=self.lang.get("auto_off"),
            command=self.toggle_auto_detect,
            fg_color="#6c757d",
            hover_color="#5a6268",
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            corner_radius=10,
            height=40
        )
        self.auto_btn.pack(pady=(0, 15), fill="x", padx=40)
    
    def create_info_section(self):
        """Create information display section"""
        info_frame = ctk.CTkFrame(self.main_container, corner_radius=12, fg_color="#f8f9fa")
        info_frame.pack(pady=10, fill="x", padx=20)
        
        info_title = ctk.CTkLabel(
            info_frame,
            text=self.lang.get("info"),
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#1a1a2e"
        )
        info_title.pack(pady=8)
        
        # Manufacturer info
        self.info_manufacturer = ctk.CTkLabel(
            info_frame,
            text="---",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#555555"
        )
        self.info_manufacturer.pack(pady=3)
        
        # Material info
        self.info_material = ctk.CTkLabel(
            info_frame,
            text="---",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#1a1a2e"
        )
        self.info_material.pack(pady=5)
        
        # Color info
        self.info_color = ctk.CTkLabel(
            info_frame,
            text="---",
            width=180,
            height=50,
            corner_radius=10,
            fg_color="#e0e0e0",
            text_color="#1a1a2e",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        self.info_color.pack(pady=10)
    
    def create_footer(self):
        """Create footer with version info"""
        footer = ctk.CTkFrame(self.main_container, fg_color="white", height=30)
        footer.pack(fill="x", side="bottom", pady=(5, 0))
        
        version_label = ctk.CTkLabel(
            footer,
            text=f"v{APP_VERSION} • {APP_AUTHOR}",
            font=ctk.CTkFont(size=10),
            text_color="#999999"
        )
        version_label.pack()
    
    def get_manufacturer_list(self):
        """Get manufacturer list for current language"""
        return [self.config.manufacturers[i][self.lang.current_lang] for i in range(21)]
    
    def select_color(self, hex_code, name):
        """Handle color selection"""
        self.selected_color_hex = hex_code
        self.selected_color_name = name
        
        text_color = "black" if hex_code in ["#FAFAFA", "#D9E3ED", "#99DEFF", "#CEC0FE", 
                                             "#CADE4B", "#E2DFCD", "#CAC59F"] else "white"
        self.color_preview.configure(text=name, fg_color=hex_code, text_color=text_color)
    
    def update_reader_status(self):
        """Update RFID reader status display"""
        if self.rfid.reader_available:
            self.status_icon.configure(text="✅", text_color="#28a745")
            self.status_text.configure(text=self.lang.get("ready"), text_color="#28a745")
            self.write_btn.configure(state="normal")
            self.read_btn.configure(state="normal")
            self.auto_btn.configure(state="normal")
        else:
            self.status_icon.configure(text="⚠️", text_color="#dc3545")
            self.status_text.configure(text=self.lang.get("not_ready"), text_color="#dc3545")
            self.write_btn.configure(state="disabled")
            self.read_btn.configure(state="disabled")
            self.auto_btn.configure(state="disabled")
    
    def update_status(self, message):
        """Update status message"""
        self.status_text.configure(text=message)
    
    def write_tag(self):
        """Write tag with current selection"""
        if not self.rfid.reader_available:
            messagebox.showerror(self.lang.get("error"), self.lang.get("no_reader"))
            return
        
        # Validate selections
        if not hasattr(self, 'manufacturer_combo') or not self.manufacturer_combo.get():
            messagebox.showerror(self.lang.get("error"), self.lang.get("no_manufacturer"))
            return
        
        if not hasattr(self, 'material_combo') or not self.material_combo.get():
            messagebox.showerror(self.lang.get("error"), self.lang.get("no_material"))
            return
        
        if not hasattr(self, 'selected_color_hex'):
            messagebox.showerror(self.lang.get("error"), self.lang.get("no_color"))
            return
        
        # Get codes
        man_name = self.manufacturer_combo.get()
        material_name = self.material_combo.get()
        
        # Find manufacturer code
        man_code = None
        for code, info in self.config.manufacturers.items():
            if info[self.lang.current_lang] == man_name:
                man_code = code
                break
        
        material_code = self.config.materials.get(material_name)
        color_code = ColorPalette.get_color_code(self.selected_color_hex)
        
        if man_code is None or material_code is None or color_code == 0:
            messagebox.showerror(self.lang.get("error"), "Invalid selection")
            return
        
        # Write to tag
        try:
            self.rfid.write_tag(material_code, color_code, man_code)
            messagebox.showinfo(self.lang.get("success"), self.lang.get("write_success"))
        except Exception as e:
            messagebox.showerror(self.lang.get("error"), self.lang.get(str(e) if str(e) in self.lang.TRANSLATIONS[self.lang.current_lang] else "write_failed"))
    
    def read_tag(self):
        """Read and display tag information"""
        if not self.rfid.reader_available:
            messagebox.showerror(self.lang.get("error"), self.lang.get("no_reader"))
            return
        
        try:
            data = self.rfid.read_tag()
            
            if data["material"] == 0 and data["color"] == 0:
                self.show_tag_info(self.lang.get("empty"), "#FFFFFF", "")
                return
            
            # Get material name
            material_name = None
            for name, code in self.config.materials.items():
                if code == data["material"]:
                    material_name = name
                    break
            
            if not material_name:
                material_name = self.lang.get("unknown")
            
            # Get color info
            hex_code, color_name = ColorPalette.get_color_name(data["color"], self.lang.current_lang)
            
            # Get manufacturer name
            manufacturer_name = self.config.manufacturers.get(data["manufacturer"], self.config.manufacturers[0])[self.lang.current_lang]
            
            self.show_tag_info(material_name, hex_code, color_name, manufacturer_name)
            
        except Exception as e:
            messagebox.showerror(self.lang.get("error"), self.lang.get("read_failed"))
    
    def show_tag_info(self, material, hex_code, color_name, manufacturer=None):
        """Display tag information in info section"""
        if manufacturer:
            self.info_manufacturer.configure(text=f"🏭 {manufacturer}")
        else:
            self.info_manufacturer.configure(text="---")
        
        self.info_material.configure(text=f"📦 {material}")
        
        if color_name and color_name != self.lang.get("empty"):
            text_color = "black" if hex_code in ["#FAFAFA", "#D9E3ED", "#99DEFF", "#CEC0FE", 
                                                 "#CADE4B", "#E2DFCD", "#CAC59F"] else "white"
            self.info_color.configure(text=f"🎨 {color_name}", fg_color=hex_code, text_color=text_color)
        else:
            self.info_color.configure(text=material, fg_color="#e0e0e0", text_color="#1a1a2e")
    
    def toggle_auto_detect(self):
        """Toggle automatic tag detection"""
        if not self.rfid.reader_available:
            messagebox.showerror(self.lang.get("error"), self.lang.get("no_reader"))
            return
        
        self.auto_detect_active = not self.auto_detect_active
        
        if self.auto_detect_active:
            self.auto_btn.configure(text=self.lang.get("auto_on"), fg_color="#dc3545")
            self.auto_detect_thread = threading.Thread(target=self.auto_detect_loop, daemon=True)
            self.auto_detect_thread.start()
        else:
            self.auto_btn.configure(text=self.lang.get("auto_off"), fg_color="#6c757d")
    
    def auto_detect_loop(self):
        """Background thread for auto detection"""
        tag_present = False
        
        while self.auto_detect_active and self.rfid.reader_available:
            try:
                now_present = self.rfid.check_presence()
                
                if now_present and not tag_present:
                    self.root.after(0, lambda: self.status_text.configure(text=self.lang.get("tag_placed")))
                    self.root.after(0, self.read_tag)
                    tag_present = True
                elif not now_present and tag_present:
                    self.root.after(0, lambda: self.status_text.configure(text=self.lang.get("tag_removed")))
                    self.root.after(0, lambda: self.show_tag_info("---", "#FFFFFF", ""))
                    tag_present = False
                
                time.sleep(0.5)
            except:
                time.sleep(1)
    
    def toggle_language(self):
        """Switch between languages"""
        self.lang.switch()
        self.update_ui_language()
    
    def update_ui_language(self):
        """Update all UI text when language changes"""
        # Update window title
        self.root.title(f"{self.lang.get('title')} v{APP_VERSION}")
        
        # Update header
        for widget in self.main_container.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkLabel) and hasattr(child, '_text'):
                        if child._text in ["BoxRFID Менеджер", "BoxRFID Manager", "BoxRFID Manager"]:
                            child.configure(text=self.lang.get("title"))
                        elif child._text in ["Управление RFID метками для QIDI Box", "RFID Tag Manager for QIDI Box", "RFID Tag Manager für QIDI Box"]:
                            child.configure(text=self.lang.get("subtitle"))
        
        # Update selection labels
        for widget in self.main_container.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and hasattr(widget, '_text'):
                if widget._text in ["Производитель", "Manufacturer", "Hersteller"]:
                    widget.configure(text=self.lang.get("manufacturer"))
                elif widget._text in ["Материал", "Material", "Material"]:
                    widget.configure(text=self.lang.get("material"))
                elif widget._text in ["Цвет", "Color", "Farbe"]:
                    widget.configure(text=self.lang.get("color"))
        
        # Update combo boxes
        self.manufacturer_combo.configure(values=self.get_manufacturer_list())
        self.material_combo.configure(values=list(self.config.materials.keys()))
        
        # Update color preview text if no color selected
        if not hasattr(self, 'selected_color_hex'):
            self.color_preview.configure(text=self.lang.get("no_color"))
        
        # Update buttons
        self.write_btn.configure(text=self.lang.get("write"))
        self.read_btn.configure(text=self.lang.get("read"))
        
        if self.auto_detect_active:
            self.auto_btn.configure(text=self.lang.get("auto_on"))
        else:
            self.auto_btn.configure(text=self.lang.get("auto_off"))
        
        # Update info section
        info_title = None
        for widget in self.main_container.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkLabel) and hasattr(child, '_text'):
                        if child._text in ["📋 ИНФОРМАЦИЯ О МЕТКЕ", "📋 TAG INFORMATION", "📋 TAG INFORMATIONEN"]:
                            child.configure(text=self.lang.get("info"))
        
        # Update reader status
        self.update_reader_status()
    
    def start_periodic_check(self):
        """Periodically check RFID reader status"""
        def check():
            self.rfid._check_reader()
            self.update_reader_status()
            self.root.after(3000, check)
        
        self.root.after(3000, check)
    
    def on_manufacturer_change(self, choice):
        """Handle manufacturer selection change"""
        pass
    
    def on_material_change(self, choice):
        """Handle material selection change"""
        pass
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

# ================================
# MAIN ENTRY POINT
# ================================
if __name__ == "__main__":
    app = ModernRFIDApp()
    app.run()