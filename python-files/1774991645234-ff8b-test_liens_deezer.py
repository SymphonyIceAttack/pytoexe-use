import requests
import webbrowser
import os

# Fichier avec tous tes liens Deezer (un lien par ligne)
fichier_liens = "liens.txt"

# Fichiers de sortie
fichier_valide = "valide.txt"
fichier_mort = "mort.txt"

# Lire les liens
if not os.path.exists(fichier_liens):
    print(f"Erreur : '{fichier_liens}' introuvable !")
    input("Appuie sur Entrée pour quitter...")
    exit()

with open(fichier_liens, "r") as f:
    liens = [l.strip() for l in f.readlines() if l.strip()]

valide = []
mort = []

print("⏳ Test des liens...")

for lien in liens:
    try:
        r = requests.head(lien, allow_redirects=True, timeout=5)
        if r.status_code == 200:
            print(f"[OK] {lien}")
            valide.append(lien)
        else:
            print(f"[MORT] {lien} (status {r.status_code})")
            mort.append(lien)
    except Exception as e:
        print(f"[ERREUR] {lien} ({e})")
        mort.append(lien)

# Sauvegarde des résultats
with open(fichier_valide, "w") as f:
    f.write("\n".join(valide))

with open(fichier_mort, "w") as f:
    f.write("\n".join(mort))

print(f"\n✅ Terminé ! {len(valide)} valides, {len(mort)} morts")

# Optionnel : ouvrir automatiquement les liens valides dans le navigateur
ouvrir = input("Ouvrir les liens valides dans le navigateur ? (o/N) : ").lower()
if ouvrir == "o":
    for lien in valide:
        webbrowser.open(lien)

input("Appuie sur Entrée pour quitter...")