import tkinter as tk
from tkinter import scrolledtext
import subprocess
import winreg
import ctypes

def run_as_admin():
    """Check if running as admin"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_manufacturer_model_final():
    """Multiple methods se detect karo - Guaranteed working"""
    manufacturer = "Unknown"
    model = "Unknown"
    
    # ========== METHOD 1: Registry (Most reliable) ==========
    try:
        # Try HKLM\SYSTEM\CurrentControlSet\Control\SystemInformation
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                            r"SYSTEM\CurrentControlSet\Control\SystemInformation")
        try:
            manufacturer = winreg.QueryValueEx(key, "SystemManufacturer")[0]
        except:
            pass
        try:
            model = winreg.QueryValueEx(key, "SystemProductName")[0]
        except:
            pass
        winreg.CloseKey(key)
    except:
        pass
    
    # Agar registry se nahi mila toh try karo alternate registry path
    if manufacturer == "Unknown" or model == "Unknown":
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                r"HARDWARE\DESCRIPTION\System\BIOS")
            try:
                manufacturer = winreg.QueryValueEx(key, "SystemManufacturer")[0]
            except:
                pass
            try:
                model = winreg.QueryValueEx(key, "SystemProductName")[0]
            except:
                pass
            winreg.CloseKey(key)
        except:
            pass
    
    # ========== METHOD 2: WMIC (Backup) ==========
    if manufacturer == "Unknown" or model == "Unknown":
        try:
            # BIOS se manufacturer
            result = subprocess.run(["wmic", "bios", "get", "manufacturer", "/value"], 
                                    capture_output=True, text=True, shell=True, timeout=5)
            for line in result.stdout.split("\n"):
                if "Manufacturer=" in line:
                    manufacturer = line.split("=")[1].strip()
                    break
        except:
            pass
        
        try:
            # Computer system se model
            result = subprocess.run(["wmic", "computersystem", "get", "model", "/value"], 
                                    capture_output=True, text=True, shell=True, timeout=5)
            for line in result.stdout.split("\n"):
                if "Model=" in line:
                    model = line.split("=")[1].strip()
                    break
        except:
            pass
    
    # ========== METHOD 3: systeminfo (Last resort) ==========
    if manufacturer == "Unknown" or model == "Unknown":
        try:
            result = subprocess.run(["systeminfo"], 
                                    capture_output=True, text=True, shell=True, timeout=10)
            for line in result.stdout.split("\n"):
                if "System Manufacturer" in line and manufacturer == "Unknown":
                    manufacturer = line.split(":")[-1].strip()
                if "System Model" in line and model == "Unknown":
                    model = line.split(":")[-1].strip()
        except:
            pass
    
    # Clean up
    manufacturer = manufacturer.strip()
    model = model.strip()
    
    if manufacturer == "" or manufacturer == "To be filled by O.E.M.":
        manufacturer = "Unknown (Generic PC)"
    if model == "" or model == "To be filled by O.E.M.":
        model = "Unknown"
    
    return manufacturer, model

def get_keys(manufacturer, model):
    m = manufacturer.lower()
    
    # Debug info
    print(f"Detected: Manufacturer={manufacturer}, Model={model}")
    
    # Lenovo
    if "lenovo" in m:
        if "thinkpad" in model.lower():
            return ("F1", "F12")
        else:
            return ("F1 or F2", "F12")
    
    # Dell
    elif "dell" in m:
        return ("F2", "F12")
    
    # HP
    elif "hp" in m or "hewlett" in m:
        return ("F10", "F9")
    
    # Asus
    elif "asus" in m or "asustek" in m:
        return ("F2 or Del", "F8 or Esc")
    
    # Acer
    elif "acer" in m:
        return ("F2", "F12")
    
    # MSI
    elif "msi" in m:
        return ("Del", "F11")
    
    # Gigabyte
    elif "gigabyte" in m:
        return ("Del", "F12")
    
    # Default
    else:
        return ("F2 or Del", "F12 or Esc")

def show_info():
    manufacturer, model = get_manufacturer_model_final()
    bios_key, boot_key = get_keys(manufacturer, model)
    
    info_text = f"""
╔══════════════════════════════════════════════════════════════╗
║                    🖥️  SYSTEM INFORMATION                      ║
╚══════════════════════════════════════════════════════════════╝

   📌 Manufacturer : {manufacturer}
   📌 Model        : {model}

╔══════════════════════════════════════════════════════════════╗
║                    🔑  ACCESS KEYS                             ║
╚══════════════════════════════════════════════════════════════╝

   🔧 BIOS / UEFI SETUP  :  Press [ {bios_key} ]
   
   📀 BOOT MENU          :  Press [ {boot_key} ]

╔══════════════════════════════════════════════════════════════╗
║                    💡  TIPS                                   ║
╚══════════════════════════════════════════════════════════════╝

   • PC restart karte hi repeatedly press karein
   • Kuch laptops mein Fn + Key press karna padta hai
   • Windows 11 mein "Restart" karein, "Shut down" nahi

╚══════════════════════════════════════════════════════════════╝
    """
    
    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, info_text)

# ========== GUI ==========
root = tk.Tk()
root.title("BIOS & Boot Key Finder - Pro")
root.geometry("650x550")
root.configure(bg="#0d0d0d")

# Title
title = tk.Label(root, text="🔍 BIOS & BOOT KEY FINDER PRO", 
                font=("Arial", 18, "bold"), bg="#0d0d0d", fg="#00ff88")
title.pack(pady=20)

subtitle = tk.Label(root, text="100% Offline | Registry + WMIC + SystemInfo", 
                   font=("Arial", 9), bg="#0d0d0d", fg="#666666")
subtitle.pack(pady=0)

# Detect Button
btn = tk.Button(root, text="🔎 DETECT MY PC KEYS", command=show_info,
               bg="#00ff88", fg="#000000", font=("Arial", 14, "bold"),
               padx=30, pady=12, cursor="hand2")
btn.pack(pady=25)

# Output Area
output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=72, height=18,
                                        font=("Consolas", 10), bg="#1a1a1a", fg="#00ff88",
                                        insertbackground="white")
output_text.pack(pady=10, padx=20)

# Footer
footer = tk.Label(root, text="✓ Works on: Dell | Lenovo | HP | Asus | Acer | MSI | Gigabyte", 
                 bg="#0d0d0d", fg="#444444", font=("Arial", 8))
footer.pack(pady=10)

# Show initial info
root.after(100, show_info)

root.mainloop()