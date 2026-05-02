import tkinter as tk
from tkinter import messagebox
import winsound
import threading
import sys
import os

# Constants for fullscreen window
WINDOW_TITLE = "SYSTEM LOCKED - RANSOMWARE ALERT"
RANSOM_MESSAGE = """
WARNING: YOUR SYSTEM HAS BEEN COMPROMISED!
---------------------------------------
YOUR FILES HAVE BEEN ENCRYPTED!
This is a simulation. No files have been modified or encrypted.
To recover your data, pay 1.0 BTC to the following wallet:
[FAKE_BTC_WALLET_ADDRESS_123456789]
After payment, email us at [FAKE_EMAIL@EXAMPLE.COM] with your transaction ID.
You have 48 hours before your files are permanently deleted.
DO NOT ATTEMPT TO CLOSE THIS WINDOW OR REBOOT YOUR SYSTEM.
---------------------------------------
THIS IS A DEMONSTRATION ONLY. YOUR PC IS SAFE.
"""

# Function to play a looping alert sound (Windows-specific)
def play_alert_sound():
    while True:
        winsound.Beep(1000, 500)  # Frequency 1000Hz, duration 500ms (repetitive beep)
        winsound.Beep(500, 500)   # Alternate tone for urgency

# Function to prevent window closure
def on_closing():
    pass  # Override the default close behavior to do nothing

# Function to create and configure the ransomware simulation window
def create_ransomware_window():
    root = tk.Tk()
    root.title(WINDOW_TITLE)
    
    # Make window fullscreen and unclosable
    root.attributes('-fullscreen', True)
    root.protocol("WM_DELETE_WINDOW", on_closing)  # Ignore close attempts
    root.resizable(False, False)
    
    # Lock focus to this window (attempts to prevent minimizing on some systems)
    root.attributes('-topmost', True)
    
    # Set threatening background and text styling
    root.configure(bg='black')
    
    # Create ransom note label
    ransom_label = tk.Label(
        root,
        text=RANSOM_MESSAGE,
        fg='red',
        bg='black',
        font=('Courier New', 16, 'bold'),
        justify='center',
        wraplength=1000
    )
    ransom_label.pack(pady=50, padx=50, fill='both', expand=True)
    
    # Add a fake "countdown timer" for added realism
    countdown_var = tk.StringVar()
    countdown_var.set("Time Remaining: 48:00:00")
    countdown_label = tk.Label(
        root,
        textvariable=countdown_var,
        fg='red',
        bg='black',
        font=('Courier New', 20, 'bold')
    )
    countdown_label.pack(pady=20)
    
    # Simulate countdown (doesn't actually decrement for simplicity, but looks real)
    def fake_countdown():
        initial_time = 48 * 3600  # 48 hours in seconds
        while True:
            hours = initial_time // 3600
            minutes = (initial_time % 3600) // 60
            seconds = initial_time % 60
            countdown_var.set(f"Time Remaining: {hours:02d}:{minutes:02d}:{seconds:02d}")
            root.update()
            initial_time -= 1 if initial_time > 0 else 0
            threading.Event().wait(1)  # Simulate 1-second delay
            
    # Start sound in a separate thread (Windows only)
    sound_thread = threading.Thread(target=play_alert_sound, daemon=True)
    sound_thread.start()
    
    # Start countdown in a separate thread
    countdown_thread = threading.Thread(target=fake_countdown, daemon=True)
    countdown_thread.start()
    
    # Run the main loop
    root.mainloop()

# Main function to start the simulation
def main():
    # Note: If not on Windows, sound won't play with winsound
    if not sys.platform.startswith('win'):
        print("Note: Alert sound simulation is Windows-specific. Sound will not play on this OS.")
        print("Consider using a library like 'pygame' for cross-platform sound.")
    
    create_ransomware_window()

if __name__ == "__main__":
    main()
