import tkinter as tk
from tkinter import messagebox
import webbrowser

def download():
    lib = library_var.get()
    prog = program_var.get()

    links = {
        "CS2": {
            "Glow": "https://www.mediafire.com/file/y018qrh5xga8uho/CS2.Glow.v.2.3.0.exe/file"
        },
        "TF2": {
            "necromancerx64": "https://www.mediafire.com/file/o9qqt18a825mb7y/NecromancerLoader.exe/file"
        }
    }

    if lib == "Select Library" or prog == "Select Program":
        messagebox.showwarning("Warning", "Please select library and program!")
        return

    webbrowser.open(links[lib][prog])


def update_programs(*args):
    program_menu["menu"].delete(0, "end")
    program_var.set("Select Program")

    if library_var.get() == "CS2":
        options = ["Glow"]
    elif library_var.get() == "TF2":
        options = ["necromancerx64"]
    else:
        options = []

    for opt in options:
        program_menu["menu"].add_command(
            label=opt,
            command=tk._setit(program_var, opt)
        )


# ---------------- MAIN WINDOW ---------------- #
root = tk.Tk()
root.title("WebMan Mod Loader")
root.geometry("1000x650")
root.configure(bg="black")
root.resizable(False, False)

# ---------------- TITLE ---------------- #
title_label = tk.Label(
    root,
    text="WEBMAN MOD LOADER",
    font=("Segoe UI", 28, "bold"),
    bg="black",
    fg="#00ffd5"   # SABİT RENK (istersen değiştir)
)
title_label.pack(pady=30)

# ---------------- LIBRARY SELECT ---------------- #
library_var = tk.StringVar(value="Select Library")
library_var.trace_add("write", update_programs)

library_menu = tk.OptionMenu(
    root,
    library_var,
    "Select Library",
    "CS2",
    "TF2"
)
library_menu.config(
    font=("Segoe UI", 18),
    bg="#111111",
    fg="white",
    width=30,
    borderwidth=0
)
library_menu["menu"].config(
    bg="#111111",
    fg="white",
    font=("Segoe UI", 16)
)
library_menu.pack(pady=20)

# ---------------- PROGRAM SELECT ---------------- #
program_var = tk.StringVar(value="Select Program")

program_menu = tk.OptionMenu(
    root,
    program_var,
    "Select Program"
)
program_menu.config(
    font=("Segoe UI", 18),
    bg="#111111",
    fg="white",
    width=30,
    borderwidth=0
)
program_menu["menu"].config(
    bg="#111111",
    fg="white",
    font=("Segoe UI", 16)
)
program_menu.pack(pady=20)

# ---------------- DOWNLOAD BUTTON ---------------- #
download_btn = tk.Button(
    root,
    text="DOWNLOAD",
    font=("Segoe UI", 20, "bold"),
    bg="#00ffd5",
    fg="black",
    width=25,
    height=2,
    borderwidth=0,
    command=download
)
download_btn.pack(pady=40)

# ---------------- FOOTER ---------------- #
footer = tk.Label(
    root,
    text="© WebMan | Mod Loader",
    bg="black",
    fg="#555555",
    font=("Segoe UI", 10)
)
footer.pack(side="bottom", pady=15)

root.mainloop()
