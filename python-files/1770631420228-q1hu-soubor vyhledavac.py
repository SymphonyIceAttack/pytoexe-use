import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# === TYPY SOUBORŮ ===
TYPY = {
    "TEXT": (".txt", ".py", ".cs", ".html", ".css", ".js", ".json", ".xml", ".log"),
    "OBRÁZEK": (".png", ".jpg", ".jpeg", ".gif", ".bmp"),
    "AUDIO": (".mp3", ".wav", ".ogg"),
    "VIDEO": (".mp4", ".avi", ".mkv"),
    "ARCHIV": (".zip", ".rar", ".7z"),
}

def urci_typ(soubor):
    ext = os.path.splitext(soubor)[1].lower()
    for typ, pripony in TYPY.items():
        if ext in pripony:
            return typ
    return "OSTATNÍ"

# === DATA ===
soubory_data = []  # (cesta, název, typ, velikost)

# === FUNKCE ===
def vybrat_slozku():
    cesta = filedialog.askdirectory()
    if cesta:
        cesta_var.set(cesta)
        nacist_soubory()

def nacist_soubory():
    seznam.delete(0, tk.END)
    soubory_data.clear()

    cesta = cesta_var.get()
    if not cesta:
        return

    povolene_typy = {t for t, v in checkboxy.items() if v.get()}

    for root, dirs, files in os.walk(cesta):
        for file in files:
            typ = urci_typ(file)
            if typ in povolene_typy:
                full = os.path.join(root, file)
                try:
                    velikost = os.path.getsize(full)
                except:
                    velikost = 0
                soubory_data.append((full, file, typ, velikost))

    seradit()

def seradit():
    kriterium = trideni_var.get()

    if kriterium == "Název A–Z":
        soubory_data.sort(key=lambda x: x[1].lower())
    elif kriterium == "Název Z–A":
        soubory_data.sort(key=lambda x: x[1].lower(), reverse=True)
    elif kriterium == "Velikost ↑":
        soubory_data.sort(key=lambda x: x[3])
    elif kriterium == "Velikost ↓":
        soubory_data.sort(key=lambda x: x[3], reverse=True)
    elif kriterium == "Typ souboru":
        soubory_data.sort(key=lambda x: x[2])

    seznam.delete(0, tk.END)
    for full, name, typ, size in soubory_data:
        seznam.insert(
            tk.END,
            f"[{typ}] {name} ({size//1024} KB) — {full}"
        )

def hledat_string():
    if not checkboxy["TEXT"].get():
        messagebox.showinfo("Info", "Pro hledání textu musí být povolen typ TEXT")
        return

    text = hledany_var.get()
    if not text:
        messagebox.showwarning("Chyba", "Zadej hledaný text")
        return

    vysledky.delete(0, tk.END)

    for full, name, typ, size in soubory_data:
        if typ != "TEXT":
            continue
        try:
            with open(full, "r", encoding="utf-8", errors="ignore") as f:
                if text in f.read():
                    vysledky.insert(tk.END, full)
        except:
            pass

    if vysledky.size() == 0:
        vysledky.insert(tk.END, "Nic nenalezeno")

# === GUI ===
okno = tk.Tk()
okno.title("Miluju davida")
okno.geometry("1150x700")

cesta_var = tk.StringVar()
hledany_var = tk.StringVar()
trideni_var = tk.StringVar(value="Název A–Z")

# Horní panel
top = tk.Frame(okno)
top.pack(fill="x", padx=10, pady=5)

tk.Entry(top, textvariable=cesta_var, width=80).pack(side="left", padx=5)
tk.Button(top, text="Vybrat složku", command=vybrat_slozku).pack(side="left")

ttk.Combobox(
    top,
    textvariable=trideni_var,
    values=["Název A–Z", "Název Z–A", "Velikost ↑", "Velikost ↓", "Typ souboru"],
    state="readonly",
    width=18
).pack(side="left", padx=10)

tk.Button(top, text="Seřadit", command=seradit).pack(side="left")

# Filtry
filtry = tk.LabelFrame(okno, text="Typy souborů")
filtry.pack(fill="x", padx=10, pady=5)

checkboxy = {}
for typ in ["TEXT", "OBRÁZEK", "AUDIO", "VIDEO", "ARCHIV", "OSTATNÍ"]:
    var = tk.BooleanVar(value=True)
    checkboxy[typ] = var
    tk.Checkbutton(filtry, text=typ, variable=var, command=nacist_soubory)\
        .pack(side="left", padx=5)

# Hledání
search = tk.Frame(okno)
search.pack(fill="x", padx=10, pady=5)

tk.Label(search, text="Hledaný text:").pack(side="left")
tk.Entry(search, textvariable=hledany_var, width=30).pack(side="left", padx=5)
tk.Button(search, text="Hledat text", command=hledat_string).pack(side="left")

# Seznamy
frame = tk.PanedWindow(okno, sashwidth=6)
frame.pack(fill="both", expand=True, padx=10, pady=10)

seznam = tk.Listbox(frame)
vysledky = tk.Listbox(frame)

frame.add(seznam)
frame.add(vysledky)

okno.mainloop()
