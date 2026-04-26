import pyautogui
import time
import random
import sys
import os

def main():
    print("=" * 50)
    print("MOVIMENTO MOUSE 10 SECONDES")
    print("=" * 50)
    print("La souris va bouger pendant 10 secondes...")
    print("Pour arrêter avant : Ctrl+C")
    print("=" * 50)
    
    start_time = time.time()
    count = 0
    
    try:
        while time.time() - start_time < 10:
            x, y = pyautogui.position()
            
            # Petits mouvements aléatoires
            new_x = x + random.randint(-150, 150)
            new_y = y + random.randint(-150, 150)
            
            pyautogui.moveTo(new_x, new_y, duration=0.1)
            
            count += 1
            remaining = int(10 - (time.time() - start_time))
            print(f"\r⏱️  Temps restant : {remaining} sec  |  Mouvements : {count}", end="")
            
            time.sleep(0.08)
        
        print("\n\n✅ Terminé ! 10 secondes sont écoulées.")
        print("La souris ne bouge plus.")
        print("Fermeture dans 3 secondes...")
        time.sleep(3)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Programme arrêté manuellement.")
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        input("Appuyez sur Enter pour quitter...")