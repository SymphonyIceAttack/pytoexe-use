"""
Скрипт для сборки Clutch Tracker в EXE файл
Установка зависимостей:
pip install pyinstaller PyQt5 matplotlib pillow
"""

import os
import sys
import shutil
from pathlib import Path

def create_spec_file():
    """Создает spec файл для PyInstaller"""
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['clutch_tracker_windows.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt5.sip',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
        'PIL',
        'PIL._tkinter_finder'
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

# Создаем однофайловый EXE
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='ClutchTracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='icon.ico'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ClutchTracker'
)
"""
    
    with open('ClutchTracker.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

def create_installer_script():
    """Создает скрипт для Inno Setup"""
    inno_script = """
; Clutch Tracker Installer
; Для компиляции требуется Inno Setup (https://jrsoftware.org/isdl.php)

[Setup]
AppName=Clutch Tracker
AppVersion=8.0
AppPublisher=Clutch Tracker Team
AppPublisherURL=https://github.com/
DefaultDirName={autopf}\\Clutch Tracker
DefaultGroupName=Clutch Tracker
UninstallDisplayIcon={app}\\ClutchTracker.exe
Compression=lzma2
SolidCompression=yes
OutputDir=installer
OutputBaseFilename=ClutchTracker_Setup
SetupIconFile=icon.ico
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать значок на рабочем столе"; GroupDescription: "Дополнительные задачи:"
Name: "quicklaunchicon"; Description: "Создать значок в панели быстрого запуска"; GroupDescription: "Дополнительные задачи:"; Flags: unchecked

[Files]
Source: "dist\\ClutchTracker\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\\Clutch Tracker"; Filename: "{app}\\ClutchTracker.exe"
Name: "{group}\\Документация"; Filename: "{app}\\README.txt"
Name: "{group}\\{cm:UninstallProgram,Clutch Tracker}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\Clutch Tracker"; Filename: "{app}\\ClutchTracker.exe"; Tasks: desktopicon
Name: "{userappdata}\\Microsoft\\Internet Explorer\\Quick Launch\\Clutch Tracker"; Filename: "{app}\\ClutchTracker.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\\ClutchTracker.exe"; Description: "{cm:LaunchProgram,Clutch Tracker}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\\unins_data.bat"; Flags: runhidden

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if MsgBox('Удалить все данные программы (документы, настройки)?', 
               mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
    begin
      DelTree(ExpandConstant('{userappdata}\\ClutchTracker'), True, True, True);
    end;
  end;
end;
"""
    
    with open('installer_script.iss', 'w', encoding='utf-8') as f:
        f.write(inno_script)

def create_readme():
    """Создает файл README"""
    readme = """
====================================
Clutch Tracker v8.0 для Windows
====================================

Программа для учета технического обслуживания автомобилей.

Системные требования:
- Windows 7/8/10/11
- 100 МБ свободного места на диске
- 2 ГБ оперативной памяти

Установка:
1. Запустите ClutchTracker_Setup.exe
2. Следуйте инструкциям установщика
3. После установки запустите программу из меню Пуск или с рабочего стола

Данные программы хранятся в папке:
%APPDATA%\\ClutchTracker

Основные функции:
- Учет автомобилей и их характеристик
- Отслеживание ТО, сцепления, колодок
- Учет страховок, диагностических карт
- Пропуска в Москву
- Тахографы и калибровки
- Ремонты и их стоимость
- Учет топлива
- Статистика расходов
- Управление документами (прикрепление PDF, изображений)

Горячие клавиши:
- Ctrl+F - поиск
- Ctrl+D - добавить запись
- Ctrl+Del - удалить запись
- F5 - обновить
- F1 - справка

Поддержка:
Email: support@clutch-tracker.ru

====================================
© 2024 Clutch Tracker Team
====================================
"""
    
    with open('README.txt', 'w', encoding='utf-8') as f:
        f.write(readme)

def create_uninstall_bat():
    """Создает bat файл для удаления данных"""
    bat_content = """@echo off
echo Удаление данных Clutch Tracker...
rmdir /s /q "%APPDATA%\\ClutchTracker"
echo Готово.
"""
    
    with open('dist\\ClutchTracker\\unins_data.bat', 'w', encoding='utf-8') as f:
        f.write(bat_content)

def create_icon():
    """Создает иконку (если нет, используем системную)"""
    # Здесь должен быть код для создания иконки
    # В реальности нужно иметь файл icon.ico
    pass

def build():
    """Основная функция сборки"""
    print("=" * 50)
    print("Сборка Clutch Tracker для Windows")
    print("=" * 50)
    
    # Проверяем наличие необходимых модулей
    try:
        import PyInstaller
        print("✓ PyInstaller найден")
    except ImportError:
        print("✗ PyInstaller не установлен. Установите: pip install pyinstaller")
        return
    
    # Создаем spec файл
    print("\n1. Создание spec файла...")
    create_spec_file()
    
    # Создаем README
    print("2. Создание README...")
    create_readme()
    
    # Запускаем PyInstaller
    print("3. Сборка EXE файла...")
    os.system('pyinstaller ClutchTracker.spec')
    
    # Создаем bat файл для удаления данных
    print("4. Создание скрипта удаления...")
    create_uninstall_bat()
    
    # Создаем скрипт для Inno Setup
    print("5. Создание скрипта установщика...")
    create_installer_script()
    
    print("\n" + "=" * 50)
    print("Сборка завершена!")
    print("=" * 50)
    print("\nСледующие шаги:")
    print("1. Установите Inno Setup (https://jrsoftware.org/isdl.php)")
    print("2. Откройте installer_script.iss в Inno Setup")
    print("3. Скомпилируйте установщик (Ctrl+F9)")
    print("\nГотовый установщик будет в папке installer/")

if __name__ == '__main__':
    build()