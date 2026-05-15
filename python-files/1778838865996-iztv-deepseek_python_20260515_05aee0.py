import tkinter as tk
from tkinter import messagebox
import subprocess
import sys

def get_manufacturer():
    try:
        result = subprocess.run(["wmic", "computersystem", "get", "manufacturer"], 
                                capture_output=True, text=True, shell=True)
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:
            manufacturer = lines[1].strip()
            return manufacturer
    except:
        pass
    return "Unknown"

def get_model():
    try:
        result = subprocess.run(["wmic", "computersystem", "get", "model"], 
                                capture_output=True, text=True, shell=True)
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:
            model = lines[1].strip()
            return model
    except:
        pass
    return "Unknown"

def get_keys(manufacturer):
    # BIOS key aur Boot Menu key ki dictionary
    keys_db = {
        "Dell": ("F2", "F12"),
        "HP": ("F10", "F9"),
        "Hewlett-Packard": ("F10", "F9"),
        "Lenovo": ("F1 or F2", "F12"),
        "LENOVO": ("F1 or F2", "F12"),
        "Acer": ("F2", "F12"),
        "Asus": ("F2 or Del", "F8 or Esc"),
        "ASUSTeK": ("F2 or Del", "F8 or Esc"),
        "MSI": ("Del", "F11"),
        "Gigabyte": ("Del", "F12"),
        "Intel": ("F2", "F10"),
        "Microsoft": ("F2", "F12"),  # Surface devices
    }
    
    for key in keys_db:
        if key.lower() in manufacturer.lower():
            return keys_db[key]
    
    # Default common keys
    return ("F2 or Del", "F12 or Esc")

def show_info():
    manufacturer = get_manufacturer()
    model = get_model()
    bios_key, boot_key = get_keys(manufacturer)
    
    info_text = f"""
═══════════════════════════════════
         SYSTEM INFORMATION
═══════════════════════════════════

Manufacturer: {manufacturer}
Model: {model}

═══════════════════════════════════
         ACCESS KEYS
═══════════════════════════════════

🔧 BIOS Setup (Settings) ke liye:
   → Press [{bios_key}] 

📀 Boot Menu ke liye:
   → Press [{boot_key}]

═══════════════════════════════════
💡 TIPS:
• PC restart karo aur turant key press karo
• Kabhi kabhi Fn key bhi press karni padti hai
═══════════════════════════════════
    """
    
    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, info_text)

# GUI banate hain
root = tk.Tk()
root.title("BIOS & Boot Menu Key Finder")
root.geometry("550x450")
root.resizable(False, False)

# Background color
root.configure(bg="#2c3e50")

title = tk.Label(root, text="🔍 BIOS & Boot Menu Key Finder", 
                font=("Arial", 16, "bold"), bg="#2c3e50", fg="white")
title.pack(pady=20)

btn = tk.Button(root, text="🔎 DETECT MY PC KEYS", command=show_info,
               bg="#3498db", fg="white", font=("Arial", 14, "bold"),
               padx=20, pady=10)
btn.pack(pady=20)

output_text = tk.Text(root, wrap=tk.WORD, width=60, height=15,
                      font=("Consolas", 11), bg="#ecf0f1", fg="#2c3e50")
output_text.pack(pady=10, padx=20)

# Footer
footer = tk.Label(root, text="© Simple Tool - Sirf Keys Batayega", 
                 bg="#2c3e50", fg="#95a5a6", font=("Arial", 8))
footer.pack(pady=10)

root.mainloop()