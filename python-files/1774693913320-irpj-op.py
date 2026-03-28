import psutil

# Информация о RAM
ram = psutil.virtual_memory()
print(f"Общая RAM: {ram.total / (1024**3):.2f} ГБ")
print(f"Использовано RAM: {ram.used / (1024**3):.2f} ГБ ({ram.percent}%)")
print(f"Свободно RAM: {ram.available / (1024**3):.2f} ГБ")

# Информация о дисковом пространстве (ROM)
disk = psutil.disk_usage('/')
print(f"\nОбщее дисковое пространство: {disk.total / (1024**3):.2f} ГБ")
print(f"Использовано: {disk.used / (1024**3):.2f} ГБ ({disk.percent}%)")
print(f"Свободно: {disk.free / (1024**3):.2f} ГБ")
