import numpy as np

# Константы
ENGLISH_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
KEY = "MTdBRlIxMjIzNTgxM0FGUjE3"
CAESAR_SHIFT = 17

# Шифр Цезаря
def caesar_cipher(text, shift, alphabet=ENGLISH_ALPHABET):
    result = []
    for char in text:
        if char in alphabet:
            idx = alphabet.index(char)
            new_idx = (idx + shift) % len(alphabet)
            result.append(alphabet[new_idx])
        else:
            result.append(char)
    return ''.join(result)

# Атбаш
def atbash_cipher(text, alphabet=ENGLISH_ALPHABET):
    reversed_alphabet = alphabet[::-1]
    result = []
    for char in text:
        if char in alphabet:
            idx = alphabet.index(char)
            result.append(reversed_alphabet[idx])
        else:
            result.append(char)
    return ''.join(result)

# Виженер
def prepare_vigenere_key(key, text_length, alphabet=ENGLISH_ALPHABET):
    key = ''.join([c for c in key if c in alphabet])
    if not key:
        key = alphabet[0]
    repeated_key = (key * (text_length // len(key) + 1))[:text_length]
    return repeated_key

def vigenere_cipher(text, key, alphabet=ENGLISH_ALPHABET, mode='encrypt'):
    if not text:
        return text
    # Учитываем только символы из алфавита
    indices = [i for i, c in enumerate(text) if c in alphabet]
    key_prepared = prepare_vigenere_key(key, len(indices), alphabet)
    result = list(text)
    for i, idx in enumerate(indices):
        char = text[idx]
        text_idx = alphabet.index(char)
        key_idx = alphabet.index(key_prepared[i])
        if mode == 'encrypt':
            new_idx = (text_idx + key_idx) % len(alphabet)
        else:
            new_idx = (text_idx - key_idx) % len(alphabet)
        result[idx] = alphabet[new_idx]
    return ''.join(result)

# Упрощенный Плейфер (замена на символ со сдвигом 5)
def playfair_cipher(text, key, alphabet=ENGLISH_ALPHABET, mode='encrypt'):
    # Упрощенная версия
    result = []
    shift = 5 if mode == 'encrypt' else -5
    for char in text:
        if char in alphabet:
            idx = alphabet.index(char)
            new_idx = (idx + shift) % len(alphabet)
            result.append(alphabet[new_idx])
        else:
            result.append(char)
    return ''.join(result)

# Упрощенный Хилл (2x2)
def hill_cipher(text, alphabet=ENGLISH_ALPHABET, mode='encrypt'):
    # Матрица для шифрования
    K = [[2, 3], [1, 4]]
    # Матрица для дешифрования (обратная матрица по модулю len(alphabet))
    K_inv = [[4, -3], [-1, 2]]
    # Приводим матрицу K_inv к положительным числам по модулю len(alphabet)
    n = len(alphabet)
    for i in range(2):
        for j in range(2):
            K_inv[i][j] = K_inv[i][j] % n

    # Дополняем текст, если длина нечетная
    if len(text) % 2 != 0:
        text += alphabet[0]

    result = []
    for i in range(0, len(text), 2):
        if i+1 < len(text) and text[i] in alphabet and text[i+1] in alphabet:
            x1 = alphabet.index(text[i])
            x2 = alphabet.index(text[i+1])
            if mode == 'encrypt':
                y1 = (K[0][0] * x1 + K[0][1] * x2) % n
                y2 = (K[1][0] * x1 + K[1][1] * x2) % n
            else:
                y1 = (K_inv[0][0] * x1 + K_inv[0][1] * x2) % n
                y2 = (K_inv[1][0] * x1 + K_inv[1][1] * x2) % n
            result.append(alphabet[y1])
            result.append(alphabet[y2])
        else:
            # Если символы не в алфавите, оставляем как есть
            result.append(text[i])
            if i+1 < len(text):
                result.append(text[i+1])
    return ''.join(result)

# Гронсфельд
def gronsfeld_cipher(text, key, alphabet=ENGLISH_ALPHABET, mode='encrypt'):
    # Ключ как последовательность чисел
    key_str = ''.join(str(ord(c) % 10) for c in key)
    if not key_str:
        key_str = '5'
    key_digits = [int(d) for d in key_str]
    result = []
    for i, char in enumerate(text):
        if char in alphabet:
            idx = alphabet.index(char)
            key_digit = key_digits[i % len(key_digits)]
            if mode == 'encrypt':
                new_idx = (idx + key_digit) % len(alphabet)
            else:
                new_idx = (idx - key_digit) % len(alphabet)
            result.append(alphabet[new_idx])
        else:
            result.append(char)
    return ''.join(result)

# Бофора
def beaufort_cipher(text, key, alphabet=ENGLISH_ALPHABET, mode='encrypt'):
    # Бофора: C = (K - P) mod n
    # Для дешифрования та же формула, потому что (K - C) mod n = P
    key_prepared = prepare_vigenere_key(key, len(text), alphabet)
    result = []
    for i, char in enumerate(text):
        if char in alphabet:
            text_idx = alphabet.index(char)
            key_idx = alphabet.index(key_prepared[i])
            new_idx = (key_idx - text_idx) % len(alphabet)
            result.append(alphabet[new_idx])
        else:
            result.append(char)
    return ''.join(result)

# Шифрование для английского текста
def encrypt_english(text):
    # Цепочка для английского
    text = caesar_cipher(text, CAESAR_SHIFT)
    text = atbash_cipher(text)
    text = caesar_cipher(text, CAESAR_SHIFT)
    text = vigenere_cipher(text, KEY, mode='encrypt')
    text = caesar_cipher(text, CAESAR_SHIFT)
    text = playfair_cipher(text, KEY, mode='encrypt')
    text = caesar_cipher(text, CAESAR_SHIFT)
    text = hill_cipher(text, mode='encrypt')
    text = caesar_cipher(text, CAESAR_SHIFT)
    text = gronsfeld_cipher(text, KEY, mode='encrypt')
    text = caesar_cipher(text, CAESAR_SHIFT)
    text = beaufort_cipher(text, KEY, mode='encrypt')
    text = caesar_cipher(text, CAESAR_SHIFT)
    return text

# Дешифрование для английского текста
def decrypt_english(text):
    # Обратная цепочка
    text = caesar_cipher(text, -CAESAR_SHIFT)
    text = beaufort_cipher(text, KEY, mode='decrypt')  # для Бофора шифрование и дешифрование одинаковы
    text = caesar_cipher(text, -CAESAR_SHIFT)
    text = gronsfeld_cipher(text, KEY, mode='decrypt')
    text = caesar_cipher(text, -CAESAR_SHIFT)
    text = hill_cipher(text, mode='decrypt')
    text = caesar_cipher(text, -CAESAR_SHIFT)
    text = playfair_cipher(text, KEY, mode='decrypt')
    text = caesar_cipher(text, -CAESAR_SHIFT)
    text = vigenere_cipher(text, KEY, mode='decrypt')
    text = caesar_cipher(text, -CAESAR_SHIFT)
    text = atbash_cipher(text)  # Атбаш обратен сам себе
    text = caesar_cipher(text, -CAESAR_SHIFT)
    return text

# Основная функция
def main():
    print("=== ШИФРАТОР/ДЕШИФРАТОР (только английские символы) ===")
    print("Остальные символы остаются без изменений.")
    while True:
        print("\nВыберите действие:")
        print("1. Зашифровать текст")
        print("2. Расшифровать текст")
        print("3. Выход")
        choice = input("Ваш выбор: ").strip()
        if choice == '1':
            text = input("Введите текст для шифрования: ")
            encrypted = encrypt_english(text)
            print(f"Зашифрованный текст: {encrypted}")
        elif choice == '2':
            text = input("Введите текст для дешифрования: ")
            decrypted = decrypt_english(text)
            print(f"Расшифрованный текст: {decrypted}")
        elif choice == '3':
            break
        else:
            print("Неверный выбор.")

if __name__ == "__main__":
    main()