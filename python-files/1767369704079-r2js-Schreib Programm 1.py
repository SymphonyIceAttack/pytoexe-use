import tkinter as tk
from tkinter import messagebox
import os

def speichern():
    dateiname = eingabe_name.get().strip()
    inhalt = textfeld.get("1.0", tk.END).strip()

    if dateiname == "":
        messagebox.showwarning("Fehler", "Bitte einen Dateinamen eingeben.")
        return
    if inhalt == "":
        messagebox.showwarning("Fehler", "Bitte einen Inhalt eingeben.")
        return

    # Pfad zum Dokumente-Ordner
    dokumente_ordner = os.path.join(os.path.expanduser("~"), "Documents")

    # Datei-Pfad erstellen
    dateipfad = os.path.join(dokumente_ordner, dateiname + ".txt")

    # Datei speichern
    with open(dateipfad, "w", encoding="utf-8") as f:
        f.write(inhalt)

    messagebox.showinfo("Gespeichert", f"Die Datei wurde gespeichert in:\n{dateipfad}")

# Fenster erstellen
fenster = tk.Tk()
fenster.title("Datei speichern")

# Dateiname
label_name = tk.Label(fenster, text="Dateiname (ohne .txt):")
label_name.pack(pady=5)

eingabe_name = tk.Entry(fenster, width=40)
eingabe_name.pack(pady=5)

# Inhalt
label_inhalt = tk.Label(fenster, text="Inhalt der Datei:")
label_inhalt.pack(pady=5)

textfeld = tk.Text(fenster, width=50, height=10)
textfeld.pack(pady=5)

# Speichern-Button
button = tk.Button(fenster, text="Speichern", command=speichern)
button.pack(pady=10)

fenster.mainloop()
