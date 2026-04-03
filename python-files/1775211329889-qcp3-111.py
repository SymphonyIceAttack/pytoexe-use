import struct
import tkinter as tk
from tkinter import ttk, filedialog
import math
import re

# ---------- PARSE ----------

def parse_hex(hex_str):
    hex_str = hex_str.lower().replace("0x","")
    for ch in [" ", "-", ","]:
        hex_str = hex_str.replace(ch, "")
    return bytes.fromhex(hex_str)

def extract_hex_from_line(line):
    return re.findall(r'[0-9A-Fa-f]{2}', line)

# ---------- CONVERT ----------

def reorder(data, order):
    return bytes([data[i] for i in order])

def to_float32(b):
    try: return struct.unpack('>f', b)[0]
    except: return None

def to_float64(b):
    try: return struct.unpack('>d', b + b)[0]
    except: return None

def to_int32(b):
    return int.from_bytes(b, "big", signed=True)

def to_int16_pairs(b):
    return [
        int.from_bytes(b[0:2], "big", signed=True),
        int.from_bytes(b[2:4], "big", signed=True)
    ]

# ---------- VALID ----------

def is_valid_float(v):
    if v is None: return False
    if math.isnan(v) or math.isinf(v): return False
    if abs(v) < 1e-20 or abs(v) > 1e10: return False
    return True

# ---------- CORE ----------

def process_block(data):
    variants = {
        "ABCD": [0,1,2,3],
        "DCBA": [3,2,1,0],
        "BADC": [1,0,3,2],
        "CDAB": [2,3,0,1],
    }

    results = []

    for name, order in variants.items():
        b = reorder(data, order)

        f32 = to_float32(b)
        f64 = to_float64(b)

        score = 0
        if is_valid_float(f32): score += 2
        if is_valid_float(f64): score += 1

        results.append({
            "values": (
                name,
                b.hex(" ").upper(),
                f"{f32:.6g}" if f32 is not None else "err",
                f"{f64:.6g}" if f64 is not None else "err",
                str(to_int32(b)),
                str(to_int16_pairs(b))
            ),
            "valid": score > 0,
            "score": score
        })

    best = max(results, key=lambda x: x["score"])
    return results, best

# ---------- MODBUS ----------

def parse_modbus(data):
    if len(data) < 5:
        return None

    # TCP
    if len(data) > 7 and data[2] == 0 and data[3] == 0:
        byte_count = data[8]
        return data[9:9+byte_count]

    # RTU
    byte_count = data[2]
    return data[3:3+byte_count]

# ---------- GUI ----------

def fill_table(data_bytes, prefix="Блок"):
    for i in range(0, len(data_bytes)-3, 4):
        block = data_bytes[i:i+4]

        tree.insert("", "end",
                    values=(prefix, block.hex(" ").upper(), "", "", "", ""),
                    tags=("block",))

        results, best = process_block(block)

        for r in results:
            if only_valid.get() and not r["valid"]:
                continue

            tag = "good" if r["valid"] else "bad"
            if r == best:
                tag = "best"

            tree.insert("", "end", values=r["values"], tags=(tag,))

# ---------- ACTIONS ----------

def convert():
    tree.delete(*tree.get_children())
    try:
        data = parse_hex(entry.get())
        fill_table(data)
        status.set("HEX OK")
    except Exception as e:
        status.set(f"Ошибка: {e}")

def convert_modbus():
    tree.delete(*tree.get_children())
    try:
        raw = parse_hex(modbus_entry.get())
        payload = parse_modbus(raw)
        if payload:
            fill_table(payload, "MB")
            status.set("Modbus OK")
        else:
            status.set("Не удалось распарсить")
    except Exception as e:
        status.set(f"Ошибка: {e}")

def load_log():
    path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if not path:
        return

    tree.delete(*tree.get_children())

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            hex_bytes = extract_hex_from_line(line)
            if len(hex_bytes) < 5:
                continue

            try:
                data = bytes.fromhex("".join(hex_bytes))
                payload = parse_modbus(data)
                if payload:
                    fill_table(payload, "LOG")
            except:
                continue

    status.set("Лог обработан")

def clear():
    tree.delete(*tree.get_children())
    entry.delete(0, tk.END)          # очистка HEX поля
    modbus_entry.delete(0, tk.END)   # очистка Modbus поля
    status.set("Очищено")

def copy():
    sel = tree.focus()
    if sel:
        root.clipboard_clear()
        root.clipboard_append(" | ".join(tree.item(sel)["values"]))

def paste():
    try:
        entry.delete(0, tk.END)
        entry.insert(0, root.clipboard_get())
    except:
        pass

# ---------- UI ----------

root = tk.Tk()
root.title("Modbus Analyzer PRO 😎")
root.geometry("1100x550")

top = tk.Frame(root)
top.pack(pady=5)

entry = tk.Entry(top, width=50)
entry.pack(side=tk.LEFT)
entry.insert(0, "42-48-00-00")

tk.Button(top, text="HEX", command=convert).pack(side=tk.LEFT)
tk.Button(top, text="Modbus", command=convert_modbus).pack(side=tk.LEFT)
tk.Button(top, text="Открыть лог", command=load_log).pack(side=tk.LEFT)
tk.Button(top, text="Очистить", command=clear).pack(side=tk.LEFT)
tk.Button(top, text="Копировать", command=copy).pack(side=tk.LEFT)
tk.Button(top, text="Вставить", command=paste).pack(side=tk.LEFT)

only_valid = tk.BooleanVar()
tk.Checkbutton(top, text="Только нормальные", variable=only_valid).pack(side=tk.LEFT)

modbus_entry = tk.Entry(root, width=80)
modbus_entry.pack()
modbus_entry.insert(0, "01 03 04 42 48 00 00")

cols = ("Endian", "HEX", "float32", "float64", "int32", "int16")
tree = ttk.Treeview(root, columns=cols, show="headings")

for c in cols:
    tree.heading(c, text=c)
    tree.column(c, anchor="center")

tree.pack(expand=True, fill="both")

tree.tag_configure("good", foreground="green")
tree.tag_configure("bad", foreground="red")
tree.tag_configure("best", foreground="blue")
tree.tag_configure("block", foreground="gray")

status = tk.StringVar()
status.set("Готов")
tk.Label(root, textvariable=status).pack()

root.mainloop()