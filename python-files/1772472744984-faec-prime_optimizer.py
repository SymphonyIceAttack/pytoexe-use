"""
PRIME Optimizer - Professional Edition
Login: PRIME / 3K
"""

import tkinter as tk
from tkinter import messagebox
import ctypes
import subprocess
import sys
import threading
import winsound
import os

class PrimeOptimizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Prime Optimizer")
        self.root.geometry("1000x650")
        self.root.configure(bg="#121212")
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

        self.sound_playing = False

        self.center_window()
        self.create_background()
        self.ask_restore_point()
        self.show_login()

    # ---------------- WINDOW ---------------- #

    def center_window(self):
        w = 1000
        h = 650
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def close_app(self):
        self.stop_sound()
        self.root.destroy()
        sys.exit()

    # ---------------- BACKGROUND ---------------- #

    def create_background(self):
        self.canvas = tk.Canvas(self.root, bg="#121212", highlightthickness=0)
        self.canvas.place(x=0, y=0, width=1000, height=650)

        # Blurred 9-tail style
        self.canvas.create_oval(380, 180, 620, 420,
                                fill="#1E1E1E", outline="#333333", width=2)

        for i in range(9):
            self.canvas.create_line(500, 350,
                                    650 + i*15, 400 + i*10,
                                    fill="#2A2A2A", width=4)

        # Blur overlay
        self.canvas.create_rectangle(0, 0, 1000, 650,
                                     fill="#121212", stipple="gray50")

    # ---------------- RESTORE POINT ---------------- #

    def ask_restore_point(self):
        if messagebox.askyesno("System Safety",
                               "Create a restore point before continuing?"):
            try:
                subprocess.run(
                    'powershell.exe Checkpoint-Computer -Description "PrimeRestore" -RestorePointType "MODIFY_SETTINGS"',
                    shell=True)
                messagebox.showinfo("Success", "Restore point created.")
            except:
                messagebox.showerror("Error", "Run as Administrator.")

    # ---------------- LOGIN ---------------- #

    def show_login(self):
        self.login_frame = tk.Frame(self.root, bg="#1E1E1E")
        self.login_frame.place(relx=0.5, rely=0.5,
                               anchor="center", width=350, height=400)

        tk.Label(self.login_frame, text="PRIME OPTIMIZER",
                 font=("Segoe UI", 18, "bold"),
                 fg="white", bg="#1E1E1E").pack(pady=30)

        tk.Label(self.login_frame, text="App ID",
                 fg="gray", bg="#1E1E1E").pack()

        self.app_id = tk.Entry(self.login_frame, bg="#2A2A2A",
                               fg="white", insertbackground="white")
        self.app_id.pack(pady=5)

        tk.Label(self.login_frame, text="Password",
                 fg="gray", bg="#1E1E1E").pack()

        self.password = tk.Entry(self.login_frame,
                                 show="●",
                                 bg="#2A2A2A",
                                 fg="white",
                                 insertbackground="white")
        self.password.pack(pady=5)

        tk.Button(self.login_frame,
                  text="Login",
                  bg="#4CAF50",
                  fg="white",
                  width=15,
                  command=self.check_login).pack(pady=20)

    def check_login(self):
        if self.app_id.get() == "PRIME" and self.password.get() == "3K":
            self.login_frame.destroy()
            self.show_main()
            winsound.Beep(800, 150)
        else:
            messagebox.showerror("Access Denied", "Invalid Credentials")

    # ---------------- MAIN UI ---------------- #

    def show_main(self):
        main = tk.Frame(self.root, bg="#1E1E1E")
        main.place(relx=0.5, rely=0.5,
                   anchor="center", width=850, height=500)

        tk.Label(main, text="Dashboard",
                 font=("Segoe UI", 16, "bold"),
                 fg="white", bg="#1E1E1E").pack(pady=20)

        tk.Button(main, text="Start Background Sound",
                  bg="#3A3A3A", fg="white",
                  width=25, command=self.play_sound).pack(pady=10)

        tk.Button(main, text="Stop Sound",
                  bg="#3A3A3A", fg="white",
                  width=25, command=self.stop_sound).pack(pady=10)

    # ---------------- SOUND ---------------- #

    def play_sound(self):
        if not self.sound_playing:
            self.sound_playing = True
            threading.Thread(target=self.sound_loop,
                             daemon=True).start()

    def sound_loop(self):
        while self.sound_playing:
            winsound.Beep(500, 200)

    def stop_sound(self):
        self.sound_playing = False


# ---------------- ADMIN CHECK ---------------- #

if __name__ == "__main__":
    if ctypes.windll.shell32.IsUserAnAdmin():
        root = tk.Tk()
        app = PrimeOptimizer(root)
        root.mainloop()
    else:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable,
            " ".join(sys.argv), None, 1)