import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys

def build():
    file = filedialog.askopenfilename(
        filetypes=[("Python files", "*.py *.pyw")]
    )
    if not file:
        return

    try:
        subprocess.run(
            ["pyinstaller", "--onefile", "--noconsole", file],
            check=True
        )
        messagebox.showinfo("OK", "EXE готов")
    except:
        messagebox.showerror("Ошибка", "Не получилось")

root = tk.Tk()
root.title("PY → EXE")
root.geometry("200x100")

tk.Button(root, text="Сделать EXE", command=build).pack(expand=True)

root.mainloop()
