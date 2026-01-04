import time
import os
import sys

def clear_screen():
    try:
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")
    except:
        # If clearing fails (online IDEs), just print new lines
        print("\n" * 50)

def loading_animation(seconds):
    print("Verifying game files", end="", flush=True)
    for _ in range(seconds):
        time.sleep(1)
        print(".", end="", flush=True)
    print("\nVerification complete! Eon is now unbanned (simulation).")

def unban_eon():
    clear_screen()
    print("Eon Unbanner by David\n")
    time.sleep(1)
    loading_animation(5)

def main():
    while True:
        clear_screen()
        print("=== Eon Unbanner by David ===")
        print("1. Unban Eon")
        print("2. Exit")

        choice = input("\nSelect an option (1-2): ").strip()

        if choice == "1":
            unban_eon()
            input("\nPress Enter to return to the main menu...")
        elif choice == "2":
            print("Exiting...")
            time.sleep(1)
            sys.exit()
        else:
            print("Invalid choice! Try again.")
            time.sleep(2)

if __name__ == "__main__":
    main()
