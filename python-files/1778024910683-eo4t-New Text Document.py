import tkinter as tk
import random
import time
import threading
import os
import sys

class FakeStrobeLight:
    def __init__(self):
        # Create the main window
        self.root = tk.Tk()
        self.root.title("System Process")
        
        # Make window full screen
        self.root.attributes('-fullscreen', True)
        
        # Remove window decorations
        self.root.overrideredirect(True)
        
        # Set initial background
        self.root.configure(bg="black")
        
        # Create a label to display text
        self.label = tk.Label(self.root, text="", font=("Arial", 24), bg="black", fg="white")
        self.label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Start the strobe effect
        self.running = True
        self.strobe_thread = threading.Thread(target=self.strobe_effect, daemon=True)
        self.strobe_thread.start()
        
        # Bind escape key to exit
        self.root.bind('<Escape>', lambda e: self.stop())
        
    def strobe_effect(self):
        colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF", "white", "black"]
        messages = [
            "SYSTEM COMPROMISED",
            "ACCESS DENIED",
            "WARNING: MALWARE DETECTED",
            "INITIALIZING PROTOCOL 7",
            "SECURITY BREACH",
            "DATA CORRUPTION",
            "SYSTEM FAILURE",
            "MEMORY DUMP IN PROGRESS"
        ]
        
        while self.running:
            try:
                # Random color
                color = random.choice(colors)
                self.root.configure(bg=color)
                self.label.configure(bg=color)
                
                # Random message
                if random.random() > 0.7:  # 30% chance to show message
                    message = random.choice(messages)
                    self.label.config(text=message)
                    
                    # Random text color (contrasting to background)
                    if color == "black":
                        text_color = "white"
                    elif color == "white":
                        text_color = "black"
                    else:
                        text_color = random.choice(["white", "black"])
                    self.label.configure(fg=text_color)
                else:
                    self.label.config(text="")
                
                # Random sleep time for varied strobe effect
                time.sleep(random.uniform(0.05, 0.3))
            except:
                break
    
    def stop(self):
        self.running = False
        self.root.destroy()
        
    def run(self):
        try:
            self.root.mainloop()
        except:
            pass

if __name__ == "__main__":
    try:
        # Hide console window on Windows
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        
        app = FakeStrobeLight()
        app.run()
    except Exception as e:
        print(f"Error: {e}")