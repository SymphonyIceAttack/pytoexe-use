import customtkinter as ctk
from tkinter import messagebox
from smartcard.System import readers
import threading
import time

# ================================
# DATABASE
# ================================
MATERIALS = {
    "PLA": 1, "PLA Matte": 2, "PLA Metal": 3, "PLA Silk": 4, "PLA-CF": 5, "PLA-Wood": 6,
    "PLA Basic": 7, "PLA Matte Basic": 8, "ABS": 11, "ABS-GF": 12, "ABS-Metal": 13, "ABS-Odorless": 14,
    "ASA": 18, "ASA-AERO": 19, "UltraPA": 24, "PA12-CF": 25, "UltraPA-CF25": 26, "PAHT-CF": 30,
    "PAHT-GF": 31, "Support For PAHT": 32, "Support For PET/PA": 33, "PC/ABS-FR": 34,
    "PET-CF": 37, "PET-GF": 38, "PETG Basic": 39, "PETG-Though": 40, "PETG": 41, "PPS-CF": 44,
    "PETG Translucent": 45, "PVA": 47, "TPU-AERO": 49, "TPU": 50
}

MATERIALS_REV = {v: k for k, v in MATERIALS.items()}

COLORS = {
    "#FAFAFA": {"de": "Weiß", "en": "White", "val": 1},
    "#060606": {"de": "Schwarz", "en": "Black", "val": 2},
    "#D9E3ED": {"de": "Grau", "en": "Gray", "val": 3},
    "#5CF30F": {"de": "Hellgrün", "en": "Light Green", "val": 4},
    "#63E492": {"de": "Mint", "en": "Mint", "val": 5},
    "#2850FF": {"de": "Blau", "en": "Blue", "val": 6},
    "#FE98FE": {"de": "Pink", "en": "Pink", "val": 7},
    "#DFD628": {"de": "Gelb", "en": "Yellow", "val": 8},
    "#228332": {"de": "Grün", "en": "Green", "val": 9},
    "#99DEFF": {"de": "Hellblau", "en": "Light Blue", "val": 10},
    "#1714B0": {"de": "Dunkelblau", "en": "Dark Blue", "val": 11},
    "#CEC0FE": {"de": "Lavendel", "en": "Lavender", "val": 12},
    "#CADE4B": {"de": "Lime", "en": "Lime", "val": 13},
    "#1353AB": {"de": "Royalblau", "en": "Royal Blue", "val": 14},
    "#5EA9FD": {"de": "Himmelblau", "en": "Sky Blue", "val": 15},
    "#A878FF": {"de": "Violett", "en": "Violet", "val": 16},
    "#FE717A": {"de": "Rosa", "en": "Rose", "val": 17},
    "#FF362D": {"de": "Rot", "en": "Red", "val": 18},
    "#E2DFCD": {"de": "Beige", "en": "Beige", "val": 19},
    "#898F9B": {"de": "Silber", "en": "Silver", "val": 20},
    "#6E3812": {"de": "Braun", "en": "Brown", "val": 21},
    "#CAC59F": {"de": "Khaki", "en": "Khaki", "val": 22},
    "#F28636": {"de": "Orange", "en": "Orange", "val": 23},
    "#B87F2B": {"de": "Bronze", "en": "Bronze", "val": 24},
}
COLORS_REV = {v["val"]: (k, v) for k, v in COLORS.items()}

# ================================
# VENDORS
# ================================
VENDORS = {
    "Unknown": 0,
    "QIDI": 1,
    "XYZ Print": 2,
    "Generic": 3,
    "Vendor A": 4,
    "Vendor B": 5,
    "Vendor C": 6,
    "Vendor D": 7,
    "Vendor E": 8,
    "Vendor F": 9,
    "Vendor G": 10,
    "Vendor H": 11,
    "Vendor I": 12,
    "Vendor J": 13,
    "Vendor K": 14,
    "Vendor L": 15,
    "Vendor M": 16,
    "Vendor N": 17,
    "Vendor O": 18,
    "Vendor P": 19,
    "Vendor Q": 20
}

VENDORS_REV = {v: k for k, v in VENDORS.items()}

# ================================
# LANGUAGE SETTINGS
# ================================
LANG = {
    "de": {
        "title": "BoxRFID Manager für QIDI Box",
        "material": "Materialtyp auswählen",
        "color": "Farbe auswählen",
        "vendor": "Hersteller auswählen",
        "write": "TAG SCHREIBEN",
        "read": "TAG LESEN",
        "done": "Schreiben abgeschlossen!",
        "error": "Fehler",
        "select_valid": "Bitte gültiges Material, Farbe und Hersteller auswählen",
        "no_color": "Keine Farbe ausgewählt",
        "tag_info": "Tag Informationen",
        "empty_tag": "Leerer RFID Tag",
        "no_reader": "Kein Lesegerät gefunden!",
        "no_key": "Kein gültiger Schlüssel gefunden",
        "auth_failed": "Authentifizierung fehlgeschlagen",
        "write_failed": "Schreiben fehlgeschlagen",
        "read_failed": "Lesen fehlgeschlagen",
        "unknown": "Unbekannt",
        "auto_detect": "Auto-Erkennung"
    },
    "en": {
        "title": "BoxRFID Manager for QIDI Box",
        "material": "Select Material",
        "color": "Select Color",
        "vendor": "Select Vendor",
        "write": "WRITE TAG",
        "read": "READ TAG",
        "done": "Write completed!",
        "error": "Error",
        "select_valid": "Please select valid material, color and vendor",
        "no_color": "No color selected",
        "tag_info": "Tag Information",
        "empty_tag": "Empty RFID Tag",
        "no_reader": "No reader found!",
        "no_key": "No valid key found",
        "auth_failed": "Authentication failed",
        "write_failed": "Write failed",
        "read_failed": "Read failed",
        "unknown": "Unknown",
        "auto_detect": "Auto Detection"
    }
}
current_lang = "de"

# ================================
# RFID FUNCTIONS
# ================================
DATA_BLOCK = 4
KEYS_TO_TRY = [
    [0xD3, 0xF7, 0xD3, 0xF7, 0xD3, 0xF7],
    [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
]

# Global variables for tag detection
auto_detect_active = False
current_tag_present = False
last_tag_data = None

def connect_reader