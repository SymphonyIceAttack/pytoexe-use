import tkinter as tk
from tkinter import messagebox
import random
import pyperclip
import time

# List of Discord usernames
usernames = [
    ".a7medo", "y.n5", "3looh", "2jzq", "boblsh_q8", "f1p5", "bwvo",
    "7chc", "rd_o", "potato198", "hshamsii_", "7oz_", "opp3672", 
    "zenos_800", "2u5.", "tl4316", "67lp", "wesam_lee", "shayb2293",
    "i.0lz", "vlvg0", "boblsh_q8k", "69l199", "dioo00512"
]

remaining_usernames = usernames.copy()

# Create main window
root = tk.Tk()
root.title("Valteo Random Picker 🎡")
root.geometry("550x450")
root.resizable(False, False)
root.config(bg="#a67bff")  # Purple background

# Cute fonts
title_font = ("Comic Sans MS", 20, "bold")
label_font = ("Comic Sans MS", 14)
button_font = ("Comic Sans MS", 14, "bold")

# Title label
title_label = tk.Label(root, text="🎡 Valteo Random Picker 🎡", font=title_font, bg="#a67bff", fg="white")
title_label.pack(pady=15)

# Selected username label
selected_label = tk.Label(root, text="✨ Spin to pick a username! ✨", font=("Comic Sans MS", 18, "bold"),
                          bg="#d6b3ff", fg="#4b0082", width=30, height=2, relief="raised", bd=5)
selected_label.pack(pady=20)

# Remaining usernames display
remaining_label = tk.Label(root, text="Remaining: " + ", ".join(remaining_usernames), wraplength=500,
                           font=label_font, bg="#a67bff", fg="white", justify="center")
remaining_label.pack(pady=10)

# Function to simulate spinning animation
def spin_animation():
    for _ in range(15):  # number of flashes
        name = random.choice(remaining_usernames)
        selected_label.config(text=f"✨ {name} ✨")
        root.update()
        time.sleep(0.05)  # faster = shorter animation

# Function to pick a random username
def spin():
    global remaining_usernames
    if not remaining_usernames:
        messagebox.showinfo("Valteo Picker", "No usernames left! Reset the list.")
        return
    spin_animation()
    username = random.choice(remaining_usernames)
    selected_label.config(text=f"💜 {username} 💜")
    # Ask if user wants to remove it
    remove = messagebox.askyesno("Remove Username?", f"Do you want to remove {username} from the next spins?")
    if remove:
        remaining_usernames.remove(username)
    remaining_label.config(text="Remaining: " + ", ".join(remaining_usernames))
    pyperclip.copy(username)  # Copy to clipboard automatically

# Function to reset the list
def reset_list():
    global remaining_usernames
    remaining_usernames = usernames.copy()
    remaining_label.config(text="Remaining: " + ", ".join(remaining_usernames))
    selected_label.config(text="✨ Spin to pick a username! ✨")

# Spin button
spin_button = tk.Button(root, text="🎯 Spin", command=spin, font=button_font, width=20,
                        bg="#ff99ff", fg="white", activebackground="#ff66ff", relief="raised", bd=5)
spin_button.pack(pady=15)

# Reset button
reset_button = tk.Button(root, text="🔄 Reset List", command=reset_list, font=button_font, width=20,
                         bg="#c266ff", fg="white", activebackground="#a64dff", relief="raised", bd=5)
reset_button.pack(pady=5)

# Run the app
root.mainloop()
