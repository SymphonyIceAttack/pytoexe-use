import keyboard
import time
import threading
import tkinter as tk
from tkinter import messagebox

# =============================
# CONFIGURACIÓN INICIAL
# =============================
running = False
listening = False
key1 = ""
key2 = ""
delay = 0.2


# =============================
# FUNCIONES
# =============================
def toggle_script():
    global running
    running = not running

    if running:
        status_label.config(text="ACTIVO", fg="green")
    else:
        status_label.config(text="INACTIVO", fg="red")


def send_key():
    time.sleep(delay)
    keyboard.press_and_release(key2)


def on_key_event(e):
    if running and e.event_type == "down" and e.name == key1:
        threading.Thread(target=send_key, daemon=True).start()


def start_listening():
    global key1, key2, delay, listening

    if listening:
        return

    key1 = entry_key1.get().lower().strip()
    key2 = entry_key2.get().lower().strip()

    try:
        delay = float(entry_delay.get())
        if delay < 0:
            raise ValueError
    except:
        messagebox.showerror("Error", "Delay inválido. Usa un número como 0.2")
        return

    if not key1 or not key2:
        messagebox.showerror("Error", "Debes ingresar ambas teclas")
        return

    try:
        keyboard.hook(on_key_event)
        keyboard.add_hotkey("F8", toggle_script)
    except:
        messagebox.showerror("Error", "Ejecuta el programa como administrador")
        return

    listening = True
    messagebox.showinfo("Listo", "Configurado correctamente.\nF8 = Activar / Desactivar")


def close_program():
    keyboard.unhook_all()
    root.destroy()


# =============================
# INTERFAZ
# =============================
root = tk.Tk()
root.title("Key Delay Pro")
root.geometry("360x320")
root.resizable(False, False)

tk.Label(root, text="TECLA 1 (detector)").pack(pady=6)
entry_key1 = tk.Entry(root)
entry_key1.pack()

tk.Label(root, text="TECLA 2 (se enviará después)").pack(pady=6)
entry_key2 = tk.Entry(root)
entry_key2.pack()

tk.Label(root, text="DELAY EN SEGUNDOS (ej: 0.2)").pack(pady=6)
entry_delay = tk.Entry(root)
entry_delay.insert(0, "0.2")
entry_delay.pack()

tk.Button(root, text="INICIAR", command=start_listening).pack(pady=12)

status_label = tk.Label(root, text="INACTIVO", fg="red", font=("Arial", 12, "bold"))
status_label.pack(pady=5)

tk.Label(root, text="F8 = Activar / Desactivar").pack(pady=5)

tk.Button(root, text="CERRAR", command=close_program).pack(pady=12)

root.mainloop()