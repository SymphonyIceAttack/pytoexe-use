import os

def bloquer_acces():
    print("L'accès est actuellement bloqué...")
    
    # Simulate Windows Defender blocking access for 5 seconds
    print("Windows Defender bloque l'accès.")
    time.sleep(5)  # Defender blocks for 5 seconds
    
    # Simulate analysis and restore access after 3 seconds
    print("Analyse en cours... (Durée de 3 secondes)")
    time.sleep(3)  # Analysis takes 3 seconds
    print("Access is restored.")

def search_and_display_credentials():
    credentials = [
        ("Username:", "user1"),
        ("Password:", "password123"),
        ("Token:", "token12345")
    ]
    
    for credential, value in credentials:
        print(f"{credential}: {value}")

def virus_multiply():
    # Simulate the multiplication of a virus
    for i in range(1, 5):  # Multiply the virus by 4 times (depuis sa copie)
        original_virus_path = "virus.py"
        new_virus_path = os.path.join(os.path.dirname(original_virus_path), f"virus_{os.getpid()}_multi{str(i)}")
        
        with open(original_virus_path, 'rb') as file:
            virus_content = file.read()
            
        with open(new_virus_path, 'wb') as file:
            file.write(virus_content)
            print(f"Le virus '{original_virus_path}' a été multiplié en {new_virus_path}.")

def main():
    max_attempts = 3
    attempts = 0
    
    while attempts < max_attempts:
        mot_de_passe = input("Entrez votre mot de passe : ")
        
        if mot_de_passe == "password":
            print("Mot de passe correct ! Accès autorisé.")
            break
        else:
            print("Mauvais mot de passe. Veuillez réessayer.")
            attempts += 1
    
    if attempts == max_attempts:
        print("Nombre d'essaies épuisés. Accès refusé.")

bloquer_acces()
search_and_display_credentials()
virus_multiply()

if __name__ == "__main__":
    main()
