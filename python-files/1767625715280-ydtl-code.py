def calculate_serial(username):
    hash_value = 0
    for char in username:
        hash_value = hash_value * 31 + ord(char)
    return hash_value

print("KeygenMe-Easy - Simulation d'un système de validation de licence")
print("Algorithme : hash = hash * 31 + ord(char)\n")

username = input("Entrez le nom d'utilisateur : ").strip()

serial = calculate_serial(username)

print(f"\nNuméro de série valide pour '{username}' : {serial}")
print("\nUtilisez ce serial dans un programme qui implémente le même algo pour valider.")

input("\nAppuyez sur Entrée pour quitter...")