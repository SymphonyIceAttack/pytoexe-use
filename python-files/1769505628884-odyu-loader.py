import tkinter as tk
from tkinter import messagebox
import webbrowser

def download():
    selected = program_var.get()

    links = {
        "CS2 Glow v2.3.0": "https://www.mediafire.com/file/y018qrh5xga8uho/CS2.Glow.v.2.3.0.exe/file"
    }

    if selected == "Select Program":
        messagebox.showwarning("Warning", "Please select a program!")
        return

    webbrowser.open(links[selected])


# Main window
root = tk.Tk()
root.title("WebManModLoader")
root.geometry("700x480")
root.resizable(False, False)
root.configure(bg="#0a0a0a")

# Title
title = tk.Label(
    root,
    text="WEBMAN MOD LOADER",
    bg="#0a0a0a",
    fg="#00ffd5",
    font=("Segoe UI", 24, "bold")
)
title.pack(pady=30)

# Subtitle
subtitle = tk.Label(
    root,
    text="SELECT A PROGRAM",
    bg="#0a0a0a",
    fg="#ff4f81",
    font=("Segoe UI", 16, "bold")
)
subtitle.pack(pady=10)

# Dropdown variable
program_var = tk.StringVar(value="Select Program")

# Dropdown menu (BIG)
dropdown = tk.OptionMenu(
    root,
    program_var,
    "CS2 Glow v2.3.0"
)

dropdown.config(
    font=("Segoe UI", 18),
    bg="#1a1a1a",
    fg="white",
    activebackground="#2d2d2d",
    activeforeground="#00ffd5",
    width=35,
    borderwidth=0,
    highlightthickness=0
)

dropdown["menu"].config(
    bg="#1a1a1a",
    fg="white",
    activebackground="#2d2d2d",
    activeforeground="#ff4f81",
    font=("Segoe UI", 16)
)

dropdown.pack(pady=30)

# Download button (BIG)
download_btn = tk.Button(
    root,
    text="DOWNLOAD",
    font=("Segoe UI", 18, "bold"),
    bg="#00ffd5",
    fg="#000000",
    activebackground="#00c9ab",
    activeforeground="black",
    width=26,
    height=2,
    borderwidth=0,
    command=download
)
download_btn.pack(pady=35)

# Footer
footer = tk.Label(
    root,
    text="© WebMan | Mod Loader",
    bg="#0a0a0a",
    fg="#555555",
    font=("Segoe UI", 10)
)
footer.pack(side="bottom", pady=15)

root.mainloop()