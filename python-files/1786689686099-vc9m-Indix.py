import hashlib
import os
import re
from pathlib import Path
from datetime import datetime
import socket

# Функция для вычисления MD5 файла
def calculate_md5(file_path):
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest().upper()
    except Exception as e:
        print(f"Ошибка при вычислении MD5: {e}")
        return None

# Функция для вычисления SHA256 файла
def calculate_sha256(file_path):
    try:
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest().upper()
    except Exception as e:
        print(f"Ошибка при вычислении SHA256: {e}")
        return None

# Функция парсинга файла с индикаторами
def parse_indicators(file_path):
    indicators = {
        'md5': set(),
        'sha256': set(),
        'files': set()
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Извлечение MD5
                md5_match = re.search(r'md5":"?([A-F0-9]{32})', line)
                if md5_match:
                    indicators['md5'].add(md5_match.group(1))
                    
                # Извлечение SHA256
                sha256_match = re.search(r'SHA256":?"?([A-F0-9]{64})', line)
                if sha256_match:
                    indicators['sha256'].add(sha256_match.group(1))
                    
                # Извлечение имен файлов
                file_match = re.search(r'([^\\\s]+\.[^.\\\s]+)', line)
                if file_match:
                    indicators['files'].add(file_match.group(1))
                    
    except Exception as e:
        print(f"Ошибка при чтении файла индикаторов: {e}")
    
    return indicators

def write_log(log_path, message):
    """Дописывает сообщение в лог-файл с временной меткой."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    try:
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)
    except Exception as e:
        # Если не удаётся записать в лог — выводим ошибку в консоль
        print(f"Не удалось записать в лог: {e}")

def main():
    # Путь к файлу с индикаторами
    indicators_file = r'\\srv-dns-01\Indix\indix.txt'
    
    # Получаем индикаторы из файла
    indicators = parse_indicators(indicators_file)
    
    # Путь к директории для сканирования
    scan_directory = r'C:\Users'  # Укажите нужную директорию
    
    # Получаем имя компьютера
    computer_name = socket.gethostname()
    
    # Формируем путь к лог-файлу: \\srv-dns-01\Indix\ИМЯ_КОМПЬЮТЕРА_scan_log.txt
    log_filename = f"{computer_name}_scan_log.txt"
    log_path = os.path.join(r'\\srv-dns-01\Indix', log_filename)
    
    try:
        # Сканируем директорию
        for root, dirs, files in os.walk(scan_directory):
            for file in files:
                file_path = os.path.join(root, file)
                
                match_found = False
                log_messages = []
                
                # Проверяем имя файла
                if file in indicators['files']:
                    msg = f"Найден подозрительный файл по имени: {file_path}"
                    print(msg)
                    log_messages.append(msg)
                    match_found = True
                    
                # Вычисляем хеши
                file_md5 = calculate_md5(file_path)
                file_sha256 = calculate_sha256(file_path)
                
                # Проверяем MD5
                if file_md5 and file_md5 in indicators['md5']:
                    msg = f"Найден подозрительный файл по MD5: {file_path} (MD5={file_md5})"
                    print(msg)
                    log_messages.append(msg)
                    match_found = True
                    
                # Проверяем SHA256
                if file_sha256 and file_sha256 in indicators['sha256']:
                    msg = f"Найден подозрительный файл по SHA256: {file_path} (SHA256={file_sha256})"
                    print(msg)
                    log_messages.append(msg)
                    match_found = True
                
                # Если найдено совпадение — записываем в лог
                if match_found:
                    for msg in log_messages:
                        write_log(log_path, msg)
                    
    except Exception as e:
        error_msg = f"Ошибка при сканировании: {e}"
        print(error_msg)
        write_log(log_path, error_msg)

if __name__ == "__main__":
    main()