import shutil
import tkinter as tk
from tkinter import messagebox

# Define o drive (Windows)
drive = "C:\\"

# Obtém espaço total e livre
total, used, free = shutil.disk_usage(drive)

# Calcula porcentagem usada
percent = round((used / total) * 100)

print(f"Uso atual do disco {drive}: {percent}%")

# Só alerta se >= 80%
if percent >= 80:
    root = tk.Tk()
    root.withdraw()  # Esconde janela principal
    
    messagebox.showwarning(
        "⚠ Aviso de Disco",
        f"ATENÇÃO!\n\nO disco {drive} está com {percent}% de uso.\n\nConsidere liberar espaço."
    )

    root.destroy()