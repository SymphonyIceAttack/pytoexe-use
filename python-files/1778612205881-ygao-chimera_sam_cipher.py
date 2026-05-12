# -*- coding: utf-8 -*-

import os
import platform

# =========================
# БАЗОВАЯ ТАБЛИЦА (БЕЗ КОЛЛИЗИЙ)
# =========================
encrypt_table = {}

# Кириллица (ключи 2..10)
ru = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
for i, ch in enumerate(ru):
    encrypt_table[ch] = (2 + i // 4, 1 + i % 4)

# Латиница (ключи 11..17)
en = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
for i, ch in enumerate(en):
    encrypt_table[ch] = (11 + i // 4, 1 + i % 4)

# Цифры (ключ 20)
digits = "0123456789"
for i, ch in enumerate(digits):
    encrypt_table[ch] = (20, i)

# Частые символы (ключ 21..29, чтобы избежать 300-309)
# Распределим символы по ключам, не более 10 на ключ
extra_groups = [
    (" .,!?-", 21),      # пробел, точка, запятая, воскл., вопрос, дефис
    (":;\"'()", 22),     # двоеточие, точка с запятой, кавычки, скобки
    ("[]{}<>", 23),      # квадратные, фигурные, угловые скобки
    ("_=+*/\\", 24),     # подчёркивание, равно, плюс, звёздочка, слеш, обратный слеш
    ("|&%#@$^~`", 25)    # другие символы
]

for chars, key in extra_groups:
    for i, ch in enumerate(chars):
        encrypt_table[ch] = (key, i)

# Отдельно пробел (ключ 30), чтобы не путать с 21,0 (пробел там же, но переопределим)
encrypt_table[' '] = (30, 0)

# Перевод строки
encrypt_table['\n'] = (99, 0)

# Обратная таблица
decrypt_table = {v: k for k, v in encrypt_table.items()}

# =========================
# ОЧИСТКА ЭКРАНА
# =========================
def clear_screen():
    """Очищает экран терминала в зависимости от ОС"""
    current_os = platform.system()
    if current_os == "Windows":
        os.system("cls")
    else:  # Linux, macOS, Unix
        os.system("clear")

def clear_and_continue():
    """Очищает экран и ждёт нажатия Enter"""
    input("\nНажмите Enter для продолжения...")
    clear_screen()

# =========================
# ШИФРОВАНИЕ
# =========================
def encode_char(ch):
    ch_upper = ch.upper()

    if ch_upper in encrypt_table:
        key, pos = encrypt_table[ch_upper]
        if ch.islower():
            return f"{key}{pos}l"
        return f"{key}{pos}"

    # fallback — unicode
    return f"#{ord(ch):04X}"

def encrypt(text: str) -> str:
    # Каждый символ превращается в токен, токены разделяются пробелом
    return " ".join(encode_char(c) for c in text)

# =========================
# ДЕШИФРОВКА
# =========================
def decode_token(token):
    # Unicode fallback
    if token.startswith("#"):
        try:
            return chr(int(token[1:], 16))
        except:
            return "?"

    # lowercase маркер
    is_lower = token.endswith("l")
    if is_lower:
        token = token[:-1]

    # Должно быть число
    if not token.isdigit():
        return "?"

    # Ключ = все цифры кроме последней, позиция = последняя цифра
    # Поддержка как 2-значных, так и 3-значных (например, 302 -> ключ=30, позиция=2)
    if len(token) < 2:
        return "?"

    key = int(token[:-1])
    pos = int(token[-1])

    if (key, pos) in decrypt_table:
        ch = decrypt_table[(key, pos)]
        return ch.lower() if is_lower else ch

    return "?"

def decrypt(code: str) -> str:
    tokens = code.split()
    result = []

    for token in tokens:
        decoded = decode_token(token)
        result.append(decoded)

    text = "".join(result)

    # Небольшая чистка: убираем лишние пробелы, но оставляем знаки препинания
    import re
    text = re.sub(r' +', ' ', text)
    text = re.sub(r' ([.,!?;:])', r'\1', text)

    return text.strip()

# =========================
# МНОГОСТРОЧНЫЙ РЕЖИМ
# =========================
def encrypt_multiline(text: str) -> str:
    # Каждая строка шифруется отдельно, строки разделяются " | "
    return " | ".join(encrypt(line) for line in text.split("\n"))

def decrypt_multiline(code: str) -> str:
    lines = code.split(" | ")
    return "\n".join(decrypt(line) for line in lines)

# =========================
# ФУНКЦИИ ДЛЯ МНОГОСТРОЧНОГО ВВОДА
# =========================
def read_multiline_input(prompt: str) -> str:
    """Читает многострочный текст до пустой строки"""
    print(prompt)
    print("(Для завершения ввода введите пустую строку)")
    lines = []
    while True:
        line = input()
        if line == "" and not lines:
            # Если первая строка пустая - возможно, пользователь просто нажал Enter
            continue
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)

def read_singleline_input(prompt: str) -> str:
    """Читает однострочный текст"""
    return input(prompt)

# =========================
# РАБОТА С ФАЙЛАМИ
# =========================
def read_file_auto(filename):
    encodings = ['utf-8', 'cp1251', 'koi8-r', 'cp866']
    for enc in encodings:
        try:
            with open(filename, "r", encoding=enc) as f:
                print(f"[OK] Прочитано в {enc}")
                return f.read()
        except:
            continue
    raise Exception("Не удалось прочитать файл")

def encrypt_file(inp, out):
    try:
        text = read_file_auto(inp)
        enc = encrypt_multiline(text)
        with open(out, "w", encoding="utf-8") as f:
            f.write(enc)
        print(f"[OK] Зашифровано → {out}")
    except Exception as e:
        print("[ERR]", e)

def decrypt_file(inp, out):
    try:
        with open(inp, "r", encoding="utf-8") as f:
            code = f.read()
        text = decrypt_multiline(code)
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[OK] Расшифровано → {out}")
    except Exception as e:
        print("[ERR]", e)

def show_file(filename):
    try:
        print(read_file_auto(filename))
    except Exception as e:
        print("[ERR]", e)

# =========================
# МЕНЮ
# =========================
def main():
    clear_screen()  # очистка при запуске
    
    while True:
        print("\n=== МЕНЮ ===")
        print("1 — Шифровать текст (многострочный)")
        print("2 — Расшифровать текст (многострочный)")
        print("3 — Шифровать файл")
        print("4 — Расшифровать файл")
        print("5 — Показать файл")
        print("0 — Выход")

        c = input("Выбор: ").strip()

        if c == "1":
            clear_screen()
            text = read_multiline_input("Введите текст для шифрования:")
            if text:
                print("\n=== ЗАШИФРОВАННЫЙ ТЕКСТ ===")
                print(encrypt_multiline(text))
                clear_and_continue()
            else:
                print("[!] Текст не введён")
                clear_and_continue()
        elif c == "2":
            clear_screen()
            code = read_multiline_input("Введите код для расшифровки:")
            if code:
                print("\n=== РАСШИФРОВАННЫЙ ТЕКСТ ===")
                print(decrypt_multiline(code))
                clear_and_continue()
            else:
                print("[!] Код не введён")
                clear_and_continue()
        elif c == "3":
            clear_screen()
            i = input("Входной файл: ")
            o = input("Выходной файл: ")
            encrypt_file(i, o)
            clear_and_continue()
        elif c == "4":
            clear_screen()
            i = input("Входной файл: ")
            o = input("Выходной файл: ")
            decrypt_file(i, o)
            clear_and_continue()
        elif c == "5":
            clear_screen()
            f = input("Имя файла: ")
            show_file(f)
            clear_and_continue()
        elif c == "0":
            clear_screen()
            print("До свидания!")
            break
        else:
            print("[!] Неверный выбор, попробуйте снова")
            clear_and_continue()

if __name__ == "__main__":
    main()