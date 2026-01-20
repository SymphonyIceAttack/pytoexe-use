import subprocess
import time
import tkinter as tk
from tkinter import messagebox

url = "https://streamable.com/yuyj9r"
brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

# Crear ventana principal (oculta)
root = tk.Tk()
root.withdraw()  # Oculta la ventana base

# Primera pregunta
resp = messagebox.askyesno(
    "Confirmación",
    "¿Desea ejecutar este programa?"
)

if not resp:
    exit()

# Segunda pregunta
resp = messagebox.askyesno(
    "Confirmación",
    "¿Está seguro?"
)

if not resp:
    exit()

# Ejecutar el programa
for i in range(50):
    subprocess.Popen([
        brave_path,
        "--new-window",
        "--window-size=400,300",
        url
    ])
    time.sleep(1.5)
