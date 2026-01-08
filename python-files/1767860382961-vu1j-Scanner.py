import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import win32com.client
import tempfile
import os

def scan():
    try:
        wia = win32com.client.Dispatch("WIA.CommonDialog")
        img = wia.ShowAcquireImage()

        if img is None:
            return

        temp_file = os.path.join(tempfile.gettempdir(), "scan.jpg")
        if os.path.exists(temp_file):
            os.remove(temp_file)

        img.SaveFile(temp_file)

        image = Image.open(temp_file)
        image.thumbnail((700, 700))
        photo = ImageTk.PhotoImage(image)

        image_label.config(image=photo)
        image_label.image = photo

    except Exception as e:
        messagebox.showerror("Fehler", str(e))


# Fenster
root = tk.Tk()
root.title("Scanner")
root.geometry("750x800")
root.resizable(False, False)

scan_button = tk.Button(
    root,
    text="Scannen",
    font=("Segoe UI", 14),
    command=scan
)
scan_button.pack(pady=10)

image_label = tk.Label(root)
image_label.pack(expand=True)

root.mainloop()
