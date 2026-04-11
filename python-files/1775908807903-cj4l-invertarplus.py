import psutil
import wmi
import tkinter as tk
from tkinter import ttk

def get_system_info():
    info = {}

    # CPU
    info["cpu"] = psutil.cpu_percent(interval=1)

    # RAM
    ram = psutil.virtual_memory()
    info["ram_total"] = round(ram.total / (1024**3), 2)
    info["ram_used"] = round(ram.used / (1024**3), 2)
    info["ram_percent"] = ram.percent

    # DISK (psutil)
    disk = psutil.disk_usage('/')
    info["disk_total"] = round(disk.total / (1024**3), 2)
    info["disk_used"] = round(disk.used / (1024**3), 2)
    info["disk_percent"] = disk.percent

    # HDD (WMI - Windows)
    c = wmi.WMI()
    disks = []
    for d in c.Win32_DiskDrive():
        disks.append({
            "model": d.Model,
            "size": round(int(d.Size) / (1024**3), 2),
            "serial": d.SerialNumber
        })

    info["hdd"] = disks

    return info


def show_info():
    data = get_system_info()

    output = ""
    output += f"CPU Usage: {data['cpu']}%\n\n"

    output += "RAM:\n"
    output += f"  Total: {data['ram_total']} GB\n"
    output += f"  Used: {data['ram_used']} GB\n"
    output += f"  Usage: {data['ram_percent']}%\n\n"

    output += "Disk:\n"
    output += f"  Total: {data['disk_total']} GB\n"
    output += f"  Used: {data['disk_used']} GB\n"
    output += f"  Usage: {data['disk_percent']}%\n\n"

    output += "HDD Info:\n"
    for h in data["hdd"]:
        output += f"  Model: {h['model']}\n"
        output += f"  Size: {h['size']} GB\n"
        output += f"  Serial: {h['serial']}\n\n"

    text.delete(1.0, tk.END)
    text.insert(tk.END, output)


# GUI
root = tk.Tk()
root.title("IT Inventory Tool")
root.geometry("600x500")

btn = ttk.Button(root, text="Get System Info", command=show_info)
btn.pack(pady=10)

text = tk.Text(root, wrap="word")
text.pack(expand=True, fill="both")

root.mainloop()