# Trouble Shooter by Greenwood
# Discord: https://discord.gg/VDY8tJWd

import time
import os

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def menu():
    clear()
    print("===================================")
    print("   Trouble Shooter by Greenwood")
    print("===================================")
    print("Discord: https://discord.gg/VDY8tJWd\n")
    print("1. Troubleshoot Eon")
    print("0. Exit")
    print("===================================")

def troubleshoot_eon():
    clear()
    print("Troubleshooting is running, please wait...\n")
    
    # Run message for 10 seconds
    for i in range(1, 11):
        print(f"Running troubleshooting... {i}/10 seconds")
        time.sleep(1)

    print("\nTroubleshoot successfully completed!")
    input("\nPress Enter to return to menu...")

while True:
    menu()
    choice = input("Select an option: ")

    if choice == "1":
        troubleshoot_eon()
    elif choice == "0":
        print("Exiting Trouble Shooter...")
        time.sleep(1)
        break
    else:
        print("Invalid option. Please try again.")
        time.sleep(1)
