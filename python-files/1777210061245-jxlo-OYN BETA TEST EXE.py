import tkinter as tk
from tkinter import messagebox, simpledialog
import os
import winsound
from PIL import Image, ImageTk
import webbrowser
import time
import calendar
import subprocess

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def load_icon(name):
    for ext in ["", ".png", ".jpg", ".ico", ".jpeg", ".bmp"]:
        path = name + ext
        if os.path.exists(path):
            return ImageTk.PhotoImage(Image.open(path).resize((20, 20)))
    return None

root = tk.Tk()
root.title("OYN")
root.attributes('-fullscreen', True)
root.overrideredirect(True)
root.iconbitmap("icon.ico")
root.configure(bg="#c0c0c0")

label = tk.Label(root, text="OYN", font=("Arial", 130, "bold"),
                 fg="#5a5a5a",
                 bg="#c0c0c0")
label.place(relx=0.5, rely=0.5, anchor="center")

winsound.PlaySound("windows", winsound.SND_ASYNC | winsound.SND_FILENAME)

icon_my_os = load_icon("my_os")
icon_pusk = load_icon("pusk")
icon_exit = load_icon("exit")
icon_provodnik = load_icon("icon_provodnik")
icon_google = load_icon("icon_google")
icon_calendar = load_icon("icon_calendar")
icon_bloknot = load_icon("icon_bloknot")
icon_calculator = load_icon("icon_calculator")
icon_terminal = load_icon("icon_terminal")
icon_window = load_icon("icon_window")

def _click():
    winsound.Beep(300, 250)
    window = tk.Toplevel(root)
    window.geometry("500x300")
    window.iconbitmap("compukter.ico")
    window.resizable(False, False)
    tk.Label(window, text="Название: OYN\nИздатель: FXRMA Corporation\nВерсия: 0.2\nГод создания: 2026").pack()
    img2 = tk.PhotoImage(file="photo.png")
    label2 = tk.Label(window, image=img2)
    label2.image = img2
    label2.pack()

def calculator():
    winsound.Beep(300, 250)
    calc = tk.Toplevel(root)
    calc.geometry("300x150")
    calc.title("Калькулятор")
    calc.resizable(False, False)
    calc.iconbitmap("icon_calculator.ico")
    entry = tk.Entry(calc, width=30)
    entry.pack(pady=10)
    result_label = tk.Label(calc, text="")
    result_label.pack()
    def calculate():
        try:
            result = eval(entry.get())
            result_label.config(text=f"= {result}")
        except:
            result_label.config(text="Ошибка!")
    tk.Button(calc, text="=", command=calculate).pack()

def pusk():
    winsound.Beep(300, 250)
    pusk_win = tk.Toplevel(root)
    pusk_win.geometry("340x300")
    pusk_win.configure(bg="#d0d0d0")
    pusk_win.title("Пуск")
    pusk_win.resizable(False, False)
    pusk_win.iconbitmap("pusk.ico")
    
    but = tk.Button(pusk_win, text="Калькулятор", compound="left", command=calculator)
    but.place(x=20, y=20)
    
    but2 = tk.Button(pusk_win, text="Блокнот", compound="left", command=bloknot)
    but2.place(x=20, y=70)
    
    but3 = tk.Button(pusk_win, text="Календарь", compound="left", command=calendar)
    but3.place(x=20, y=120)

def ex():
    root.destroy()
    
def calendar():
    
    winsound.Beep(300, 250)
    cal = tk.Toplevel(root)
    cal.iconbitmap("icon_calendar.ico")
    cal.resizable(False, False)
    cal.title("Календарь")
    
    from datetime import datetime
    now = datetime.now().strftime("%d.%m.%Y")
    
    tk.Label(cal, text=now, font=("Arial", 40)).pack()

def bloknot():
    winsound.Beep(300, 250)
    blok = tk.Toplevel(root)
    blok.title("Блокнот")
    blok.resizable(False, False)
    blok.iconbitmap("icon_bloknot.ico")
    text = tk.Text(blok, height=5, width=45)
    text.pack()

def provod():
    winsound.Beep(300, 250)
    prov = tk.Toplevel(root)
    prov.geometry("500x550")
    prov.title("Проводник")
    prov.resizable(False, False)
    prov.iconbitmap("icon_provodnik.ico")

    listbox = tk.Listbox(prov, width=50, height=20)
    listbox.pack()

    def refresh():
        listbox.delete(0, tk.END)
        for item in os.listdir("."):
            listbox.insert(tk.END, item)

    def papka():
        name = simpledialog.askstring("Название", "Введите название папки:")
        if name:
            os.makedirs(name)
            refresh()

    tk.Button(prov, text="Создать папку", command=papka).pack()
    refresh()
    
def browser():
    winsound.Beep(300, 250)
    webbrowser.open("https://google.com")
    
def terminal():
    term = tk.Toplevel(root)
    term.title("Терминал")
    term.geometry("350x235")
    term.resizable(False, False)
    term.iconbitmap("icon_terminal.ico")
    
    out = tk.Text(term, height=5, width=45)
    out.pack()
    
    entry = tk.Entry(term)
    entry.pack(fill='x')
    entry.focus()
    
    def com(e=None):
        cmd = entry.get().strip().lower()
        entry.delete(0, tk.END)
        
        if cmd == "exit": root.destroy()
        elif cmd == "window":
            win = tk.Tk()
            win.iconbitmap("icon_window.ico")
            win.geometry("300x300")
            win.mainloop()
        else: out.insert(tk.END, cmd + "\n")
        
    entry.bind('<Return>', com)

    tk.Button(term, text="Воспроизвести", command=com).pack()
    
btn1 = tk.Button(root, text="Моя OS", image=icon_my_os, compound="left", command=_click)
btn1.place(x=20, y=20)
btn1.image = icon_my_os

btn2 = tk.Button(root, text="Пуск", image=icon_pusk, compound="left", command=pusk)
btn2.place(x=20, y=70)
btn2.image = icon_pusk

btn3 = tk.Button(root, text="Выйти", image=icon_exit, compound="left", command=ex)
btn3.place(x=20, y=280)
btn3.image = icon_exit

btn4 = tk.Button(root, text="Проводник", image=icon_provodnik, compound="left", command=provod)
btn4.place(x=20, y=120)
btn4.image = icon_provodnik

btn5 = tk.Button(root, text="Google", image=icon_google, compound="left", command=browser)
btn5.place(x=20, y=170)
btn5.image = icon_google

btn6 = tk.Button(root, text="Терминал", image=icon_terminal, compound="left", command=terminal)
btn6.place(x=20, y=230)
btn6.image = icon_terminal

root.mainloop()