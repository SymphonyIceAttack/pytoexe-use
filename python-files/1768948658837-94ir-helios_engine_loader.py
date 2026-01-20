
import tkinter as tk
from tkinter import messagebox

VALID_LICENSE_KEYS = {
    "HELIOS-FULL-2026-ABC123",
    "HELIOS-FULL-2026-XYZ789"
}

def validate_license():
    license_key = entry_key.get().strip()

    if not license_key:
        messagebox.showerror("Error", "Please enter a license key.")
        return

    if license_key in VALID_LICENSE_KEYS:
        messagebox.showinfo(
            "License Verified",
            "Helios Engine Full Version activated successfully."
        )
    else:
        messagebox.showerror(
            "Invalid License",
            "This license key is not valid. Please purchase the Full Version."
        )

root = tk.Tk()
root.title("Helios Engine Loader")
root.geometry("400x220")
root.resizable(False, False)

tk.Label(root, text="Helios Engine", font=("Arial", 16, "bold")).pack(pady=(20, 5))
tk.Label(root, text="Full Version Loader", font=("Arial", 10)).pack(pady=(0, 15))

tk.Label(root, text="License Key:").pack()
entry_key = tk.Entry(root, width=40)
entry_key.pack(pady=5)

tk.Button(root, text="Activate", width=20, command=validate_license).pack(pady=15)

tk.Label(root, text="© 2026 Helios Engine", font=("Arial", 8)).pack(side="bottom", pady=5)

root.mainloop()
