import os
import base64

# Python script that will be packaged into the executable.
# We will create a simple tkinter GUI app that uses the pygame library
# to control the joystick vibration. Pygame handles joystick/controller
# inputs and rumble features well across different OS.

python_script = """
import pygame
import tkinter as tk
from tkinter import messagebox
import threading
import time

class ControllerVibrator:
    def __init__(self):
        self.is_vibrating = False
        self.joystick = None
        self.init_pygame()

    def init_pygame(self):
        pygame.init()
        pygame.joystick.init()
        self.find_controller()

    def find_controller(self):
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            return True
        return False

    def start_vibration(self):
        if not self.joystick:
            if not self.find_controller():
                return False
        
        self.is_vibrating = True
        
        # Pygame's rumble function: rumble(low_frequency, high_frequency, duration_ms)
        # We start a loop in a separate thread to keep it vibrating indefinitely
        # without freezing the GUI.
        def vibrate_loop():
            while self.is_vibrating:
                # Vibrate for 2 seconds at full power on both motors
                # We renew the command every 1.5 seconds to ensure continuous rumble
                if self.joystick:
                    try:
                        self.joystick.rumble(1.0, 1.0, 2000)
                    except Exception as e:
                        print("Error during rumble:", e)
                time.sleep(1.5)

        threading.Thread(target=vibrate_loop, daemon=True).start()
        return True

    def stop_vibration(self):
        self.is_vibrating = False
        if self.joystick:
            try:
                self.joystick.stop_rumble()
            except:
                pass

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 PS4 Controller Dauer-Vibration")
        self.root.geometry("450x300")
        self.root.configure(bg="#1a1a1a")
        
        self.vibrator = ControllerVibrator()

        # Title Label
        title = tk.Label(root, text="🎮 PS4 Controller als Auto 🚗", 
                         font=("Arial", 16, "bold"), bg="#1a1a1a", fg="white")
        title.pack(pady=20)

        # Status Label
        self.status_label = tk.Label(root, text="Status: Bereit", 
                                     font=("Arial", 12), bg="#1a1a1a", fg="#f39c12")
        self.status_label.pack(pady=10)

        # Start Button
        self.start_btn = tk.Button(root, text="🟢 STARTEN (ENDLOS)", 
                                   font=("Arial", 14, "bold"), bg="#2ecc71", fg="white", 
                                   activebackground="#27ae60", activeforeground="white",
                                   command=self.on_start)
        self.start_btn.pack(pady=10, fill=tk.X, padx=50)

        # Stop Button
        self.stop_btn = tk.Button(root, text="🔴 STOPPEN", 
                                  font=("Arial", 14, "bold"), bg="#e74c3c", fg="white", 
                                  activebackground="#c0392b", activeforeground="white",
                                  command=self.on_stop)
        self.stop_btn.pack(pady=10, fill=tk.X, padx=50)
        
        # Initial check
        if not self.vibrator.joystick:
            self.status_label.config(text="Warte auf Controller...", fg="#e74c3c")
        else:
            name = self.vibrator.joystick.get_name()
            self.status_label.config(text=f"Verbunden: {name}", fg="#2ecc71")

    def on_start(self):
        success = self.vibrator.start_vibration()
        if success:
            self.status_label.config(text="🏎️ LÄUFT... Dauerfeuer ist aktiv!", fg="#f39c12")
        else:
            self.status_label.config(text="❌ Kein Controller gefunden!", fg="#e74c3c")
            messagebox.showwarning("Fehler", "Es wurde kein Controller gefunden. Bitte anschließen und versuchen Sie es erneut.")

    def on_stop(self):
        self.vibrator.stop_vibration()
        self.status_label.config(text="🛑 Gestoppt.", fg="#2ecc71")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
"""

# Write the python script to a file
script_path = "/mnt/data/controller_vibration.py"
with open(script_path, "w", encoding="utf-8") as f:
    f.write(python_script)

# We will provide the python script and instructions on how to compile it to exe
# because generating a direct .exe in this environment and passing it to the user 
# is highly restricted (security risks with arbitrary executables).
# Instead, we will generate the Python file and provide a bat file / instructions 
# on how they can easily create the exe themselves using pyinstaller.