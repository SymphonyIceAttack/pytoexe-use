#Python Multitool
#Made by https://github.com/Mads-Milo

from colorama import *
import os
import subprocess

def banner():
    global cmd

    print(Fore.CYAN + "=====================")
    print("   Phantom Toolkit")
    print("  Made By Mads Milo")
    print("=====================")
    print("=====================================================")
    print("[1] Network Scanner   [2] Domain IP  [3] Ddos Scanner")
    print("=====================================================")
    print("\n")
    cmd = input(Fore.BLUE + "Enter Number >> ")

Fore.RESET
banner()

while True:
    if cmd == "1":
        os.system('cls' if os.name == 'nt' else 'clear')
        subprocess.run(["python", "network_scanner.py"])
        input(Fore.GREEN + "\nPress Enter to return to main menu...")
        os.system('cls' if os.name == 'nt' else 'clear')
        banner()
    elif cmd == "2":
        os.system('cls' if os.name == 'nt' else 'clear')
        subprocess.run(["python", "ip-from-domain.py"])
        input(Fore.GREEN + "\nPress Enter to return to main menu...")
        os.system('cls' if os.name == 'nt' else 'clear')
        banner()
    elif cmd == "3":
        os.system('cls' if os.name == 'nt' else 'clear')
        subprocess.run(["python", "ddos_checker.py"])
        input(Fore.GREEN + "\nPress Enter to return to main menu...")
        os.system('cls' if os.name == 'nt' else 'clear')
        banner()