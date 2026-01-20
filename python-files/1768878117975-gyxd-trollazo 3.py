
# BSOD FALSA SIN PYGAME
# SALIDA SECRETA: CTRL + ALT + Q

import tkinter as tk
import random
import time
import threading
import sys
import ctypes

# -------- CONFIG --------
DELAY_INICIAL = random.randint(25, 60)  # segundos
BLUE = "#0078D7"
WHITE = "#F5F5F5"

# -------- OCULTAR CONSOLA (WINDOWS) --------
ctypes.windll.user32.ShowWindow(
    ctypes.windll.kernel32.GetConsoleWindow(), 0
)

# -------- VENTANA --------
root = tk.Tk()
root.configure(bg=BLUE)
root.attributes("-fullscreen", True)
root.overrideredirect(True)
root.withdraw()  # empieza oculta

WIDTH = root.winfo_screenwidth()
HEIGHT = root.winfo_screenheight()

progress = 0

# -------- SALIDA SECRETA --------
def exit_program(event=None):
    root.destroy()
    sys.exit()

root.bind("<Control-Alt-q>", exit_program)

# -------- UI BSOD --------
sad_label = tk.Label(
    root, text=":(", font=("Segoe UI", 72),
    fg=WHITE, bg=BLUE
)
sad_label.place(x=80, y=60)

text1 = tk.Label(
    root,
    text="Your PC ran into a problem and needs to restart.",
    font=("Segoe UI", 26),
    fg=WHITE, bg=BLUE
)
text1.place(x=80, y=160)

text2 = tk.Label(
    root,
    text="We're just collecting some error info, and then we'll restart for you.",
    font=("Segoe UI", 26),
    fg=WHITE, bg=BLUE
)
text2.place(x=80, y=200)

progress_label = tk.Label(
    root, text="0% complete",
    font=("Segoe UI", 22),
    fg=WHITE, bg=BLUE
)
progress_label.place(x=80, y=260)

error_label = tk.Label(
    root,
    text="Stop code: CRITICAL_PROCESS_DIED",
    font=("Segoe UI", 22),
    fg=WHITE, bg=BLUE
)
error_label.place(x=80, y=HEIGHT - 120)

# -------- LÓGICA --------
def show_bsod():
    global progress
