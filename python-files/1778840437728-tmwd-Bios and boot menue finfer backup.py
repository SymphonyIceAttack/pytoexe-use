import tkinter as tk
from tkinter import scrolledtext
import subprocess

def get_manufacturer():
    try:
        result = subprocess.run(["wmic", "computersystem", "get", "manufacturer"], 
                                capture_output=True, text=True, shell=True)
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:
            return lines[1].strip()
    except:
        pass
    return "Unknown"

def get_model():
    try:
        result = subprocess.run(["wmic", "computersystem", "get", "model"], 
                                capture_output=True, text=True, shell=True)
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:
            return lines[1].strip()
    except:
        pass
    return "Unknown"

def get_keys(manufacturer, model):
    # Latest database 2024-2025
    db = {
        "Dell": ("F2", "F12"),
        "HP": ("F10", "F9"),
        "Hewlett-Packard": ("F10", "F9"),
        "Lenovo ThinkPad": ("Enter then F1", "F12"),
        "Lenovo": ("F2 or Fn+F2", "F12"),
        "LENOVO": ("F2 or Fn+F2", "F12"),
        "Acer": ("F2", "F12"),
        "Asus": ("F2 or Del", "F8 or Esc"),
        "ASUSTeK": ("F2 or Del", "F8 or Esc"),
        "MSI": ("Del", "F11"),
        "Gigabyte": ("Del", "F12"),
        "Intel": ("F2", "F10"),
        "Microsoft": ("Volume Up + Power", "Volume Down + Power"),
        "Samsung": ("F2", "F12 or Esc"),
        "Sony": ("F2", "F11 or Esc"),
        "Toshiba": ("F2", "F12 or F2"),
        "Huawei": ("F2", "F12"),
        "Xiaomi": ("F2", "F10"),
        "Realme": ("F2", "F12"),
        "LG": ("F2", "F9 or F12"),
        "Razer": ("F1", "F12"),
    }
    
    for key in db:
        if key.lower() in manufacturer.lower():
            return db[key]
    
    # Default for latest PCs
    return ("F2 or Del", "F12 or Esc")

def show_info():
    manufacturer = get_manufacturer()
    model = get_model()
    bios_key, boot_key = get_keys(manufacturer, model)
    
    info_text = f"""
═══════════════════════════════════════
         🖥️  SYSTEM INFO
═══════════════════════════════════════

Manufacturer: {manufacturer}
Model: {model}

═══════════════════════════════════════
         🔑  ACCESS KEYS
═══════════════════════════════════════

🔧 BIOS / UEFI SETUP ke liye:
   👉 Press [{bios_key}]

📀 BOOT MENU ke liye:
   👉 Press [{boot_key}]

═══════════════════════════════════════
         💡  TIPS
═══════════════════════════════════════

• PC restart karte hi repeatedly press karein
• Kuch laptops mein Fn key bhi press karni padti hai
• Windows 11 Fast Boot mein restart karna better hai
═══════════════════════════════════════
    """
    
    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, info_text)

# GUI
root = tk.Tk()
root.title("BIOS & Boot Key Finder v2.0 (Latest)")
root.geometry("600x500")
root.configure(bg="#1a1a2e")

title = tk.Label(root, text="🔍 BIOS & BOOT KEY FINDER", 
                font=("Arial", 16, "bold"), bg="#1a1a2e", fg="#00ff88")
title.pack(pady=20)

subtitle = tk.Label(root, text="Supports 2024-2025 PCs | 100% Offline", 
                   font=("Arial", 9), bg="#1a1a2e", fg="#888888")
subtitle.pack(pady=0)

btn = tk.Button(root, text="🔎 DETECT MY PC KEYS", command=show_info,
               bg="#00ff88", fg="#1a1a2e", font=("Arial", 13, "bold"),
               padx=25, pady=10, relief=tk.RAISED)
btn.pack(pady=20)

output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=15,
                                        font=("Consolas", 10), bg="#0f0f1a", fg="#00ff88",
                                        insertbackground="white")
output_text.pack(pady=10, padx=20)

footer = tk.Label(root, text="© Ultimate Key Finder | Works on ALL latest PCs", 
                 bg="#1a1a2e", fg="#555555", font=("Arial", 8))
footer.pack(pady=10)

root.mainloop()