import os
import sys

def convert():
    if len(sys.argv) < 2:
        print("Usage: Glissez un fichier GEDCOM sur cet executable.")
        input("Appuyez sur Entree pour quitter...")
        return
    
    fichier_entree = sys.argv[1]
    nom_base = os.path.splitext(fichier_entree)[0]
    fichier_sortie = f"{nom_base}_pour_Heredis.ged"

    try:
        # Lecture en encodage DOS (Griot)
        with open(fichier_entree, 'r', encoding='cp850', errors='ignore') as f:
            contenu = f.read()
        
        # Correction des en-tetes pour Heredis
        contenu = contenu.replace('CHAR IBMPC', 'CHAR UTF-8')
        contenu = contenu.replace('CHAR ANSEL', 'CHAR UTF-8')
        
        # Sauvegarde en format moderne
        with open(fichier_sortie, 'w', encoding='utf-8') as f:
            f.write(contenu)
            
        print(f"Succes ! Fichier cree : {fichier_sortie}")
        print("Vous pouvez l'importer dans Heredis 2026.")
        input("Appuyez sur Entree pour fermer...")
    except Exception as e:
        print(f"Erreur : {e}")
        input("Appuyez sur Entree pour fermer...")

if __name__ == '__main__':
    convert()