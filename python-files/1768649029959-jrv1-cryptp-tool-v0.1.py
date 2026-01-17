import os
import sys
import time
from colorama import Fore, init

init(autoreset=True)

def clear():
    os.system("cls")

def loading():
    clear()
    print(Fore.GREEN + "Inizializzazione CRYPTO TOOL...\n")

    total_time = 12
    steps = 100
    delay = total_time / steps

    for i in range(steps + 1):
        bar = "█" * (i // 2) + "-" * (50 - i // 2)
        sys.stdout.write(
            f"\r{Fore.RED}[{bar}]{Fore.GREEN} {i}%"
        )
        sys.stdout.flush()
        time.sleep(delay)

    time.sleep(1)

def menu():
    clear()
    print(Fore.RED + "╔════════════════════════════╗")
    print(Fore.RED + "║        CRYPTO TOOL         ║")
    print(Fore.RED + "╚════════════════════════════╝\n")

    print(Fore.GREEN + "[1]")
    print(Fore.RED   + "[2]")
    print(Fore.GREEN + "[3]")
    print(Fore.RED   + "[4]")
    print(Fore.GREEN + "[5]")
    print(Fore.RED   + "[6]\n")

    scelta = input(Fore.GREEN + ">>> ")

    if scelta == "6":
        print(Fore.RED + "\nChiusura manuale...")
        input(Fore.GREEN + "Premi INVIO per uscire")
        sys.exit()

    input(Fore.RED + "\nPremi INVIO per tornare al menu...")

# MAIN PROTETTO
try:
    loading()
    while True:
        menu()
except Exception as e:
    print("\nERRORE:", e)
    input("\nPremi INVIO per chiudere...")
