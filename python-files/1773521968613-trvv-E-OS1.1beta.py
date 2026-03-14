import tkinter as tk
import keyboard 
import time
from tkinter import *
from tkinter import messagebox, filedialog, scrolledtext 
import webbrowser
from PIL import Image , ImageTk
import os
import sys
from tkinter import filedialog
from tkinter import scrolledtext
import subprocess
root=tk.Tk()
root.title("E-OS 1.1")
root.geometry("1920x1080")
root.configure(bg = "purple")
def butoon_google():
    webbrowser.open("https://www.google.com/")
def butoon_steam():
    webbrowser.open("steam://open/main")
def launch_system_notepad():
    notepad_path = "notepad.exe" 
    try:
        standard_path_1 = "C:\\Windows\\System32\\notepad.exe"
        standard_path_2 = "C:\\Windows\\notepad.exe" 

        if os.path.exists(standard_path_1):
            subprocess.Popen([standard_path_1])
        elif os.path.exists(standard_path_2):
            subprocess.Popen([standard_path_2])
        else:
            subprocess.Popen([notepad_path])
    except FileNotFoundError:
        messagebox.showerror("E-OS Ошибка", "Не удалось найти или запустить системный блокнот. Проверьте его наличие.")
    except Exception as e:
        messagebox.showerror("E-OS Ошибка", f"Произошла ошибка при запуске блокнота: {e}")

hello_label = tk.Label(text="Добро пожаловать в E-OS! \n загружаем ОС..." , fg = "white" , bg = "purple" , font=("Arial" , 50))
hello_label.pack(pady = 30) 
def hello_hide():
    hello_label.destroy()
    b1 = Button(root , text="🌐Google" , command=butoon_google )
    b1.pack()
    b1.place(x=10 , y=120)
    b2 = Button(root , text="🎮Steam" , command=butoon_steam )
    b2.pack()
    b2.place(x=10 , y=240)
    b3 = Button(root , text="📝Блокнот" , command=launch_system_notepad)
    b3.pack()
    b3.place(x=10 , y=360)

root.after(3000 , hello_hide) 
root.mainloop()