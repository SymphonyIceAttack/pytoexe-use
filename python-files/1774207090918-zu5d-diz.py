import hashlib
import os

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("="*50)
    print("       CRACKME v1.0 by FREDERIK")
    print("="*50)
    print("Найди правильный пароль.\n")
    
    # Хеш правильного пароля (пароль: fr3d3r1k2027)
    correct_hash = "a7c5f4c8a9d2b1e3f6h9j2k4l5m6n7p8q9r0s1t2u3v4w5x6y7z8"
    
    password = input("[?] Введи пароль: ")
    
    # Примитивная защита для примера
    if len(password) < 4:
        print("\n[!] Слишком коротко. Попробуй ещё.")
        return
    
    # Генерация "хеша" (упрощённая, для тренировки)
    fake_hash = ""
    for i, char in enumerate(password):
        fake_hash += chr((ord(char) + i) % 26 + 97)
    
    # Реальный пароль: fr3d3r1k2027
    if password == "fr3d3r1k2027":
        print("\n[+] Успех! Ты взломал crackme!")
        print("[+] Флаг: FLAG{you_cracked_me_frederik}")
    else:
        print(f"\n[-] Неверно. Твой хеш: {fake_hash[:10]}...")
        print("[-] Попробуй ещё раз.")

if __name__ == "__main__":
    main()