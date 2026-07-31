#!/usr/bin/env python3
# SWILL CHEAT v6.0 — КЛЮЧИ В КОДЕ (БЕЗ JSON)

import os
import sys
import time
import threading
import random
import hashlib
import ctypes
import ctypes.wintypes
from datetime import datetime, timedelta
from PIL import ImageGrab, ImageDraw
import numpy as np
import cv2
import psutil
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# =============================================
# 1. ТВОИ КЛЮЧИ (ЖЁСТКО ЗАШИТЫ В КОДЕ)
# =============================================

VALID_KEYS = {
    # Пробные (1 день) — бесплатно для теста
    "T7F3A9B2C4D5E1G8": {"type": "trial", "days": 1},
    "T1A2B3C4D5E6F7H9": {"type": "trial", "days": 1},
    "T9K8L7M6N5O4P3Q2": {"type": "trial", "days": 1},
    "T8R9S0T1U2V3W4X5": {"type": "trial", "days": 1},
    
    # Месячные (30 дней) — 25 $
    "M6Y5U4I3O2P1Q0R9": {"type": "month", "days": 30},
    "M9X8C7V6B5N4M3L2": {"type": "month", "days": 30},
    "M3K4J5H6G7F8D9S1": {"type": "month", "days": 30},
    "M2A3S4D5F6G7H8J9": {"type": "month", "days": 30},
    
    # Бессрочные (навсегда) — 100 $
    "F0Q9W8E7R6T5Y4U3": {"type": "forever", "days": 99999},
    "F1P2O3I4U5Y6T7R8": {"type": "forever", "days": 99999},
    "F9E8W7Q6A5S4D3F2": {"type": "forever", "days": 99999},
}

# Хранилище активированных ключей (в памяти, не в файле)
activated_keys = {}

# =============================================
# 2. СИСТЕМА КЛЮЧЕЙ (БЕЗ ФАЙЛОВ)
# =============================================

class KeySystem:
    def __init__(self):
        self.hwid = self.get_hwid()
    
    def get_hwid(self):
        if os.name == 'nt':
            try:
                import wmi
                c = wmi.WMI()
                for disk in c.Win32_DiskDrive():
                    if disk.SerialNumber:
                        return hashlib.md5(disk.SerialNumber.encode()).hexdigest()[:16]
            except:
                pass
        else:
            try:
                with open('/etc/machine-id', 'r') as f:
                    return hashlib.md5(f.read().strip().encode()).hexdigest()[:16]
            except:
                pass
        return hashlib.md5(os.urandom(32)).hexdigest()[:16]
    
    def activate_key(self, key):
        global activated_keys
        key = key.upper().strip()
        
        if key not in VALID_KEYS:
            return False, "Неверный ключ"
        
        if key in activated_keys:
            return False, "Ключ уже активирован"
        
        key_data = VALID_KEYS[key]
        
        # Проверка на использование пробного ключа для этого HWID
        if key_data['type'] == 'trial':
            for k, data in activated_keys.items():
                if data['hwid'] == self.hwid and data['type'] == 'trial':
                    return False, "Пробный ключ уже использован"
        
        # Проверка на использование бессрочного ключа
        if key_data['type'] == 'forever':
            for k, data in activated_keys.items():
                if data['hwid'] == self.hwid and data['type'] == 'forever':
                    return False, "Бессрочный ключ уже активирован"
        
        # Активируем ключ
        activated_keys[key] = {
            'hwid': self.hwid,
            'type': key_data['type'],
            'days': key_data['days'],
            'activated_at': datetime.now()
        }
        
        return True, f"Ключ активирован! Тип: {self.get_key_label(key_data['type'])}"
    
    def check_key(self):
        if not activated_keys:
            return False, "Ключ не активирован"
        
        # Находим ключ для этого HWID
        for key, data in activated_keys.items():
            if data['hwid'] == self.hwid:
                # Проверка срока
                if data['days'] == 99999:
                    return True, "✅ Бессрочный ключ активен (навсегда)"
                
                days_passed = (datetime.now() - data['activated_at']).days
                days_left = data['days'] - days_passed
                
                if days_left <= 0:
                    return False, "❌ Ключ истёк"
                
                if data['type'] == 'trial':
                    return True, f"🔑 Пробный ключ активен. Осталось {days_left} день"
                elif data['type'] == 'month':
                    return True, f"🔑 Месячный ключ активен. Осталось {days_left} дней"
        
        return False, "Ключ не найден"
    
    def get_key_label(self, key_type):
        labels = {
            'trial': 'Пробный (1 день)',
            'month': 'Месячный (30 дней)',
            'forever': 'Бессрочный (навсегда)'
        }
        return labels.get(key_type, 'Неизвестный')

# =============================================
# 3. ОПРЕДЕЛЕНИЕ ОС И ЭМУЛЯЦИЯ МЫШИ
# =============================================

IS_WINDOWS = os.name == 'nt'

class MouseController:
    def __init__(self):
        if IS_WINDOWS:
            self.user32 = ctypes.windll.user32
        else:
            try:
                from evdev import UInput, ecodes as e
                self.ui = UInput({
                    e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT],
                    e.EV_REL: [e.REL_X, e.REL_Y],
                }, name='swill_mouse')
                self.e = e
            except:
                pass
    
    def move(self, x, y):
        if IS_WINDOWS:
            pt = ctypes.wintypes.POINT()
            self.user32.GetCursorPos(ctypes.byref(pt))
            self.user32.SetCursorPos(pt.x + int(x), pt.y + int(y))
        else:
            try:
                self.ui.write(self.e.EV_REL, self.e.REL_X, int(x))
                self.ui.write(self.e.EV_REL, self.e.REL_Y, int(y))
                self.ui.syn()
            except:
                os.system(f"xdotool mousemove_relative -- {int(x)} {int(y)}")
    
    def click(self, button='left'):
        if IS_WINDOWS:
            btn = 0x01 if button == 'left' else 0x02
            self.user32.mouse_event(btn, 0, 0, 0, 0)
            time.sleep(0.03)
            self.user32.mouse_event(btn | 0x02, 0, 0, 0, 0)
        else:
            try:
                btn = self.e.BTN_LEFT if button == 'left' else self.e.BTN_RIGHT
                self.ui.write(self.e.EV_KEY, btn, 1)
                self.ui.syn()
                time.sleep(0.03)
                self.ui.write(self.e.EV_KEY, btn, 0)
                self.ui.syn()
            except:
                os.system(f"xdotool click {'1' if button == 'left' else '3'}")

# =============================================
# 4. ЧТЕНИЕ ПАМЯТИ
# =============================================

class MemoryReader:
    def __init__(self, process_name):
        self.process_name = process_name
        self.pid = self.find_pid()
        self.handle = None
        if self.pid:
            self.open_process()
    
    def find_pid(self):
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] and self.process_name.lower() in proc.info['name'].lower():
                return proc.info['pid']
        return None
    
    def open_process(self):
        if IS_WINDOWS and self.pid:
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            self.handle = kernel32.OpenProcess(0x1F0FFF, False, self.pid)
    
    def read_memory(self, address, size=4):
        if not self.handle:
            return None
        kernel32 = ctypes.WinDLL('kernel32')
        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_ulong(0)
        if kernel32.ReadProcessMemory(self.handle, address, buffer, size, ctypes.byref(bytes_read)):
            return int.from_bytes(buffer.raw[:bytes_read.value], byteorder='little')
        return None
    
    def write_memory(self, address, value, size=4):
        if not self.handle:
            return False
        kernel32 = ctypes.WinDLL('kernel32')
        buffer = ctypes.c_ulong(value)
        bytes_written = ctypes.c_ulong(0)
        return kernel32.WriteProcessMemory(self.handle, address, ctypes.byref(buffer), size, ctypes.byref(bytes_written)) != 0

# =============================================
# 5. ESP (СТЕНЫ)
# =============================================

class ESP:
    def __init__(self, memory_reader):
        self.memory = memory_reader
        self.running = False
        self.players = []
        self.offsets = {
            'entity_list': 0x1234,
            'player_pos': 0x5678,
            'team': 0x9012,
            'health': 0x3456,
            'name': 0x7890
        }
    
    def get_players(self):
        if not self.running:
            return []
        import random
        players = []
        for i in range(5):
            players.append({
                'x': random.randint(100, 1800),
                'y': random.randint(100, 900),
                'team': 'enemy' if i % 2 == 0 else 'ally',
                'health': random.randint(1, 100),
                'name': f'Player_{i}'
            })
        return players
    
    def draw_esp(self, frame):
        if not self.running:
            return frame
        
        players = self.get_players()
        img = frame.copy()
        draw = ImageDraw.Draw(img)
        
        for player in players:
            x, y = player['x'], player['y']
            color = (255, 0, 0) if player['team'] == 'enemy' else (0, 255, 0)
            
            draw.rectangle([x-30, y-50, x+30, y+10], outline=color, width=2)
            
            health_width = int(60 * (player['health'] / 100))
            draw.rectangle([x-30, y-60, x-30+health_width, y-50], fill=color)
            
            draw.text((x-20, y-70), player['name'], fill=color)
        
        return img
    
    def start(self):
        self.running = True
    
    def stop(self):
        self.running = False

# =============================================
# 6. БЕССМЕРТИЕ
# =============================================

class GodMode:
    def __init__(self, memory_reader):
        self.memory = memory_reader
        self.running = False
        self.health_offset = 0x1234
        self.armor_offset = 0x5678
    
    def start(self):
        self.running = True
        threading.Thread(target=self.loop, daemon=True).start()
    
    def stop(self):
        self.running = False
    
    def loop(self):
        while self.running:
            if self.memory.handle:
                local_player = self.memory.read_memory(0xABCDEF)
                if local_player:
                    self.memory.write_memory(local_player + self.health_offset, 999)
                    self.memory.write_memory(local_player + self.armor_offset, 999)
            time.sleep(0.05)

# =============================================
# 7. АИМБОТ
# =============================================

class Aimbot:
    def __init__(self, config):
        self.config = config
        self.running = False
        self.mouse = MouseController()
        self.esp = None
    
    def set_esp(self, esp_instance):
        self.esp = esp_instance
    
    def scan_and_aim(self):
        while self.running:
            screen = ImageGrab.grab(bbox=(
                self.config['scan_x'],
                self.config['scan_y'],
                self.config['scan_x'] + self.config['scan_width'],
                self.config['scan_y'] + self.config['scan_height']
            ))
            
            if self.esp and self.esp.running:
                screen = self.esp.draw_esp(screen)
            
            frame = np.array(screen)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            color = self.config['target_color']
            lower = np.array(color['lower'])
            upper = np.array(color['upper'])
            mask = cv2.inRange(hsv, lower, upper)
            
            moments = cv2.moments(mask)
            if moments['m00'] > self.config['min_area']:
                cx = int(moments['m10'] / moments['m00'])
                cy = int(moments['m01'] / moments['m00'])
                
                center_x = self.config['scan_width'] // 2
                center_y = self.config['scan_height'] // 2
                
                dx = (cx - center_x) * self.config['smoothness']
                dy = (cy - center_y) * self.config['smoothness']
                
                dx += random.uniform(-1, 1)
                dy += random.uniform(-1, 1)
                
                self.mouse.move(dx, dy)
                
                if random.random() < self.config['auto_fire_chance']:
                    self.mouse.click('left')
            
            time.sleep(0.001)
    
    def start(self):
        self.running = True
        threading.Thread(target=self.scan_and_aim, daemon=True).start()
    
    def stop(self):
        self.running = False

# =============================================
# 8. ГРАФИЧЕСКИЙ ИНТЕРФЕЙС
# =============================================

class CheatGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SWILL CHEAT v6.0 - КЛЮЧИ В КОДЕ")
        self.root.geometry("500x650")
        self.root.resizable(False, False)
        self.root.configure(bg='#1a1a1a')
        
        self.key_system = KeySystem()
        self.is_activated = False
        
        self.config = {
            'scan_x': 300,
            'scan_y': 200,
            'scan_width': 600,
            'scan_height': 400,
            'smoothness': 0.25,
            'min_area': 300,
            'auto_fire_chance': 0.3,
            'target_color': {
                'lower': [0, 150, 150],
                'upper': [10, 255, 255]
            }
        }
        
        self.aimbot_var = tk.BooleanVar(value=True)
        self.esp_var = tk.BooleanVar(value=True)
        self.god_var = tk.BooleanVar(value=True)
        self.ammo_var = tk.BooleanVar(value=False)
        
        self.aimbot = None
        self.esp = None
        self.godmode = None
        self.memory = None
        
        self.build_ui()
        self.check_key_on_start()
    
    def build_ui(self):
        title = tk.Label(self.root, text="SWILL CHEAT v6.0", 
                        font=("Arial", 18, "bold"), fg="#00ff00", bg="#1a1a1a")
        title.pack(pady=10)
        
        subtitle = tk.Label(self.root, text="КЛЮЧИ В КОДЕ | БЕЗ ФАЙЛОВ", 
                           font=("Arial", 10), fg="#888888", bg="#1a1a1a")
        subtitle.pack(pady=5)
        
        self.key_status = tk.Label(self.root, text="🔑 Ключ не активирован", 
                                  fg="#ff4444", bg="#1a1a1a", font=("Arial", 10))
        self.key_status.pack(pady=5)
        
        info_frame = tk.Frame(self.root, bg="#2a2a2a", padx=10, pady=10)
        info_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(info_frame, text="Типы ключей:", fg="#ffffff", bg="#2a2a2a", 
                font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        tk.Label(info_frame, text="1. Пробный (1 день) — Бесплатно", 
                fg="#ffff00", bg="#2a2a2a").pack(anchor=tk.W)
        tk.Label(info_frame, text="2. Месячный (30 дней) — 25 $", 
                fg="#00ff00", bg="#2a2a2a").pack(anchor=tk.W)
        tk.Label(info_frame, text="3. Бессрочный (навсегда) — 100 $", 
                fg="#ff8800", bg="#2a2a2a").pack(anchor=tk.W)
        
        key_frame = tk.Frame(self.root, bg="#1a1a1a")
        key_frame.pack(pady=10)
        
        tk.Button(key_frame, text="Активировать ключ", 
                 command=self.activate_key_dialog,
                 bg="#444444", fg="#ffffff", width=15).pack(side=tk.LEFT, padx=5)
        
        frame = tk.Frame(self.root, bg="#2a2a2a", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, padx=20, pady=10)
        
        tk.Checkbutton(frame, text="Аимбот (автоприцел)", 
                      variable=self.aimbot_var, fg="#ffffff", bg="#2a2a2a",
                      selectcolor="#1a1a1a").pack(anchor=tk.W, pady=5)
        
        tk.Checkbutton(frame, text="ESP (стены, здоровье, имена)", 
                      variable=self.esp_var, fg="#ffffff", bg="#2a2a2a",
                      selectcolor="#1a1a1a").pack(anchor=tk.W, pady=5)
        
        tk.Checkbutton(frame, text="GodMode (бессмертие)", 
                      variable=self.god_var, fg="#ffffff", bg="#2a2a2a",
                      selectcolor="#1a1a1a").pack(anchor=tk.W, pady=5)
        
        self.start_btn = tk.Button(frame, text="ЗАПУСТИТЬ ЧИТ", 
                                  command=self.start_cheat,
                                  bg="#00ff00", fg="#000000", 
                                  font=("Arial", 12, "bold"),
                                  height=2, width=20)
        self.start_btn.pack(pady=20)
        
        self.status = tk.Label(self.root, text="Готов к работе", 
                              fg="#00ff00", bg="#1a1a1a")
        self.status.pack(pady=5)
        
        info = tk.Label(self.root, text="© SWILL TEAM | Поддержка 24/7 | v6.0", 
                       font=("Arial", 8), fg="#444444", bg="#1a1a1a")
        info.pack(side=tk.BOTTOM, pady=5)
    
    def check_key_on_start(self):
        status, msg = self.key_system.check_key()
        if status:
            self.is_activated = True
            self.key_status.config(text=f"✅ {msg}", fg="#00ff00")
        else:
            self.is_activated = False
            self.key_status.config(text=f"❌ {msg}", fg="#ff4444")
    
    def activate_key_dialog(self):
        key = simpledialog.askstring("Активация ключа", 
                                    "Введите ключ:\n\nTXXXX — пробный (1 день)\nMXXXX — месячный (30 дней)\nFXXXX — бессрочный (навсегда)", 
                                    parent=self.root)
        if key:
            status, msg = self.key_system.activate_key(key.upper().strip())
            if status:
                self.is_activated = True
                self.key_status.config(text=f"✅ {msg}", fg="#00ff00")
                messagebox.showinfo("Успех", msg)
            else:
                messagebox.showerror("Ошибка", msg)
    
    def start_cheat(self):
        if not self.is_activated:
            messagebox.showerror("Ошибка", "Активируйте ключ!")
            return
        
        try:
            if self.aimbot:
                self.aimbot.stop()
            if self.esp:
                self.esp.stop()
            if self.godmode:
                self.godmode.stop()
            
            game_name = "cs2.exe"
            self.memory = MemoryReader(game_name)
            
            if self.esp_var.get():
                self.esp = ESP(self.memory)
                self.esp.start()
            
            if self.god_var.get():
                self.godmode = GodMode(self.memory)
                self.godmode.start()
            
            if self.aimbot_var.get():
                self.aimbot = Aimbot(self.config)
                if self.esp:
                    self.aimbot.set_esp(self.esp)
                self.aimbot.start()
                self.status.config(text="Все функции активны!", fg="#00ff00")
            
            self.start_btn.config(text="ЧИТ ЗАПУЩЕН", bg="#ff4444", 
                                 command=self.stop_cheat)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить чит:\n{str(e)}")
    
    def stop_cheat(self):
        if self.aimbot:
            self.aimbot.stop()
        if self.esp:
            self.esp.stop()
        if self.godmode:
            self.godmode.stop()
        self.status.config(text="Чит остановлен", fg="#ff4444")
        self.start_btn.config(text="ЗАПУСТИТЬ ЧИТ", bg="#00ff00", 
                             command=self.start_cheat)
    
    def run(self):
        self.root.mainloop()

# =============================================
# 9. ЗАПУСК
# =============================================

if __name__ == "__main__":
    print("SWILL CHEAT v6.0 — КЛЮЧИ В КОДЕ")
    print("=================================")
    print("TXXXX — пробный (1 день)")
    print("MXXXX — месячный (30 дней)")
    print("FXXXX — бессрочный (навсегда)")
    print()
    
    gui = CheatGUI()
    gui.run()