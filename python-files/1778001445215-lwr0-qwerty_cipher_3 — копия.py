"""
Шифр на основе русской QWERTY-клавиатуры.
Шифрование — сдвиг на одну клавишу вправо по строке.
Дешифрование — сдвиг влево.

Правила:
  - х, ъ, э, ё, ь, ю — без изменений (конец строки или особые буквы).
  - б → ю при шифровании (б стоит перед ю, это допустимо).
  - ю → б при дешифровании НЕ происходит (ю всегда остаётся собой).
  - пробел, ! и ? — без изменений.
"""

ROWS = [
    "йцукенгшщзх",   # х — конец, без изменений; ъ отдельно
    "фывапролджэ",   # э — конец, без изменений
    "яченсмитбю",    # ь убрана из строки (обрабатывается как SKIP)
                     # б→ю разрешено; ю — конец, без изменений как источник
]

# Буквы, которые НИКОГДА не являются источником замены
# (остаются собой при шифровании и дешифровании)
SKIP_SOURCE = set("хъэьюёЁ !?")


def _build_maps():
    """Строим словари замен для шифрования и дешифрования."""
    enc_map = {}
    dec_map = {}
    for row in ROWS:
        for i, ch in enumerate(row):
            if ch in SKIP_SOURCE:
                continue  # эта буква не шифруется

            next_ch = row[i + 1] if i + 1 < len(row) else None
            prev_ch = row[i - 1] if i > 0 else None

            # шифрование: сдвиг вправо
            # next_ch может быть ю — это разрешено (б→ю)
            if next_ch is not None:
                enc_map[ch] = next_ch
                enc_map[ch.upper()] = next_ch.upper()

            # дешифрование: сдвиг влево
            # но если prev_ch в SKIP_SOURCE — назад не идём
            if prev_ch is not None and prev_ch not in SKIP_SOURCE:
                dec_map[ch] = prev_ch
                dec_map[ch.upper()] = prev_ch.upper()

    return enc_map, dec_map


ENC_MAP, DEC_MAP = _build_maps()


def encrypt(text: str) -> str:
    return "".join(ENC_MAP.get(ch, ch) for ch in text)


def decrypt(text: str) -> str:
    return "".join(DEC_MAP.get(ch, ch) for ch in text)


def show_map():
    """Вывести таблицу замен."""
    print("Таблица замен (шифрование):")
    print(f"  {'Оригинал':<12} {'Зашифровано'}")
    print("  " + "-" * 24)
    shown = set()
    for row in ROWS:
        parts = []
        for ch in row:
            enc = ENC_MAP.get(ch, ch)
            if ch not in shown:
                parts.append(f"{ch}→{enc}")
                shown.add(ch)
        print("  " + "  ".join(parts))
    print()


def main():
    show_map()
    print("=" * 40)

    while True:
        print("\nВыберите действие:")
        print("  1 — Зашифровать")
        print("  2 — Расшифровать")
        print("  0 — Выход")

        choice = input("> ").strip()

        if choice == "0":
            break
        elif choice == "1":
            text = input("Текст: ")
            print(f"Результат: {encrypt(text)}")
        elif choice == "2":
            text = input("Текст: ")
            print(f"Результат: {decrypt(text)}")
        else:
            print("Неверный выбор.")


if __name__ == "__main__":
    samples = [
        "привет",
        "Как дела?",
        "Это тест!",
    ]
    for s in samples:
        enc = encrypt(s)
        dec = decrypt(enc)
        print(f"  {s:<15} → {enc:<15} → {dec}")
    print()
    main()
