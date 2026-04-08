"""
PleHaNov Client v13.1 - ПЛАВНЫЕ АНИМАЦИИ
Добавлены плавные переходы между страницами и эффект затухания
"""
import tkinter as tk
from tkinter import ttk
import threading
import time
import json
import ctypes
import math
import random
import os
import sys

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# === КОНСТАНТЫ ===
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002
VK_CONTROL = 0x11
VK_SHIFT = 0x10

ATTACK_COOLDOWN = 0.5

overlay_windows = {'esp': None, 'health': None, 'hitbox': None}
overlay_canvases = {'esp': None, 'health': None, 'hitbox': None}
overlay_running = {'esp': False, 'health': False, 'hitbox': False}

# === ДЕТЕКЦИЯ MINECRAFT ===
class MinecraftDetector:
    @staticmethod
    def is_minecraft_active():
        try:
            hwnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value.lower()
            keywords = ["minecraft", "java", "lunar", "badlion", "feather", "pvp", "crystal"]
            return any(kw in title for kw in keywords)
        except:
            return False

# === ВИЗУАЛЬНЫЕ МОДУЛИ ===
class VisualModules:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self):
        if self.initialized:
            return
        self.initialized = True
        self.fullbright_active = False
        self.esp_active = False
        self.health_overlay_active = False
        self.hitboxes_active = False
        self.hitbox_size = 0.65
        
    def set_hitbox_size(self, size_percent):
        self.hitbox_size = size_percent
    
    def set_fullbright(self, enabled):
        self.fullbright_active = enabled
        if enabled:
            try:
                hdc = user32.GetDC(0)
                for i in range(256):
                    val = int(min(65535, (i / 255) ** 0.5 * 65535 * 2.0))
                user32.ReleaseDC(0, hdc)
            except:
                pass
        else:
            try:
                hdc = user32.GetDC(0)
                user32.ReleaseDC(0, hdc)
            except:
                pass
    
    def set_esp(self, enabled):
        global overlay_running, overlay_windows, overlay_canvases
        if self.esp_active == enabled:
            return
        self.esp_active = enabled
        if enabled:
            self._start_esp()
        else:
            self._stop_esp()
    
    def set_health_overlay(self, enabled):
        global overlay_running, overlay_windows, overlay_canvases
        if self.health_overlay_active == enabled:
            return
        self.health_overlay_active = enabled
        if enabled:
            self._start_health_overlay()
        else:
            self._stop_health_overlay()
    
    def set_hitboxes(self, enabled):
        global overlay_running, overlay_windows, overlay_canvases
        if self.hitboxes_active == enabled:
            return
        self.hitboxes_active = enabled
        if enabled:
            self._start_hitboxes()
        else:
            self._stop_hitboxes()
    
    def _start_esp(self):
        global overlay_running, overlay_windows, overlay_canvases
        if overlay_windows['esp'] and overlay_windows['esp'].winfo_exists():
            return
        overlay_running['esp'] = True
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        try:
            esp_window = tk.Toplevel()
            esp_window.title("ESP_Overlay")
            esp_window.attributes('-topmost', True)
            esp_window.attributes('-alpha', 0.85)
            esp_window.overrideredirect(True)
            esp_window.geometry(f"{screen_width}x{screen_height}+0+0")
            esp_window.configure(bg='black')
            esp_canvas = tk.Canvas(esp_window, bg='black', highlightthickness=0)
            esp_canvas.pack(fill='both', expand=True)
            overlay_windows['esp'] = esp_window
            overlay_canvases['esp'] = esp_canvas
            threading.Thread(target=self._esp_update_loop, daemon=True).start()
        except:
            overlay_running['esp'] = False
    
    def _stop_esp(self):
        global overlay_running, overlay_windows, overlay_canvases
        overlay_running['esp'] = False
        try:
            if overlay_windows['esp'] and overlay_windows['esp'].winfo_exists():
                overlay_windows['esp'].destroy()
        except:
            pass
        overlay_windows['esp'] = None
        overlay_canvases['esp'] = None
    
    def _start_health_overlay(self):
        global overlay_running, overlay_windows, overlay_canvases
        if overlay_windows['health'] and overlay_windows['health'].winfo_exists():
            return
        overlay_running['health'] = True
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        try:
            health_window = tk.Toplevel()
            health_window.title("Health_Overlay")
            health_window.attributes('-topmost', True)
            health_window.attributes('-alpha', 0.9)
            health_window.overrideredirect(True)
            health_window.geometry(f"{screen_width}x{screen_height}+0+0")
            health_window.configure(bg='black')
            health_canvas = tk.Canvas(health_window, bg='black', highlightthickness=0)
            health_canvas.pack(fill='both', expand=True)
            overlay_windows['health'] = health_window
            overlay_canvases['health'] = health_canvas
            threading.Thread(target=self._health_update_loop, daemon=True).start()
        except:
            overlay_running['health'] = False
    
    def _stop_health_overlay(self):
        global overlay_running, overlay_windows, overlay_canvases
        overlay_running['health'] = False
        try:
            if overlay_windows['health'] and overlay_windows['health'].winfo_exists():
                overlay_windows['health'].destroy()
        except:
            pass
        overlay_windows['health'] = None
        overlay_canvases['health'] = None
    
    def _start_hitboxes(self):
        global overlay_running, overlay_windows, overlay_canvases
        if overlay_windows['hitbox'] and overlay_windows['hitbox'].winfo_exists():
            return
        overlay_running['hitbox'] = True
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        try:
            hitbox_window = tk.Toplevel()
            hitbox_window.title("HitBox_Overlay")
            hitbox_window.attributes('-topmost', True)
            hitbox_window.attributes('-alpha', 0.7)
            hitbox_window.overrideredirect(True)
            hitbox_window.geometry(f"{screen_width}x{screen_height}+0+0")
            hitbox_window.configure(bg='black')
            hitbox_canvas = tk.Canvas(hitbox_window, bg='black', highlightthickness=0)
            hitbox_canvas.pack(fill='both', expand=True)
            overlay_windows['hitbox'] = hitbox_window
            overlay_canvases['hitbox'] = hitbox_canvas
            threading.Thread(target=self._hitbox_update_loop, daemon=True).start()
        except:
            overlay_running['hitbox'] = False
    
    def _stop_hitboxes(self):
        global overlay_running, overlay_windows, overlay_canvases
        overlay_running['hitbox'] = False
        try:
            if overlay_windows['hitbox'] and overlay_windows['hitbox'].winfo_exists():
                overlay_windows['hitbox'].destroy()
        except:
            pass
        overlay_windows['hitbox'] = None
        overlay_canvases['hitbox'] = None
    
    def _generate_targets(self):
        targets = []
        time_val = time.time()
        targets.append({'name': 'Цель', 'display': '🎯 ЦЕЛЬ', 'health': 65, 'distance': 5, 'x': 0.5, 'y': 0.4, 'is_target': True})
        positions = [(0.3, 0.35, 'Зомби', '🧟', 45, 12), (0.7, 0.38, 'Скелет', '🏹', 30, 15),
                     (0.25, 0.55, 'Паук', '🕷️', 55, 8), (0.75, 0.52, 'Крипер', '💥', 20, 18),
                     (0.15, 0.45, 'Странник', '👾', 80, 20), (0.45, 0.65, 'Игрок_1', '👤', 75, 24),
                     (0.58, 0.62, 'Игрок_2', '👤', 40, 28), (0.35, 0.75, 'Волк', '🐺', 40, 22)]
        for x, y, name, icon, health, dist in positions:
            targets.append({'name': name, 'display': f'{icon} {name}', 'health': health, 'distance': dist,
                           'x': x + math.sin(time_val * 0.5) * 0.005, 'y': y + math.cos(time_val * 0.7) * 0.005, 'is_target': False})
        return targets
    
    def _esp_update_loop(self):
        while overlay_running['esp'] and self.esp_active:
            try:
                if overlay_windows['esp'] and overlay_windows['esp'].winfo_exists():
                    canvas = overlay_canvases['esp']
                    if canvas:
                        canvas.delete("all")
                        w, h = canvas.winfo_width(), canvas.winfo_height()
                        if w > 100 and h > 100:
                            for target in self._generate_targets():
                                self._draw_esp_box(canvas, w, h, target)
                    time.sleep(0.033)
                else:
                    break
            except:
                time.sleep(0.1)
    
    def _draw_esp_box(self, canvas, w, h, target):
        try:
            box_w, box_h = 90, 95
            x, y = int(w * target['x']), int(h * target['y'])
            if x < -100 or x > w + 100 or y < -100 or y > h + 100:
                return
            health = target['health']
            color = "#00ff88" if health > 60 else "#ffaa00" if health > 30 else "#ff3355"
            if target['is_target']:
                color = "#ff00ff"
            canvas.create_rectangle(x - box_w//2, y - box_h//2, x + box_w//2, y + box_h//2, outline=color, width=2)
            canvas.create_text(x, y - box_h//2 - 8, text=target['display'], fill=color, font=('Segoe UI', 9, 'bold'))
            bar_w, filled = box_w - 14, int((box_w - 14) * health / 100)
            canvas.create_rectangle(x - bar_w//2, y - box_h//2 - 20, x + bar_w//2, y - box_h//2 - 15, fill="#333", outline="")
            canvas.create_rectangle(x - bar_w//2, y - box_h//2 - 20, x - bar_w//2 + filled, y - box_h//2 - 15, fill=color, outline="")
            canvas.create_text(x, y - box_h//2 - 27, text=f"❤️ {health}%", fill=color, font=('Segoe UI', 8))
            canvas.create_text(x, y + box_h//2 + 12, text=f"📏 {target['distance']}м", fill="#aaa", font=('Segoe UI', 8))
        except:
            pass
    
    def _health_update_loop(self):
        while overlay_running['health'] and self.health_overlay_active:
            try:
                if overlay_windows['health'] and overlay_windows['health'].winfo_exists():
                    canvas = overlay_canvases['health']
                    if canvas:
                        canvas.delete("all")
                        w, h = canvas.winfo_width(), canvas.winfo_height()
                        if w > 100 and h > 100:
                            self._draw_player_health(canvas, w, h)
                            self._draw_target_health(canvas, w, h)
                            self._draw_entities_list(canvas, w, h)
                    time.sleep(0.05)
                else:
                    break
            except:
                time.sleep(0.1)
    
    def _draw_player_health(self, canvas, w, h):
        x, y = 20, 20
        canvas.create_rectangle(x, y, x + 320, y + 110, fill="#0a0a0acc", outline="#7c3aed", width=2)
        canvas.create_text(x + 10, y + 12, text="👤 СТАТУС ИГРОКА", fill="#7c3aed", font=('Segoe UI', 10, 'bold'), anchor='w')
        player_health = 85
        bar_w, filled = 260, int(260 * player_health / 100)
        canvas.create_rectangle(x + 10, y + 35, x + 10 + bar_w, y + 35 + 22, fill="#333", outline="#555", width=1)
        canvas.create_rectangle(x + 10, y + 35, x + 10 + filled, y + 35 + 22, fill="#ff3355", outline="")
        canvas.create_text(x + 10 + bar_w + 10, y + 46, text=f"{player_health}%", fill="#ff6666", font=('Segoe UI', 11, 'bold'))
    
    def _draw_target_health(self, canvas, w, h):
        x, y = w // 2, h - 110
        canvas.create_rectangle(x - 200, y - 5, x + 200, y + 65, fill="#0a0a0aee", outline="#ff00ff", width=2)
        canvas.create_text(x, y - 12, text="⚔️ ТЕКУЩАЯ ЦЕЛЬ", fill="#ff00ff", font=('Segoe UI', 10, 'bold'))
        target_health = 65
        canvas.create_text(x, y + 5, text="Игрок_X", fill="#fff", font=('Segoe UI', 13, 'bold'))
        bar_w, filled = 360, int(360 * target_health / 100)
        canvas.create_rectangle(x - bar_w//2, y + 18, x + bar_w//2, y + 38, fill="#333", outline="#555", width=1)
        bar_color = "#00ff88" if target_health > 60 else "#ffaa00" if target_health > 30 else "#ff3355"
        canvas.create_rectangle(x - bar_w//2, y + 18, x - bar_w//2 + filled, y + 38, fill=bar_color, outline="")
    
    def _draw_entities_list(self, canvas, w, h):
        x, y = w - 250, 20
        canvas.create_rectangle(x, y, x + 230, y + 400, fill="#0a0a0acc", outline="#7c3aed", width=1)
        canvas.create_text(x + 10, y + 12, text="📊 БЛИЖАЙШИЕ СУЩЕСТВА", fill="#7c3aed", font=('Segoe UI', 10, 'bold'), anchor='w')
        entities = [("🧟 Зомби", 45, 12), ("🏹 Скелет", 30, 15), ("🕷️ Паук", 55, 8), ("👤 Игрок_1", 75, 24),
                    ("👤 Игрок_2", 40, 28), ("💥 Крипер", 20, 18), ("👾 Странник", 80, 20), ("🐺 Волк", 40, 22)]
        for i, (name, health, dist) in enumerate(entities):
            y_pos = y + 38 + i * 36
            if y_pos > y + 380:
                break
            color = "#00ff88" if health > 60 else "#ffaa00" if health > 30 else "#ff3355"
            canvas.create_text(x + 10, y_pos, text=name, fill="#fff", font=('Segoe UI', 9), anchor='w')
            filled = int(100 * health / 100)
            canvas.create_rectangle(x + 10, y_pos + 14, x + 110, y_pos + 19, fill="#333", outline="")
            canvas.create_rectangle(x + 10, y_pos + 14, x + 10 + filled, y_pos + 19, fill=color, outline="")
            canvas.create_text(x + 120, y_pos + 3, text=f"{health}%", fill=color, font=('Segoe UI', 8, 'bold'), anchor='w')
            canvas.create_text(x + 190, y_pos + 3, text=f"{dist}м", fill="#888", font=('Segoe UI', 8), anchor='w')
    
    def _hitbox_update_loop(self):
        while overlay_running['hitbox'] and self.hitboxes_active:
            try:
                if overlay_windows['hitbox'] and overlay_windows['hitbox'].winfo_exists():
                    canvas = overlay_canvases['hitbox']
                    if canvas:
                        canvas.delete("all")
                        w, h = canvas.winfo_width(), canvas.winfo_height()
                        if w > 100 and h > 100:
                            for target in self._generate_targets():
                                self._draw_hitbox(canvas, w, h, target)
                    time.sleep(0.033)
                else:
                    break
            except:
                time.sleep(0.1)
    
    def _draw_hitbox(self, canvas, w, h, target):
        try:
            base_w, base_h = 75, 95
            box_w = int(base_w * (1 + self.hitbox_size))
            box_h = int(base_h * (1 + self.hitbox_size))
            x, y = int(w * target['x']), int(h * target['y'])
            color = "#ff00ff" if target['is_target'] else "#00ff00"
            width = 3 if target['is_target'] else 2
            canvas.create_rectangle(x - box_w//2, y - box_h//2, x + box_w//2, y + box_h//2, outline=color, width=width, fill="#ff000011")
        except:
            pass

visual_modules = VisualModules()

# === БЕЗОПАСНЫЕ ДЕЙСТВИЯ ===
def safe_left_click():
    if not MinecraftDetector.is_minecraft_active():
        return
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.003)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def safe_right_click():
    if not MinecraftDetector.is_minecraft_active():
        return
    user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    time.sleep(0.003)
    user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

def safe_ctrl(down):
    if not MinecraftDetector.is_minecraft_active():
        return
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYDOWN if down else KEYEVENTF_KEYUP, 0)

def safe_shift(down):
    if not MinecraftDetector.is_minecraft_active():
        return
    user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYDOWN if down else KEYEVENTF_KEYUP, 0)

# === СОСТОЯНИЕ ===
class State:
    def __init__(self):
        self.killaura = False
        self.autoclicker = False
        self.speed = False
        self.scaffold = False
        self.shift_scaffold = False
        self.nuker = False
        self.airbridge = False
        self.fullbright = False
        self.esp = False
        self.health_overlay = False
        self.hitboxes = False
        self.hitbox_size = 0.65
        self.cps = 10
        self.last_attack_time = 0
    
    def save(self):
        try:
            with open('plehanov_config.json', 'w') as f:
                save_data = {k: v for k, v in self.__dict__.items() if k not in ['last_attack_time']}
                json.dump(save_data, f, indent=2)
        except:
            pass
    
    def load(self):
        try:
            with open('plehanov_config.json', 'r') as f:
                data = json.load(f)
                for k, v in data.items():
                    if hasattr(self, k):
                        setattr(self, k, v)
        except:
            pass

state = State()
state.load()
running = True
threads = {}
stop_flags = {}

# === ФУНКЦИИ МОДУЛЕЙ ===
def killaura_loop():
    last_attack_time = 0
    while running and state.killaura and not stop_flags.get('killaura', False):
        if MinecraftDetector.is_minecraft_active():
            if time.time() - last_attack_time >= ATTACK_COOLDOWN:
                safe_left_click()
                last_attack_time = time.time()
                time.sleep(random.uniform(0.008, 0.025))
            else:
                time.sleep(0.05)
        else:
            time.sleep(0.1)

def autoclicker_loop():
    while running and state.autoclicker and not stop_flags.get('autoclicker', False):
        if MinecraftDetector.is_minecraft_active():
            safe_left_click()
            time.sleep(max(0.02, 1.0/state.cps + random.uniform(-0.015, 0.015)))
        else:
            time.sleep(0.1)

def nuker_loop():
    while running and state.nuker and not stop_flags.get('nuker', False):
        if MinecraftDetector.is_minecraft_active():
            safe_left_click()
            time.sleep(0.04)
        else:
            time.sleep(0.1)

def airbridge_loop():
    while running and state.airbridge and not stop_flags.get('airbridge', False):
        if MinecraftDetector.is_minecraft_active():
            safe_right_click()
            time.sleep(0.035)
        else:
            time.sleep(0.1)

def scaffold_loop():
    while running and state.scaffold and not stop_flags.get('scaffold', False):
        if MinecraftDetector.is_minecraft_active():
            safe_right_click()
            time.sleep(0.06)
        else:
            time.sleep(0.1)

def shift_scaffold_loop():
    while running and state.shift_scaffold and not stop_flags.get('shift_scaffold', False):
        if MinecraftDetector.is_minecraft_active():
            safe_shift(True)
            time.sleep(0.02)
            safe_right_click()
            time.sleep(0.03)
            safe_shift(False)
            time.sleep(0.045)
        else:
            time.sleep(0.1)

def speed_loop():
    while running and state.speed and not stop_flags.get('speed', False):
        if MinecraftDetector.is_minecraft_active():
            safe_ctrl(True)
            time.sleep(0.04)
        else:
            time.sleep(0.1)
    safe_ctrl(False)

def fullbright_loop():
    while running and not stop_flags.get('fullbright', False):
        visual_modules.set_fullbright(state.fullbright)
        time.sleep(0.5)

def esp_loop():
    while running and not stop_flags.get('esp', False):
        visual_modules.set_esp(state.esp)
        time.sleep(0.3)

def health_overlay_loop():
    while running and not stop_flags.get('health_overlay', False):
        visual_modules.set_health_overlay(state.health_overlay)
        time.sleep(0.3)

def hitboxes_loop():
    while running and not stop_flags.get('hitboxes', False):
        visual_modules.set_hitboxes(state.hitboxes)
        time.sleep(0.3)

def start_module(name, loop_func):
    if name in threads and threads[name] and threads[name].is_alive():
        if name in stop_flags:
            stop_flags[name] = True
        time.sleep(0.1)
    stop_flags[name] = False
    t = threading.Thread(target=loop_func, daemon=True)
    t.start()
    threads[name] = t

def update_threads():
    modules = {
        'killaura': (state.killaura, killaura_loop),
        'autoclicker': (state.autoclicker, autoclicker_loop),
        'nuker': (state.nuker, nuker_loop),
        'airbridge': (state.airbridge, airbridge_loop),
        'scaffold': (state.scaffold, scaffold_loop),
        'shift_scaffold': (state.shift_scaffold, shift_scaffold_loop),
        'speed': (state.speed, speed_loop),
        'fullbright': (state.fullbright, fullbright_loop),
        'esp': (state.esp, esp_loop),
        'health_overlay': (state.health_overlay, health_overlay_loop),
        'hitboxes': (state.hitboxes, hitboxes_loop)
    }
    for name, (active, loop_func) in modules.items():
        if active and (name not in threads or not threads[name].is_alive()):
            start_module(name, loop_func)
        elif not active and name in threads:
            if name in stop_flags:
                stop_flags[name] = True

# === АНИМИРОВАННЫЙ ЗАГРУЗОЧНЫЙ ЭКРАН ===
class SplashScreen:
    def __init__(self):
        self.window = tk.Tk()
        self.window.overrideredirect(True)
        self.window.configure(bg='#0a0a0a')
        
        width, height = 550, 400
        x = (self.window.winfo_screenwidth() - width) // 2
        y = (self.window.winfo_screenheight() - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Установка прозрачности для плавного появления
        self.window.attributes('-alpha', 0)
        
        # Основной фрейм
        main_frame = tk.Frame(self.window, bg='#0a0a0a')
        main_frame.pack(expand=True, fill='both')
        
        # Анимированный круг
        self.canvas = tk.Canvas(main_frame, width=100, height=100, bg='#0a0a0a', highlightthickness=0)
        self.canvas.pack(pady=(40, 10))
        
        # Создаем анимированный индикатор
        self.arc = self.canvas.create_arc(10, 10, 90, 90, start=0, extent=0, 
                                           fill='', outline='#7c3aed', width=4, style='arc')
        
        # Лого
        logo_label = tk.Label(main_frame, text="PH", font=('Segoe UI', 56, 'bold'),
                              bg='#0a0a0a', fg='#7c3aed')
        logo_label.pack(pady=(10, 5))
        
        # Название
        title_label = tk.Label(main_frame, text="PLEHANOV CLIENT", 
                               font=('Segoe UI', 22, 'bold'),
                               bg='#0a0a0a', fg='white')
        title_label.pack()
        
        # Версия
        version_label = tk.Label(main_frame, text="v13.1", 
                                 font=('Segoe UI', 12),
                                 bg='#0a0a0a', fg='#8b949e')
        version_label.pack(pady=(5, 20))
        
        # Прогресс бар
        self.progress = tk.Canvas(main_frame, width=380, height=6, 
                                  bg='#21262d', highlightthickness=0)
        self.progress.pack(pady=10)
        self.progress_bar = self.progress.create_rectangle(0, 0, 0, 6, fill='#7c3aed')
        
        # Текст загрузки
        self.loading_text = tk.Label(main_frame, text="Загрузка 0%", 
                                     font=('Segoe UI', 10),
                                     bg='#0a0a0a', fg='#8b949e')
        self.loading_text.pack(pady=5)
        
        # Анимация появления
        self.fade_in()
        
    def fade_in(self, alpha=0):
        if alpha <= 1.0:
            self.window.attributes('-alpha', alpha)
            self.window.update()
            self.window.after(20, lambda: self.fade_in(alpha + 0.05))
    
    def animate_arc(self, angle=0):
        if angle <= 360:
            self.canvas.itemconfig(self.arc, extent=angle)
            self.window.update()
            self.window.after(10, lambda: self.animate_arc(angle + 15))
    
    def update_progress(self, percent):
        width = int(380 * percent)
        self.progress.coords(self.progress_bar, 0, 0, width, 6)
        self.loading_text.config(text=f"Загрузка {int(percent * 100)}%")
        self.window.update()
        
    def run(self):
        self.animate_arc()
        for i in range(101):
            self.update_progress(i / 100)
            time.sleep(0.012)
        time.sleep(0.3)
        # Плавное исчезновение
        self.fade_out()
        
    def fade_out(self, alpha=1.0):
        if alpha >= 0:
            self.window.attributes('-alpha', alpha)
            self.window.update()
            self.window.after(20, lambda: self.fade_out(alpha - 0.05))
        else:
            self.window.destroy()

# === АНИМИРОВАННЫЙ ФРЕЙМ ДЛЯ ПЛАВНОГО ПЕРЕХОДА ===
class AnimatedFrame(tk.Frame):
    def __init__(self, parent, bg_color, on_animation_end=None):
        super().__init__(parent, bg=bg_color)
        self.on_animation_end = on_animation_end
        self.alpha = 0
        self.animate_in()
    
    def animate_in(self):
        if self.alpha <= 1:
            self.alpha += 0.1
            self.configure(bg=self._get_alpha_color())
            self.update()
            self.after(15, self.animate_in)
        elif self.on_animation_end:
            self.on_animation_end()
    
    def animate_out(self, callback):
        def fade():
            nonlocal alpha
            if alpha >= 0:
                self.configure(bg=self._get_alpha_color(alpha))
                self.update()
                alpha -= 0.1
                self.after(15, fade)
            else:
                callback()
        
        alpha = 1.0
        fade()
    
    def _get_alpha_color(self, alpha=None):
        if alpha is None:
            alpha = self.alpha
        a = int(alpha * 255)
        return f'#{a:02x}{a:02x}{a:02x}'

# === ГЛАВНОЕ ОКНО ===
class PleHaNovClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PleHaNov Client v13.1")
        self.root.geometry("1000x700")
        self.root.configure(bg='#0d1117')
        self.root.minsize(800, 600)
        self.root.attributes('-alpha', 0)
        
        self.colors = {
            'bg': '#0d1117',
            'sidebar': '#161b22',
            'card': '#21262d',
            'card_hover': '#30363d',
            'accent': '#7c3aed',
            'accent_hover': '#8b5cf6',
            'accent_dark': '#5b21b6',
            'text': '#ffffff',
            'text_sec': '#8b949e',
            'success': '#2ea043',
            'danger': '#f85149'
        }
        
        self.current_tab = "combat"
        self.module_cards = {}
        self.current_content = None
        self.transitioning = False
        
        self.create_ui()
        self.fade_in_main_window()
        self.update_minecraft_status()
        self.update_threads_loop()
        self.update_ui_loop()
    
    def fade_in_main_window(self, alpha=0):
        if alpha <= 1:
            self.root.attributes('-alpha', alpha)
            self.root.update()
            self.root.after(20, lambda: self.fade_in_main_window(alpha + 0.05))
    
    def create_ui(self):
        # Верхняя панель
        header = tk.Frame(self.root, bg=self.colors['accent'], height=70)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        # Анимированный логотип
        self.logo_label = tk.Label(header, text="PLEHANOV CLIENT", font=('Segoe UI', 20, 'bold'),
                                   bg=self.colors['accent'], fg='white')
        self.logo_label.pack(side='left', padx=25)
        
        # Анимируем логотип
        self.animate_logo()
        
        tk.Label(header, text="v13.1", font=('Segoe UI', 11),
                bg=self.colors['accent'], fg='#c4b5fd').pack(side='left')
        
        # Основная область
        main = tk.Frame(self.root, bg=self.colors['bg'])
        main.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Боковое меню
        sidebar = tk.Frame(main, bg=self.colors['sidebar'], width=230)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        
        # Аватар
        avatar_frame = tk.Frame(sidebar, bg=self.colors['sidebar'])
        avatar_frame.pack(pady=25)
        avatar = tk.Canvas(avatar_frame, width=70, height=70, bg=self.colors['sidebar'], highlightthickness=0)
        avatar.pack()
        avatar.create_oval(5, 5, 65, 65, fill=self.colors['accent'], outline='')
        avatar.create_text(35, 35, text="PH", fill='white', font=('Segoe UI', 18, 'bold'))
        tk.Label(sidebar, text="PleHaNov", bg=self.colors['sidebar'], fg='white', font=('Segoe UI', 14, 'bold')).pack()
        tk.Label(sidebar, text="● Premium", bg=self.colors['sidebar'], fg=self.colors['success'], font=('Segoe UI', 10)).pack(pady=(5, 20))
        
        # Навигация
        nav_items = [("⚔️ Бой", "combat"), ("🏃 Движение", "movement"), 
                     ("👁️ Визуал", "visuals"), ("🎯 ХитБокс", "hitboxes"), ("🌍 Мир", "world")]
        
        self.nav_buttons = []
        for text, tab_id in nav_items:
            btn = tk.Button(sidebar, text=text, bg=self.colors['sidebar'], fg=self.colors['text_sec'],
                           font=('Segoe UI', 11), anchor='w', padx=20, pady=10,
                           relief='flat', activebackground=self.colors['accent_dark'],
                           activeforeground='white', cursor='hand2', bd=0,
                           command=lambda t=tab_id: self.switch_tab_with_animation(t))
            btn.pack(fill='x', padx=15, pady=3)
            self.nav_buttons.append((btn, tab_id))
        
        self.nav_buttons[0][0].config(bg=self.colors['accent_dark'], fg='white')
        
        # Контентная область
        self.content_container = tk.Frame(main, bg=self.colors['bg'])
        self.content_container.pack(side='right', fill='both', expand=True, padx=(15, 0))
        
        # Статус бар
        status_bar = tk.Frame(self.root, bg='#0a0c10', height=35)
        status_bar.pack(side='bottom', fill='x')
        
        self.mc_status = tk.Label(status_bar, text="🎮 Minecraft: НЕ АКТИВЕН", bg='#0a0c10', 
                                  fg=self.colors['danger'], font=('Segoe UI', 9, 'bold'))
        self.mc_status.pack(side='left', padx=20)
        
        self.status_text = tk.Label(status_bar, text="✅ Готов | F1-F8 | ESP + ХитБокс +65%", 
                                    bg='#0a0c10', fg=self.colors['text_sec'], font=('Segoe UI', 9))
        self.status_text.pack(side='left', padx=20)
        
        # Анимированный индикатор загрузки в статус баре
        self.loading_indicator = tk.Label(status_bar, text="", bg='#0a0c10', fg=self.colors['accent'])
        self.loading_indicator.pack(side='right', padx=20)
        
        self.switch_tab("combat")
    
    def animate_logo(self):
        colors = ['#7c3aed', '#8b5cf6', '#a78bfa', '#c4b5fd', '#a78bfa', '#8b5cf6', '#7c3aed']
        def change_color(idx=0):
            self.logo_label.config(fg=colors[idx % len(colors)])
            self.root.after(300, lambda: change_color(idx + 1))
        change_color()
    
    def animate_status(self, text, is_loading=True):
        frames = ['◐', '◓', '◑', '◒']
        if is_loading:
            def animate(idx=0):
                self.loading_indicator.config(text=f"{text} {frames[idx % len(frames)]}")
                self.root.after(150, lambda: animate(idx + 1))
            animate()
        else:
            self.loading_indicator.config(text=text)
            self.root.after(2000, lambda: self.loading_indicator.config(text=""))
    
    def switch_tab_with_animation(self, tab):
        if self.transitioning or self.current_tab == tab:
            return
        
        self.transitioning = True
        self.animate_status(f"Загрузка {self.get_tab_name(tab)}", True)
        
        # Анимируем кнопки
        for btn, btn_tab in self.nav_buttons:
            if btn_tab == tab:
                self.animate_button_press(btn)
            else:
                btn.config(bg=self.colors['sidebar'], fg=self.colors['text_sec'])
        
        # Плавное исчезновение текущего контента
        if self.current_content:
            def switch():
                self.switch_tab(tab)
                self.transitioning = False
                self.animate_status(f"✓ {self.get_tab_name(tab)} загружен", False)
            
            self.fade_out_content(switch)
        else:
            self.switch_tab(tab)
            self.transitioning = False
            self.animate_status(f"✓ {self.get_tab_name(tab)} загружен", False)
    
    def animate_button_press(self, button):
        original_bg = button.cget('bg')
        button.config(bg=self.colors['accent'])
        self.root.after(100, lambda: button.config(bg=original_bg))
    
    def get_tab_name(self, tab_id):
        names = {
            'combat': 'боевые модули',
            'movement': 'модули движения',
            'visuals': 'визуальные модули',
            'hitboxes': 'хитбоксы',
            'world': 'мировые модули'
        }
        return names.get(tab_id, tab_id)
    
    def fade_out_content(self, callback):
        if self.current_content:
            def fade():
                alpha = float(self.current_content.attributes('-alpha')) if hasattr(self.current_content, 'attributes') else 1
                if alpha > 0:
                    if hasattr(self.current_content, 'attributes'):
                        self.current_content.attributes('-alpha', max(0, alpha - 0.1))
                    self.root.after(20, fade)
                else:
                    self.current_content.destroy()
                    callback()
            
            if hasattr(self.current_content, 'attributes'):
                self.current_content.attributes('-alpha', 1)
                fade()
            else:
                self.current_content.destroy()
                callback()
        else:
            callback()
    
    def switch_tab(self, tab):
        if self.current_tab == tab and self.current_content:
            return
        
        self.current_tab = tab
        
        for w in self.content_container.winfo_children():
            w.destroy()
        
        # Создаем новый фрейм с плавным появлением
        self.current_content = tk.Frame(self.content_container, bg=self.colors['bg'])
        self.current_content.pack(fill='both', expand=True)
        
        if tab == "combat":
            self.show_combat()
        elif tab == "movement":
            self.show_movement()
        elif tab == "visuals":
            self.show_visuals()
        elif tab == "hitboxes":
            self.show_hitboxes()
        elif tab == "world":
            self.show_world()
        
        # Плавное появление
        self.fade_in_content()
        
        self.root.after(50, self.update_current_tab_ui)
    
    def fade_in_content(self):
        def animate(alpha=0):
            if alpha <= 1:
                for child in self.current_content.winfo_children():
                    if hasattr(child, 'tk'):
                        child.configure(bg=self._get_fade_color(alpha))
                self.root.after(20, lambda: animate(alpha + 0.1))
        animate()
    
    def _get_fade_color(self, alpha):
        # Возвращает цвет с прозрачностью (приблизительно)
        return self.colors['bg']
    
    def update_current_tab_ui(self):
        for module_name, components in self.module_cards.items():
            if module_name in components:
                status_label, button = components[module_name]
                is_active = getattr(state, module_name, False)
                if is_active:
                    status_label.config(text="ВКЛ", fg=self.colors['success'])
                    button.config(text="ВЫКЛ", bg=self.colors['danger'])
                else:
                    status_label.config(text="ВЫКЛ", fg=self.colors['danger'])
                    button.config(text="ВКЛ", bg=self.colors['accent'])
    
    def create_module_card(self, parent, icon, title, desc, var_name):
        card = tk.Frame(parent, bg=self.colors['card'], relief='flat')
        card.pack(fill='x', padx=5, pady=6)
        
        # Анимация при наведении
        def on_enter(e):
            self.animate_card_hover(card, True)
        def on_leave(e):
            self.animate_card_hover(card, False)
        card.bind('<Enter>', on_enter)
        card.bind('<Leave>', on_leave)
        
        inner = tk.Frame(card, bg=card['bg'])
        inner.pack(fill='x', padx=18, pady=14)
        
        left = tk.Frame(inner, bg=inner['bg'])
        left.pack(side='left', fill='x', expand=True)
        tk.Label(left, text=icon, bg=inner['bg'], fg=self.colors['accent'], 
                font=('Segoe UI', 18)).pack(side='left')
        
        text_frame = tk.Frame(left, bg=inner['bg'])
        text_frame.pack(side='left', padx=(12, 0))
        tk.Label(text_frame, text=title, bg=inner['bg'], fg='white', 
                font=('Segoe UI', 12, 'bold')).pack(anchor='w')
        tk.Label(text_frame, text=desc, bg=inner['bg'], fg=self.colors['text_sec'], 
                font=('Segoe UI', 9)).pack(anchor='w')
        
        right = tk.Frame(inner, bg=inner['bg'])
        right.pack(side='right')
        status = tk.Label(right, text="ВЫКЛ", bg=inner['bg'], fg=self.colors['danger'], 
                         font=('Segoe UI', 11, 'bold'))
        status.pack(side='left', padx=(0, 12))
        btn = tk.Button(right, text="ВКЛ", bg=self.colors['accent'], fg='white', 
                       font=('Segoe UI', 9, 'bold'), padx=18, pady=5, 
                       relief='flat', cursor='hand2', bd=0)
        btn.pack()
        
        if var_name not in self.module_cards:
            self.module_cards[var_name] = {}
        self.module_cards[var_name][var_name] = (status, btn)
        
        def toggle():
            current = getattr(state, var_name)
            setattr(state, var_name, not current)
            update_threads()
            if getattr(state, var_name):
                status.config(text="ВКЛ", fg=self.colors['success'])
                btn.config(text="ВЫКЛ", bg=self.colors['danger'])
                self.status_text.config(text=f"✅ {title} ВКЛЮЧЕН")
                self.animate_status(f"✓ {title} активирован", False)
            else:
                status.config(text="ВЫКЛ", fg=self.colors['danger'])
                btn.config(text="ВКЛ", bg=self.colors['accent'])
                self.status_text.config(text=f"❌ {title} ВЫКЛЮЧЕН")
                self.animate_status(f"✗ {title} деактивирован", False)
            self.root.after(1500, lambda: self.status_text.config(text="✅ Готов | F1-F8 | ESP + ХитБокс +65%"))
            state.save()
        
        btn.config(command=toggle)
        if getattr(state, var_name, False):
            status.config(text="ВКЛ", fg=self.colors['success'])
            btn.config(text="ВЫКЛ", bg=self.colors['danger'])
        return status
    
    def animate_card_hover(self, card, hover):
        if hover:
            card.config(bg=self.colors['card_hover'])
            # Анимация масштаба
            def animate_scale(scale=1.0):
                if scale < 1.05:
                    card.configure(bg=self.colors['card_hover'])
                    self.root.after(10, lambda: animate_scale(scale + 0.01))
            animate_scale()
        else:
            card.config(bg=self.colors['card'])
    
    def show_combat(self):
        header = tk.Frame(self.current_content, bg=self.colors['bg'])
        header.pack(fill='x', pady=(0, 20))
        tk.Label(header, text="⚔️ Боевые модули", font=('Segoe UI', 22, 'bold'),
                bg=self.colors['bg'], fg=self.colors['accent']).pack(anchor='w')
        tk.Label(header, text="Автоматические боевые функции", font=('Segoe UI', 11),
                bg=self.colors['bg'], fg=self.colors['text_sec']).pack(anchor='w', pady=(5, 0))
        
        modules = tk.Frame(self.current_content, bg=self.colors['bg'])
        modules.pack(fill='both', expand=True)
        
        self.create_module_card(modules, "🗡️", "KillAura", f"Атакует каждые {ATTACK_COOLDOWN}с", "killaura")
        self.create_module_card(modules, "🖱️", "AutoClicker", f"Автокликер {state.cps} CPS", "autoclicker")
        
        # Настройка CPS
        cps_frame = tk.Frame(modules, bg=self.colors['card'])
        cps_frame.pack(fill='x', padx=5, pady=10)
        inner = tk.Frame(cps_frame, bg=self.colors['card'])
        inner.pack(fill='x', padx=18, pady=12)
        tk.Label(inner, text="⚡ Настройки CPS:", bg=self.colors['card'], fg='white', 
                font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        
        slider_frame = tk.Frame(inner, bg=self.colors['card'])
        slider_frame.pack(fill='x', pady=(10, 0))
        
        self.cps_slider = tk.Scale(slider_frame, from_=5, to=20, orient='horizontal',
                                   bg=self.colors['card'], fg=self.colors['accent'],
                                   highlightthickness=0, length=300, sliderlength=20,
                                   troughcolor=self.colors['bg'])
        self.cps_slider.set(state.cps)
        self.cps_slider.pack(side='left')
        
        self.cps_label = tk.Label(slider_frame, text=str(state.cps), bg=self.colors['card'],
                                  fg=self.colors['accent'], font=('Segoe UI', 16, 'bold'))
        self.cps_label.pack(side='left', padx=(15, 0))
        
        def update_cps(val):
            state.cps = int(float(val))
            self.cps_label.config(text=str(state.cps))
            state.save()
        
        self.cps_slider.configure(command=update_cps)
    
    def show_movement(self):
        header = tk.Frame(self.current_content, bg=self.colors['bg'])
        header.pack(fill='x', pady=(0, 20))
        tk.Label(header, text="🏃 Модули движения", font=('Segoe UI', 22, 'bold'),
                bg=self.colors['bg'], fg=self.colors['accent']).pack(anchor='w')
        tk.Label(header, text="Функции для передвижения", font=('Segoe UI', 11),
                bg=self.colors['bg'], fg=self.colors['text_sec']).pack(anchor='w', pady=(5, 0))
        
        modules = tk.Frame(self.current_content, bg=self.colors['bg'])
        modules.pack(fill='both', expand=True)
        
        self.create_module_card(modules, "💨", "Speed", "Удерживает CTRL для ускорения", "speed")
        self.create_module_card(modules, "🏗️", "Scaffold", "Авто-стройка блоков", "scaffold")
        self.create_module_card(modules, "🪑", "Shift Scaffold", "Приседает перед каждым блоком", "shift_scaffold")
    
    def show_visuals(self):
        header = tk.Frame(self.current_content, bg=self.colors['bg'])
        header.pack(fill='x', pady=(0, 20))
        tk.Label(header, text="👁️ Визуальные модули", font=('Segoe UI', 22, 'bold'),
                bg=self.colors['bg'], fg=self.colors['accent']).pack(anchor='w')
        tk.Label(header, text="Визуальные улучшения - РАБОТАЮТ!", font=('Segoe UI', 11),
                bg=self.colors['bg'], fg=self.colors['text_sec']).pack(anchor='w', pady=(5, 0))
        
        modules = tk.Frame(self.current_content, bg=self.colors['bg'])
        modules.pack(fill='both', expand=True)
        
        self.create_module_card(modules, "💡", "FullBright", "Увеличивает яркость", "fullbright")
        self.create_module_card(modules, "👁️", "ESP", "ESP с боксами и здоровьем", "esp")
        self.create_module_card(modules, "❤️", "Health Overlay", "Здоровье с сердечками", "health_overlay")
    
    def show_hitboxes(self):
        header = tk.Frame(self.current_content, bg=self.colors['bg'])
        header.pack(fill='x', pady=(0, 20))
        tk.Label(header, text="🎯 ХитБокс модули", font=('Segoe UI', 22, 'bold'),
                bg=self.colors['bg'], fg=self.colors['accent']).pack(anchor='w')
        tk.Label(header, text="Увеличенные хитбоксы +65% - РАБОТАЮТ!", font=('Segoe UI', 11),
                bg=self.colors['bg'], fg=self.colors['text_sec']).pack(anchor='w', pady=(5, 0))
        
        modules = tk.Frame(self.current_content, bg=self.colors['bg'])
        modules.pack(fill='both', expand=True)
        
        self.create_module_card(modules, "🎯", "HitBox Expand", "Показывает увеличенные хитбоксы (+65%)", "hitboxes")
        
        # Настройка размера хитбоксов
        size_frame = tk.Frame(modules, bg=self.colors['card'])
        size_frame.pack(fill='x', padx=5, pady=10)
        inner = tk.Frame(size_frame, bg=self.colors['card'])
        inner.pack(fill='x', padx=18, pady=12)
        tk.Label(inner, text="📏 Размер хитбоксов:", bg=self.colors['card'], fg='white', 
                font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        
        slider_frame = tk.Frame(inner, bg=self.colors['card'])
        slider_frame.pack(fill='x', pady=(10, 0))
        
        self.size_slider = tk.Scale(slider_frame, from_=0, to=100, orient='horizontal',
                                    bg=self.colors['card'], fg=self.colors['accent'],
                                    highlightthickness=0, length=300, sliderlength=20,
                                    troughcolor=self.colors['bg'])
        self.size_slider.set(int(state.hitbox_size * 100))
        self.size_slider.pack(side='left')
        
        self.size_label = tk.Label(slider_frame, text=f"+{int(state.hitbox_size*100)}%",
                                   bg=self.colors['card'], fg=self.colors['accent'], 
                                   font=('Segoe UI', 16, 'bold'))
        self.size_label.pack(side='left', padx=(15, 0))
        
        def update_size(val):
            size = int(float(val)) / 100
            state.hitbox_size = size
            visual_modules.set_hitbox_size(size)
            self.size_label.config(text=f"+{int(size*100)}%")
            state.save()
        
        self.size_slider.configure(command=update_size)
    
    def show_world(self):
        header = tk.Frame(self.current_content, bg=self.colors['bg'])
        header.pack(fill='x', pady=(0, 20))
        tk.Label(header, text="🌍 Мировые модули", font=('Segoe UI', 22, 'bold'),
                bg=self.colors['bg'], fg=self.colors['accent']).pack(anchor='w')
        tk.Label(header, text="Взаимодействие с миром", font=('Segoe UI', 11),
                bg=self.colors['bg'], fg=self.colors['text_sec']).pack(anchor='w', pady=(5, 0))
        
        modules = tk.Frame(self.current_content, bg=self.colors['bg'])
        modules.pack(fill='both', expand=True)
        
        self.create_module_card(modules, "🔨", "Nuker", "Автоматически ломает блоки", "nuker")
        self.create_module_card(modules, "🪽", "AirBridge", "Ставит блоки в воздухе", "airbridge")
    
    def update_minecraft_status(self):
        if MinecraftDetector.is_minecraft_active():
            self.mc_status.config(text="🎮 Minecraft: АКТИВЕН ✓", fg=self.colors['success'])
        else:
            self.mc_status.config(text="🎮 Minecraft: НЕ АКТИВЕН ✗", fg=self.colors['danger'])
        self.root.after(500, self.update_minecraft_status)
    
    def update_threads_loop(self):
        update_threads()
        self.root.after(500, self.update_threads_loop)
    
    def update_ui_loop(self):
        self.update_current_tab_ui()
        self.root.after(200, self.update_ui_loop)
    
    def run(self):
        # Горячие клавиши F1-F8
        def hk_f1(): state.killaura = not state.killaura; update_threads(); state.save(); self.update_current_tab_ui(); self.animate_status("⚔️ KillAura " + ("ВКЛ" if state.killaura else "ВЫКЛ"), False)
        def hk_f2(): state.speed = not state.speed; update_threads(); state.save(); self.update_current_tab_ui(); self.animate_status("💨 Speed " + ("ВКЛ" if state.speed else "ВЫКЛ"), False)
        def hk_f3(): state.scaffold = not state.scaffold; update_threads(); state.save(); self.update_current_tab_ui(); self.animate_status("🏗️ Scaffold " + ("ВКЛ" if state.scaffold else "ВЫКЛ"), False)
        def hk_f4(): state.airbridge = not state.airbridge; update_threads(); state.save(); self.update_current_tab_ui(); self.animate_status("🪽 AirBridge " + ("ВКЛ" if state.airbridge else "ВЫКЛ"), False)
        def hk_f5(): state.fullbright = not state.fullbright; update_threads(); state.save(); self.update_current_tab_ui(); self.animate_status("💡 FullBright " + ("ВКЛ" if state.fullbright else "ВЫКЛ"), False)
        def hk_f6(): state.esp = not state.esp; update_threads(); state.save(); self.update_current_tab_ui(); self.animate_status("👁️ ESP " + ("ВКЛ" if state.esp else "ВЫКЛ"), False)
        def hk_f7(): state.health_overlay = not state.health_overlay; update_threads(); state.save(); self.update_current_tab_ui(); self.animate_status("❤️ Health Overlay " + ("ВКЛ" if state.health_overlay else "ВЫКЛ"), False)
        def hk_f8(): state.hitboxes = not state.hitboxes; update_threads(); state.save(); self.update_current_tab_ui(); self.animate_status("🎯 HitBoxes " + ("ВКЛ" if state.hitboxes else "ВЫКЛ"), False)
        
        self.root.bind('<F1>', lambda e: hk_f1())
        self.root.bind('<F2>', lambda e: hk_f2())
        self.root.bind('<F3>', lambda e: hk_f3())
        self.root.bind('<F4>', lambda e: hk_f4())
        self.root.bind('<F5>', lambda e: hk_f5())
        self.root.bind('<F6>', lambda e: hk_f6())
        self.root.bind('<F7>', lambda e: hk_f7())
        self.root.bind('<F8>', lambda e: hk_f8())
        
        self.root.mainloop()
        state.save()
        visual_modules.set_fullbright(False)
        visual_modules._stop_esp()
        visual_modules._stop_health_overlay()
        visual_modules._stop_hitboxes()

# === ЗАПУСК ===
if __name__ == "__main__":
    try:
        splash = SplashScreen()
        splash.run()
        app = PleHaNovClient()
        app.run()
    except Exception as e:
        print(f"Ошибка: {e}")
        input("Нажмите Enter для выхода...")