import customtkinter as ctk
from tkinter import messagebox
from smartcard.System import readers
import threading
import time

# ================================
# DATABASE
# ================================

# Производители материалов (0-20) согласно вашему списку
MANUFACTURERS = {
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
    12: {"de": "Creality", "en": "Creality", "ru": "Creality"},  # Дубликат, но оставим как есть
    13: {"de": "Polymaker", "en": "Polymaker", "ru": "Polymaker"},
    14: {"de": "Elegoo", "en": "Elegoo", "ru": "Elegoo"},
    15: {"de": "Anycubic", "en": "Anycubic", "ru": "Anycubic"},
    16: {"de": "Sunlu", "en": "Sunlu", "ru": "Sunlu"},
    # 17-20 без производителя
    17: {"de": "Unknown", "en": "Unknown", "ru": "Неизвестно"},
    18: {"de": "Unknown", "en": "Unknown", "ru": "Неизвестно"},
    19: {"de": "Unknown", "en": "Unknown", "ru": "Неизвестно"},
    20: {"de": "Unknown", "en": "Unknown", "ru": "Неизвестно"}
}

MANUFACTURERS_REV_DE = {v["de"]: k for k, v in MANUFACTURERS.items()}
MANUFACTURERS_REV_EN = {v["en"]: k for k, v in MANUFACTURERS.items()}
MANUFACTURERS_REV_RU = {v["ru"]: k for k, v in MANUFACTURERS.items()}

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
    "#FAFAFA": {"de": "Weiß", "en": "White", "ru": "Белый", "val": 1},
    "#060606": {"de": "Schwarz", "en": "Black", "ru": "Черный", "val": 2},
    "#D9E3ED": {"de": "Grau", "en": "Gray", "ru": "Серый", "val": 3},
    "#5CF30F": {"de": "Hellgrün", "en": "Light Green", "ru": "Светло-зеленый", "val": 4},
    "#63E492": {"de": "Mint", "en": "Mint", "ru": "Мятный", "val": 5},
    "#2850FF": {"de": "Blau", "en": "Blue", "ru": "Синий", "val": 6},
    "#FE98FE": {"de": "Pink", "en": "Pink", "ru": "Розовый", "val": 7},
    "#DFD628": {"de": "Gelb", "en": "Yellow", "ru": "Желтый", "val": 8},
    "#228332": {"de": "Grün", "en": "Green", "ru": "Зеленый", "val": 9},
    "#99DEFF": {"de": "Hellblau", "en": "Light Blue", "ru": "Голубой", "val": 10},
    "#1714B0": {"de": "Dunkelblau", "en": "Dark Blue", "ru": "Темно-синий", "val": 11},
    "#CEC0FE": {"de": "Lavendel", "en": "Lavender", "ru": "Лавандовый", "val": 12},
    "#CADE4B": {"de": "Lime", "en": "Lime", "ru": "Лаймовый", "val": 13},
    "#1353AB": {"de": "Royalblau", "en": "Royal Blue", "ru": "Королевский синий", "val": 14},
    "#5EA9FD": {"de": "Himmelblau", "en": "Sky Blue", "ru": "Небесно-голубой", "val": 15},
    "#A878FF": {"de": "Violett", "en": "Violet", "ru": "Фиолетовый", "val": 16},
    "#FE717A": {"de": "Rosa", "en": "Rose", "ru": "Розовый", "val": 17},
    "#FF362D": {"de": "Rot", "en": "Red", "ru": "Красный", "val": 18},
    "#E2DFCD": {"de": "Beige", "en": "Beige", "ru": "Бежевый", "val": 19},
    "#898F9B": {"de": "Silber", "en": "Silver", "ru": "Серебряный", "val": 20},
    "#6E3812": {"de": "Braun", "en": "Brown", "ru": "Коричневый", "val": 21},
    "#CAC59F": {"de": "Khaki", "en": "Khaki", "ru": "Хаки", "val": 22},
    "#F28636": {"de": "Orange", "en": "Orange", "ru": "Оранжевый", "val": 23},
    "#B87F2B": {"de": "Bronze", "en": "Bronze", "ru": "Бронзовый", "val": 24},
}
COLORS_REV = {v["val"]: (k, v) for k, v in COLORS.items()}

# ================================
# LANGUAGE SETTINGS
# ================================
LANG = {
    "de": {
        "title": "BoxRFID Manager für QIDI Box",
        "material": "Materialtyp auswählen",
        "manufacturer": "Hersteller auswählen",
        "color": "Farbe auswählen",
        "write": "TAG SCHREIBEN",
        "read": "TAG LESEN",
        "done": "Schreiben abgeschlossen!",
        "error": "Fehler",
        "select_valid": "Bitte gültiges Material, Hersteller und Farbe auswählen",
        "no_color": "Keine Farbe ausgewählt",
        "no_manufacturer": "Kein Hersteller ausgewählt",
        "tag_info": "Tag Informationen",
        "empty_tag": "Leerer RFID Tag",
        "no_reader": "Kein Lesegerät gefunden! Bitte RFID Reader anschließen",
        "no_key": "Kein gültiger Schlüssel gefunden",
        "auth_failed": "Authentifizierung fehlgeschlagen",
        "write_failed": "Schreiben fehlgeschlagen",
        "read_failed": "Lesen fehlgeschlagen",
        "unknown": "Unbekannt",
        "auto_detect": "Auto-Erkennung",
        "legacy_tag": "Altes Format",
        "reader_ready": "RFID Bereit",
        "reader_not_ready": "Kein RFID Reader"
    },
    "en": {
        "title": "BoxRFID Manager for QIDI Box",
        "material": "Select Material",
        "manufacturer": "Select Manufacturer",
        "color": "Select Color",
        "write": "WRITE TAG",
        "read": "READ TAG",
        "done": "Write completed!",
        "error": "Error",
        "select_valid": "Please select valid material, manufacturer and color",
        "no_color": "No color selected",
        "no_manufacturer": "No manufacturer selected",
        "tag_info": "Tag Information",
        "empty_tag": "Empty RFID Tag",
        "no_reader": "No reader found! Please connect RFID reader",
        "no_key": "No valid key found",
        "auth_failed": "Authentication failed",
        "write_failed": "Write failed",
        "read_failed": "Read failed",
        "unknown": "Unknown",
        "auto_detect": "Auto Detection",
        "legacy_tag": "Legacy Format",
        "reader_ready": "RFID Ready",
        "reader_not_ready": "No RFID Reader"
    },
    "ru": {
        "title": "BoxRFID Менеджер для QIDI Box",
        "material": "Выберите тип материала",
        "manufacturer": "Выберите производителя",
        "color": "Выберите цвет",
        "write": "ЗАПИСАТЬ ТЕГ",
        "read": "СЧИТАТЬ ТЕГ",
        "done": "Запись завершена!",
        "error": "Ошибка",
        "select_valid": "Пожалуйста, выберите материал, производителя и цвет",
        "no_color": "Цвет не выбран",
        "no_manufacturer": "Производитель не выбран",
        "tag_info": "Информация о теге",
        "empty_tag": "Пустой RFID тег",
        "no_reader": "Устройство чтения не найдено! Пожалуйста, подключите RFID ридер",
        "no_key": "Действительный ключ не найден",
        "auth_failed": "Ошибка аутентификации",
        "write_failed": "Ошибка записи",
        "read_failed": "Ошибка чтения",
        "unknown": "Неизвестно",
        "auto_detect": "Авто-обнаружение",
        "legacy_tag": "Старый формат",
        "reader_ready": "RFID Готов",
        "reader_not_ready": "Нет RFID ридера"
    }
}
current_lang = "ru"  # Русский язык по умолчанию

# ================================
# RFID FUNCTIONS
# ================================
DATA_BLOCK = 4
KEYS_TO_TRY = [
    [0xD3, 0xF7, 0xD3, 0xF7, 0xD3, 0xF7],
    [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
]

# Global variables
auto_detect_active = False
auto_detect_lock = threading.Lock()
current_tag_present = False
last_tag_data = None
reader_available = False
detection_thread = None

def check_rfid_reader():
    """Check if RFID reader is available"""
    global reader_available
    try:
        r = readers()
        if r and len(r) > 0:
            reader_available = True
            return True
        else:
            reader_available = False
            return False
    except Exception as e:
        print(f"Reader check error: {e}")
        reader_available = False
        return False

def update_reader_status():
    """Update UI based on reader availability"""
    if reader_available:
        status_label.configure(
            text="🟢 " + LANG[current_lang]["reader_ready"],
            text_color="green"
        )
        write_btn.configure(state="normal", fg_color="#28a745")
        read_btn.configure(state="normal", fg_color="#007bff")
        auto_detect_btn.configure(state="normal", fg_color="#6c757d")
    else:
        status_label.configure(
            text="🔴 " + LANG[current_lang]["reader_not_ready"],
            text_color="red"
        )
        write_btn.configure(state="disabled", fg_color="#6c757d")
        read_btn.configure(state="disabled", fg_color="#6c757d")
        auto_detect_btn.configure(state="disabled", fg_color="#6c757d")

def connect_reader():
    """Establish connection to RFID reader"""
    if not reader_available:
        raise Exception(LANG[current_lang]["no_reader"])
    
    try:
        r = readers()
        if not r:
            raise Exception(LANG[current_lang]["no_reader"])
        conn = r[0].createConnection()
        conn.connect()
        return conn
    except Exception as e:
        raise Exception(LANG[current_lang]["no_reader"])

def load_key(conn, key):
    """Load authentication key to reader"""
    LOAD_KEY = [0xFF, 0x82, 0x00, 0x00, 0x06] + key
    _, sw1, sw2 = conn.transmit(LOAD_KEY)
    return (sw1 == 0x90 and sw2 == 0x00)

def authenticate_block(conn, block, key_type=0x60):
    """Authenticate access to block"""
    AUTH_BLOCK = [0xFF, 0x86, 0x00, 0x00, 0x05,
                  0x01, 0x00, block, key_type, 0x00]
    _, sw1, sw2 = conn.transmit(AUTH_BLOCK)
    return (sw1 == 0x90 and sw2 == 0x00)

def find_working_key(conn, block):
    """Find a working authentication key"""
    for key in KEYS_TO_TRY:
        if load_key(conn, key) and authenticate_block(conn, block):
            return key
    raise Exception(LANG[current_lang]["no_key"])

def write_tag(material_num, color_num, manufacturer_num, value_num=1):
    """Write data to RFID tag"""
    if not reader_available:
        messagebox.showerror(LANG[current_lang]["error"], LANG[current_lang]["no_reader"])
        return
    
    conn = None
    try:
        conn = connect_reader()
        working_key = find_working_key(conn, DATA_BLOCK)

        if not load_key(conn, working_key) or not authenticate_block(conn, DATA_BLOCK):
            raise Exception(LANG[current_lang]["auth_failed"])

        # Format: [material, color, manufacturer, value, ... padding]
        data_bytes = [material_num, color_num, manufacturer_num, value_num] + [0x00]*12
        WRITE_BLOCK = [0xFF, 0xD6, 0x00, DATA_BLOCK, 0x10] + data_bytes
        _, sw1, sw2 = conn.transmit(WRITE_BLOCK)

        if sw1 != 0x90 or sw2 != 0x00:
            raise Exception(LANG[current_lang]["write_failed"])

        messagebox.showinfo("OK", LANG[current_lang]["done"])
        
    except Exception as e:
        messagebox.showerror(LANG[current_lang]["error"], str(e))
    finally:
        if conn:
            try:
                conn.disconnect()
            except:
                pass

def read_tag():
    """Read data from RFID tag with backward compatibility"""
    if not reader_available:
        messagebox.showerror(LANG[current_lang]["error"], LANG[current_lang]["no_reader"])
        return False
    
    global last_tag_data
    
    conn = None
    try:
        conn = connect_reader()
        working_key = find_working_key(conn, DATA_BLOCK)

        if not load_key(conn, working_key) or not authenticate_block(conn, DATA_BLOCK):
            raise Exception(LANG[current_lang]["auth_failed"])

        READ_BLOCK = [0xFF, 0xB0, 0x00, DATA_BLOCK, 0x10]
        data, sw1, sw2 = conn.transmit(READ_BLOCK)

        if sw1 != 0x90 or sw2 != 0x00:
            raise Exception(LANG[current_lang]["read_failed"])

        material_val = data[0]
        color_val = data[1]
        manufacturer_val = data[2] if len(data) > 2 else 0
        
        # Backward compatibility check for old format
        is_old_format = False
        if len(data) > 3:
            is_old_format = (manufacturer_val == 0 and data[3] == 0 and material_val != 0)
        
        # Store tag data for comparison
        last_tag_data = (material_val, color_val, manufacturer_val)
        
        # Check if tag is empty
        if material_val == 0 and color_val == 0 and manufacturer_val == 0:
            show_tag_info(LANG[current_lang]["empty_tag"], "#FFFFFF", "", "")
            return True
        else:
            material_name = MATERIALS_REV.get(material_val, LANG[current_lang]["unknown"])
            color_hex, color_dict = COLORS_REV.get(color_val, ("#FFFFFF", {"de": LANG[current_lang]["unknown"], "en": LANG[current_lang]["unknown"], "ru": LANG[current_lang]["unknown"]}))
            
            if is_old_format:
                manufacturer_name = f"{LANG[current_lang]['unknown']} ({LANG[current_lang]['legacy_tag']})"
            else:
                manufacturer_name = MANUFACTURERS.get(manufacturer_val, MANUFACTURERS[0])[current_lang]
            
            show_tag_info(material_name, color_hex, color_dict[current_lang], manufacturer_name)
            
        return True
        
    except Exception as e:
        print(f"Read error: {e}")
        return False
    finally:
        if conn:
            try:
                conn.disconnect()
            except:
                pass

def check_tag_presence():
    """Quick check if a tag is present without full authentication"""
    if not reader_available:
        return False
    
    conn = None
    try:
        r = readers()
        if not r:
            return False
            
        conn = r[0].createConnection()
        conn.connect()
        return True
        
    except:
        return False
    finally:
        if conn:
            try:
                conn.disconnect()
            except:
                pass

def auto_detect_tag():
    """Background thread to automatically detect and read tags"""
    global current_tag_present, last_tag_data, auto_detect_active
    
    tag_present = False
    tag_removed_timestamp = 0
    tag_removed_delay = 1.0
    
    while True:
        with auto_detect_lock:
            if not auto_detect_active:
                break
        
        if not reader_available:
            time.sleep(1)
            continue
        
        try:
            tag_now_present = check_tag_presence()
            
            if tag_now_present and not tag_present:
                print("Tag detected, reading...")
                if read_tag():
                    tag_present = True
                    current_tag_present = True
                    tag_removed_timestamp = 0
                time.sleep(0.2)
            
            elif not tag_now_present and tag_present:
                print("Tag removed")
                if tag_removed_timestamp == 0:
                    tag_removed_timestamp = time.time()
                elif time.time() - tag_removed_timestamp > tag_removed_delay:
                    tag_present = False
                    current_tag_present = False
                    last_tag_data = None
                    root.after(0, lambda: show_tag_info("---", "#FFFFFF", "---", "---"))
            
            elif tag_now_present and tag_present:
                try:
                    if check_tag_presence():
                        pass
                except:
                    if read_tag():
                        tag_removed_timestamp = 0
            
            time.sleep(0.3)
            
        except Exception as e:
            print(f"Auto-detect error: {e}")
            time.sleep(1)
            tag_present = False

# ================================
# GUI
# ================================
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Create main window
root = ctk.CTk()
root.title(LANG[current_lang]["title"])
root.geometry("500x900")

# Main frame
main_frame = ctk.CTkFrame(root, corner_radius=15, fg_color="white")
main_frame.pack(padx=20, pady=20, fill="both", expand=True)

# Header with language selector
header_frame = ctk.CTkFrame(main_frame, fg_color="white", height=40)
header_frame.pack(fill="x", padx=10, pady=(10, 5))

title_label = ctk.CTkLabel(header_frame, text=LANG[current_lang]["title"],
                           font=("Segoe UI", 18, "bold"), text_color="black")
title_label.pack(side="left", padx=10)

# Language selector (now with 3 languages)
def switch_lang():
    """Switch between German, English and Russian"""
    global current_lang
    
    current_man = manufacturer_var.get()
    current_man_num = None
    
    # Find current manufacturer number
    if current_lang == "de":
        current_man_num = MANUFACTURERS_REV_DE.get(current_man)
    elif current_lang == "en":
        current_man_num = MANUFACTURERS_REV_EN.get(current_man)
    else:  # ru
        current_man_num = MANUFACTURERS_REV_RU.get(current_man)
    
    # Cycle through languages: ru -> de -> en -> ru
    if current_lang == "ru":
        current_lang = "de"
    elif current_lang == "de":
        current_lang = "en"
    else:  # en
        current_lang = "ru"
    
    update_labels()
    
    # Restore manufacturer selection
    if current_man_num is not None:
        manufacturer_var.set(MANUFACTURERS[current_man_num][current_lang])
    
    update_reader_status()

# Language button with flag emojis for better UX
lang_btn = ctk.CTkButton(header_frame, text="🌐 RU/DE/EN", command=switch_lang,
                         width=80, height=30, 
                         fg_color="#2b2b2b", hover_color="#3b3b3b", text_color="white",
                         font=("Segoe UI", 10, "bold"), corner_radius=6)
lang_btn.pack(side="right", padx=10)

# Status bar
status_frame = ctk.CTkFrame(main_frame, fg_color="white", height=30)
status_frame.pack(fill="x", padx=10, pady=(0, 10))

status_label = ctk.CTkLabel(status_frame, text="", font=("Segoe UI", 11, "bold"))
status_label.pack(side="left", padx=10)

# Manufacturer selection
man_label = ctk.CTkLabel(main_frame, text=LANG[current_lang]["manufacturer"],
                         font=("Segoe UI", 14, "bold"), text_color="black")
man_label.pack(pady=(10, 5))

manufacturer_var = ctk.StringVar(value=MANUFACTURERS[0][current_lang])

class CustomOptionMenu(ctk.CTkOptionMenu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, '_dropdown_menu'):
            self._dropdown_menu.configure(font=("Segoe UI", 14, "bold"))

def get_manufacturer_list():
    return [MANUFACTURERS[i][current_lang] for i in range(21)]

manufacturer_combo = CustomOptionMenu(main_frame, values=get_manufacturer_list(), variable=manufacturer_var,
                                     fg_color="#f1f1f1", button_color="#f1f1f1", text_color="black",
                                     font=("Segoe UI", 14, "bold"),
                                     width=220, height=35)
manufacturer_combo.pack(pady=5)

# Material selection
mat_label = ctk.CTkLabel(main_frame, text=LANG[current_lang]["material"],
                         font=("Segoe UI", 14, "bold"), text_color="black")
mat_label.pack(pady=(10, 5))

material_var = ctk.StringVar()

material_combo = CustomOptionMenu(main_frame, values=list(MATERIALS.keys()), variable=material_var,
                                 fg_color="#f1f1f1", button_color="#f1f1f1", text_color="black",
                                 font=("Segoe UI", 14, "bold"),
                                 width=220, height=35)
material_combo.pack(pady=5)

# Color selection
col_label = ctk.CTkLabel(main_frame, text=LANG[current_lang]["color"],
                         font=("Segoe UI", 14, "bold"), text_color="black")
col_label.pack(pady=(10, 5))

color_var = ctk.StringVar()
color_preview = ctk.CTkLabel(main_frame, text=LANG[current_lang]["no_color"], width=220, height=40,
                             corner_radius=8, fg_color="white", text_color="black", 
                             font=("Segoe UI", 14, "bold"))
color_preview.pack(pady=10)

# Color palette 8x3
color_frame = ctk.CTkFrame(main_frame, fg_color="white")
color_frame.pack(pady=5)

def select_color(hex_code, name):
    """Handle color selection"""
    color_var.set(hex_code)
    text_color = "black" if hex_code in ["#FAFAFA", "#D9E3ED", "#99DEFF", "#CEC0FE", 
                                         "#CADE4B", "#E2DFCD", "#CAC59F"] else "white"
    color_preview.configure(text=name, fg_color=hex_code, text_color=text_color)

# Create color buttons
row, col = 0, 0
for hex_code, vals in COLORS.items():
    btn = ctk.CTkButton(color_frame, text="", width=40, height=40, fg_color=hex_code,
                        hover_color=hex_code, corner_radius=6,
                        command=lambda h=hex_code, v=vals: select_color(h, v[current_lang]))
    btn.grid(row=row, column=col, padx=3, pady=3)
    col += 1
    if col >= 8: 
        col, row = 0, row + 1

# Action buttons
def on_write():
    """Handle write button click"""
    if not reader_available:
        messagebox.showerror(LANG[current_lang]["error"], LANG[current_lang]["no_reader"])
        return
    
    mat = material_var.get()
    col_hex = color_var.get()
    man_name = manufacturer_var.get()
    
    if not man_name or man_name == "":
        messagebox.showerror(LANG[current_lang]["error"], LANG[current_lang]["no_manufacturer"])
        return
    
    if mat not in MATERIALS:
        messagebox.showerror(LANG[current_lang]["error"], LANG[current_lang]["select_valid"])
        return
    
    if col_hex not in COLORS:
        messagebox.showerror(LANG[current_lang]["error"], LANG[current_lang]["no_color"])
        return
    
    # Get manufacturer number based on current language
    if current_lang == "de":
        manufacturer_num = MANUFACTURERS_REV_DE.get(man_name, 0)
    elif current_lang == "en":
        manufacturer_num = MANUFACTURERS_REV_EN.get(man_name, 0)
    else:  # ru
        manufacturer_num = MANUFACTURERS_REV_RU.get(man_name, 0)
    
    try:
        write_tag(MATERIALS[mat], COLORS[col_hex]["val"], manufacturer_num, 1)
    except Exception as e:
        messagebox.showerror(LANG[current_lang]["error"], str(e))

write_btn = ctk.CTkButton(main_frame, text=LANG[current_lang]["write"], command=on_write,
                          fg_color="#28a745", hover_color="#218838", text_color="white",
                          font=("Segoe UI", 14, "bold"), corner_radius=12, height=45)
write_btn.pack(pady=(20, 10), fill="x", padx=40)

def on_read():
    """Handle read button click"""
    if not reader_available:
        messagebox.showerror(LANG[current_lang]["error"], LANG[current_lang]["no_reader"])
        return
    read_tag()

read_btn = ctk.CTkButton(main_frame, text=LANG[current_lang]["read"], command=on_read,
                         fg_color="#007bff", hover_color="#0069d9", text_color="white",
                         font=("Segoe UI", 14, "bold"), corner_radius=12, height=45)
read_btn.pack(pady=(0, 10), fill="x", padx=40)

# Auto-detection button
def toggle_auto_detect():
    """Toggle automatic tag detection"""
    global auto_detect_active, detection_thread
    
    if not reader_available:
        messagebox.showerror(LANG[current_lang]["error"], LANG[current_lang]["no_reader"])
        return
    
    with auto_detect_lock:
        auto_detect_active = not auto_detect_active
    
    if auto_detect_active:
        auto_detect_btn.configure(text="⏺️ " + LANG[current_lang]["auto_detect"], 
                                 fg_color="#28a745", hover_color="#218838")
        detection_thread = threading.Thread(target=auto_detect_tag, daemon=True)
        detection_thread.start()
    else:
        auto_detect_btn.configure(text="⭕ " + LANG[current_lang]["auto_detect"], 
                                 fg_color="#6c757d", hover_color="#5a6268")

auto_detect_btn = ctk.CTkButton(main_frame, text="⭕ " + LANG[current_lang]["auto_detect"], 
                                command=toggle_auto_detect,
                                fg_color="#6c757d", hover_color="#5a6268", text_color="white",
                                font=("Segoe UI", 12), corner_radius=8, height=35)
auto_detect_btn.pack(pady=(0, 15))

# Info section
info_frame = ctk.CTkFrame(main_frame, corner_radius=12, fg_color="#e9ecef")
info_frame.pack(pady=10, fill="x", padx=20)

info_title = ctk.CTkLabel(info_frame, text=LANG[current_lang]["tag_info"],
                          font=("Segoe UI", 15, "bold"), text_color="black")
info_title.pack(pady=5)

info_manufacturer = ctk.CTkLabel(info_frame, text="---", 
                                 font=("Segoe UI", 14, "bold"), text_color="black")
info_manufacturer.pack(pady=3)

info_material = ctk.CTkLabel(info_frame, text="---", 
                             font=("Segoe UI", 18, "bold"), text_color="black")
info_material.pack(pady=5)

info_color = ctk.CTkLabel(info_frame, text="---", width=200, height=50, corner_radius=8,
                          fg_color="white", font=("Segoe UI", 14), text_color="black")
info_color.pack(pady=10)

def show_tag_info(material, hex_code, name, manufacturer="---"):
    """Display tag information"""
    info_manufacturer.configure(text=manufacturer, font=("Segoe UI", 14, "bold"))
    info_material.configure(text=material, font=("Segoe UI", 18, "bold"))
    
    if name and name != "---" and name != "":
        text_color = "black" if hex_code in ["#FAFAFA", "#D9E3ED", "#99DEFF", "#CEC0FE", 
                                           "#CADE4B", "#E2DFCD", "#CAC59F"] else "white"
        info_color.configure(text=name, fg_color=hex_code, text_color=text_color, 
                            font=("Segoe UI", 14, "bold"))
    else:
        info_color.configure(text="---", fg_color="#FFFFFF", text_color="black",
                            font=("Segoe UI", 14))

def update_labels():
    """Update all UI labels when language changes"""
    root.title(LANG[current_lang]["title"])
    title_label.configure(text=LANG[current_lang]["title"])
    man_label.configure(text=LANG[current_lang]["manufacturer"])
    mat_label.configure(text=LANG[current_lang]["material"])
    col_label.configure(text=LANG[current_lang]["color"])
    
    if not color_var.get():
        color_preview.configure(text=LANG[current_lang]["no_color"])
    
    write_btn.configure(text=LANG[current_lang]["write"])
    read_btn.configure(text=LANG[current_lang]["read"])
    info_title.configure(text=LANG[current_lang]["tag_info"])
    
    # Update manufacturer dropdown
    manufacturer_combo.configure(values=get_manufacturer_list())
    
    # Update color buttons text
    for hex_code, vals in COLORS.items():
        if color_var.get() == hex_code:
            select_color(hex_code, vals[current_lang])
            break
    
    # Update auto detect button
    if auto_detect_active:
        auto_detect_btn.configure(text="⏺️ " + LANG[current_lang]["auto_detect"])
    else:
        auto_detect_btn.configure(text="⭕ " + LANG[current_lang]["auto_detect"])

# Initialize
manufacturer_var.set(MANUFACTURERS[0][current_lang])

# Check RFID reader at startup
check_rfid_reader()
update_reader_status()

# Start periodic reader check (every 5 seconds)
def periodic_reader_check():
    """Periodically check if RFID reader is still connected"""
    check_rfid_reader()
    root.after(5000, periodic_reader_check)

periodic_reader_check()

# Start the application
root.mainloop()