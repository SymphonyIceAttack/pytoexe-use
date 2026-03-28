import tkinter as tk
from tkinter import ttk
import psutil

def get_size(bytes, suffix="B"):
    """
    Конвертирует байты в читаемый формат (KB, MB, GB и т. д.)
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f} {unit}{suffix}"
        bytes /= factor

def update_memory_info():
    """
    Обновляет информацию о памяти и отображает её в интерфейсе.
    """
    # Информация о RAM
    ram = psutil.virtual_memory()
    ram_total = get_size(ram.total)
    ram_available = get_size(ram.available)
    ram_used = get_size(ram.used)
    ram_percent = ram.percent

    # Информация о ROM (дисковая память) — берём первый диск
    disk = psutil.disk_usage('/')
    disk_total = get_size(disk.total)
    disk_used = get_size(disk.used)
    disk_free = get_size(disk.free)
    disk_percent = disk.percent

    # Обновляем текстовые поля
    ram_total_label.config(text=f"Всего RAM: {ram_total}")
    ram_available_label.config(text=f"Доступно RAM: {ram_available}")
    ram_used_label.config(text=f"Использовано RAM: {ram_used} ({ram_percent}%)")

    disk_total_label.config(text=f"Всего ROM: {disk_total}")
    disk_used_label.config(text=f"Использовано ROM: {disk_used} ({disk_percent}%)")
    disk_free_label.config(text=f"Свободно ROM: {disk_free}")

    # Запускаем обновление каждые 2 секунды
    root.after(2000, update_memory_info)

# Создаём главное окно
root = tk.Tk()
root.title("Информация о памяти")
root.geometry("400x300")
root.resizable(False, False)

# Стиль
style = ttk.Style()
style.theme_use("clam")

# Фрейм для RAM
ram_frame = ttk.LabelFrame(root, text="Оперативная память (RAM)", padding=10)
ram_frame.pack(fill="x", padx=10, pady=5)

ram_total_label = ttk.Label(ram_frame, text="Всего RAM: ")
ram_total_label.pack(anchor="w")

ram_available_label = ttk.Label(ram_frame, text="Доступно RAM: ")
ram_available_label.pack(anchor="w")

ram_used_label = ttk.Label(ram_frame, text="Использовано RAM: ")
ram_used_label.pack(anchor="w")

# Фрейм для ROM
disk_frame = ttk.LabelFrame(root, text="Дисковая память (ROM)", padding=10)
disk_frame.pack(fill="x", padx=10, pady=5)

disk_total_label = ttk.Label(disk_frame, text="Всего ROM: ")
disk_total_label.pack(anchor="w")

disk_used_label = ttk.Label(disk_frame, text="Использовано ROM: ")
disk_used_label.pack(anchor="w")

disk_free_label = ttk.Label(disk_frame, text="Свободно ROM: ")
disk_free_label.pack(anchor="w")

# Кнопка обновления (на случай, если нужно обновить вручную)
update_button = ttk.Button(root, text="Обновить", command=update_memory_info)
update_button.pack(pady=10)

# Первое обновление информации
update_memory_info()

# Запуск главного цикла
root.mainloop()
