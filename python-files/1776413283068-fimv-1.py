import tkinter as tk
from tkinter import messagebox
import os

def create_bat():
    username = entry_user.get()
    password = entry_pass.get()

    if not username or not password:
        messagebox.showerror("Fehler", "Bitte Nutzername und Passwort eingeben.")
        return

    # BAT Inhalt
    bat_content = f"""@echo off
echo {username} {password} | clip
start msedge "https://he.edumaps.de/"
"""

    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    file_path = os.path.join(desktop, "edumaps_login.bat")

    with open(file_path, "w") as f:
        f.write(bat_content)

    messagebox.showinfo("Erfolg", f"Datei wurde erstellt:\n{file_path}")


def show_info():
    info_text = (
        "Tutorial:\n\n"
        "1. Geben Sie Ihren EduMaps Nutzernamen ein.\n"
        "2. Geben Sie Ihr Passwort ein.\n"
        "3. Klicken Sie auf 'Erstellen'.\n"
        "4. Eine .bat Datei wird auf Ihrem Desktop erstellt.\n"
        "5. Doppelklick auf die Datei öffnet EduMaps.\n"
        "\nHinweis: Automatisches Einloggen funktioniert nur eingeschränkt im Browser."
    )
    messagebox.showinfo("Info", info_text)


# GUI
root = tk.Tk()
root.title("edumaps")
root.geometry("400x250")

# Labels & Eingaben
label_user = tk.Label(root, text="Nutzername:")
label_user.pack(pady=5)

entry_user = tk.Entry(root, width=30)
entry_user.pack()

label_pass = tk.Label(root, text="Passwort:")
label_pass.pack(pady=5)

entry_pass = tk.Entry(root, width=30, show="*")
entry_pass.pack()

# Button erstellen
btn_create = tk.Button(root, text="Erstellen", command=create_bat)
btn_create.pack(pady=15)

# Info unten rechts
frame_bottom = tk.Frame(root)
frame_bottom.pack(fill="both", expand=True)

btn_info = tk.Button(frame_bottom, text="Info", command=show_info)
btn_info.pack(side="right", padx=10, pady=10)

root.mainloop()
