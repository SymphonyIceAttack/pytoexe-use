import argparse
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import getpass 

# --- КОНСТАНТЫ ---
ITERATIONS = 480000
KEY_LENGTH = 32

# --- ФУНКЦИИДЕШИФРОВАНИЯ ---

def generate_key(password: bytes, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=KEY_LENGTH, salt=salt, iterations=ITERATIONS, backend=default_backend())
    return kdf.derive(password)

def encrypt_data(data: bytes, key: bytes, salt: bytes) -> tuple:
    iv = os.urandom(12) 
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()
    tag = encryptor.tag
    return iv, tag, ciphertext

def decrypt_data(iv: bytes, tag: bytes, ciphertext: bytes, key: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()

# --- ИНТЕРАКТИВНЫЕ ФУНКЦИИ ---

def handle_decryption():
    print("\n--- РЕЖИМ ДЕШИФРОВАНИЯ: Mozhaev ENIGMA 4/44 ---")
    
    password = getpass.getpass("Введите СЕКРЕТНЫЙ ПАРОЛЬ: ")
    
    salt_hex = input("Введите SALT (HEX): ")
    iv_hex = input("Введите IV (HEX): ")
    tag_hex = input("Введите TAG (HEX): ")
    ciphertext_hex = input("Введите CIPHERTEXT (HEX): ")
    
    try:
        salt = bytes.fromhex(salt_hex)
        iv = bytes.fromhex(iv_hex)
        tag = bytes.fromhex(tag_hex)
        ciphertext = bytes.fromhex(ciphertext_hex)
        
        password_bytes = password.encode('utf-8')
        key = generate_key(password_bytes, salt)
        
        decrypted_bytes = decrypt_data(iv, tag, ciphertext, key)
        
        print("\n[УСПЕХ] Дешифрование прошло успешно!")
        print("ДЕШИФРОВАННЫЙ ТЕКСТ:")
        print(decrypted_bytes.decode('utf-8'))
        
    except ValueError:
        print("\n[ОШИБКА]: Ошибка формата HEX. Проверьте, что все введенные данные являются валидными шестнадцатеричными строками.")
    except Exception:
        print("\n[ОШИБКА ДЕШИФРОВАНИЯ]: Пароль, Соль или другие компоненты неверны. Данные либо повреждены, либо ключ не подходит.")


def main_menu():
    print("\n=====================================================")
    print("                 MOZHAEV ENIGMA 4/44                  ")
    print("=====================================================")
    
    while True:
        print("\nВыберите действие:")
        print("  2. Расшифровать (Decryption)")
        print("  3. Выход")
        
        choice = input("Введите номер (1, 2 или 3): ").strip()
        
        if choice == '1':
            handle_encryption()
        elif choice == '2':
            handle_decryption()
        elif choice == '3':
            print("Mozhaev ENIGMA 4/44: Программа завершена.")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    from cryptography.hazmat.backends import default_backend
    main_menu()