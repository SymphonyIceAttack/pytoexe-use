import os
import shutil
import tkinter as tk
from tkinter import messagebox

def scan_system():
    temp_paths = ["C:\\Windows\\Temp", "C:\\Windows\\Prefetch"]
    found = []
    for path in temp_paths:
        if os.path.exists(path):
            files = os.listdir(path)
            if files:
                found.append(f"{path} - {len(files)} files")
    if found:
        messagebox.showinfo("Scan Result", "Found temporary files:\n\n" + "\n".join(found))
    else:
        messagebox.showinfo("Scan Result", "System looks clean.\nNo temporary files found.")

def clean_system():
    temp_paths = ["C:\\Windows\\Temp", "C:\\Windows\\Prefetch"]
    deleted = 0
    for path in temp_paths:
        if os.path.exists(path):
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                        deleted += 1
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                        deleted += 1
                except:
                    pass
    messagebox.showinfo("Clean Complete", f"Cleanup finished.\nDeleted items: {deleted}")

app = tk.Tk()
app.title("PC Clean Helper")
app.geometry("300x200")
app.resizable(False, False)

tk.Label(app, text="PC Clean Helper", font=("Arial", 14, "bold")).pack(pady=10)
tk.Button(app, text="SCAN", width=20, height=2, command=scan_system).pack(pady=5)
tk.Button(app, text="CLEAN", width=20, height=2, command=clean_system).pack(pady=5)

app.mainloop()
