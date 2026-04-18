BINARY_MAP = {
    "SSSS": "0",
    "SSSL": "1",
    "SSLS": "2",
    "SSLL": "3",
    "SLSS": "4",
    "SLSL": "5",
    "SLLS": "6",
    "SLLL": "7",
    "LSSS": "8",
    "LSSL": "9",
}

MORSE_MAP = {
    "LLLLL": "0",
    "SLLLL": "1",
    "SSLLL": "2",
    "SSSLL": "3",
    "SSSSL": "4",
    "SSSSS": "5",
    "LSSSS": "6",
    "LLSSS": "7",
    "LLLSS": "8",
    "LLLLS": "9",
}


def clean_input(raw):
    allowed = "-.| "
    result = ""
    for ch in raw:
        if ch in allowed:
            result += ch
    return result.strip()


def build_candidates(raw):
    cleaned = clean_input(raw)
    compact = ""

    for ch in cleaned:
        if ch in "-.":
            compact += ch

    if compact == "":
        return []

    candidates = []

    direct_seq = compact.replace("-", "S").replace(".", "L")
    candidates.append(("direct", direct_seq))

    seq = ""
    i = 0
    ok = True

    while i < len(compact):
        ch = compact[i]
        j = i

        while j < len(compact) and compact[j] == ch:
            j += 1

        run_len = j - i

        if ch == "-":
            seq += "S" * run_len
        else:
            if run_len % 3 != 0:
                ok = False
                break
            seq += "L" * (run_len // 3)

        i = j

    if ok:
        candidates.append(("cell", seq))

    return candidates


def decode_groups(seq, group_size, mapping):
    if len(seq) % group_size != 0:
        return None

    groups = []
    i = 0

    while i < len(seq):
        group = seq[i:i + group_size]
        if group not in mapping:
            return None
        groups.append(group)
        i += group_size

    code = ""
    for group in groups:
        code += mapping[group]

    return code


def detect_and_decode(raw):
    candidates = build_candidates(raw)
    results = []

    for input_mode, seq in candidates:
        binary_code = decode_groups(seq, 4, BINARY_MAP)
        if binary_code is not None:
            score = 0
            if len(binary_code) == 3:
                score += 10
            if input_mode == "cell":
                score += 5
            score += 1
            results.append(("Binary Numeric", binary_code, score))

        morse_code = decode_groups(seq, 5, MORSE_MAP)
        if morse_code is not None:
            score = 0
            if len(morse_code) == 3:
                score += 10
            if input_mode == "cell":
                score += 5
            results.append(("Morse Numeric", morse_code, score))

    if len(results) == 0:
        return None

    best = results[0]
    for item in results[1:]:
        if item[2] > best[2]:
            best = item

    return best


def main():
    while True:
        raw = input("Введите сигнал: ").strip()

        if raw.lower() in ["q", "quit", "exit"]:
            break

        result = detect_and_decode(raw)

        if result is None:
            print("Тип: Не определён")
            print("Код: Ошибка")
        else:
            print("Тип: " + result[0])
            print("Код: " + result[1])


main()