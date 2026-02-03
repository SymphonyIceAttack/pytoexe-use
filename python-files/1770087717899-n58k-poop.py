import webbrowser
import time
import tkinter as tk
from tkinter import messagebox

# List of websites to open
websites = [
    "https://en.wikipedia.org/wiki/Israel",
    "https://en.wikipedia.org/wiki/Agartha",
    "https://en.wikipedia.org/wiki/Coin_edge"
]

# Optional: Show a message first
root = tk.Tk()
root.withdraw()  # Hide the main window
messagebox.showinfo("Opening Websites", "This program will open 3 websites in your browser.")
root.destroy()

# Open websites with a small delay between them
for site in websites:
    webbrowser.open(site)
    time.sleep(1)  # 1-second delay between tabs