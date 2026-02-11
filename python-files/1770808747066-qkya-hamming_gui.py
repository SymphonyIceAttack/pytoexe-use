import tkinter as tk
from tkinter import ttk, messagebox

# ---------- ЛОГИКА ----------

def calculate_m(k):
    m = 0
    while (2 ** m) < (k + m + 1):
        m += 1
    return m


def encode():
    global encoded_code, m, k

    data = entry_input.get()

    if not data or not all(c in "01" for c in data) or len(data) > 20:
        messagebox.showerror("Ошибка", "Введите двоичную последовательность (до 20 бит)")
        return

    k = len(data)
    m = calculate_m(k)
    n = k + m

    entry_k.delete(0, tk.END)
    entry_k.insert(0, str(k))

    entry_m.delete(0, tk.END)
    entry_m.insert(0, str(m))

    entry_n.delete(0, tk.END)
    entry_n.insert(0, str(n + 1))

    code = ["0"] * (n + 1)
    j = 0

    for i in range(1, n + 1):
        if (i & (i - 1)) != 0:
            code[i] = data[j]
            j += 1

    parity_list = []

    for i in range(m):
        pos = 2 ** i
        parity = 0
        for j in range(1, n + 1):
            if j & pos:
                parity ^= int(code[j])
        code[pos] = str(parity)
        parity_list.append(f"a{pos} = {parity}")

    overall = 0
    for i in range(1, n + 1):
        overall ^= int(code[i])

    code[0] = str(overall)
    parity_list.insert(0, f"a0 = {overall}")

    encoded_code = "".join(code)

    entry_encoded.delete(0, tk.END)
    entry_encoded.insert(0, encoded_code)

    combo_a["values"] = parity_list
    combo_a.set("")


def decode():
    received = entry_received.get()

    if not received or not all(c in "01" for c in received):
        messagebox.showerror("Ошибка", "Введите корректную кодовую комбинацию")
        return

    code = list(received)
    n = len(code) - 1

    syndrome = 0
    check_list = []

    for i in range(m):
        pos = 2 ** i
        parity = 0
        for j in range(1, n + 1):
            if j & pos:
                parity ^= int(code[j])
        check_list.append(f"E{pos} = {parity}")
        if parity != 0:
            syndrome += pos

    overall = 0
    for c in code:
        overall ^= int(c)

    check_list.insert(0, f"E0 = {overall}")

    combo_e["values"] = check_list
    combo_e.set("")

    entry_syndrome.delete(0, tk.END)
    entry_syndrome.insert(0, bin(syndrome)[2:])

    entry_r.delete(0, tk.END)
    entry_N.delete(0, tk.END)

    if syndrome == 0 and overall == 0:
        entry_r.insert(0, "0")
    elif syndrome != 0 and overall == 1:
        entry_r.insert(0, "1")
        entry_N.insert(0, str(syndrome))
        code[syndrome] = "1" if code[syndrome] == "0" else "0"
    elif syndrome != 0 and overall == 0:
        entry_r.insert(0, "2")
        entry_result.delete(0, tk.END)
        entry_result.insert(0, "Повторная передача")
        return
    else:
        entry_r.insert(0, "3+")

    result = ""
    for i in range(1, len(code)):
        if (i & (i - 1)) != 0:
            result += code[i]

    entry_result.delete(0, tk.END)
    entry_result.insert(0, result)


# ---------- ИНТЕРФЕЙС ----------

root = tk.Tk()
root.title("Расширенный код Хэмминга")
root.geometry("820x520")
root.resizable(False, False)

# Заголовок
tk.Label(root, text="Расширенный код Хэмминга", font=("Arial", 12, "bold")).place(x=20, y=10)

# Информационная последовательность
tk.Label(root, text="Информационная последовательность").place(x=50, y=60)
entry_input = tk.Entry(root, width=40)
entry_input.place(x=50, y=85)

btn_input = tk.Button(root, text="ВВОД", width=15, command=encode)
btn_input.place(x=600, y=80)

# k m n
tk.Label(root, text="k").place(x=60, y=130)
entry_k = tk.Entry(root, width=8)
entry_k.place(x=40, y=155)

tk.Label(root, text="m").place(x=180, y=130)
entry_m = tk.Entry(root, width=8)
entry_m.place(x=160, y=155)

tk.Label(root, text="n").place(x=300, y=130)
entry_n = tk.Entry(root, width=8)
entry_n.place(x=280, y=155)

# Кодировать
btn_encode = tk.Button(root, text="КОДИРОВАТЬ", width=15, command=encode)
btn_encode.place(x=600, y=140)

# Кодовая комбинация
tk.Label(root, text="Кодовая комбинация").place(x=50, y=200)
entry_encoded = tk.Entry(root, width=40)
entry_encoded.place(x=50, y=225)

combo_a = ttk.Combobox(root, width=20)
combo_a.place(x=600, y=225)

# Принятая комбинация
tk.Label(root, text="Принятая кодовая комбинация").place(x=50, y=260)
entry_received = tk.Entry(root, width=40)
entry_received.place(x=50, y=285)

btn_decode = tk.Button(root, text="ДЕКОДИРОВАТЬ", width=15, command=decode)
btn_decode.place(x=600, y=280)

# Контрольное число
tk.Label(root, text="Контрольное число").place(x=50, y=330)
entry_syndrome = tk.Entry(root, width=10)
entry_syndrome.place(x=50, y=355)

tk.Label(root, text="r").place(x=180, y=330)
entry_r = tk.Entry(root, width=10)
entry_r.place(x=160, y=355)

tk.Label(root, text="N").place(x=300, y=330)
entry_N = tk.Entry(root, width=10)
entry_N.place(x=280, y=355)

combo_e = ttk.Combobox(root, width=20)
combo_e.place(x=600, y=355)

# Результат
tk.Label(root, text="Результат").place(x=50, y=400)
entry_result = tk.Entry(root, width=40)
entry_result.place(x=50, y=425)

btn_exit = tk.Button(root, text="ВЫХОД", width=15, command=root.destroy)
btn_exit.place(x=600, y=420)

root.mainloop()
