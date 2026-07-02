import sys

def run_main_application():
    """
    This function represents the main core of your application.
    Replace the placeholder code below with your actual program logic.
    """
    print("\n[+] Initializing main application modules...")
    
    # --- Place your application logic here ---
    print("[+] Application is running successfully.")
    # -----------------------------------------
    
    # Keeps the console window open when running as an .exe
    input("\nPress Enter to exit...")

def verify_key():
    """
    Prompts the user for a key and checks if it begins with 'SYBE'.
    """
    print("====================================")
    print("        APPLICATION LOGIN           ")
    print("====================================")
    
    user_input = input("Enter your product key: ").strip()
    
    # Check if the input starts with the required prefix
    if user_input.startswith("SYBE"):
        print("\n[✔] Key validation successful!")
        run_main_application()
    else:
        print("\n[❌] Invalid key. Access denied.")
        input("\nPress Enter to exit...")
        sys.exit()

if __name__ == "__main__":
    verify_key()