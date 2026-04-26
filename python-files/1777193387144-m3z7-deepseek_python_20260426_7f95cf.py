import pyautogui
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from pynput import keyboard, mouse

# Отключаем встроенную паузу pyautogui для максимальной скорости
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

class UltraClicker:
    def __init__(self, root):
        self.root = root
        self.root.title("SWILL UltraClicker v1.0")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        
        # Переменные состояния
        self.clicking = False
        self.click_thread = None
        self.hotkey_listener = None
        self.mouse_listener = None
        
        # Параметры клика
        self.delay = tk.DoubleVar(value=0.001)  # 1 миллисекунда по умолчанию
        self.button = tk.StringVar(value="left")
        self.clicks_per_click = tk.IntVar(value=1)
        self.use_hotkey = tk.BooleanVar(value=True)
        self.hotkey_key = tk.StringVar(value="F6")
        self.stop_hotkey = tk.StringVar(value="F7")
        
        # Стиль
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Arial', 10), padding=6)
        style.configure('TLabel', font=('Arial', 10))
        style.configure('TEntry', font=('Arial', 10))
        
        self.create_widgets()
        self.start_hotkey_listener()
        
    def create_widgets(self):
        # Рамка настроек скорости
        speed_frame = ttk.LabelFrame(self.root, text="Скорость клика", padding=10)
        speed_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(speed_frame, text="Задержка (сек):").grid(row=0, column=0, sticky="w")
        self.delay_entry = ttk.Entry(speed_frame, textvariable=self.delay, width=15)
        self.delay_entry.grid(row=0, column=1, padx=5)
        ttk.Label(speed_frame, text="(0 = максимальная скорость, ~0.0001 сек)").grid(row=0, column=2, padx=5)
        
        # Ползунок для быстрой настройки
        self.delay_slider = ttk.Scale(speed_frame, from_=0, to=0.05, variable=self.delay, orient="horizontal")
        self.delay_slider.grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)
        
        # Рамка кнопки мыши
        mouse_frame = ttk.LabelFrame(self.root, text="Кнопка мыши", padding=10)
        mouse_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Radiobutton(mouse_frame, text="Левая", variable=self.button, value="left").pack(side="left", padx=10)
        ttk.Radiobutton(mouse_frame, text="Правая", variable=self.button, value="right").pack(side="left", padx=10)
        ttk.Radiobutton(mouse_frame, text="Средняя", variable=self.button, value="middle").pack(side="left", padx=10)
        
        ttk.Label(mouse_frame, text="Кликов за одно нажатие:").pack(side="left", padx=10)
        self.clicks_spin = ttk.Spinbox(mouse_frame, from_=1, to=100, textvariable=self.clicks_per_click, width=5)
        self.clicks_spin.pack(side="left")
        
        # Рамка горячих клавиш
        hotkey_frame = ttk.LabelFrame(self.root, text="Горячие клавиши", padding=10)
        hotkey_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(hotkey_frame, text="Старт/Стоп:").grid(row=0, column=0, sticky="w")
        self.hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.hotkey_key, width=10)
        self.hotkey_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(hotkey_frame, text="Аварийная остановка:").grid(row=1, column=0, sticky="w")
        self.stop_hotkey_entry = ttk.Entry(hotkey_frame, textvariable=self.stop_hotkey, width=10)
        self.stop_hotkey_entry.grid(row=1, column=1, padx=5)
        
        # Кнопки управления
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=20)
        
        self.start_btn = ttk.Button(control_frame, text="▶ СТАРТ (F6)", command=self.start_clicking, width=20)
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹ СТОП (F7)", command=self.stop_clicking, width=20)
        self.stop_btn.pack(side="left", padx=5)
        
        # Статус
        self.status_label = ttk.Label(self.root, text="Статус: Остановлен", font=('Arial', 12, 'bold'), foreground='red')
        self.status_label.pack(pady=10)
        
        # Лог скорости
        self.log_text = tk.Text(self.root, height=10, width=60)
        self.log_text.pack(padx=10, pady=10)
        scrollbar = ttk.Scrollbar(self.log_text)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)
        
        self.log("SWILL UltraClicker готов. Скорость не ограничена.")
        
    def log(self, msg):
        self.log_text.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see("end")
        
    def click_loop(self):
        """Суперскоростной цикл кликов"""
        self.log(f"Кликер активирован. Задержка: {self.delay.get()} сек, Кнопка: {self.button.get()}")
        last_time = time.perf_counter()
        click_count = 0
        
        while self.clicking:
            start = time.perf_counter()
            
            # Выполняем множественные клики за итерацию (для сверхвысокой частоты)
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
            
            # Задержка (если больше 0)
            delay_val = self.delay.get()
            if delay_val > 0:
                time.sleep(delay_val)
            else:
                # Микро-задержка для снижения нагрузки на CPU
                time.sleep(0.00001)
            
            # Логируем скорость раз в секунду
            now = time.perf_counter()
            if now - last_time >= 1.0:
                cps = click_count / (now - last_time)
                self.status_label.config(text=f"Статус: КЛИКАЕТ | {cps:.0f} кликов/сек")
                self.log(f"Скорость: {cps:.2f} CPS (кликов/сек)")
                last_time = now
                click_count = 0
        
        self.status_label.config(text="Статус: Остановлен", foreground='red')
        self.log("Кликер остановлен")
        
    def start_clicking(self):
        if self.clicking:
            self.log("Кликер уже работает")
            return
        self.clicking = True
        self.status_label.config(text="Статус: ЗАПУСК...", foreground='green')
        self.click_thread = threading.Thread(target=self.click_loop, daemon=True)
        self.click_thread.start()
        
    def stop_clicking(self):
        self.clicking = False
        if self.click_thread:
            self.click_thread.join(timeout=0.5)
            
    def on_press(self, key):
        try:
            # Глобальный слушатель клавиш
            from pynput.keyboard import Key, KeyCode
            hotkey_str = self.hotkey_key.get().upper()
            stop_str = self.stop_hotkey.get().upper()
            
            # Преобразуем
            pressed = None
            if hasattr(key, 'char') and key.char:
                pressed = key.char.upper()
            elif hasattr(key, 'name'):
                pressed = key.name.upper()
            else:
                pressed = str(key).upper().replace("KEY.", "")
            
            if pressed == hotkey_str or (hotkey_str == "F6" and key == Key.f6):
                if self.clicking:
                    self.stop_clicking()
                else:
                    self.start_clicking()
            elif pressed == stop_str or (stop_str == "F7" and key == Key.f7):
                self.stop_clicking()
        except Exception as e:
            self.log(f"Ошибка горячей клавиши: {e}")
            
    def start_hotkey_listener(self):
        def on_press(key):
            self.on_press(key)
        self.hotkey_listener = keyboard.Listener(on_press=on_press, daemon=True)
        self.hotkey_listener.start()
        
    def on_closing(self):
        self.stop_clicking()
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.root.destroy()

if __name__ == "__main__":
    # Проверка зависимостей
    try:
        import pyautogui, pynput
    except ImportError:
        print("Установите зависимости: pip install pyautogui pynput")
        exit(1)
    
    root = tk.Tk()
    app = UltraClicker(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()