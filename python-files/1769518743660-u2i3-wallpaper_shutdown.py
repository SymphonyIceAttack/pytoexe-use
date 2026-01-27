import os
import sys
import ctypes
import subprocess
import time
from pathlib import Path

def hide_console():
    """Скрывает консольное окно"""
    try:
        # Для Windows - скрываем консоль
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 0)  # 0 = SW_HIDE
    except:
        pass

def set_wallpaper(image_path):
    """Устанавливает обои рабочего стола"""
    try:
        SPI_SETDESKWALLPAPER = 20
        SPIF_UPDATEINIFILE = 0x01
        SPIF_SENDWININICHANGE = 0x02
        
        # Конвертируем путь
        abs_path = os.path.abspath(image_path)
        
        if not os.path.exists(abs_path):
            return False
        
        # Устанавливаем обои
        result = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER,
            0,
            abs_path,
            SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE
        )
        
        return bool(result)
    except Exception as e:
        return False

def shutdown_pc():
    """Выключает компьютер"""
    try:
        # Выключение через 2 секунды
        subprocess.run(["shutdown", "/s", "/t", "2", "/f"], shell=True)
        return True
    except:
        return False

def find_image():
    """Ищет изображение в папке D:\DP"""
    try:
        dp_path = Path("D:/DP")
        
        if not dp_path.exists():
            # Пробуем разные варианты написания диска
            dp_path = Path("D:/dp")
            if not dp_path.exists():
                return None
        
        # Проверяем файлы
        image_files = []
        for file in dp_path.iterdir():
            if file.is_file():
                ext = file.suffix.lower()
                if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']:
                    image_files.append(str(file))
        
        if image_files:
            # Берем первый найденный файл
            return image_files[0]
        return None
    except:
        return None

def main():
    # Скрываем консоль
    hide_console()
    
    # Даем время для запуска
    time.sleep(1)
    
    # Ищем изображение
    image_path = find_image()
    
    if image_path:
        # Устанавливаем обои
        set_wallpaper(image_path)
        time.sleep(1)  # Ждем применения обоев
    
    # Выключаем компьютер
    shutdown_pc()

if __name__ == "__main__":
    main()