import sys
import os
import subprocess

# АВТОУСТАНОВЩИК ЗАВИСИМОСТЕЙ (запускается один раз)
def install_package(package):
    try:
        __import__(package)
    except ImportError:
        print(f"Устанавливаю {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])
        print(f"{package} установлен!")

# Проверяем и устанавливаем все нужные библиотеки
required_packages = ["pyautogui", "pynput"]
for pkg in required_packages:
    install_package(pkg)

# Теперь импортируем
import pyautogui
import threading
import time
import tkinter as tk
from tkinter import ttk
from pynput import keyboard

# Отключаем встроенную паузу pyautogui для максимальной скорости
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

class UltraClicker:
    def __init__(self, root):
        self.root = root
        self.root.title("SWILL UltraClicker v2.0")
        self.root.geometry("550x650")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        
        # Устанавливаем иконку (опционально, если файл есть)
        try:
            self.root.iconbitmap(default='icon.ico')
        except:
            pass
        
        # Переменные состояния
        self.clicking = False
        self.click_thread = None
        self.hotkey_listener = None
        
        # Параметры клика
        self.delay = tk.DoubleVar(value=0.001)
        self.button = tk.StringVar(value="left")
        self.clicks_per_click = tk.IntVar(value=1)
        self.hotkey_key = tk.StringVar(value="F6")
        self.stop_hotkey = tk.StringVar(value="F7")
        
        # Стиль - делаем красиво
        style = ttk.Style()
        style.theme_use('clam')
        
        # Настраиваем цвета
        self.root.configure(bg='#1e1e1e')
        style.configure('TFrame', background='#1e1e1e')
        style.configure('TLabel', background='#1e1e1e', foreground='#ffffff', font=('Segoe UI', 10))
        style.configure('TLabelframe', background='#1e1e1e', foreground='#ffffff', font=('Segoe UI', 10, 'bold'))
        style.configure('TLabelframe.Label', background='#1e1e1e', foreground='#00ff00')
        style.configure('TButton', font=('Segoe UI', 10, 'bold'), padding=8)
        style.map('TButton', background=[('active', '#45a049')])
        style.configure('TEntry', fieldbackground='#2d2d2d', foreground='#ffffff', font=('Segoe UI', 10))
        
        self.create_widgets()
        self.start_hotkey_listener()
        
        # Центрируем окно на экране
        self.center_window()
        
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_widgets(self):
        # Заголовок
        title_label = tk.Label(self.root, text="⚡ SWILL ULTRA CLICKER ⚡", 
                                font=('Segoe UI', 16, 'bold'), 
                                bg='#1e1e1e', fg='#00ff00')
        title_label.pack(pady=10)
        
        # Рамка настроек скорости
        speed_frame = ttk.LabelFrame(self.root, text=" СКОРОСТЬ КЛИКА ", padding=10)
        speed_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(speed_frame, text="Задержка между кликами (сек):").pack(anchor="w")
        delay_entry = ttk.Entry(speed_frame, textvariable=self.delay, width=15)
        delay_entry.pack(anchor="w", pady=5)
        
        # Ползунок
        self.delay_slider = ttk.Scale(speed_frame, from_=0, to=0.05, variable=self.delay, orient="horizontal")
        self.delay_slider.pack(fill="x", pady=5)
        
        ttk.Label(speed_frame, text="Совет: 0 = максимальная скорость (до 100 000 кликов/сек)", 
                  font=('Segoe UI', 8), foreground='#aaaaaa').pack(anchor="w")
        
        # Рамка кнопки мыши
        mouse_frame = ttk.LabelFrame(self.root, text=" КНОПКА МЫШИ ", padding=10)
        mouse_frame.pack(fill="x", padx=10, pady=5)
        
        btn_frame = tk.Frame(mouse_frame, bg='#1e1e1e')
        btn_frame.pack()
        
        ttk.Radiobutton(btn_frame, text="🖱 Левая", variable=self.button, value="left").pack(side="left", padx=10)
        ttk.Radiobutton(btn_frame, text="🖱 Правая", variable=self.button, value="right").pack(side="left", padx=10)
        ttk.Radiobutton(btn_frame, text="🖱 Средняя", variable=self.button, value="middle").pack(side="left", padx=10)
        
        ttk.Label(mouse_frame, text="Кликов за цикл:").pack(anchor="w", pady=(10,0))
        clicks_spin = ttk.Spinbox(mouse_frame, from_=1, to=100, textvariable=self.clicks_per_click, width=10)
        clicks_spin.pack(anchor="w", pady=5)
        
        # Рамка горячих клавиш
        hotkey_frame = ttk.LabelFrame(self.root, text=" ГОРЯЧИЕ КЛАВИШИ ", padding=10)
        hotkey_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(hotkey_frame, text="Старт/Стоп:").grid(row=0, column=0, sticky="w", padx=5)
        hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.hotkey_key, width=10)
        hotkey_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(hotkey_frame, text="Аварийная остановка:").grid(row=1, column=0, sticky="w", padx=5)
        stop_hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.stop_hotkey, width=10)
        stop_hotkey_entry.grid(row=1, column=1, padx=5)
        
        ttk.Label(hotkey_frame, text="⚠ Горячие клавиши работают даже когда окно не активно", 
                  font=('Segoe UI', 8), foreground='#ffaa00').grid(row=2, column=0, columnspan=2, pady=5)
        
        # Кнопки управления
        control_frame = tk.Frame(self.root, bg='#1e1e1e')
        control_frame.pack(pady=20)
        
        self.start_btn = tk.Button(control_frame, text="▶ СТАРТ", command=self.start_clicking,
                                   bg='#2e7d32', fg='white', font=('Segoe UI', 12, 'bold'),
                                   width=12, height=1, relief='flat', cursor='hand2')
        self.start_btn.pack(side="left", padx=10)
        
        self.stop_btn = tk.Button(control_frame, text="⏹ СТОП", command=self.stop_clicking,
                                  bg='#c62828', fg='white', font=('Segoe UI', 12, 'bold'),
                                  width=12, height=1, relief='flat', cursor='hand2')
        self.stop_btn.pack(side="left", padx=10)
        
        # Статус
        self.status_label = tk.Label(self.root, text="● СТАТУС: ОСТАНОВЛЕН", 
                                      font=('Segoe UI', 12, 'bold'), 
                                      bg='#1e1e1e', fg='#ff4444')
        self.status_label.pack(pady=10)
        
        # Инфопанель
        self.info_label = tk.Label(self.root, text="Горячие клавиши активны | FPS не ограничен", 
                                    font=('Segoe UI', 9), 
                                    bg='#1e1e1e', fg='#888888')
        self.info_label.pack()
        
        # Лог
        log_frame = ttk.LabelFrame(self.root, text=" ЛОГ СКОРОСТИ ", padding=5)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.log_text = tk.Text(log_frame, height=12, width=60, bg='#2d2d2d', 
                                fg='#00ff00', font=('Consolas', 9), wrap='word')
        self.log_text.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log("="*50)
        self.log("SWILL UltraClicker v2.0 ЗАПУЩЕН")
        self.log("="*50)
        self.log(f"Скорость: {self.delay.get()} сек")
        self.log(f"Горячие клавиши: {self.hotkey_key.get()} - старт/стоп, {self.stop_hotkey.get()} - аварийная остановка")
        self.log("Ожидание команды...")
        
    def log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {msg}\n")
        self.log_text.see("end")
        
    def click_loop(self):
        self.log(f"Кликер АКТИВИРОВАН | Задержка: {self.delay.get()} сек | Кнопка: {self.button.get()}")
        last_time = time.perf_counter()
        click_count = 0
        
        while self.clicking:
            start = time.perf_counter()
            
            for _ in range(self.clicks_per_click.get()):
                if not self.clicking:
                    break
                if self.button.get() == "left":
                    pyautogui.click(button='left')
                elif self.button.get() == "right":
                    pyautogui.click(button='right')
                else:
                    pyautogui.click(button='middle')
                click_count += 1
            
            delay_val = self.delay.get()
            if delay_val > 0:
                time.sleep(delay_val)
            else:
                time.sleep(0.00001)
            
            now = time.perf_counter()
            if now - last_time >= 1.0:
                cps = click_count / (now - last_time)
                self.status_label.config(text=f"● КЛИКАЕТ | {cps:.0f} CPS", fg='#00ff00')
                self.log(f"⚡ СКОРОСТЬ: {cps:.2f} кликов/сек | Всего: {click_count}")
                last_time = now
                click_count = 0
        
        self.status_label.config(text="● СТАТУС: ОСТАНОВЛЕН", fg='#ff4444')
        self.log("Кликер ОСТАНОВЛЕН")
        
    def start_clicking(self):
        if self.clicking:
            self.log("Кликер уже работает!")
            return
        self.clicking = True
        self.click_thread = threading.Thread(target=self.click_loop, daemon=True)
        self.click_thread.start()
        
    def stop_clicking(self):
        if not self.clicking:
            return
        self.clicking = False
        if self.click_thread:
            self.click_thread.join(timeout=0.5)
        
    def on_press(self, key):
        try:
            hotkey_str = self.hotkey_key.get().upper()
            stop_str = self.stop_hotkey.get().upper()
            
            pressed = None
            if hasattr(key, 'char') and key.char:
                pressed = key.char.upper()
            elif hasattr(key, 'name'):
                pressed = key.name.upper()
            else:
                pressed = str(key).upper().replace("KEY.", "")
            
            if pressed == hotkey_str:
                if self.clicking:
                    self.stop_clicking()
                else:
                    self.start_clicking()
            elif pressed == stop_str:
                self.stop_clicking()
        except:
            pass
            
    def start_hotkey_listener(self):
        self.hotkey_listener = keyboard.Listener(on_press=self.on_press, daemon=True)
        self.hotkey_listener.start()
        
    def on_closing(self):
        self.stop_clicking()
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.root.destroy()

# ТОЧКА ВХОДА - ПРОСТО ЗАПУСКАЕТСЯ ДВОЙНЫМ КЛИКОМ
if __name__ == "__main__":
    # Отключаем консольное окно (на Windows)
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass
    
    root = tk.Tk()
    app = UltraClicker(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()