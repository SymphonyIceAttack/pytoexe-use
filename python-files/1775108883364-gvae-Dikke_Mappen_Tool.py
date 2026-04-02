import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, scrolledtext

# === DEFAULT TEMPLATE ===
DEFAULT_TEMPLATE = {
    "Afbeeldingen": [],
    "Berekeningen": [],
    "Excel": [],
    "Inventor": [],
    "PDF": []
}

# === FUNCTIES ===

def maak_submappen(basis_pad, structuur):
    for mapnaam, submappen in structuur.items():
        pad = os.path.join(basis_pad, mapnaam)
        os.makedirs(pad, exist_ok=True)
        for sub in submappen:
            os.makedirs(os.path.join(pad, sub), exist_ok=True)


def maak_mappen(excel_bestand, output_pad, hoofdmap_naam, template):
    try:
        df = pd.read_excel(excel_bestand)
        hoofdmap_pad = os.path.join(output_pad, hoofdmap_naam)
        os.makedirs(hoofdmap_pad, exist_ok=True)

        for _, row in df.iterrows():
            order = str(row[0]).strip()
            bon = str(row[1]).strip()
            omschrijving = str(row[2]).strip()
            if order.lower() == 'nan' or bon.lower() == 'nan':
                continue

            mapnaam = f"{order}.{bon} - {omschrijving}"
            map_pad = os.path.join(hoofdmap_pad, mapnaam)
            os.makedirs(map_pad, exist_ok=True)
            maak_submappen(map_pad, template)

        messagebox.showinfo("Klaar", "Mappenstructuur succesvol aangemaakt!")
    except Exception as e:
        messagebox.showerror("Fout", str(e))

# === TEMPLATE EDITOR ===

def bewerk_template(template):
    nieuw_template = {}
    for mapnaam in template.keys():
        sub = simpledialog.askstring("Submappen", f"Submappen voor '{mapnaam}' (komma gescheiden):", initialvalue=','.join(template[mapnaam]))
        if sub:
            sublijst = [s.strip() for s in sub.split(',') if s.strip()]
        else:
            sublijst = []
        nieuw_template[mapnaam] = sublijst
    return nieuw_template

# === PREVIEW FUNCTIE ===

def preview_mappen():
    excel_bestand = excel_entry.get()
    hoofdmap = hoofdmap_entry.get()
    template = template_var.get()

    if not excel_bestand or not hoofdmap:
        messagebox.showwarning("Let op", "Vul Excel bestand en hoofdmap in")
        return

    try:
        df = pd.read_excel(excel_bestand)
        preview_text.delete(1.0, tk.END)
        preview_text.insert(tk.END, f"{hoofdmap}/\n")

        for _, row in df.iterrows():
            order = str(row[0]).strip()
            bon = str(row[1]).strip()
            omschrijving = str(row[2]).strip()
            if order.lower() == 'nan' or bon.lower() == 'nan':
                continue

            mapnaam = f"{order}.{bon} - {omschrijving}"
            preview_text.insert(tk.END, f"  {mapnaam}/\n")
            for hoofd, sub in template.items():
                preview_text.insert(tk.END, f"    {hoofd}/\n")
                for s in sub:
                    preview_text.insert(tk.END, f"      {s}/\n")

    except Exception as e:
        messagebox.showerror("Fout", str(e))

# === GUI ===

def kies_excel():
    bestand = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    excel_entry.delete(0, tk.END)
    excel_entry.insert(0, bestand)


def kies_output():
    map_pad = filedialog.askdirectory()
    output_entry.delete(0, tk.END)
    output_entry.insert(0, map_pad)


def start():
    excel_bestand = excel_entry.get()
    output_pad = output_entry.get()
    hoofdmap = hoofdmap_entry.get()

    if not excel_bestand or not output_pad or not hoofdmap:
        messagebox.showwarning("Let op", "Vul alles in")
        return

    template = template_var.get()
    maak_mappen(excel_bestand, output_pad, hoofdmap, template)


def bewerk_template_gui():
    nieuwe_template = bewerk_template(template_var.get())
    template_var.set(nieuwe_template)
    messagebox.showinfo("Template opgeslagen", "Nieuwe mappenstructuur template is opgeslagen")

# === WINDOW ===
root = tk.Tk()
root.title("Excel naar Mappenstructuur")
root.geometry("600x550")

# Excel
 tk.Label(root, text="Excel bestand:").pack()
excel_entry = tk.Entry(root, width=60)
excel_entry.pack()
tk.Button(root, text="Bladeren", command=kies_excel).pack()

# Drag & drop support
def drop(event):
    bestand = event.data
    excel_entry.delete(0, tk.END)
    excel_entry.insert(0, bestand)

excel_entry.drop_target_register(tk.DND_FILES)
excel_entry.dnd_bind('<<Drop>>', drop)

# Output
 tk.Label(root, text="Output map:").pack()
output_entry = tk.Entry(root, width=60)
output_entry.pack()
tk.Button(root, text="Kies map", command=kies_output).pack()

# Hoofdmap
 tk.Label(root, text="Hoofdmap naam:").pack()
hoofdmap_entry = tk.Entry(root, width=60)
hoofdmap_entry.insert(0, "20250433 - Sorteerlijn")
hoofdmap_entry.pack()

# Template
template_var = tk.Variable(value=DEFAULT_TEMPLATE)
 tk.Button(root, text="Bewerk template", command=bewerk_template_gui, bg="orange", fg="black").pack(pady=10)

# Preview knop
 tk.Button(root, text="Preview mappen", command=preview_mappen, bg="blue", fg="white").pack(pady=5)
preview_text = scrolledtext.ScrolledText(root, width=70, height=20)
preview_text.pack()

# Start knop
 tk.Button(root, text="Maak mappen", command=start, bg="green", fg="white").pack(pady=15)

root.mainloop()

# === EXE MAKEN ===
# pip install pyinstaller
# pyinstaller --onefile --noconsole script.py
