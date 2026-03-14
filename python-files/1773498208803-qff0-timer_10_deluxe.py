#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ИСПРАВЛЕННЫЙ скрипт для создания .exe файла
"""

import os
import sys
import subprocess
import shutil

def check_files():
    """Проверка наличия необходимых файлов"""
    print("📋 Проверка файлов...")
    
    # Проверяем основной файл
    if not os.path.exists('timer_10_deluxe.py'):
        print("❌ Файл timer_10_deluxe.py не найден!")
        print("   Создайте этот файл сначала.")
        return False
        
    print(f"✅ Найден: timer_10_deluxe.py ({os.path.getsize('timer_10_deluxe.py')} байт)")
    
    # Проверяем текущую директорию
    current_dir = os.getcwd()
    print(f"📁 Текущая папка: {current_dir}")
    print(f"📁 Содержимое: {', '.join(os.listdir(current_dir))}")
    
    return True

def create_icon_simple():
    """Простое создание иконки"""
    try:
        from PIL import Image, ImageDraw
        
        # Создаем простое изображение
        img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Рисуем красный круг
        draw.ellipse([10, 10, 246, 246], fill='#ff6b6b')
        
        # Сохраняем
        img.save('timer_icon.ico', format='ICO')
        print("✅ Иконка создана")
        return True
    except Exception as e:
        print(f"⚠️ Не удалось создать иконку: {e}")
        return False

def build_exe_simple():
    """Простая сборка .exe"""
    
    print("=" * 60)
    print("🔨 СОЗДАНИЕ .EXE ФАЙЛА")
    print("=" * 60)
    print()
    
    # Проверяем файлы
    if not check_files():
        return False
        
    # Создаем иконку
    create_icon_simple()
    
    # Очищаем старые папки
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            
    print("\n📦 Запуск PyInstaller...")
    print()
    
    # Простые параметры для PyInstaller
    params = [
        'pyinstaller',
        '--onefile',              # Один файл
        '--windowed',              # Без консоли
        '--name=timer_10_deluxe',  # Имя файла
        '--icon=timer_icon.ico',   # Иконка (если есть)
        'timer_10_deluxe.py'       # Основной файл
    ]
    
    try:
        # Запускаем PyInstaller
        result = subprocess.run(params, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n✅ Сборка завершена успешно!")
            
            # Копируем .exe в текущую папку
            exe_source = os.path.join('dist', 'timer_10_deluxe.exe')
            if os.path.exists(exe_source):
                shutil.copy2(exe_source, 'timer_10_deluxe.exe')
                print(f"📁 Файл создан: timer_10_deluxe.exe")
                print(f"📁 Размер: {os.path.getsize('timer_10_deluxe.exe') / 1024 / 1024:.2f} MB")
                
                # Создаем простой батник
                with open('start.bat', 'w') as f:
                    f.write('@echo off\nstart timer_10_deluxe.exe')
                    
                return True
            else:
                print("❌ Не найден .exe файл в папке dist")
                return False
        else:
            print("❌ Ошибка PyInstaller:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Ошибка сборки: {e}")
        return False

def main():
    print("=" * 60)
    print("   СОЗДАНИЕ .EXE ДЛЯ ТАЙМЕРА 10 СЕКУНД")
    print("=" * 60)
    print()
    
    # Проверяем Python
    print(f"🐍 Python версия: {sys.version}")
    print()
    
    # Проверяем PyInstaller
    try:
        import PyInstaller
        print("✅ PyInstaller найден")
    except ImportError:
        print("📦 Установка PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        
    # Проверяем PIL
    try:
        from PIL import Image
        print("✅ Pillow найден")
    except ImportError:
        print("📦 Установка Pillow...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
        
    print()
    
    # Создаем .exe
    if build_exe_simple():
        print("\n" + "=" * 60)
        print("✅ ГОТОВО! .EXE ФАЙЛ СОЗДАН")
        print("=" * 60)
        print("\n👉 Запустите timer_10_deluxe.exe")
        print("👉 Или запустите start.bat")
    else:
        print("\n❌ Ошибка создания .exe")
        print("\n💡 Решение:")
        print("1. Убедитесь, что файл timer_10_deluxe.py существует")
        print("2. Запустите команду вручную:")
        print("   pyinstaller --onefile --windowed --name=timer_10_deluxe timer_10_deluxe.py")

if __name__ == "__main__":
    main()