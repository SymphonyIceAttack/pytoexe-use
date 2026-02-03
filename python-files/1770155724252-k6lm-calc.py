import tkinter as tk
from tkinter import filedialog, messagebox
import math
import time
from PIL import Image, ImageTk

root = tk.Tk()
root.title("Retro Calculator 2005 Edition")
root.geometry("900x600")
root.resizable(False, False)

bg_label = None

def import_background():
    global bg_label
    path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")])
    if path:
        img = Image.open(path)
        img = img.resize((900, 600))
        img = ImageTk.PhotoImage(img)
        if bg_label:
            bg_label.destroy()
        bg_label = tk.Label(root, image=img)
        bg_label.image = img
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

def update_clock():
    now = time.strftime("%H:%M:%S")
    clock_label.config(text=now)
    clock_label.after(1000, update_clock)

expression = ""

def click(value):
    global expression
    expression += str(value)
    entry.delete(0, tk.END)
    entry.insert(0, expression)

def clear():
    global expression
    expression = ""
    entry.delete(0, tk.END)

def calculate():
    global expression
    try:
        result = str(eval(expression))
        entry.delete(0, tk.END)
        entry.insert(0, result)
        expression = result
    except:
        messagebox.showerror("Error", "Invalid Expression")
        clear()

def save_notes():
    text = notes.get("1.0", tk.END)
    path = filedialog.asksaveasfilename(defaultextension=".txt")
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

font_style = ("Courier New", 14, "bold")
menu = tk.Menu(root)
root.config(menu=menu)
menu.add_command(label="Import Background", command=import_background)

clock_label = tk.Label(root, font=("Digital-7", 26), bg="black", fg="lime")
clock_label.place(x=20, y=20, width=200)
update_clock()

calc_frame = tk.Frame(root, bd=5, relief="ridge", bg="#c0c0c0")
calc_frame.place(x=20, y=90, width=300, height=460)

entry = tk.Entry(calc_frame, font=font_style, justify="right")
entry.pack(fill="x", pady=5)

buttons = [
    "7", "8", "9", "/", "sin",
    "4", "5", "6", "*", "cos",
    "1", "2", "3", "-", "tan",
    "0", ".", "=", "+", "√",
    "C"
]

def scientific_func(value):
    global expression
    try:
        num = float(expression)
        if value == "sin":
            result = math.sin(math.radians(num))
        elif value == "cos":
            result = math.cos(math.radians(num))
        elif value == "tan":
            result = math.tan(math.radians(num))
        elif value == "√":
            result = math.sqrt(num)
        expression = str(result)
        entry.delete(0, tk.END)
        entry.insert(0, expression)
    except:
        pass

row = 1
col = 0
for b in buttons:
    if b == "=":
        cmd = calculate
    elif b == "C":
        cmd = clear
    elif b in ["sin", "cos", "tan", "√"]:
        cmd = lambda x=b: scientific_func(x)
    else:
        cmd = lambda x=b: click(x)
    tk.Button(calc_frame, text=b, width=5, height=2, font=font_style, bg="#e0e0e0", command=cmd).grid(row=row, column=col, padx=2, pady=2)
    col += 1
    if col > 4:
        col = 0
        row += 1

notes_frame = tk.Frame(root, bd=5, relief="ridge", bg="#f0f0f0")
notes_frame.place(x=350, y=90, width=520, height=460)

notes = tk.Text(notes_frame, font=("Arial", 12))
notes.pack(fill="both", expand=True)

save_btn = tk.Button(root, text="Save Notes", font=font_style, command=save_notes)
save_btn.place(x=700, y=560)

root.mainloop()
