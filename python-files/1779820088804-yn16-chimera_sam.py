# -*- coding: utf-8 -*-

import os
import platform
import random
import re

DEBUG = False


def debug_print(*args, **kwargs):
    if DEBUG:
        print("[DEBUG]", *args, **kwargs)


class StealthKeyCipher:
    def __init__(self):
        self.ru_upper = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
        self.ru_lower = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

        self.en_upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.en_lower = "abcdefghijklmnopqrstuvwxyz"

        self.digits = "0123456789"

        self.special_map = {
            ' ': (30, 0),
            '\n': (99, 0),
            '\t': (99, 1),
            '\r': (99, 2),

            '.': (21, 1),
            ',': (21, 2),
            '!': (21, 3),
            '?': (21, 4),
            '-': (21, 5),

            ':': (22, 0),
            ';': (22, 1),
            '"': (22, 2),
            "'": (22, 3),
            '(': (22, 4),
            ')': (22, 5),

            '[': (23, 0),
            ']': (23, 1),
            '{': (23, 2),
            '}': (23, 3),
            '<': (23, 4),
            '>': (23, 5),

            '`': (24, 0),
            '~': (24, 1),
            '@': (24, 2),
            '#': (24, 3),
            '$': (24, 4),
            '%': (24, 5),

            '^': (25, 0),
            '&': (25, 1),
            '*': (25, 2),
            '=': (25, 3),
            '+': (25, 4),
            '\\': (25, 5),

            '|': (26, 0),
            '/': (26, 1),
            '№': (26, 2)
        }

        self.rev_special = {v: k for k, v in self.special_map.items()}

    def _generate_shuffle(self, seed):
        random.seed(seed)

        ru_shuffled = list(self.ru_upper)
        random.shuffle(ru_shuffled)

        en_shuffled = list(self.en_upper)
        random.shuffle(en_shuffled)

        digits_shuffled = list(self.digits)
        random.shuffle(digits_shuffled)

        return {
            'ru': ''.join(ru_shuffled),
            'en': ''.join(en_shuffled),
            'digits': ''.join(digits_shuffled)
        }

    def _is_russian(self, ch):
        return ch in self.ru_upper or ch in self.ru_lower

    def _is_english(self, ch):
        return ch in self.en_upper or ch in self.en_lower

    def _encode_char(self, ch, shuffle_data):
        is_lower = False
        ch_upper = ch

        if self._is_russian(ch):
            is_lower = ch in self.ru_lower
            ch_upper = ch.upper()

        elif self._is_english(ch):
            is_lower = ch in self.en_lower
            ch_upper = ch.upper()

        if ch_upper in shuffle_data['ru']:
            idx = shuffle_data['ru'].index(ch_upper)

            key = 2 + idx // 4
            pos = 1 + idx % 4

            result = f"{key}{pos}"

            return result + 'l' if is_lower else result

        if ch_upper in shuffle_data['en']:
            idx = shuffle_data['en'].index(ch_upper)

            key = 11 + idx // 4
            pos = 1 + idx % 4

            result = f"{key}{pos}"

            return result + 'l' if is_lower else result

        if ch in self.digits:
            idx = shuffle_data['digits'].index(ch)
            return f"20{idx}"

        if ch in self.special_map:
            key, pos = self.special_map[ch]
            return f"{key}{pos}"

        return f"#{ord(ch):04X}"

    def _decode_char(self, token, shuffle_data):
        if token.startswith("#"):
            try:
                code = int(token[1:], 16)
                return chr(code)
            except:
                return "?"

        is_lower = token.endswith('l')

        if is_lower:
            token = token[:-1]

        if not token or len(token) < 2:
            return "?"

        if not token.isdigit():
            return "?"

        try:
            key = int(token[:-1])
            pos = int(token[-1])
        except:
            return "?"

        if 2 <= key <= 10:
            idx = (key - 2) * 4 + (pos - 1)

            if 0 <= idx < len(shuffle_data['ru']):
                ch = shuffle_data['ru'][idx]
                return ch.lower() if is_lower else ch

        if 11 <= key <= 17:
            idx = (key - 11) * 4 + (pos - 1)

            if 0 <= idx < len(shuffle_data['en']):
                ch = shuffle_data['en'][idx]
                return ch.lower() if is_lower else ch

        if key == 20:
            if 0 <= pos < len(shuffle_data['digits']):
                return shuffle_data['digits'][pos]

        if (key, pos) in self.rev_special:
            return self.rev_special[(key, pos)]

        return "?"

    def _key_to_tokens(self, key, num_tokens):
        tokens = []

        bits_per_token = 12

        for i in range(num_tokens - 1, -1, -1):
            value = (key >> (i * bits_per_token)) & ((1 << bits_per_token) - 1)
            tokens.append(f"{value:04d}")

        return tokens

    def _tokens_to_key(self, tokens):
        key = 0
        bits_per_token = 12

        for token in tokens:
            if token.isdigit() and len(token) == 4:
                value = int(token)

                if 0 <= value <= 4095:
                    key = (key << bits_per_token) | value
                else:
                    return None
            else:
                return None

        return key

    def _insert_key_tokens(self, data_tokens, key_tokens):
        result = list(data_tokens)

        insert_positions = [
            i for i, t in enumerate(data_tokens)
            if t == '300'
        ]

        inserted = 0

        for i, token in enumerate(key_tokens):
            if i < len(insert_positions):
                pos = insert_positions[i] + 1 + inserted
                result.insert(pos, token)
                inserted += 1
            else:
                result.append(token)

        return result

    def _extract_key_tokens(self, all_tokens, K):
        key_tokens = []
        data_tokens = []

        for token in all_tokens:
            if (
                token.isdigit()
                and len(token) == 4
                and 0 <= int(token) <= 4095
            ):
                if len(key_tokens) < K:
                    key_tokens.append(token)
                else:
                    data_tokens.append(token)
            else:
                data_tokens.append(token)

        return key_tokens, data_tokens

    def encrypt(self, text):
        text_len = len(text)

        if text_len < 100:
            K = 8 + (text_len % 5)
        elif text_len < 1000:
            K = 12 + (text_len % 9)
        else:
            K = 16 + (text_len % 9)

        K = min(max(K, 8), 24)

        max_key = (1 << (K * 12)) - 1

        master_key = random.randint(0, max_key)

        shuffle_data = self._generate_shuffle(master_key)

        data_tokens = [
            self._encode_char(ch, shuffle_data)
            for ch in text
        ]

        key_tokens = self._key_to_tokens(master_key, K)

        final_tokens = self._insert_key_tokens(
            data_tokens,
            key_tokens
        )

        marker_token = f"{2400 + K}"

        final_tokens.append(marker_token)

        return ' '.join(final_tokens)

    def decrypt(self, encrypted_text):
        encrypted_text = encrypted_text.strip()

        encrypted_text = re.sub(r'\s+', ' ', encrypted_text)

        tokens = encrypted_text.split()

        if len(tokens) < 2:
            return ""

        marker_index = -1

        for i in range(len(tokens) - 1, -1, -1):
            tok = tokens[i]

            if tok.isdigit() and len(tok) == 4:
                val = int(tok)

                if 2400 <= val <= 2480:
                    marker_index = i
                    break

        if marker_index == -1:
            return ""

        K = int(tokens[marker_index]) - 2400

        all_tokens = tokens[:marker_index]

        key_tokens, data_tokens = self._extract_key_tokens(all_tokens, K)

        if len(key_tokens) < K:
            return ""

        master_key = self._tokens_to_key(key_tokens[:K])

        if master_key is None:
            return ""

        shuffle_data = self._generate_shuffle(master_key)

        result_chars = []

        for token in data_tokens:
            result_chars.append(
                self._decode_char(token, shuffle_data)
            )

        return ''.join(result_chars)


cipher = StealthKeyCipher()


def encrypt_multiline(text: str) -> str:
    lines = text.split('\n')

    encrypted_lines = []

    for line in lines:
        encrypted_lines.append(
            cipher.encrypt(line)
        )

    return '\n|||\n'.join(encrypted_lines)


def decrypt_multiline(code: str) -> str:
    code = code.replace('\r\n', '\n').replace('\r', '\n')

    lines = re.split(
        r'\s*\|\|\|\s*',
        code.strip()
    )

    decrypted_lines = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        decrypted_lines.append(
            cipher.decrypt(line)
        )

    return '\n'.join(decrypted_lines)


def clear_screen():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")


def clear_and_continue():
    input("\nНажмите Enter для продолжения...")
    clear_screen()


def read_multiline_input(prompt: str) -> str:
    print(prompt)
    print("(Для завершения ввода нажмите Enter два раза)")

    lines = []

    empty_count = 0

    while True:
        try:
            line = input()
        except EOFError:
            break

        if line == "":
            empty_count += 1

            if empty_count >= 2:
                break

            lines.append("")
        else:
            empty_count = 0
            lines.append(line)

    return "\n".join(lines)


def read_file_auto(filename):
    encodings = [
        'utf-8',
        'cp1251',
        'koi8-r',
        'cp866',
        'latin-1'
    ]

    for enc in encodings:
        try:
            with open(filename, "r", encoding=enc) as f:
                return f.read()
        except:
            pass

    raise Exception("Не удалось прочитать файл")


def encrypt_file(inp, out):
    try:
        print(f"Чтение файла {inp}...")

        text = read_file_auto(inp)

        print(f"Размер текста: {len(text)} символов")

        print("Шифрование...")

        enc = encrypt_multiline(text)

        print(f"Запись в {out}...")

        with open(out, "w", encoding="utf-8") as f:
            f.write(enc)

        print(f"[OK] Зашифровано -> {out}")

    except Exception as e:
        print(f"[ERR] {e}")


def decrypt_file(inp, out):
    try:
        print(f"Чтение файла {inp}...")

        with open(inp, "r", encoding="utf-8") as f:
            code = f.read()

        print("Расшифровка...")

        text = decrypt_multiline(code)

        print(f"Запись в {out}...")

        with open(out, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"[OK] Расшифровано -> {out}")

    except Exception as e:
        print(f"[ERR] {e}")


def show_file(filename):
    try:
        content = read_file_auto(filename)

        print("\n" + "=" * 60)
        print(content)
        print("=" * 60)

    except Exception as e:
        print("[ERR]", e)


def main():
    clear_screen()
    while True:
        print("\n" + "─" * 50)

        print("ОСНОВНОЕ МЕНЮ")

        print("─" * 50)

        print("1 — Шифровать текст")
        print("2 — Расшифровать текст")
        print("3 — Шифровать файл")
        print("4 — Расшифровать файл")
        print("5 — Показать файл")
        print("0 — Выход")

        print("─" * 50)

        c = input("Выбор: ").strip()

        if c == "1":
            clear_screen()

            print("=== ШИФРОВАНИЕ ТЕКСТА ===\n")

            text = read_multiline_input(
                "Введите текст для шифрования:"
            )

            if text:
                print("\nШифрование...")

                encrypted = encrypt_multiline(text)

                print("\n" + "═" * 60)
                print("ЗАШИФРОВАННЫЙ ТЕКСТ:")
                print("═" * 60)

                print(encrypted)

                print("═" * 60)

            else:
                print("[!] Текст не введён")

            clear_and_continue()

        elif c == "2":
            clear_screen()

            print("=== РАСШИФРОВКА ТЕКСТА ===\n")

            code = read_multiline_input(
                "Введите код для расшифровки:"
            )

            if code:
                print("\nРасшифровка...")

                try:
                    decrypted = decrypt_multiline(code)

                    print("\n" + "═" * 60)
                    print("РАСШИФРОВАННЫЙ ТЕКСТ:")
                    print("═" * 60)

                    print(decrypted)

                    print("═" * 60)

                except Exception as e:
                    print(f"[ERR] {e}")

            else:
                print("[!] Код не введён")

            clear_and_continue()

        elif c == "3":
            clear_screen()

            print("=== ШИФРОВАНИЕ ФАЙЛА ===\n")

            i = input("Входной файл: ").strip()

            if not i:
                print("[!] Имя файла не указано")
                clear_and_continue()
                continue

            o = input("Выходной файл: ").strip()

            if not o:
                o = i + ".encrypted"

            encrypt_file(i, o)

            clear_and_continue()

        elif c == "4":
            clear_screen()

            print("=== РАСШИФРОВКА ФАЙЛА ===\n")

            i = input("Входной файл: ").strip()

            if not i:
                print("[!] Имя файла не указано")
                clear_and_continue()
                continue

            o = input("Выходной файл: ").strip()

            if not o:
                o = i + ".decrypted"

            decrypt_file(i, o)

            clear_and_continue()

        elif c == "5":
            clear_screen()

            print("=== ПРОСМОТР ФАЙЛА ===\n")

            f = input("Имя файла: ").strip()

            if f:
                show_file(f)
            else:
                print("[!] Имя файла не указано")

            clear_and_continue()

        elif c == "0":
            clear_screen()
            break

        else:
            print("[!] Неверный выбор")
            clear_and_continue()


if __name__ == "__main__":
    main()
