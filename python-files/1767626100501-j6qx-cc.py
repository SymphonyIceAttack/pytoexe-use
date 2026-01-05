def check_serial(username, serial):
    hash_value = 0
    for char in username:
        hash_value = hash_value * 31 + ord(char)
    return hash_value == serial

print("Programme protégé - Validation de licence")

username = input("Nom d'utilisateur : ").strip()
try:
    serial = int(input("Numéro de série : "))
except:
    print("Wrong !")
    input(); exit()

if check_serial(username, serial):
    print("Correct !")
else:
    print("Wrong !")

input("\nAppuyez sur Entrée pour quitter...")