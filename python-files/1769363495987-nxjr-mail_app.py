import tkinter as tk
from tkinter import simpledialog, messagebox
import json
import pyperclip
import os

# Bestandspaden
script_dir = os.path.dirname(os.path.realpath(__file__))
template_file = os.path.join(script_dir, "templates.json")

# Laad templates
def laad_templates():
    if os.path.exists(template_file):
        with open(template_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Sla templates op
def sla_templates_op(templates):
    with open(template_file, "w", encoding="utf-8") as f:
        json.dump(templates, f, indent=4, ensure_ascii=False)

templates = laad_templates()
favorieten = set()

# Gebruik template
def gebruik_template(titel):
    tekst = templates[titel]
    naam = simpledialog.askstring("Naam", "Vul de naam in:")
    if not naam:
        return
    tekst = tekst.replace("{NAAM}", naam)
    pyperclip.copy(tekst)
    messagebox.showinfo("Gekopieerd", "De tekst is gekopieerd naar het klembord.\nPlak deze in je e-mail.")

# Voeg template toe
def voeg_template_toe():
    titel = simpledialog.askstring("Nieuwe template", "Titel van de template:")
    if not titel:
        return
    if titel in templates:
        messagebox.showerror("Fout", "Deze template bestaat al!")
        return
    inhoud = simpledialog.askstring("Inhoud template", "Typ de template (gebruik {NAAM} voor de naam):")
    if not inhoud:
        return
    templates[titel] = inhoud
    sla_templates_op(templates)
    update_knoppen()

# Verwijder template
def verwijder_template(titel):
    if messagebox.askyesno("Verwijderen", f"Weet je zeker dat je '{titel}' wilt verwijderen?"):
        del templates[titel]
        favorieten.discard(titel)
        sla_templates_op(templates)
        update_knoppen()

# Toggle favoriet
def toggle_favoriet(titel):
    if titel in favorieten:
        favorieten.remove(titel)
    else:
        favorieten.add(titel)
    update_knoppen()

# Update knoppen
def update_knoppen():
    for widget in knoppen_frame.winfo_children():
        widget.destroy()

    zoek = zoek_entry.get().lower()
    for titel in templates:
        if zoek in titel.lower():
            fav = "★ " if titel in favorieten else ""
            btn = tk.Button(knoppen_frame, text=fav+titel, width=40,
                            command=lambda t=titel: gebruik_template(t))
            btn.pack(pady=2)
            btn.bind("<Button-3>", lambda e, t=titel: verwijder_template(t))
            btn.bind("<Control-Button-1>", lambda e, t=titel: toggle_favoriet(t))

# Keybindings voor sneltoetsen
def sneltoetsen(event):
    key = event.char
    if key.isdigit():
        nummer = int(key) - 1
        titels = list(templates.keys())
        if 0 <= nummer < len(titels):
            gebruik_template(titels[nummer])

# Hoofdvenster
root = tk.Tk()
root.title("Mail Template Tool")
root.geometry("450x500")

# Zoekbalk
zoek_entry = tk.Entry(root, width=50)
zoek_entry.pack(pady=5)
zoek_entry.insert(0, "")
zoek_entry.bind("<KeyRelease>", lambda e: update_knoppen())

# Knoppenframe
knoppen_frame = tk.Frame(root)
knoppen_frame.pack(pady=5)

# Template beheer knoppen
beheer_frame = tk.Frame(root)
beheer_frame.pack(pady=10)
tk.Button(beheer_frame, text="Nieuwe template", command=voeg_template_toe).pack(side="left", padx=5)

# Initialiseer knoppen
update_knoppen()

# Sneltoetsen
root.bind("<Key>", sneltoetsen)

root.mainloop()
