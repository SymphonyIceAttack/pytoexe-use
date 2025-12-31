import os
import sys
import ctypes

def is_admin():
    """Vérifie si le script est exécuté avec les droits d'administrateur."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def modifier_heure():
    # Si nous ne sommes pas administrateur, on relance le script avec les droits
    if not is_admin():
        print("Demande des droits administrateur...")
        # Relance le script avec le paramètre 'runas' (exécuter en tant qu'admin)
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        return

    # --- Le code ci-dessous ne s'exécute que si on a les droits ---
    print("=== Application de Modification de l'Heure ===")
    print("Statut : Connecté en tant qu'Administrateur")
    print("-" * 40)
    
    nouvelle_heure = input("Entrez la nouvelle heure (HH:MM:SS) : ")
    
    try:
        # Commande Windows pour changer l'heure
        os.system(f"time {nouvelle_heure}")
        print(f"\n✅ Succès ! L'heure a été modifiée : {nouvelle_heure}")
    except Exception as e:
        print(f"\n❌ Erreur : {e}")

    input("\nAppuyez sur Entrée pour quitter...")

if __name__ == "__main__":
    modifier_heure()