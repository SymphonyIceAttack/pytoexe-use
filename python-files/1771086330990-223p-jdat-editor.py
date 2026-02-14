import tkinter as tk
from tkinter import messagebox
import os
import subprocess

# Chemins des fichiers à vérifier
fichiers_a_verifier = [
    r"C:\jdat\jdat.exe",
    r"C:\jdat\jdat-shell.exe",
    r"C:\Windows\system32\jdat-shell.bat"
]

# Vérification des fichiers
for f in fichiers_a_verifier:
    if not os.path.exists(f):
        root = tk.Tk()
        root.withdraw()  # Cache la fenêtre principale
        messagebox.showerror(
            "Fichiers manquants",
            f"Jdat est introuvable:\n{f}\nVeuliez installer Jdat sur le site officiel"
        )
        root.destroy()
        exit()  # Ferme l'application si un fichier est manquant

# --- Fenêtre principale ---
root = tk.Tk()
root.title("Éditeur JDAT")

# Zone de texte pour coder
zone_code = tk.Text(root, width=60, height=20)
zone_code.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

# Fonctions des boutons
def ouvrir_fichier():
    from tkinter import filedialog
    fichier = filedialog.askopenfilename()
    if fichier:
        with open(fichier, 'r') as f:
            zone_code.delete("1.0", tk.END)
            zone_code.insert(tk.END, f.read())
        label_explorer.config(text=f"Fichier ouvert: {fichier}")

def sauvegarder_fichier():
    from tkinter import filedialog
    fichier = filedialog.asksaveasfilename(defaultextension=".txt")
    if fichier:
        with open(fichier, 'w') as f:
            f.write(zone_code.get("1.0", tk.END))
        label_explorer.config(text=f"Fichier sauvegardé: {fichier}")

def creer_fichier():
    zone_code.delete("1.0", tk.END)
    label_explorer.config(text="Nouveau fichier")

def executer_shell():
    try:
        resultat = subprocess.run(r"C:\jdat\jdat-shell.exe", shell=True, capture_output=True, text=True)
        messagebox.showinfo("Résultat", resultat.stdout or "Pas de sortie")
    except Exception as e:
        messagebox.showerror("Erreur", str(e))

# Boutons
btn_ouvrir = tk.Button(root, text="Ouvrir", command=ouvrir_fichier)
btn_ouvrir.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

btn_sauvegarder = tk.Button(root, text="Sauvegarder", command=sauvegarder_fichier)
btn_sauvegarder.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

btn_creer = tk.Button(root, text="Créer fichier", command=creer_fichier)
btn_creer.grid(row=1, column=2, sticky="ew", padx=5, pady=5)

btn_shell = tk.Button(root, text="Shell", command=executer_shell)
btn_shell.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

# Explorateur / label
label_explorer = tk.Label(root, text="Explorateur de fichiers")
label_explorer.grid(row=3, column=0, columnspan=3, sticky="w", padx=10, pady=5)

root.mainloop()
