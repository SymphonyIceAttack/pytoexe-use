import os
import shutil
from datetime import datetime
from tkinter import Tk, filedialog

# Extensiones y nombres de carpetas
PHOTO_EXTS = [".jpg", ".jpeg", ".png", ".heic", ".webp"]
VIDEO_EXTS = [".mp4", ".mov", ".avi", ".mkv"]
PHOTO_FOLDER = "Fotos"
SCREENSHOT_FOLDER = "Screenshots iPhone"
VIDEO_FOLDER = "Videos"

# Función para determinar tipo de archivo
def file_type(filename):
    name, ext = os.path.splitext(filename.lower())
    if ext in VIDEO_EXTS:
        return VIDEO_FOLDER
    elif "screenshot" in name or name.startswith("img_"):
        return SCREENSHOT_FOLDER
    elif ext in PHOTO_EXTS:
        return PHOTO_FOLDER
    else:
        return None

# Función para obtener año y mes
def file_date(file_path):
    timestamp = os.path.getmtime(file_path)
    dt = datetime.fromtimestamp(timestamp)
    return dt.year, dt.strftime("%B").upper()

# Pedir carpeta al usuario
Tk().withdraw()
FOLDER_PATH = filedialog.askdirectory(title="Selecciona la carpeta a organizar")
if not FOLDER_PATH:
    print("No se seleccionó carpeta. Saliendo...")
    exit()

# Recorrer archivos y organizar
for item in os.listdir(FOLDER_PATH):
    full_path = os.path.join(FOLDER_PATH, item)
    if os.path.isfile(full_path):
        tipo = file_type(item)
        if tipo:
            year, month = file_date(full_path)
            year_folder = os.path.join(FOLDER_PATH, str(year))
            month_folder = os.path.join(year_folder, f"{month} {year}")
            target_folder = os.path.join(month_folder, tipo)
            os.makedirs(target_folder, exist_ok=True)
            shutil.move(full_path, os.path.join(target_folder, item))

print("Organización completada.")
input("Presiona ENTER para salir...")