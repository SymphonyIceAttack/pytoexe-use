import struct
import tkinter as tk
from tkinter import ttk
import math

# ---------- PARSE ----------

def parse_hex(hex_str):
    hex_str = hex_str.lower().replace("0x","")
    for ch in [" ", "-", ","]:
        hex_str = hex_str.replace(ch, "")
    return bytes.fromhex(hex_str)

def reorder(data, order):
    return bytes([data[i] for i in order])

# ---------- CONVERT ----------

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

# ---------- VALIDATION ----------

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

    # ⭐ выбираем лучший вариант
    best = max(results, key=lambda x: x["score"])
    return results, best

# ---------- MODBUS ----------

def parse_modbus(hex_str):
    data = parse_hex(hex_str)

    # TCP (MBAP)
    if len(data) > 7 and data[2] == 0 and data[3] == 0:
        length = data[4]*256 + data[5]
        func = data[7]
        byte_count = data[8]
        payload = data[9:9+byte_count]
        return "TCP", func, payload

    # RTU
    addr = data[0]
    func = data[1]
    byte_count = data[2]
    payload = data[3:3+byte_count]

    return f"RTU addr={addr}", func, payload

# ---------- GUI ACTIONS ----------

def fill_table(data_bytes, prefix="Блок"):
    block_num = 1

    for i in range(0, len(data_bytes)-3, 4):
        block = data_bytes[i:i+4]

        tree.insert("", "end",
                    values=(f"{prefix} {block_num}", block.hex(" ").upper(), "", "", "", ""),
                    tags=("block",))

        results, best = process_block(block)

        for r in results:
            tag = "good" if r["valid"] else "bad"
            if r == best:
                tag = "best"
            tree.insert("", "end", values=r["values"], tags=(tag,))

        block_num += 1

def convert():
    tree.delete(*tree.get_children())
    try:
        data = parse_hex(entry.get())
        fill_table(data)
        status.set("HEX обработан")
    except Exception as e:
        status.set(f"Ошибка: {e}")

def convert_modbus():
    tree.delete(*tree.get_children())
    try:
        mode, func, payload = parse_modbus(modbus_entry.get())
        fill_table(payload, prefix="MB")
        status.set(f"{mode} func={func}")
    except Exception as e:
        status.set(f"Ошибка Modbus: {e}")

def clear_table():
    tree.delete(*tree.get_children())
    status.set("Очищено")

def copy_selected():
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

# ---------- GUI ----------

root = tk.Tk()
root.title("HEX / Modbus Analyzer 😎")
root.geometry("1000x500")

top = tk.Frame(root)
top.pack(pady=5)

entry = tk.Entry(top, width=60)
entry.pack(side=tk.LEFT, padx=5)
entry.insert(0, "42-48-00-00")

tk.Button(top, text="HEX", command=convert).pack(side=tk.LEFT)
tk.Button(top, text="Modbus", command=convert_modbus).pack(side=tk.LEFT)
tk.Button(top, text="Очистить", command=clear_table).pack(side=tk.LEFT)
tk.Button(top, text="Копировать", command=copy_selected).pack(side=tk.LEFT)
tk.Button(top, text="Вставить", command=paste).pack(side=tk.LEFT)

modbus_entry = tk.Entry(root, width=80)
modbus_entry.pack(pady=5)
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