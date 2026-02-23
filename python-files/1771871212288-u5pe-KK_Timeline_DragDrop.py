import tkinter as tk
from tkinter import messagebox, filedialog
import re

def check_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            content = f.read().decode('utf-8', errors='ignore')

        if "KStudio" not in content:
            messagebox.showinfo("Result", f"{file_path}\nNot a Koikatsu Studio scene file.")
            return

        if "timeline" not in content:
            messagebox.showinfo("Result", f"{file_path}\nNO TIMELINE detected.")
            return

        duration = None
        if "duration" in content:
            pos = content.find("duration")
            sub = content[pos:pos+50]
            match = re.search(r'\d+(\.\d+)?', sub)
            if match:
                duration = match.group()

        if duration:
            messagebox.showinfo("Result", f"{file_path}\nHAS TIMELINE (Duration: {duration}s)")
        else:
            messagebox.showinfo("Result", f"{file_path}\nHAS TIMELINE detected.")

    except Exception as e:
        messagebox.showerror("Error", str(e))

root = tk.Tk()
root.title("KK Timeline Checker - Drag & Drop")
root.geometry("400x150")
root.resizable(False, False)

label = tk.Label(root, text="Drag & Drop Koikatsu PNG scenes here\nor double‑click to browse", width=50, height=10)
label.pack(expand=True, fill='both')

def drop(event):
    files = root.tk.splitlist(event.data)
    for file_path in files:
        if file_path.lower().endswith(".png"):
            check_file(file_path)

def open_file(event):
    file = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
    if file:
        check_file(file)

label.bind("<Double‑Button‑1>", open_file)

try:
    import tkinterdnd2 as tkdnd
    label.drop_target_register(tkdnd.DND_FILES)
    label.dnd_bind('<<Drop>>', drop)
except:
    pass

root.mainloop()