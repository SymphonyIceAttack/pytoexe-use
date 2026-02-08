#!/usr/bin/env python3
"""
Установочный файл для программы УАЗ AECS Editor
Автор: MashaGPT
Версия: 1.0.0
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path
import zipfile
import json

# ============================================================================
# КОНФИГУРАЦИЯ УСТАНОВКИ
# ============================================================================

class InstallerConfig:
    """Конфигурация установщика"""
    
    APP_NAME = "УАЗ AECS Editor"
    APP_VERSION = "1.0.0"
    COMPANY_NAME = "MashaGPT"
    APP_DESCRIPTION = "Программа для работы с прошивками ЭБУ УАЗ AECS"
    
    # Пути установки
    DEFAULT_INSTALL_DIR = r"C:\Program Files\UAZ-AECS-Editor"
    START_MENU_FOLDER = "УАЗ AECS Editor"
    
    # Требования
    REQUIRED_PYTHON_VERSION = (3, 8)
    REQUIRED_PACKAGES = [
        "tkinter",
        "pillow",
        "numpy",
        "pandas",
        "matplotlib"
    ]
    
    # Файлы для установки
    FILES_TO_INSTALL = [
        "main.py",
        "requirements.txt",
        "README.md",
        "LICENSE",
        "icons/",
        "docs/",
        "examples/"
    ]

# ============================================================================
# УСТАНОВЩИК
# ============================================================================

class UAZAECSInstaller:
    """Класс установщика программы"""
    
    def __init__(self):
        self.config = InstallerConfig()
        self.install_dir = None
        self.temp_dir = None
        self.is_admin = self._check_admin()
        
    def _check_admin(self) -> bool:
        """Проверка прав администратора"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    def _create_shortcut(self, target_path: str, shortcut_path: str, description: str = ""):
        """Создание ярлыка"""
        try:
            import winshell
            from win32com.client import Dispatch
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target_path
            shortcut.WorkingDirectory = os.path.dirname(target_path)
            shortcut.Description = description
            shortcut.save()
            return True
        except Exception as e:
            print(f"Ошибка создания ярлыка: {e}")
            return False
    
    def _create_batch_file(self, python_path: str, script_path: str, batch_path: str):
        """Создание BAT файла для запуска"""
        content = f"""@echo off
echo Запуск {self.config.APP_NAME} v{self.config.APP_VERSION}
echo.
"{python_path}" "{script_path}" %*
pause
"""
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _create_exe_with_pyinstaller(self, script_path: str, output_dir: str):
        """Создание EXE файла с помощью PyInstaller"""
        try:
            spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{script_path}'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='UAZ_AECS_Editor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icons/app_icon.ico',
)
"""
            # Создаем spec файл
            spec_path = os.path.join(output_dir, "uaz_aecs_editor.spec")
            with open(spec_path, 'w', encoding='utf-8') as f:
                f.write(spec_content)
            
            # Запускаем PyInstaller
            cmd = [sys.executable, "-m", "pyinstaller", "--onefile", "--noconsole", 
                   f"--icon=icons/app_icon.ico", script_path]
            
            print("Создание EXE файла...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("EXE файл успешно создан!")
                return True
            else:
                print(f"Ошибка создания EXE: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Ошибка при создании EXE: {e}")
            return False
    
    def _check_python_installation(self):
        """Проверка установки Python"""
        print("Проверка установки Python...")
        
        # Проверяем версию Python
        if sys.version_info < self.config.REQUIRED_PYTHON_VERSION:
            print(f"Требуется Python {self.config.REQUIRED_PYTHON_VERSION[0]}.{self.config.REQUIRED_PYTHON_VERSION[1]} или выше")
            return False
        
        print(f"Python {sys.version} обнаружен")
        return True
    
    def _install_requirements(self):
        """Установка необходимых пакетов"""
        print("Установка необходимых пакетов...")
        
        try:
            # Проверяем наличие pip
            import pip
            
            # Устанавливаем пакеты
            for package in self.config.REQUIRED_PACKAGES:
                print(f"Установка {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            
            print("Все пакеты успешно установлены!")
            return True
            
        except Exception as e:
            print(f"Ошибка установки пакетов: {e}")
            return False
    
    def _create_windows_registry_entries(self):
        """Создание записей в реестре Windows"""
        try:
            import winreg
            
            # Ключи реестра
            app_key = f"Software\\{self.config.COMPANY_NAME}\\{self.config.APP_NAME}"
            
            # Создаем ключи
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, app_key) as key:
                winreg.SetValueEx(key, "Version", 0, winreg.REG_SZ, self.config.APP_VERSION)
                winreg.SetValueEx(key, "InstallPath", 0, winreg.REG_SZ, self.install_dir)
                winreg.SetValueEx(key, "InstallDate", 0, winreg.REG_SZ, 
                                 str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            # Регистрируем расширение файлов .uaec
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, ".uaec") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, "UAZAECS.Firmware")
            
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, "UAZAECS.Firmware") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, "Файл прошивки УАЗ AECS")
            
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, "UAZAECS.Firmware\\shell\\open\\command") as key:
                exe_path = os.path.join(self.install_dir, "UAZ_AECS_Editor.exe")
                winreg.SetValue(key, "", winreg.REG_SZ, f'"{exe_path}" "%1"')
            
            print("Записи реестра созданы успешно!")
            return True
            
        except Exception as e:
            print(f"Ошибка создания записей реестра: {e}")
            return False
    
    def _create_uninstaller(self):
        """Создание деинсталлятора"""
        uninstaller_script = f"""#!/usr/bin/env python3
"""
        uninstaller_path = os.path.join(self.install_dir, "uninstall.py")
        
        with open(uninstaller_path, 'w', encoding='utf-8') as f:
            f.write(uninstaller_script)
        
        # Создаем BAT файл для деинсталляции
        bat_content = f"""@echo off
echo Удаление {self.config.APP_NAME} v{self.config.APP_VERSION}
echo.
echo ВНИМАНИЕ: Это действие удалит программу и все связанные файлы!
echo.
set /p confirm="Вы уверены? (y/N): "
if /i "%confirm%"=="y" (
    python "{uninstaller_path}"
    rmdir /s /q "{self.install_dir}"
    echo Программа удалена успешно!
) else (
    echo Удаление отменено.
)
pause
"""
        
        bat_path = os.path.join(self.install_dir, "uninstall.bat")
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(bat_content)
        
        return True
    
    def install(self, install_dir: str = None):
        """Основная процедура установки"""
        print(f"=== Установка {self.config.APP_NAME} v{self.config.APP_VERSION} ===")
        print()
        
        # Проверяем Python
        if not self._check_python_installation():
            print("Ошибка: Python не установлен или версия слишком старая!")
            return False
        
        # Определяем директорию установки
        if install_dir:
            self.install_dir = install_dir
        else:
            self.install_dir = self.config.DEFAULT_INSTALL_DIR
        
        print(f"Директория установки: {self.install_dir}")
        
        # Создаем временную директорию
        self.temp_dir = tempfile.mkdtemp(prefix="uaz_aecs_install_")
        print(f"Временная директория: {self.temp_dir}")
        
        try:
            # Создаем директорию установки
            os.makedirs(self.install_dir, exist_ok=True)
            
            # Копируем файлы программы
            print("Копирование файлов программы...")
            
            # Создаем структуру директорий
            subdirs = ["icons", "docs", "examples", "logs", "config"]
            for subdir in subdirs:
                os.makedirs(os.path.join(self.install_dir, subdir), exist_ok=True)
            
            # Копируем основной файл программы
            main_program = """#!/usr/bin/env python3
\"\"\"
УАЗ AECS Editor - Программа для работы с прошивками ЭБУ УАЗ AECS
\"\"\"

import sys
import os

# Добавляем путь к библиотекам
lib_path = os.path.join(os.path.dirname(__file__), 'lib')
if os.path.exists(lib_path):
    sys.path.insert(0, lib_path)

from main import main

if __name__ == "__main__":
    main()
"""
            
            main_path = os.path.join(self.install_dir, "uaz_aecs_editor.py")
            with open(main_path, 'w', encoding='utf-8') as f:
                f.write(main_program)
            
            # Создаем конфигурационный файл
            config = {
                "app_name": self.config.APP_NAME,
                "version": self.config.APP_VERSION,
                "install_path": self.install_dir,
                "settings": {
                    "auto_update": True,
                    "backup_enabled": True,
                    "backup_path": os.path.join(self.install_dir, "backups"),
                    "log_level": "INFO"
                }
            }
            
            config_path = os.path.join(self.install_dir, "config", "config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # Создаем README
            readme_content = f"""# {self.config.APP_NAME} v{self.config.APP_VERSION}

{self.config.APP_DESCRIPTION}

## Системные требования
- Windows 7/8/10/11 (64-bit)
- Python 3.8 или выше
- 2 ГБ оперативной памяти
- 100 МБ свободного места на диске

## Установка
1. Запустите установщик `setup.exe`
2. Следуйте инструкциям мастера установки
3. После установки программа будет доступна в меню Пуск

## Использование
1. Запустите программу из меню Пуск или с рабочего стола
2. Откройте файл прошивки (.bin, .hex, .uaec)
3. Работайте с датчиками, картами калибровок и HEX редактором

## Поддерживаемые функции
- Чтение/запись прошивок ЭБУ УАЗ AECS
- Управление датчиками (включение/отключение)
- Редактирование карт калибровок
- HEX редактор
- Расчет контрольных сумм
- Экспорт/импорт данных в CSV

## Лицензия
Программа распространяется под лицензией MIT.

## Техническая поддержка
По вопросам технической поддержки обращайтесь:
- Email: support@mashagpt.ru
- Сайт: https://mashagpt.ru

© {self.config.COMPANY_NAME} {datetime.now().year}
"""
            
            readme_path = os.path.join(self.install_dir, "README.md")
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            # Создаем файл требований
            requirements = """tkinter>=8.6
pillow>=9.0
numpy>=1.21
pandas>=1.3
matplotlib>=3.5
pyinstaller>=5.0
"""
            
            req_path = os.path.join(self.install_dir, "requirements.txt")
            with open(req_path, 'w', encoding='utf-8') as f:
                f.write(requirements)
            
            # Устанавливаем зависимости
            if not self._install_requirements():
                print("Предупреждение: не удалось установить все зависимости")
            
            # Создаем EXE файл
            print("Создание исполняемого файла...")
            if not self._create_exe_with_pyinstaller(main_path, self.install_dir):
                print("Предупреждение: не удалось создать EXE файл")
                # Создаем BAT файл как запасной вариант
                python_exe = sys.executable
                bat_path = os.path.join(self.install_dir, "UAZ_AECS_Editor.bat")
                self._create_batch_file(python_exe, main_path, bat_path)
            
            # Создаем ярлыки
            print("Создание ярлыков...")
            
            # Ярлык на рабочем столе
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            desktop_shortcut = os.path.join(desktop, f"{self.config.APP_NAME}.lnk")
            
            exe_path = os.path.join(self.install_dir, "UAZ_AECS_Editor.exe")
            if os.path.exists(exe_path):
                target_path = exe_path
            else:
                target_path = os.path.join(self.install_dir, "UAZ_AECS_Editor.bat")
            
            self._create_shortcut(target_path, desktop_shortcut, self.config.APP_DESCRIPTION)
            
            # Ярлык в меню Пуск
            start_menu = os.path.join(os.getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs")
            start_menu_dir = os.path.join(start_menu, self.config.START_MENU_FOLDER)
            os.makedirs(start_menu_dir, exist_ok=True)
            
            start_menu_shortcut = os.path.join(start_menu_dir, f"{self.config.APP_NAME}.lnk")
            self._create_shortcut(target_path, start_menu_shortcut, self.config.APP_DESCRIPTION)
            
            # Создаем записи в реестре
            if self.is_admin:
                print("Создание записей реестра...")
                self._create_windows_registry_entries()
            else:
                print("Предупреждение: для создания записей реестра требуются права администратора")
            
            # Создаем деинсталлятор
            print("Создание деинсталлятора...")
            self._create_uninstaller()
            
            # Создаем файл лицензии
            license_content = """MIT License

Copyright (c) 2024 MashaGPT

Разрешается бесплатное использование, копирование, изменение, объединение, публикация, распространение, сублицензирование и/или продажа копий Программного обеспечения при соблюдении следующих условий:

Вышеуказанное уведомление об авторских правах и данное разрешение должны быть включены во все копии или существенные части Программного обеспечения.

ПРОГРАММНОЕ ОБЕСПЕЧЕНИЕ ПРЕДОСТАВЛЯЕТСЯ «КАК ЕСТЬ», БЕЗ КАКИХ-ЛИБО ГАРАНТИЙ, ЯВНЫХ ИЛИ ПОДРАЗУМЕВАЕМЫХ, ВКЛЮЧАЯ, НО НЕ ОГРАНИЧИВАЯСЬ ГАРАНТИЯМИ ТОВАРНОЙ ПРИГОДНОСТИ, СООТВЕТСТВИЯ ПО ЕГО КОНКРЕТНОМУ НАЗНАЧЕНИЮ И ОТСУТСТВИЯ НАРУШЕНИЙ ПРАВ. НИ В КАКОМ СЛУЧАЕ АВТОРЫ ИЛИ ПРАВООБЛАДАТЕЛИ НЕ НЕСУТ ОТВЕТСТВЕННОСТИ ПО ИСКАМ О ВОЗМЕЩЕНИИ УЩЕРБА, УБЫТКОВ ИЛИ ДРУГИХ ТРЕБОВАНИЙ ПО ДЕЙСТВУЮЩЕМУ ПРАВУ, ДОГОВОРУ ИЛИ ИНОМУ, ВОЗНИКШИМ ИЗ, ИМЕЮЩИМ ПРИЧИНОЙ ИЛИ СВЯЗАННЫМ С ПРОГРАММНЫМ ОБЕСПЕЧЕНИЕМ ИЛИ ИСПОЛЬЗОВАНИЕМ ПРОГРАММНОГО ОБЕСПЕЧЕНИЯ ИЛИ ИНЫМИ ДЕЙСТВИЯМИ С ПРОГРАММНЫМ ОБЕСПЕЧЕНИЕМ.
"""
            
            license_path = os.path.join(self.install_dir, "LICENSE")
            with open(license_path, 'w', encoding='utf-8') as f:
                f.write(license_content)
            
            # Очищаем временную директорию
            shutil.rmtree(self.temp_dir)
            
            print()
            print("=" * 50)
            print(f"Установка {self.config.APP_NAME} завершена успешно!")
            print(f"Программа установлена в: {self.install_dir}")
            print("Ярлыки созданы на рабочем столе и в меню Пуск")
            print("=" * 50)
            
            return True
            
        except Exception as e:
            print(f"Ошибка установки: {e}")
            import traceback
            traceback.print_exc()
            
            # Очищаем временную директорию
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            
            return False
    
    def uninstall(self):
        """Деинсталляция программы"""
        print(f"=== Удаление {self.config.APP_NAME} ===")
        
        if not os.path.exists(self.install_dir):
            print("Программа не установлена!")
            return False
        
        try:
            # Удаляем ярлыки
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            desktop_shortcut = os.path.join(desktop, f"{self.config.APP_NAME}.lnk")
            if os.path.exists(desktop_shortcut):
                os.remove(desktop_shortcut)
            
            start_menu = os.path.join(os.getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs")
            start_menu_dir = os.path.join(start_menu, self.config.START_MENU_FOLDER)
            if os.path.exists(start_menu_dir):
                shutil.rmtree(start_menu_dir)
            
            # Удаляем записи реестра
            try:
                import winreg
                app_key = f"Software\\{self.config.COMPANY_NAME}\\{self.config.APP_NAME}"
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, app_key)
                
                # Удаляем ассоциацию файлов
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, ".uaec")
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, "UAZAECS.Firmware")
            except:
                pass
            
            # Удаляем директорию установки
            shutil.rmtree(self.install_dir)
            
            print("Программа успешно удалена!")
            return True
            
        except Exception as e:
            print(f"Ошибка удаления: {e}")
            return False

# ============================================================================
# NSIS СКРИПТ ДЛЯ СОЗДАНИЯ УСТАНОВОЧНОГО ПАКЕТА
# ============================================================================

def create_nsis_script():
    """Создание NSIS скрипта для установщика"""
    nsis_script = f"""; NSIS скрипт установки УАЗ AECS Editor
; Автор: MashaGPT
; Версия: 1.0.0

Unicode true
ManifestDPIAware true

!define APP_NAME "{InstallerConfig.APP_NAME}"
!define APP_VERSION "{InstallerConfig.APP_VERSION}"
!define COMPANY_NAME "{InstallerConfig.COMPANY_NAME}"
!define APP_DESCRIPTION "{InstallerConfig.APP_DESCRIPTION}"
!define INSTALL_DIR "$PROGRAMFILES\\UAZ-AECS-Editor"

Name "${{APP_NAME}}"
OutFile "UAZ_AECS_Editor_Setup.exe"
InstallDir "${{INSTALL_DIR}}"
InstallDirRegKey HKLM "Software\\${{COMPANY_NAME}}\\${{APP_NAME}}" "InstallPath"
RequestExecutionLevel admin
ShowInstDetails show
ShowUninstDetails show

; Иконки
!define MUI_ICON "icons\\app_icon.ico"
!define MUI_UNICON "icons\\uninstall_icon.ico"

; Современный интерфейс
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"

; Страницы установки
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "$(MUILicense)"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Страницы удаления
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Языки
!insertmacro MUI_LANGUAGE "Russian"

; Функции
Function .onInit
  ; Проверка прав администратора
  UserInfo::GetAccountType
  pop $0
  ${{If}} $0 != "admin"
    MessageBox MB_OK|MB_ICONEXCLAMATION "Для установки требуются права администратора!"
    Quit
  ${{EndIf}}
  
  ; Проверка установленной версии
  ReadRegStr $0 HKLM "Software\\${{COMPANY_NAME}}\\${{APP_NAME}}" "Version"
  ${{If}} $0 != ""
    MessageBox MB_YESNO|MB_ICONQUESTION "Программа уже установлена. Переустановить?" IDYES yes IDNO no
    no:
      Quit
    yes:
  ${{EndIf}}
FunctionEnd

Function un.onInit
  MessageBox MB_YESNO|MB_ICONQUESTION "Удалить ${{APP_NAME}}?" IDYES yes IDNO no
  no:
    Quit
  yes:
FunctionEnd

; Секция установки
Section "Основные файлы" SecMain
  SectionIn RO
  
  SetOutPath "$INSTDIR"
  
  ; Копируем файлы программы
  File /r "dist\\*.*"
  File /r "icons\\*.*"
  File /r "docs\\*.*"
  File /r "examples\\*.*"
  
  ; Создаем директории
  CreateDirectory "$INSTDIR\\logs"
  CreateDirectory "$INSTDIR\\backups"
  CreateDirectory "$INSTDIR\\config"
  
  ; Записываем информацию об установке
  WriteRegStr HKLM "Software\\${{COMPANY_NAME}}\\${{APP_NAME}}" "Version" "${{APP_VERSION}}"
  WriteRegStr HKLM "Software\\${{COMPANY_NAME}}\\${{APP_NAME}}" "InstallPath" "$INSTDIR"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "DisplayName" "${{APP_NAME}}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "UninstallString" '"$INSTDIR\\uninstall.exe"'
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "DisplayVersion" "${{APP_VERSION}}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "Publisher" "${{COMPANY_NAME}}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "DisplayIcon" "$INSTDIR\\UAZ_AECS_Editor.exe"
  WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "NoModify" 1
  WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "NoRepair" 1
  
  ; Создаем деинсталлятор
  WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

Section "Ярлыки" SecShortcuts
  ; Ярлык в меню Пуск
  CreateDirectory "$SMPROGRAMS\\${{APP_NAME}}"
  CreateShortCut "$SMPROGRAMS\\${{APP_NAME}}\\${{APP_NAME}}.lnk" "$INSTDIR\\UAZ_AECS_Editor.exe" "" "$INSTDIR\\icons\\app_icon.ico" 0
  
  ; Ярлык на рабочем столе
  CreateShortCut "$DESKTOP\\${{APP_NAME}}.lnk" "$INSTDIR\\UAZ_AECS_Editor.exe" "" "$INSTDIR\\icons\\app_icon.ico" 0
  
  ; Ярлык быстрого запуска
  CreateShortCut "$QUICKLAUNCH\\${{APP_NAME}}.lnk" "$INSTDIR\\UAZ_AECS_Editor.exe" "" "$INSTDIR\\icons\\app_icon.ico" 0
SectionEnd

Section "Ассоциации файлов" SecAssoc
  ; Ассоциация с .uaec файлами
  WriteRegStr HKCR ".uaec" "" "UAZAECS.Firmware"
  WriteRegStr HKCR "UAZAECS.Firmware" "" "Файл прошивки УАЗ AECS"
  WriteRegStr HKCR "UAZAECS.Firmware\\DefaultIcon" "" "$INSTDIR\\icons\\firmware_icon.ico"
  WriteRegStr HKCR "UAZAECS.Firmware\\shell\\open\\command" "" '"$INSTDIR\\UAZ_AECS_Editor.exe" "%1"'
SectionEnd

Section "Распаковать примеры" SecExamples
  ; Создаем ярлык к примерам
  CreateShortCut "$SMPROGRAMS\\${{APP_NAME}}\\Примеры.lnk" "$INSTDIR\\examples"
SectionEnd

; Секция удаления
Section "Uninstall"
  ; Удаляем файлы
  RMDir /r "$INSTDIR"
  
  ; Удаляем ярлыки
  Delete "$DESKTOP\\${{APP_NAME}}.lnk"
  Delete "$QUICKLAUNCH\\${{APP_NAME}}.lnk"
  RMDir /r "$SMPROGRAMS\\${{APP_NAME}}"
  
  ; Удаляем записи реестра
  DeleteRegKey HKLM "Software\\${{COMPANY_NAME}}\\${{APP_NAME}}"
  DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}"
  
  ; Удаляем ассоциации файлов
  DeleteRegKey HKCR ".uaec"
  DeleteRegKey HKCR "UAZAECS.Firmware"
  
  ; Очищаем переменные окружения
  DeleteRegValue HKCU "Environment" "UAZ_AECS_EDITOR_PATH"
  SendMessage ${{HWND_BROADCAST}} ${{WM_WININICHANGE}} 0 "STR:Environment" /TIMEOUT=5000
SectionEnd

; Описание секций
LangString DESC_SecMain ${{LANG_RUSSIAN}} "Основные файлы программы"
LangString DESC_SecShortcuts ${{LANG_RUSSIAN}} "Создать ярлыки в меню Пуск и на рабочем столе"
LangString DESC_SecAssoc ${{LANG_RUSSIAN}} "Ассоциировать .uaec файлы с программой"
LangString DESC_SecExamples ${{LANG_RUSSIAN}} "Распаковать примеры прошивок"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT $SecMain $(DESC_SecMain)
  !insertmacro MUI_DESCRIPTION_TEXT $SecShortcuts $(DESC_SecShortcuts)
  !insertmacro MUI_DESCRIPTION_TEXT $SecAssoc $(DESC_SecAssoc)
  !insertmacro MUI_DESCRIPTION_TEXT $SecExamples $(DESC_SecExamples)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Лицензия
LicenseLangString MUILicense ${{LANG_RUSSIAN}} "license.txt"

; Файл лицензии
!insertmacro MUI_RESERVEFILE_LANGDLL
"""
    
    return nsis_script

# ============================================================================
# BAT ФАЙЛ ДЛЯ СОЗДАНИЯ УСТАНОВОЧНОГО ПАКЕТА
# ============================================================================

def create_build_script():
    """Создание BAT файла для сборки установочного пакета"""
    build_script = f"""@echo off
chcp 65001
title Сборка установочного пакета УАЗ AECS Editor

echo ============================================
echo   Сборка установочного пакета
echo   {InstallerConfig.APP_NAME} v{InstallerConfig.APP_VERSION}
echo ============================================
echo.

REM Проверка необходимых инструментов
echo Проверка установленных инструментов...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Ошибка: Python не установлен!
    pause
    exit /b 1
)

where pip >nul 2>nul
if %errorlevel% neq 0 (
    echo Ошибка: pip не установлен!
    pause
    exit /b 1
)

echo Python обнаружен: %python%
echo.

REM Создание виртуального окружения
echo Создание виртуального окружения...
python -m venv venv
if %errorlevel% neq 0 (
    echo Ошибка создания виртуального окружения!
    pause
    exit /b 1
)

echo Активация виртуального окружения...
call venv\\Scripts\\activate.bat
if %errorlevel% neq 0 (
    echo Ошибка активации виртуального окружения!
    pause
    exit /b 1
)

REM Установка зависимостей
echo Установка зависимостей...
pip install --upgrade pip
pip install pyinstaller==5.13.0
pip install tkinter pillow numpy pandas matplotlib
if %errorlevel% neq 0 (
    echo Ошибка установки зависимостей!
    pause
    exit /b 1
)

REM Создание структуры директорий
echo Создание структуры директорий...
mkdir dist 2>nul
mkdir build 2>nul
mkdir icons 2>nul
mkdir docs 2>nul
mkdir examples 2>nul

REM Копирование файлов программы
echo Копирование файлов программы...
copy /Y "uaz_aecs_editor.py" "dist\\"
copy /Y "requirements.txt" "dist\\"
copy /Y "README.md" "dist\\"
copy /Y "LICENSE" "dist\\"

REM Создание иконок (заглушки)
echo Создание иконок...
echo placeholder > icons\\app_icon.ico
echo placeholder > icons\\firmware_icon.ico
echo placeholder > icons\\uninstall_icon.ico

REM Создание документации
echo Создание документации...
echo # Руководство пользователя > docs\\manual.md
echo. >> docs\\manual.md
echo Программа для работы с прошивками ЭБУ УАЗ AECS >> docs\\manual.md

REM Создание примеров
echo Создание примеров про