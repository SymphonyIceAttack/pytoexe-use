import tkinter as tk
from tkinter import messagebox

def open_menu():
    messagebox.showinfo("Menu", "Menu Opened")

app = tk.Tk()
app.title("Menu")
app.geometry("250x150")
app.resizable(False, False)

tk.Button(app, text="OPEN", width=20, height=2, command=open_menu).pack(pady=15)
tk.Button(app, text="EXIT", width=20, height=2, command=app.destroy).pack()

app.mainloop()
