import tkinter as tk
from tkinter import ttk
import math
import random
# ---------------- Fonctions ----------------
def calculer_resultat():
    try:
        Z = int(entry_Z.get())
        A = int(entry_A.get())
        choix = combo.get()

        if choix == "Nombre de neutrons":
            resultat = A - Z
            label_resultat["text"] = f"Nombre de neutrons : {resultat}"
        elif choix == "masse des neutrons":
            resultat = (A - Z) * 1.6749286e-27
            label_resultat["text"] = f"masse des neutrons : {resultat} kg"
        elif choix == "masse des électrons":
            resultat = Z * 9.10938356e-31
            label_resultat["text"] = f"masse des électrons : {resultat} kg"
        elif choix == "masse des protones":
            resultat = Z * 1.6726219e-27
            label_resultat["text"] = f"masse des protones : {resultat} kg"
        elif choix == "masse du noyau":
            resultat = (A - Z) * 1.6749286e-27 + Z * 1.6726219e-27
            label_resultat["text"] = f"masse du noyau : {resultat} kg"
        elif choix == "Charge du noyau":
            resultat = f"{Z} e⁺"
            label_resultat["text"] = f"Charge du noyau : {resultat}"
        elif choix == "Charge des électrons":
            resultat = f"{Z} e⁻"
            label_resultat["text"] = f"Charge des électrons : {resultat}"
        elif choix == "Charge de l'atome":
            label_resultat["text"] = "Charge de l'atome : neutre (0)"

        slide_to_frame(frame_resultat)
    except:
        label_resultat["text"] = "Erreur dans les données."
        slide_to_frame(frame_resultat)
def slide_to_frame(frame):
    # Simple transition fade (simulate with raise)
    frame.tkraise()
# ---------------- Animation atomique ----------------
electrons = []
angles = []
rayons = []
vitesse = []
orbites_max = 3  # nombre d'orbites K,L,M
def init_electrons(Z):
    global electrons, angles, rayons, vitesse
    electrons.clear()
    angles.clear()
    rayons.clear()
    vitesse.clear()
    # Répartir les électrons par orbite (simplifié : K=2, L=8, M=18, N=30)
    orbites = [2, 8, 18, 30]
    total = 0
    for i, max_e in enumerate(orbites):
        nb = min(max_e, Z-total)
        for j in range(nb):
            electrons.append(j)
            angles.append(j*(2*math.pi/nb))
            rayons.append(50 + i*40)  # orbite rayon
            vitesse.append(0.05 + 0.01*i)  # vitesse différente par orbite
        total += nb
        if total >= Z:
            break
pulse = 0
pulse_dir = 1
def dessiner_modele_atomique():
    global pulse, pulse_dir
    canvas.delete("all")
    # fond dynamique
    canvas.configure(bg=random.choice(["#0f0f0f", "#1a1a2e", "#2e1a3c", "#1a2e3c"]))
    # Noyau qui pulse
    pulse += 0.3 * pulse_dir
    if pulse > 6 or pulse < -6:
        pulse_dir *= -1
    taille_noyau = 20 + pulse
    canvas.create_oval(200-taille_noyau, 200-taille_noyau,
                       200+taille_noyau, 200+taille_noyau,
                       fill="orange", outline="yellow", width=2)
    # orbites et électrons
    couleurs_orbites = ["#ff6b6b", "#6bafff", "#6bff95", "#ff6bf3"]
    for i, angle in enumerate(angles):
        r = rayons[i]
        # orbite
        canvas.create_oval(200-r, 200-r, 200+r, 200+r,
                           outline=random.choice(couleurs_orbites), dash=(3,3), width=2)
        # position electron
        x = 200 + r * math.cos(angle)
        y = 200 + r * math.sin(angle)
        couleur_e = random.choice(["blue", "cyan", "magenta", "lime", "gold"])
        canvas.create_oval(x-7, y-7, x+7, y+7, fill=couleur_e)
        # avancer angle
        angles[i] += vitesse[i]
    canvas.after(50, dessiner_modele_atomique)
# ---------------- Interface Tkinter ---------------- n9aad interface
root = tk.Tk()
root.title("Assistant Atomique 🧪❇")
root.geometry("400x800")
root.configure(bg="#0b0f14")
frame_menu = tk.Frame(root, bg="#0b0f14")
frame_saisie = tk.Frame(root,bg="#0b0f14")
frame_resultat = tk.Frame(root,bg="#0b0f14")
for frame in (frame_menu, frame_saisie, frame_resultat):
    frame.grid(row=0, column=0, sticky='nsew')
# -------- Menu -------- lpage d'accueil
tk.Label(frame_menu, text="Bienvenue dans l'Assistant Atomique 🧪❇", font=("Consolas", 14), bg="#0b0f14", fg="#00f5d4").pack(pady=30)
tk.Button(frame_menu, text="Commencer", command=lambda: slide_to_frame(frame_saisie), fg="#9ab300").pack(pady=10)
tk.Button(frame_menu, text="Quitter", command=root.destroy, fg="#9ab300").pack(pady=10)
# -------- Saisie --------# lpage li fihaa les entry w les boutons ofen keydkhl l user data
tk.Label(frame_saisie, text="Entrez les données de l'atome", font=("Consolas", 13),fg="#ffcc00",bg="#0b0f14").pack(pady=10)
tk.Label(frame_saisie, text="Nombre atomique (Z)",font=("Consolas", 12),fg="#ffcc00",bg="#0b0f14").pack()
entry_Z = tk.Entry(frame_saisie)
entry_Z.pack()
tk.Label(frame_saisie, text="Nombre de masse (A)",font=("Consolas", 12),fg="#ffcc00",bg="#0b0f14").pack()
entry_A = tk.Entry(frame_saisie)
entry_A.pack()
tk.Label(frame_saisie, text="Choisissez le calcul à faire",font=("Consolas", 12),fg="#cc0000",bg="#0b0f14").pack(pady=5)
combo = ttk.Combobox(frame_saisie, values=[
    "Nombre de neutrons",
    "Charge du noyau",
    "Charge des électrons",
    "Charge de l'atome",
    "masse des neutrons",
    "masse des protones",
    "masse des électrons",
    "masse du noyau"
])
combo.current(0)
combo.pack()
tk.Button(frame_saisie, text="Calculer", command=calculer_resultat).pack(pady=10)
tk.Button(frame_saisie, text="Retour au menu", command=lambda: slide_to_frame(frame_menu)).pack()
# -------- Résultat --------# lpage li fihaa lresultat w lcanvas
label_resultat = tk.Label(frame_resultat, text="", font=("Consolas", 12))
label_resultat.pack(pady=10)
canvas = tk.Canvas(frame_resultat, width=400, height=400, bg="black")
canvas.pack(pady=10)
tk.Button(frame_resultat, text="Initialiser le modèle atomique",
          command=lambda: init_electrons(int(entry_Z.get()))).pack(pady=5)
tk.Button(frame_resultat, text="Nouveau calcul", command=lambda: slide_to_frame(frame_saisie)).pack()
tk.Button(frame_resultat, text="Menu principal", command=lambda: slide_to_frame(frame_menu)).pack(pady=5)
slide_to_frame(frame_menu)
dessiner_modele_atomique()
root.mainloop()