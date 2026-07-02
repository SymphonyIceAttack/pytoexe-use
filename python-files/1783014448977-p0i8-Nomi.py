import os
import random
import string
import time

GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"

os.system("cls" if os.name == "nt" else "clear")

print(GREEN + """
 ____  ____  ______   ________  ____   ____   ______   
|_  _||_  _||_   _ `.|_   __  ||_  _| |_  _|.' ____ \  
  \ \  / /    | | `. \ | |_ \_|  \ \   / /  | (___ \_| 
   > `' <     | |  | | |  _| _    \ \ / /    _.____`.  
 _/ /'`\ \_  _| |_.' /_| |__/ |    \ ' /    | \____) | 
|____||____||______.'|________|     \_/      \______.' 
""" + RESET)

print(CYAN + "Developed By Rinascere\n" + RESET)

while True:
    try:
        quantita = int(input("➜ Inserisci Quanti Nomi Generare: "))
        break
    except ValueError:
        print("Inserisci un numero valido.")

while True:
    try:
        lunghezza = int(input("➜ Inserisci Lunghezza (3/4/5...): "))
        if lunghezza > 0:
            break
    except ValueError:
        pass
    print("Inserisci un numero valido.")

print(YELLOW + "\nGenerazione in corso...\n" + RESET)

for i in range(31):
    barra = "█" * i + "░" * (30 - i)
    print(f"\r[{barra}] {i * 100 // 30}%", end="", flush=True)
    time.sleep(0.03)

caratteri = string.ascii_lowercase + string.digits

cartella = os.path.dirname(os.path.abspath(__file__))
file_txt = os.path.join(cartella, "nomi.txt")

print(GREEN + "\n\n========== NOMI GENERATI ==========\n" + RESET)

with open(file_txt, "w", encoding="utf-8") as f:
    for i in range(1, quantita + 1):
        nome = "".join(random.choice(caratteri) for _ in range(lunghezza))
        print(f"[{i:03}] {nome}")
        f.write(nome + "\n")

print(CYAN + "\n"Tieni i* Nom*)
print("Generazione completata!")
print(f"File salvato in:\n{file_txt}")
print("Developed by Rinascere" + RESET)

input("\nPremi INVIO per uscire...")