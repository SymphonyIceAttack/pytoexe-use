import tkinter as tk
from tkinter import scrolledtext
import subprocess
import sys
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_bios_info():
    output_text.delete(1.0, tk.END)
    try:
        result = subprocess.run(["wmic", "bios", "get", "manufacturer,smbiosbiosversion,serialnumber"], 
                                capture_output=True, text=True, shell=True)
        output_text.insert(tk.END, "═══ BIOS INFORMATION ═══\n\n")
        output_text.insert(tk.END, result.stdout)
    except Exception as e:
        output_text.insert(tk.END, f"Error: {e}")

def get_boot_info():
    output_text.delete(1.0, tk.END)
    try:
        result = subprocess.run(["bcdedit", "/enum"], 
                                capture_output=True, text=True, shell=True)
        output_text.insert(tk.END, "═══ BOOT CONFIGURATION ═══\n\n")
        output_text.insert(tk.END, result.stdout)
    except Exception as e:
        output_text.insert(tk.END, f"Error: {e}")

def get_system_info():
    output_text.delete(1.0, tk.END)
    try:
        result = subprocess.run(["systeminfo"], 
                                capture_output=True, text=True, shell=True)
        output_text.insert(tk.END, "═══ COMPLETE SYSTEM INFO ═══\n\n")
        output_text.insert(tk.END, result.stdout[:5000])
    except Exception as e:
        output_text.insert(tk.END, f"Error: {e}")

# GUI
root = tk.Tk()
root.title("BIOS & Boot Info Tool v1.0")
root.geometry("750x550")
root.resizable(True, True)

# Admin check
if not is_admin():
    tk.messagebox.showwarning("Admin Required", "Kuch info ke liye 'Run as Administrator' better hai!\n\nRight-click karein aur 'Run as Administrator' select karein.")

title = tk.Label(root, text="System Information Tool", font=("Arial", 16, "bold"))
title.pack(pady=10)

frame = tk.Frame(root)
frame.pack(pady=10)

btn_bios = tk.Button(frame, text="🔍 Get BIOS Info", command=get_bios_info, bg="#4CAF50", fg="white", padx=15, pady=5, font=("Arial", 10))
btn_bios.pack(side=tk.LEFT, padx=5)

btn_boot = tk.Button(frame, text="📀 Get Boot Info", command=get_boot_info, bg="#2196F3", fg="white", padx=15, pady=5, font=("Arial", 10))
btn_boot.pack(side=tk.LEFT, padx=5)

btn_system = tk.Button(frame, text="🖥️ Full System Info", command=get_system_info, bg="#FF9800", fg="white", padx=15, pady=5, font=("Arial", 10))
btn_system.pack(side=tk.LEFT, padx=5)

output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=90, height=25, font=("Consolas", 9))
output_text.pack(pady=10, padx=10)

root.mainloop()