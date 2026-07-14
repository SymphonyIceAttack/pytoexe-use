import os
import socket
import platform
from datetime import datetime
import subprocess

LOG_PATH = r"C:\Logs"
LOG_FILE = os.path.join(LOG_PATH, "usb_logs.log")

def get_system_info():
    """Собирает информацию о системе и пользователе."""
    info = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hostname": socket.gethostname(),
        "username": os.environ.get("USERNAME") or os.environ.get("USER", "unknown"),
        "os_name": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        # Защита от пустой строки
        "processor": platform.processor() or "unknown",
        "cwd": os.getcwd(),
        "python_version": platform.python_version(),
    }
    return info

def get_usb_devices_wmic():
    """
    Выполняет команду wmic и возвращает её вывод.
    Обрабатывает кодировку, чтобы кириллица читалась корректно.
    """
    command = 'wmic path Win32_USBControllerDevice get Dependent | find "USBSTOR"'
    
    try:
        # shell=True нужен, чтобы работала труба (|) и find
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=False,  # Получаем байты для ручной обработки кодировки
            timeout=10   # Защита от зависания команды
        )
        
        # WMIC в Windows обычно выдает cp866. Пробуем декодировать.
        # Если у тебя специфическая консоль, возможно, придется поменять на 'cp437'
        output = result.stdout.decode('cp866', errors='replace')
        error = result.stderr.decode('cp866', errors='replace') if result.stderr else ""
        
        if result.returncode != 0 and not output.strip():
            return f"Ошибка выполнения WMIC: {error}"
            
        return output
    except subprocess.TimeoutExpired:
        return "Ошибка: выполнение команды заняло слишком много времени."
    except Exception as e:
        return f"Произошла ошибка при запуске WMIC: {str(e)}"

def save_to_log(info, usb_output, log_file):
    """Создаёт папку (если нет) и записывает информацию в лог-файл."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"LOG ENTRY: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("--- SYSTEM INFO ---\n")
        for key, value in info.items():
            f.write(f"{key}: {value}\n")
        
        f.write("\n--- USB DEVICES (WMIC OUTPUT) ---\n")
        # Добавляем вывод команды. Если он пустой, так и запишем
        if usb_output.strip():
            f.write(usb_output + "\n")
        else:
            f.write("(Нет подключенных устройств USBSTOR или команда вернула пустой результат)\n")
            
        f.write("=" * 60 + "\n\n")

if __name__ == "__main__":
    try:
        system_info = get_system_info()
        usb_data = get_usb_devices_wmic()
        save_to_log(system_info, usb_data, LOG_FILE)
        print(f"Информация успешно сохранена в {LOG_FILE}")
        
        # Опционально: показать результат и в консоль тоже
        print("\nРезультат WMIC:")
        print(usb_data)
        
    except PermissionError:
        print("Ошибка: нет прав на запись в C:\\Logs. Запустите скрипт от имени администратора.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")