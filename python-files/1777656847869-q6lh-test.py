import platform
import psutil
import GPUtil
import socket
from datetime import datetime

def get_size(bytes, suffix="B"):
    """Переводит байты в человекочитаемый вид"""
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

def main():
    print("="*60)
    print(" "*15 + "SYSTEM INFO CHECKER v1.0")
    print("="*60)
    print(f"Время проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*60)

    # 1. Операционная система
    print("\n[1] ОПЕРАЦИОННАЯ СИСТЕМА")
    print(f"  Система: {platform.system()} {platform.release()} ({platform.version()})")
    print(f"  Архитектура: {platform.machine()}")
    print(f"  Имя компьютера: {socket.gethostname()}")

    # 2. Процессор
    print("\n[2] ПРОЦЕССОР (CPU)")
    print(f"  Модель: {platform.processor()}")
    cpu_freq = psutil.cpu_freq()
    if cpu_freq:
        print(f"  Тактовая частота: {cpu_freq.current:.2f} МГц")
    print(f"  Ядер (физических): {psutil.cpu_count(logical=False)}")
    print(f"  Потоков (логических): {psutil.cpu_count(logical=True)}")
    cpu_percent = psutil.cpu_percent(interval=1)
    print(f"  Загрузка (в момент запроса): {cpu_percent}%")

    # 3. Оперативная память (RAM)
    print("\n[3] ОПЕРАТИВНАЯ ПАМЯТЬ (RAM)")
    mem = psutil.virtual_memory()
    print(f"  Всего: {get_size(mem.total)}")
    print(f"  Доступно: {get_size(mem.available)}")
    print(f"  Используется: {get_size(mem.used)} ({mem.percent}%)")

    # 4. Видеокарта (GPU) через GPUtil
    print("\n[4] ВИДЕОКАРТА (GPU)")
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            for i, gpu in enumerate(gpus):
                print(f"  GPU {i+1}: {gpu.name}")
                print(f"    Загрузка: {gpu.load*100:.1f}%")
                print(f"    Память: всего {gpu.memoryTotal} MB / используется {gpu.memoryUsed} MB")
                print(f"    Температура: {gpu.temperature}°C")
        else:
            print("  Не найдена или драйвер NVIDIA не установлен.")
    except Exception as e:
        print(f"  Не удалось получить данные о GPU: {e}")
        print("  (Для NVIDIA нужен драйвер и установленный GPUtil: pip install gputil)")

    # 5. Диски (хранилища)
    print("\n[5] ДИСКИ И РАЗДЕЛЫ")
    partitions = psutil.disk_partitions()
    for partition in partitions:
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            print(f"  Диск {partition.device} ({partition.mountpoint})")
            print(f"    Тип: {partition.fstype}")
            print(f"    Всего: {get_size(usage.total)}")
            print(f"    Свободно: {get_size(usage.free)} ({usage.percent}% занято)")
        except PermissionError:
            continue

    # 6. Сеть — IP-адреса
    print("\n[6] СЕТЬ")
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
        print(f"  Локальный IP: {local_ip}")
    except:
        print("  Локальный IP: не определён")

    # 7. Дополнительно — uptime системы
    print("\n[7] РАБОТА СИСТЕМЫ")
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    print(f"  Включён с: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}")
    days = uptime.days
    hours = uptime.seconds // 3600
    minutes = (uptime.seconds % 3600) // 60
    print(f"  Время работы: {days} дн, {hours} ч, {minutes} мин")

    print("\n" + "="*60)
    print(" "*20 + "ПРОВЕРКА ЗАВЕРШЕНА")
    print("="*60)
    input("\nНажмите Enter, чтобы выйти...")

if __name__ == "__main__":
    main()