import threading
import time

# === НАСТРОЙКИ ===
CPU_THREADS = 16     # сколько потоков грузят CPU
RAM_MB = 16028       # сколько MB занять (например 2048 = 2GB)
STEP_MB = 300        # шаг выделения памяти
DELAY = 0.05        # задержка между шагами

# === НАГРУЗКА CPU ===
def cpu_load():
    while True:
        x = 0
        for i in range(10_000_000):
            x += i * i

# === НАГРУЗКА RAM ===
def ram_load():
    data = []
    allocated = 0

    while allocated < RAM_MB:
        data.append(bytearray(1024 * 1024 * STEP_MB))
        allocated += STEP_MB
        print(f"RAM: {allocated} MB")
        time.sleep(DELAY)

    print("RAM заполнена, удерживаем...")
    while True:
        time.sleep(1)

# === ЗАПУСК ===
print("Запуск нагрузки...")

# CPU потоки
for _ in range(CPU_THREADS):
    t = threading.Thread(target=cpu_load)
    t.daemon = True
    t.start()

# RAM поток
ram_thread = threading.Thread(target=ram_load)
ram_thread.daemon = True
ram_thread.start()

# удержание программы
while True:
    time.sleep(1)