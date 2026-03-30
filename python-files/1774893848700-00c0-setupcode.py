 import tkinter as tk
from tkinter import messagebox, simpledialog

def main():
    root = tk.Tk()
    root.withdraw()  # Hauptfenster verstecken

    # Schritt 1: Lizenzdaten eingeben
    eingabe = simpledialog.askstring(
        "Lizenzdaten",
        "Lizenzdaten bitte eintragen:",
        parent=root
    )

    if eingabe is None:
        root.destroy()
        return

    # Schritt 2: Bestätigung
    bestaetigung = messagebox.askquestion(
        "Aktivierung vorbereiten",
        "Aktivierung des Computers vorbereiten?",
        icon="question",
        default="yes",
        type=messagebox.YESNO
    )

    # Buttons auf Deutsch umbenennen
    # Da tkinter keine nativen deutschen Buttons unterstützt, nutzen wir ein eigenes Fenster:
    confirm_window = tk.Toplevel(root)
    confirm_window.title("Aktivierung vorbereiten")
    confirm_window.geometry("350x120")
    confirm_window.resizable(False, False)
    confirm_window.grab_set()

    result = {"value": None}

    tk.Label(confirm_window, text="Aktivierung des Computers vorbereiten?",
             wraplength=300, pady=20).pack()

    btn_frame = tk.Frame(confirm_window)
    btn_frame.pack()

    def on_ja():
        result["value"] = True
        confirm_window.destroy()

    def on_abbrechen():
        result["value"] = False
        confirm_window.destroy()

    tk.Button(btn_frame, text="Ja", width=10, command=on_ja).pack(side="left", padx=10)
    tk.Button(btn_frame, text="Abbrechen", width=10, command=on_abbrechen).pack(side="left", padx=10)

    root.wait_window(confirm_window)

    if not result["value"]:
        root.destroy()
        return

    # Schritt 3: Abschlussmeldung
    final_window = tk.Toplevel(root)
    final_window.title("Aktivierung abgeschlossen")
    final_window.geometry("400x130")
    final_window.resizable(False, False)
    final_window.grab_set()

    tk.Label(
        final_window,
        text="Ihr Computer wurde fertig auf die Aktivierung\nvon Windows 11 konfiguriert.",
        wraplength=360,
        pady=25
    ).pack()

    def on_fertig():
        final_window.destroy()
        root.destroy()

    tk.Button(final_window, text="Fertig", width=10, command=on_fertig).pack()

    root.wait_window(final_window)

if __name__ == "__main__":
    main()
