import tkinter as tk
from tkinter import messagebox

def hamming_encode(data):
    k = len(data)
    m = 1
    while (2**m - 1) < (k + m):
        m += 1
    n = k + m + 1  # +1 для a0

    # Позиции степеней двойки
    parity_positions = [2**i for i in range(m)]

    # Вставка информационных бит в кодовое слово
    code = []
    data_idx = 0
    for i in range(1, n):
        if i in parity_positions:
            code.append(0)  # временно
        else:
            code.append(int(data[data_idx]))
            data_idx += 1

    # Вычисление проверочных бит
    for p in parity_positions:
        xor_sum = 0
        for i in range(1, n):
            if i & p:
                xor_sum ^= code[i - 1]
        code[p - 1] = xor_sum

    # Вычисление a0 (общая четность всех бит)
    total_xor = 0
    for bit in code:
        total_xor ^= bit
    code.insert(0, total_xor)  # a0 на позицию 0

    return code, k, m, n, parity_positions

def hamming_decode(received, k, m, parity_positions):
    n = len(received)
    a0 = received[0]
    bits = received[1:]

    # Вычисление синдрома
    syndrome = 0
    for p in parity_positions:
        xor_sum = 0
        for i in range(1, n):
            if i & p:
                xor_sum ^= received[i]
        syndrome |= (xor_sum << (p.bit_length() - 1))

    # Вычисление E0
    total_xor = 0
    for bit in received:
        total_xor ^= bit
    E0 = total_xor

    # Определение кратности ошибки
    if syndrome == 0 and E0 == 0:
        r = 0
        error_pos = None
    elif syndrome != 0 and E0 == 1:
        r = 1
        error_pos = syndrome
    elif syndrome != 0 and E0 == 0:
        r = 2
        error_pos = None
    else:
        r = 3  # нечетная, >=3
        error_pos = None

    # Исправление однократной ошибки
    corrected = received[:]
    if r == 1 and error_pos is not None:
        corrected[error_pos] ^= 1

    # Извлечение информационных бит
    info_bits = []
    for i in range(1, len(corrected)):
        if i not in parity_positions:
            info_bits.append(str(corrected[i]))
    info_str = ''.join(info_bits)

    return syndrome, E0, r, error_pos, corrected, info_str

def on_encode():
    data = entry_info.get().strip()
    if not data or not all(c in '01' for c in data):
        messagebox.showerror("Ошибка", "Введите двоичную последовательность (0 и 1)")
        return
    if len(data) > 20:
        messagebox.showerror("Ошибка", "Длина не более 20 бит")
        return

    code, k, m, n, parity_positions = hamming_encode(data)

    label_k_var.set(k)
    label_m_var.set(m)
    label_n_var.set(n)

    list_a.delete(0, tk.END)
    list_a.insert(0, f"a0 = {code[0]}")
    for i, p in enumerate(parity_positions):
        list_a.insert(i + 1, f"a{p} = {code[p]}")

    code_str = ''.join(map(str, code))
    entry_code.delete(0, tk.END)
    entry_code.insert(0, code_str)

    # По умолчанию принятая комбинация = переданной
    entry_received.delete(0, tk.END)
    entry_received.insert(0, code_str)

    # Сохраняем для декодирования
    global last_code, last_k, last_m, last_parity_positions
    last_code = code
    last_k = k
    last_m = m
    last_parity_positions = parity_positions

def on_decode():
    received_str = entry_received.get().strip()
    if not received_str or not all(c in '01' for c in received_str):
        messagebox.showerror("Ошибка", "Введите двоичную последовательность")
        return

    received = list(map(int, received_str))
    syndrome, E0, r, error_pos, corrected, info_str = hamming_decode(
        received, last_k, last_m, last_parity_positions
    )

    # Отображение проверок E
    list_e.delete(0, tk.END)
    list_e.insert(0, f"E0 = {E0}")
    for i in range(last_m):
        shift = last_m - i - 1
        bit = (syndrome >> shift) & 1
        list_e.insert(i + 1, f"E{i + 1} = {bit}")

    # Контрольное число S
    entry_syndrome.delete(0, tk.END)
    entry_syndrome.insert(0, f"{syndrome:0{last_m}b}")

    # Кратность ошибки
    label_r_var.set(r)

    # Номер искаженного символа
    entry_n.delete(0, tk.END)
    if r == 1 and error_pos is not None:
        entry_n.insert(0, str(error_pos))

    # Результат
    entry_result.delete(0, tk.END)
    if r == 2:
        entry_result.insert(0, "Повторная передача")
    else:
        entry_result.insert(0, info_str)

# Интерфейс
root = tk.Tk()
root.title("Расширенный код Хэмминга")
root.geometry("800x700")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack(fill=tk.BOTH, expand=True)

tk.Label(frame, text="Информационная последовательность:").grid(row=0, column=0, sticky='w')
entry_info = tk.Entry(frame, width=30)
entry_info.grid(row=0, column=1)

tk.Button(frame, text="Ввод", command=on_encode).grid(row=0, column=2)

tk.Label(frame, text="k (информационные)").grid(row=1, column=0, sticky='w')
label_k_var = tk.StringVar()
tk.Label(frame, textvariable=label_k_var, relief='sunken', width=10).grid(row=1, column=1, sticky='w')

tk.Label(frame, text="m (проверочные)").grid(row=2, column=0, sticky='w')
label_m_var = tk.StringVar()
tk.Label(frame, textvariable=label_m_var, relief='sunken', width=10).grid(row=2, column=1, sticky='w')

tk.Label(frame, text="n (общее)").grid(row=3, column=0, sticky='w')
label_n_var = tk.StringVar()
tk.Label(frame, textvariable=label_n_var, relief='sunken', width=10).grid(row=3, column=1, sticky='w')

tk.Button(frame, text="Кодировать", command=on_encode).grid(row=4, column=0, pady=5)

tk.Label(frame, text="а:").grid(row=5, column=0, sticky='nw')
list_a = tk.Listbox(frame, height=6, width=20)
list_a.grid(row=5, column=1, sticky='w')

tk.Label(frame, text="Кодовая комбинация:").grid(row=6, column=0, sticky='w')
entry_code = tk.Entry(frame, width=40)
entry_code.grid(row=6, column=1, columnspan=2, sticky='w')

tk.Label(frame, text="Принятая кодовая комбинация:").grid(row=7, column=0, sticky='w')
entry_received = tk.Entry(frame, width=40)
entry_received.grid(row=7, column=1, columnspan=2, sticky='w')

tk.Button(frame, text="Декодировать", command=on_decode).grid(row=8, column=0, pady=5)

tk.Label(frame, text="Е:").grid(row=9, column=0, sticky='nw')
list_e = tk.Listbox(frame, height=6, width=20)
list_e.grid(row=9, column=1, sticky='w')

tk.Label(frame, text="Контрольное число:").grid(row=10, column=0, sticky='w')
entry_syndrome = tk.Entry(frame, width=20)
entry_syndrome.grid(row=10, column=1, sticky='w')

tk.Label(frame, text="r (кратность ошибки):").grid(row=11, column=0, sticky='w')
label_r_var = tk.StringVar()
tk.Label(frame, textvariable=label_r_var, relief='sunken', width=10).grid(row=11, column=1, sticky='w')

tk.Label(frame, text="N (номер искаж. символа):").grid(row=12, column=0, sticky='w')
entry_n = tk.Entry(frame, width=10)
entry_n.grid(row=12, column=1, sticky='w')

tk.Label(frame, text="Результат:").grid(row=13, column=0, sticky='w')
entry_result = tk.Entry(frame, width=40)
entry_result.grid(row=13, column=1, columnspan=2, sticky='w')

root.mainloop()