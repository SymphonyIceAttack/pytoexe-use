import tkinter as tk

compteur = 0

def ajouter():
    global compteur
    compteur += 1
    label.config(text=f"Compteur : {compteur}")

def retirer():
    global compteur
    compteur -= 1
    label.config(text=f"Compteur : {compteur}")

def reset():
    global compteur
    compteur = 0
    label.config(text=f"Compteur : {compteur}")


fenetre = tk.Tk()

fenetre.title("Ward DJet")
fenetre.geometry("700x500")

titre = tk.Label(
    fenetre,
    text="🚀 WARD DJET",
    font=("Arial", 28, "bold")
)

titre.pack(pady=30)

description = tk.Label(
    fenetre,
    text="Mon application Python",
    font=("Arial", 16)
)

description.pack()

label = tk.Label(
    fenetre,
    text="Compteur : 0",
    font=("Arial", 20)
)

label.pack(pady=30)

tk.Button(
    fenetre,
    text="➕ Ajouter",
    command=ajouter,
    width=20
).pack(pady=5)

tk.Button(
    fenetre,
    text="➖ Retirer",
    command=retirer,
    width=20
).pack(pady=5)

tk.Button(
    fenetre,
    text="🔄 Réinitialiser",
    command=reset,
    width=20
).pack(pady=5)

fenetre.mainloop()
