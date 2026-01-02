import os
import sys
import ctypes
import subprocess
import platform
import tkinter as tk
from tkinter import messagebox

def is_admin():
    """Vérifie si le script est lancé avec les droits d'administrateur."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Relance le script avec les droits d'administrateur (Windows)."""
    # Si on n'est pas admin, on relance le script avec le verbe 'runas'
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

def creer_compte():
    username = entry_user.get()
    password = entry_pass.get()

    if not username or not password:
        messagebox.showwarning("Attention", "Veuillez remplir tous les champs.")
        return

    try:
        # Commande Windows pour ajouter un utilisateur
        subprocess.run(f"net user {username} {password} /add", shell=True, check=True, capture_output=True)
        messagebox.showinfo("Succès", f"La session '{username}' a été créée avec succès !")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Erreur", f"Échec de la création.\nErreur : {e.stderr.decode('cp850')}")

# --- Logique de démarrage ---
if platform.system() == "Windows":
    if not is_admin():
        # Si on n'est pas admin, on demande l'autorisation et on quitte la version actuelle
        run_as_admin()
        sys.exit()

# --- Interface Graphique (Tkinter) ---
app = tk.Tk()
app.title("Créateur de Sessions (Mode Admin)")
app.geometry("350x300")
app.configure(padx=20, pady=20)

tk.Label(app, text="🚀 Créateur de Session Rapide", font=("Arial", 12, "bold")).pack(pady=10)

tk.Label(app, text="Nom d'utilisateur :").pack(anchor="w")
entry_user = tk.Entry(app, width=30)
entry_user.pack(pady=5)

tk.Label(app, text="Mot de passe :").pack(anchor="w")
entry_pass = tk.Entry(app, width=30, show="*")
entry_pass.pack(pady=5)

btn_creer = tk.Button(app, text="Créer la session maintenant", command=creer_compte, 
                      bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), height=2)
btn_creer.pack(pady=20, fill="x")

app.mainloop()