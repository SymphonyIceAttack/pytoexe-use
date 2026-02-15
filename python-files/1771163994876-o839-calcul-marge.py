import tkinter as tk
from tkinter import messagebox

def calculer():
    try:
        achat_ht = float(entry_achat.get())
        marge = float(entry_marge.get())

        taux_social = 0.13
        taux_tva = 0.20

        # -------- SANS TVA --------
        achat_ttc = achat_ht * (1 + taux_tva)
        prix_sans_tva = (achat_ttc + marge) / (1 - taux_social)

        # -------- AVEC TVA --------
        prix_ht = (achat_ht + marge) / (1 - taux_social)
        prix_ttc = prix_ht * (1 + taux_tva)

        resultat_text.set(
            f"SANS TVA : {prix_sans_tva:.2f} €\n\n"
            f"AVEC TVA : {prix_ttc:.2f} € TTC\n"
            f"(soit {prix_ht:.2f} € HT)"
        )

    except ValueError:
        messagebox.showerror("Erreur", "Veuillez remplir correctement les champs.")

# Fenêtre principale
app = tk.Tk()
app.title("Calculateur de Marge")
app.geometry("350x300")
app.resizable(False, False)

# Titre
tk.Label(app, text="Calculateur de Marge", font=("Arial", 14, "bold")).pack(pady=10)
tk.Label(app, text="Cotisation Sociale 13%").pack()

# Champ Achat
tk.Label(app, text="Prix d'achat HT (€)").pack(pady=(15, 0))
entry_achat = tk.Entry(app)
entry_achat.pack()

# Champ Marge
tk.Label(app, text="Marge nette souhaitée (€)").pack(pady=(15, 0))
entry_marge = tk.Entry(app)
entry_marge.pack()

# Bouton
tk.Button(app, text="Calculer", command=calculer, bg="#27b671", fg="white").pack(pady=15)

# Résultat
resultat_text = tk.StringVar()
tk.Label(app, textvariable=resultat_text, justify="left").pack()

app.mainloop()
