import tkinter as tk
from tkinter import messagebox
import webbrowser


def activate():
    key = key_entry.get().strip()

    if not key:
        messagebox.showwarning(
            "Activation",
            "Please enter your activation key."
        )
        return

    messagebox.showinfo(
        "Activation",
        "Activation will be connected later."
    )


def purchase():
    webbrowser.open("https://example.com")


# Window
root = tk.Tk()
root.title("Data Recovery")
root.geometry("490x500")
root.configure(bg="#0f172a")
root.resizable(False, False)

# Container
container = tk.Frame(
    root,
    bg="#0f172a",
    padx=35,
    pady=55
)
container.pack(fill="both", expand=True)

# Logo
logo = tk.Label(
    container,
    text="DATA RECOVERY",
    font=("Arial", 28, "bold"),
    fg="#38bdf8",
    bg="#0f172a"
)
logo.pack(pady=(0, 8))

# Subtitle
subtitle = tk.Label(
    container,
    text="Professional File Recovery",
    font=("Arial", 11),
    fg="#94a3b8",
    bg="#0f172a"
)
subtitle.pack(pady=(0, 45))

# Label
label = tk.Label(
    container,
    text="Activation Key",
    font=("Arial", 11),
    fg="#cbd5e1",
    bg="#0f172a",
    anchor="w"
)
label.pack(fill="x", pady=(0, 8))

# Entry
key_entry = tk.Entry(
    container,
    font=("Arial", 14),
    bg="#1e293b",
    fg="white",
    insertbackground="white",
    relief="flat"
)
key_entry.pack(fill="x", ipady=10)

# Activate button
activate_button = tk.Button(
    container,
    text="ACTIVATE",
    command=activate,
    font=("Arial", 11, "bold"),
    bg="#0ea5e9",
    fg="white",
    activebackground="#0284c7",
    activeforeground="white",
    relief="flat",
    cursor="hand2"
)
activate_button.pack(fill="x", pady=(22, 0), ipady=10)

# Purchase link
purchase_button = tk.Label(
    container,
    text="Don't have an activation key? Purchase a license",
    font=("Arial", 9),
    fg="#94a3b8",
    bg="#0f172a",
    cursor="hand2"
)
purchase_button.pack(pady=(25, 0))

purchase_button.bind("<Button-1>", lambda event: purchase())

root.mainloop()