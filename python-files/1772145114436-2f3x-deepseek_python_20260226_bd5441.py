#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для сборки Clutch Tracker в EXE файл
Использование: python build_exe.py
"""

import os
import sys
import shutil
import subprocess

def check_dependencies():
    """Проверка наличия необходимых пакетов"""
    print("Проверка зависимостей...")
    
    required_packages = ['pyinstaller', 'PyQt5', 'matplotlib', 'pillow', 'plyer']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ✗ {package}")
    
    if missing_packages:
        print("\nУстановка недостающих пакетов...")
        for package in missing_packages:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    return True

def create_icon():
    """Создание иконки (если её нет)"""
    icon_path = 'icon.ico'
    
    if not os.path.exists(icon_path):
        print("Создание иконки...")
        # Создаем простую иконку через PIL
        try:
            from PIL import Image, ImageDraw
            
            # Создаем изображение 256x256
            img = Image.new('RGBA', (256, 256), color=(0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Рисуем круг
            draw.ellipse([10, 10, 246, 246], fill='#4a90e2')
            
            # Рисуем букву "C"
            from PIL import ImageFont
            try:
                font = ImageFont.truetype("arial.ttf", 150)
            except:
                font = ImageFont.load_default()
            
            draw.text((78, 68), "C", fill='white', font=font)
            
            # Сохраняем как ICO
            img.save(icon_path, format='ICO', sizes=[(256, 256)])
            print(f"  ✓ Иконка создана: {icon_path}")
        except Exception as e:
            print(f"  Не удалось создать иконку: {e}")
            return False
    
    return True

def create_spec_file():
    """Создание spec файла для PyInstaller"""
    print("Создание spec файла...")
    
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['clutch_tracker.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icon.ico', '.'),
    ],
    hiddenimports=[
        'PyQt5.sip',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
        'PIL',
        'PIL._tkinter_finder',
        'plyer',
        'plyer.platforms.win.notification',
        'win32event',
        'win32api',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ClutchTracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'
)
"""
    
    with open('ClutchTracker.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("  ✓ spec файл создан")
    return True

def build_exe():
    """Сборка EXE файла"""
    print("\nСборка EXE файла...")
    
    # Очистка старых файлов
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    
    # Запуск PyInstaller
    result = subprocess.run([
        'pyinstaller',
        '--clean',
        '--noconfirm',
        'ClutchTracker.spec'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("  ✓ EXE файл создан")
        return True
    else:
        print("  ✗ Ошибка сборки:")
        print(result.stderr)
        return False

def create_portable_version():
    """Создание портативной версии"""
    print("\nСоздание портативной версии...")
    
    portable_dir = 'ClutchTracker_Portable'
    if os.path.exists(portable_dir):
        shutil.rmtree(portable_dir)
    
    os.makedirs(portable_dir)
    
    # Копируем EXE файл
    shutil.copy2('dist/ClutchTracker.exe', portable_dir)
    
    # Создаем README для портативной версии
    with open(f'{portable_dir}/README.txt', 'w', encoding='utf-8') as f:
        f.write("""Clutch Tracker - Портативная версия
================================

Для запуска программы:
1. Запустите файл ClutchTracker.exe
2. Все данные будут храниться в папке data/ внутри этой директории

Системные требования:
- Windows 7/8/10/11
- 100 МБ свободного места

Поддержка: support@clutch-tracker.ru
""")
    
    print(f"  ✓ Портативная версия создана: {portable_dir}/")
    return True

def main():
    """Главная функция"""
    print("=" * 60)
    print("Clutch Tracker - Сборка для Windows")
    print("=" * 60)
    
    # Проверка зависимостей
    if not check_dependencies():
        print("\nОшибка: Не удалось установить зависимости")
        return
    
    # Создание иконки
    if not create_icon():
        print("\nПредупреждение: Продолжаем без иконки")
    
    # Создание spec файла
    if not create_spec_file():
        return
    
    # Сборка EXE
    if not build_exe():
        return
    
    # Создание портативной версии
    create_portable_version()
    
    print("\n" + "=" * 60)
    print("Сборка завершена успешно!")
    print("=" * 60)
    print("\nФайлы:")
    print("  - dist/ClutchTracker.exe  (основной EXE файл)")
    print("  - ClutchTracker_Portable/ (портативная версия)")
    print("\nДля создания установщика:")
    print("  1. Скачайте Inno Setup: https://jrsoftware.org/isdl.php")
    print("  2. Откройте файл installer.iss в Inno Setup")
    print("  3. Нажмите Ctrl+F9 для компиляции")

if __name__ == '__main__':
    main()