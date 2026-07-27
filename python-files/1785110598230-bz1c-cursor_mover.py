import tkinter as tk
from tkinter import ttk
import pyautogui
import random
import time
import threading

class CursorMoverApp:
    def __init__(self, master):
        self.master = master
        master.title("Random Cursor Mover")
        
        # --- State Variables ---
        self.is_running = False
        self.stop_event = threading.Event()
        self.movement_thread = None

        # --- GUI Setup ---
        self.frame = ttk.Frame(master, padding="20 20 20 20")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Status Label (Timer/Status)
        ttk.Label(self.frame, text="Status: Stopped", font=('Arial', 14)).grid(row=0, column=0, columnspan=2, pady=10)
        self.status_label = ttk.Label(self.frame, text="Ready to start.", font=('Arial', 12))
        self.status_label.grid(row=1, column=0, columnspan=2, pady=5)

        # Timer/Interval Display (Fixed at 5 seconds for this requirement)
        ttk.Label(self.frame, text="Movement Interval:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.interval_label = ttk.Label(self.frame, text="5 Seconds", font=('Arial', 12, 'bold'))
        self.interval_label.grid(row=2, column=1, sticky=tk.E)

        # Control Buttons
        self.start_button = ttk.Button(self.frame, text="Start Movement", command=self.start_movement)
        self.start_button.grid(row=3, column=0, padx=5, pady=20, sticky=tk.W)

        self.stop_button = ttk.Button(self.frame, text="Stop Movement", command=self.stop_movement, state=tk.DISABLED)
        self.stop_button.grid(row=3, column=1, padx=5, pady=20, sticky=tk.E)

    def move_cursor(self):
        """Moves the mouse cursor to a random position on the screen."""
        try:
            screen_width, screen_height = pyautogui.size()
            random_x = random.randint(0, screen_width - 1)
            random_y = random.randint(0, screen_height - 1)

            # Update GUI status safely from the thread
            self.master.after(0, lambda x=random_x, y=random_y: self.status_label.config(text=f"Moving to ({x}, {y})..."))
            
            pyautogui.moveTo(random_x, random_y, duration=0.5) 

        except Exception as e:
            self.master.after(0, lambda: self.status_label.config(text=f"Error during movement: {e}"))


    def run_movement_loop(self):
        """The function that runs in a separate thread to handle timed movements."""
        while not self.stop_event.is_set():
            # 1. Perform the action (move cursor)
            self.move_cursor()

            # 2. Wait for the interval, checking stop_event periodically
            self.stop_event.wait(5) # Waits up to 5 seconds or until set() is called

        # Cleanup when loop exits
        self.master.after(0, self._on_stopped)


    def start_movement(self):
        """Initializes and starts the movement thread."""
        if not self.is_running:
            print("Starting cursor mover...")
            self.stop_event.clear() # Ensure stop flag is clear
            self.is_running = True

            # Update GUI state
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="Running... Cursor moving every 5s.")

            # Start the background thread
            self.movement_thread = threading.Thread(target=self.run_movement_loop, daemon=True)
            self.movement_thread.start()


    def stop_movement(self):
        """Signals the movement thread to stop and waits for it to finish."""
        if self.is_running:
            print("Stopping cursor mover...")
            # Signal the loop to exit gracefully
            self.stop_event.set() 

            # Wait a short time for the thread to acknowledge the signal
            if self.movement_thread and self.movement_thread.is_alive():
                self.movement_thread.join(timeout=1) # Give it 1 second to finish

            self._on_stopped()


    def _on_stopped(self):
        """Updates the GUI after stopping."""
        self.is_running = False
        # Update GUI state
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Stopped.")


if __name__ == "__main__":
    try:
        # Check for pyautogui dependency first
        import pyautogui 
    except ImportError:
        print("FATAL ERROR: 'pyautogui' library is required but not found.")
        print("Please run: pip install pyautogui")
        sys.exit(1)

    root = tk.Tk()
    app = CursorMoverApp(root)
    # Start the Tkinter main loop
    root.mainloop()
