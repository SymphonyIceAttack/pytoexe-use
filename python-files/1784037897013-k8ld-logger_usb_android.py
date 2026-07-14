import os
import socket
import platform
from datetime import datetime
import subprocess
import ctypes

# --- МАГИЯ СКРЫТИЯ ОКНА (Работает даже для .py файлов) ---
try:
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 0)
except Exception:
    pass
# ---------------------------------------------------------

BASE_LOG_DIR = r"C:\Logs"
ANDROID_FOLDERS = {"DCIM", "Pictures", "Android", "Camera", "Movies", "Music", "Download"}

def log_error(message):
    try:
        os.makedirs(BASE_LOG_DIR, exist_ok=True)
        # Для ошибок тоже используем имя ПК
        hostname = socket.gethostname()
        error_log_file = os.path.join(BASE_LOG_DIR, f"{hostname}_error.log")
        with open(error_log_file, "a", encoding="utf-8") as f:
            f.write(f"[ERROR] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    except:
        pass

def get_system_info():
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hostname": socket.gethostname(),
        "username": os.environ.get("USERNAME") or os.environ.get("USER", "unknown"),
        "os_name": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "cwd": os.getcwd(),
        "python_version": platform.python_version(),
    }

def run_wmic_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=False,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        output = result.stdout.decode('cp866', errors='replace')
        error = result.stderr.decode('cp866', errors='replace') if result.stderr else ""
        if result.returncode != 0:
            return None, f"Ошибка WMIC: {error}"
        return output, None
    except subprocess.TimeoutExpired:
        return None, "Ошибка: выполнение команды WMIC заняло слишком много времени."
    except Exception as e:
        return None, str(e)

def get_usb_devices_wmic():
    cmd = 'wmic path Win32_USBControllerDevice get Dependent | find "USBSTOR"'
    output, err = run_wmic_command(cmd)
    if err:
        return err
    return output if output.strip() else "(Нет подключенных устройств USBSTOR)"

def find_android_folders():
    result_lines = []
    result_lines.append("Поиск папок Android на съёмных дисках:")
    disk_cmd = 'wmic logicaldisk get Caption,Description,DriveType'
    output, err = run_wmic_command(disk_cmd)
    if err:
        return [f"Не удалось получить список дисков: {err}"]

    lines = output.strip().splitlines()
    removable_drives = []

    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 3:
            continue
        drive_letter = parts[0].strip()
        drive_type = parts[-1].strip()
        if drive_type == "2":
            removable_drives.append(drive_letter)

    if not removable_drives:
        return ["Съёмные диски не найдены."]

    result_lines.append(f"Найдено съёмных дисков: {', '.join(removable_drives)}\n")

    for drive in removable_drives:
        root_path = f"{drive}\\"
        result_lines.append(f"--- Проверка диска {drive} ---")
        found_any = False
        try:
            if os.path.exists(root_path):
                entries = os.listdir(root_path)
                for entry in entries:
                    entry_path = os.path.join(root_path, entry)
                    if os.path.isdir(entry_path):
                        folder_name = entry.strip().lower()
                        if folder_name in {f.lower() for f in ANDROID_FOLDERS}:
                            result_lines.append(f"[НАЙДЕНО] {entry_path}")
                            found_any = True
                if not found_any:
                    result_lines.append(f"[Нет характерных папок Android]")
            else:
                result_lines.append(f"[Диск недоступен или не смонтирован]")
        except PermissionError:
            result_lines.append(f"[Отказано в доступе к диску {drive}]")
        except Exception as e:
            result_lines.append(f"[Ошибка при сканировании {drive}: {e}]")

    return result_lines

def save_to_log(info, usb_output, android_results, log_file):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"LOG ENTRY: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        f.write("--- SYSTEM INFO ---\n")
        for key, value in info.items():
            f.write(f"{key}: {value}\n")
        f.write("\n--- USB DEVICES (WMIC OUTPUT) ---\n")
        f.write(str(usb_output) + "\n")
        f.write("\n--- ANDROID FOLDERS SEARCH RESULTS ---\n")
        for line in android_results:
            f.write(line + "\n")
        f.write("=" * 60 + "\n\n")

if __name__ == "__main__":
    try:
        system_info = get_system_info()
        hostname = system_info["hostname"]  # берём имя ПК из системной информации
        log_file_path = os.path.join(BASE_LOG_DIR, f"{hostname}.log")  # лог по имени ПК

        usb_data = get_usb_devices_wmic()
        android_data = find_android_folders()

        save_to_log(system_info, usb_data, android_data, log_file_path)

    except PermissionError:
        log_error("Нет прав на запись в C:\\Logs. Требуется запуск от администратора.")
    except Exception as e:
        log_error(f"Критическая ошибка скрипта: {str(e)}")