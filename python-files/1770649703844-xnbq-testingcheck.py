import os
import random
import string
import time
import ctypes
from datetime import datetime, timedelta


def random_date(start_year=2020, end_year=2025):
    """Генерирует случайную дату для подделки времени создания."""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    random_date = start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))
    return time.mktime(random_date.timetuple())


def mutate_file(input_file):
    # 1. Генерируем случайное имя файла
    new_name = "".join(random.choices(string.ascii_lowercase + string.digits, k=10)) + ".exe"

    try:
        with open(input_file, 'rb') as f:
            data = f.read()

        # 2. Меняем сигнатуру (добавляем случайный мусор в конец файла)
        # Это меняет размер файла и его MD5 хеш
        junk_size = random.randint(1024, 1024 * 50)  # Добавляем от 1 до 50 КБ мусора
        junk_data = os.urandom(junk_size)

        mutated_data = data + junk_data

        with open(new_name, 'wb') as f:
            f.write(mutated_data)

        # 3. Меняем дату создания, изменения и доступа
        rand_time = random_date()
        os.utime(new_name, (rand_time, rand_time))

        # (Опционально) Для Windows: меняем дату создания через ctypes
        handle = ctypes.windll.kernel32.CreateFileW(new_name, 256, 0, None, 3, 128, None)
        if handle != -1:
            ctypes_time = ctypes.c_longlong(int((rand_time * 10000000) + 116444736000000000))
            ctypes.windll.kernel32.SetFileTime(handle, ctypes.byref(ctypes_time), None, None)
            ctypes.windll.kernel32.CloseHandle(handle)

        print(f"[+] Успех!")
        print(f"[*] Новый файл: {new_name}")
        print(f"[*] Добавлено мусора: {junk_size} байт")

    except Exception as e:
        print(f"[-] Ошибка: {e}")


if __name__ == "__main__":
    # Укажи имя своего скомпилированного чита
    target = "main.exe"
    if os.path.exists(target):
        mutate_file(target)
    else:
        print(f"[-] Файл {target} не найден. Сначала скомпилируй его в EXE.")