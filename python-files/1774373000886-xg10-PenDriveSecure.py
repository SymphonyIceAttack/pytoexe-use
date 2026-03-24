import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from cryptography.fernet import Fernet
import threading
import time
import psutil  # Para detección de unidades

# --- Funciones de detección ---
def listar_pen_drives():
    drives = []
    for part in psutil.disk_partitions(all=False):
        if 'removable' in part.opts or 'cdrom' in part.opts:
            drives.append(part.device)
    return drives

def actualizar_unidades():
    unidades = listar_pen_drives()
    combo_unidades['values'] = unidades
    if unidades:
        combo_unidades.current(0)
    root.after(3000, actualizar_unidades)  # Actualiza cada 3 segundos

# --- Funciones de operaciones ---
def mostrar_info():
    unidad = combo_unidades.get()
    if not unidad:
        messagebox.showwarning("Aviso", "Selecciona una unidad.")
        return
    try:
        total, usado, libre = shutil.disk_usage(unidad)
        info_text.set(f"Unidad: {unidad}\nTotal: {total//(1024*1024)} MB\nUsado: {usado//(1024*1024)} MB\nLibre: {libre//(1024*1024)} MB")
    except Exception as e:
        messagebox.showerror("Error", f"No se puede obtener información:\n{e}")

def backup():
    unidad = combo_unidades.get()
    if not unidad:
        messagebox.showwarning("Aviso", "Selecciona una unidad.")
        return
    carpeta_destino = filedialog.askdirectory(title="Selecciona carpeta de destino")
    if carpeta_destino:
        threading.Thread(target=realizar_backup, args=(unidad, carpeta_destino)).start()

def realizar_backup(unidad, destino):
    try:
        destino_final = os.path.join(destino, os.path.basename(unidad))
        shutil.copytree(unidad, destino_final, dirs_exist_ok=True)
        messagebox.showinfo("Éxito", "Backup completado.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo hacer backup:\n{e}")

def formatear():
    unidad = combo_unidades.get()
    if not unidad:
        messagebox.showwarning("Aviso", "Selecciona una unidad.")
        return
    confirm = messagebox.askyesno("Confirmar", f"¿Seguro que quieres formatear {unidad}?")
    if confirm:
        threading.Thread(target=realizar_formateo, args=(unidad,)).start()

def realizar_formateo(unidad):
    try:
        for root_dir, dirs, files in os.walk(unidad):
            for f in files:
                os.remove(os.path.join(root_dir, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root_dir, d))
        messagebox.showinfo("Éxito", f"{unidad} formateada correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo formatear:\n{e}")

# --- Cifrado con Fernet ---
def cifrar():
    unidad = combo_unidades.get()
    if not unidad:
        messagebox.showwarning("Aviso", "Selecciona una unidad.")
        return
    password = simpledialog.askstring("Contraseña", "Ingresa contraseña de cifrado:", show='*')
    if not password:
        return
    key = Fernet.generate_key()
    fernet = Fernet(key)
    carpeta = filedialog.askdirectory(title="Selecciona carpeta dentro del pen drive para cifrar")
    if carpeta:
        threading.Thread(target=cifrar_archivos, args=(carpeta, fernet)).start()
        # Guardar key en PC (para desencriptar después)
        with open(os.path.join(os.getcwd(), "key.key"), "wb") as kf:
            kf.write(key)

def cifrar_archivos(carpeta, fernet):
    for root_dir, dirs, files in os.walk(carpeta):
        for f in files:
            ruta = os.path.join(root_dir, f)
            with open(ruta, "rb") as file:
                datos = file.read()
            datos_enc = fernet.encrypt(datos)
            with open(ruta + ".enc", "wb") as file:
                file.write(datos_enc)
            os.remove(ruta)
    messagebox.showinfo("Cifrado", f"Archivos cifrados en {carpeta}. Clave guardada en {os.getcwd()}")

# --- Interfaz ---
root = tk.Tk()
root.title("Pen Drive Secure Tool")
root.geometry("450x400")

tk.Label(root, text="Selecciona unidad:").pack(pady=5)
combo_unidades = ttk.Combobox(root, values=listar_pen_drives())
combo_unidades.pack(pady=5)

info_text = tk.StringVar()
tk.Label(root, textvariable=info_text).pack(pady=10)

tk.Button(root, text="Mostrar Información", command=mostrar_info).pack(pady=5)
tk.Button(root, text="Backup de Unidad", command=backup).pack(pady=5)
tk.Button(root, text="Formatear Unidad", command=formatear).pack(pady=5)
tk.Button(root, text="Cifrar Archivos", command=cifrar).pack(pady=5)

# Actualización automática de unidades
root.after(1000, actualizar_unidades)
root.mainloop()