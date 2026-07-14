import os
import sys
import time
import threading
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
LOG_FILE_PATH = r"C:\Logs\log_file.log"

def setup_logger():
    """Настраивает логгер для записи в файл и вывода в консоль"""
    logger = logging.getLogger("USBCopyMonitor")
    logger.setLevel(logging.INFO)
    
    # Формат записи: Время | Уровень | Сообщение
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    # Хендлер для файла
    try:
        file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except PermissionError:
        print(f"ОШИБКА: Нет прав на запись в {LOG_FILE_PATH}. Проверьте существование папки C:\\Logs.")
        sys.exit(1)
    except FileNotFoundError:
        print(f"ОШИБКА: Папка для логов не найдена. Создайте C:\\Logs вручную.")
        sys.exit(1)

    # Хендлер для консоли (чтобы видеть происходящее в реальном времени)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger()

class USBCopyHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            msg = f"СОЗДАН ФАЙЛ: {event.src_path}"
            logger.info(msg)
            self.process_file(event.src_path, "created")

    def on_modified(self, event):
        # Игнорируем временные файлы браузеров или системных процессов, если нужно
        if not event.is_directory and not event.src_path.endswith(".tmp"):
            # Получаем размер файла для логирования
            try:
                size_bytes = os.path.getsize(event.src_path)
                size_mb = size_bytes / (1024 * 1024)
                msg = f"ИЗМЕНЕН ФАЙЛ (размер: {size_mb:.2f} MB): {event.src_path}"
                logger.info(msg)
                # Можно добавить логику: если файл еще копируется (размер растет), не обрабатывать сразу
                # self.process_file(event.src_path, "modified") 
            except FileNotFoundError:
                pass # Файл мог быть удален мгновенно

    def process_file(self, file_path, event_type):
        """Логика обработки и логирования результата"""
        try:
            # --- ЗДЕСЬ ВАША ЛОГИКА ---
            # Например, копирование в архив, проверка хеша и т.д.
            # Сейчас просто эмулируем обработку и логируем факт
            
            file_name = os.path.basename(file_path)
            dest_folder = r"C:\Logs\CopiedFiles" # Папка для сохранения копий (создайте её вручную!)
            
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)
                logger.warning(f"Папка назначения {dest_folder} не существовала, создана автоматически.")

            # Эмуляция "сохранения того, что копируется" (копируем сам файл в лог-папку)
            import shutil
            dest_path = os.path.join(dest_folder, file_name)
            
            # Копируем файл (блокирующая операция, лучше делать в отдельном потоке в продакшене)
            shutil.copy2(file_path, dest_path) 
            
            logger.success(f"УСПЕШНО ОБРАБОТАНО ({event_type}): {file_name} -> сохранен в {dest_path}")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {file_path}: {str(e)}")

# Добавляем кастомный уровень логирования 'SUCCESS' для наглядности
def add_success_level(logger):
    SUCCESS_LEVEL_NUM = 25
    logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")
    def success(self, message, *args, **kws):
        if self.isEnabledFor(SUCCESS_LEVEL_NUM):
            self._log(SUCCESS_LEVEL_NUM, message, args, **kws)
    logging.Logger.success = success

add_success_level(logger)

def get_usb_drives():
    drives = []
    if sys.platform == 'win32':
        import string
        import ctypes
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drive = f"{letter}:\\ "
                if ctypes.windll.kernel32.GetDriveTypeW(drive) == 2: # 2 = DRIVE_REMOVABLE
                    drives.append(drive.strip())
            bitmask >>= 1
    else:
        # Заглушка для не-Windows систем, так как путь лога жестко задан под Windows
        logger.error("Скрипт настроен под Windows (путь C:\\Logs). На других ОС требуется правка путей.")
        return []
    return drives

def monitor_drive(path):
    event_handler = USBCopyHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    logger.info(f"[МОНИТОРИНГ] Запущен для диска: {path}")
    return observer

def main():
    logger.info("=== ЗАПУСК СКРИПТА МОНИТОРИНГА USB ===")
    logger.info("Ожидание активности на USB-накопителях...")

    observers = []
    current_drives = get_usb_drives()
    
    if not current_drives:
        logger.warning("На момент запуска USB-накопители не обнаружены.")
    else:
        for drive in current_drives:
            obs = monitor_drive(drive)
            observers.append(obs)

    # Поток для отслеживания новых подключений
    def check_new_drives_loop():
        while True:
            time.sleep(5)
            new_drives = get_usb_drives()
            for drive in new_drives:
                if not any(drive.startswith(obs.watch.path) for obs in observers):
                    logger.info(f"\n[НОВОЕ УСТРОЙСТВО] Обнаружено новое устройство: {drive}")
                    obs = monitor_drive(drive)
                    observers.append(obs)

    thread = threading.Thread(target=check_new_drives_loop, daemon=True)
    thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Остановка скрипта пользователем (Ctrl+C)...")
        for obs in observers:
            obs.stop()
        for obs in observers:
            obs.join()
        logger.info("Все наблюдатели остановлены. Завершение работы.")

if __name__ == "__main__":
    main()