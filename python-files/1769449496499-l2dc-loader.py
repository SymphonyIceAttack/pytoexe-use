import tkinter as tk
import webbrowser

def download():
    selected = program_var.get()

    links = {
        "CS2 Glow": "https://example.com/cs2_glow.exe"  # örnek link
    }

    if selected in links:
        webbrowser.open(links[selected])

# Ana pencere
root = tk.Tk()
root.title("WebManModLoader")
root.geometry("460x300")
root.resizable(False, False)

# 🎨 Siyah tema
root.configure(bg="#0f0f0f")

# Başlık
title = tk.Label(
    root,
    text="PROGRAMLAR / PROGRAMS",
    bg="#0f0f0f",
    fg="#ffffff",
    font=("Segoe UI", 15, "bold")
)
title.pack(pady=25)

# Büyük açılır menü
program_var = tk.StringVar(value="Program Seç")

dropdown = tk.OptionMenu(
    root,
    program_var,
    "CS2 Glow"
)

dropdown.config(
    font=("Segoe UI", 13),
    bg="#1a1a1a",
    fg="white",
    activebackground="#2a2a2a",
    activeforeground="white",
    width=28,
    borderwidth=0,
    highlightthickness=0
)

dropdown["menu"].config(
    bg="#1a1a1a",
    fg="white",
    activebackground="#2a2a2a",
    font=("Segoe UI", 12)
)

dropdown.pack(pady=10)

# İndir butonu
download_btn = tk.Button(
    root,
    text="İNDİR",
    font=("Segoe UI", 13, "bold"),
    bg="#202020",
    fg="white",
    activebackground="#3a3a3a",
    activeforeground="white",
    width=22,
    height=2,
    borderwidth=0,
    command=download
)
download_btn.pack(pady=25)

root.mainloop()
