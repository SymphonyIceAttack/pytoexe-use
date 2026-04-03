import struct
import tkinter as tk
from tkinter import ttk
import math

def parse_hex(hex_str):
    hex_str = hex_str.replace(" ", "").replace("-", "").replace(",", "").replace("0x","")
    return bytes.fromhex(hex_str)

def reorder(data, order):
    return bytes([data[i] for i in order])

def to_float32(b):
    try:
        return struct.unpack('>f', b)[0]
    except:
        return None

def to_float64(b):
    try:
        return struct.unpack('>d', b + b)[0]
    except:
        return None

def to_int32(b):
    return int.from_bytes(b, byteorder='big', signed=True)

def to_int16_pairs(b):
    return [
        int.from_bytes(b[0:2], byteorder='big', signed=True),
        int.from_bytes(b[2:4], byteorder='big', signed=True)
    ]

def is_valid_float(val):
    if val is None:
        return False
    if math.isnan(val) or math.isinf(val):
        return False
    if abs(val) < 1e-20 or abs(val) > 1e20:
        return False
    return True

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

        results.append({
            "values": (
                name,
                b.hex(" ").upper(),
                f"{f32:.6g}" if f32 is not None else "err",
                f"{f64:.6g}" if f64 is not None else "err",
                str(to_int32(b)),
                str(to_int16_pairs(b))
            ),
            "valid": is_valid_float(f32) or is_valid_float(f64)
        })

    return results

def convert():
    tree.delete(*tree.get_children())

    try:
        data = parse_hex(entry.get())

        if len(data) < 4:
            status.set("❌ Нужно минимум 4 байта")
            return

        block_num = 1
        for i in range(0, len(data)-3, 4):
            block = data[i:i+4]

            tree.insert("", "end",
                        values=(f"Блок {block_num}", block.hex(" ").upper(), "", "", "", ""),
                        tags=("block",))

            for r in process_block(block):
                tag = "good" if r["valid"] else "bad"
                tree.insert("", "end", values=r["values"], tags=(tag,))

            block_num += 1

        status.set("✅ Готово")

    except Exception as e:
        status.set(f"Ошибка: {e}")

def clear_table():
    tree.delete(*tree.get_children())
    status.set("Таблица очищена")

def copy_selected():
    selected = tree.focus()
    if selected:
        values = tree.item(selected, 'values')
        root.clipboard_clear()
        root.clipboard_append(" | ".join(values))

def paste_from_clipboard():
    try:
        text = root.clipboard_get()
        entry.delete(0, tk.END)
        entry.insert(0, text)
        status.set("Вставлено из буфера")
    except:
        status.set("Буфер пуст")

# GUI
root = tk.Tk()
root.title("HEX Converter PRO 😎")
root.geometry("950x450")

top_frame = tk.Frame(root)
top_frame.pack(pady=5)

entry = tk.Entry(top_frame, width=60)
entry.pack(side=tk.LEFT, padx=5)
entry.insert(0, "42-00-00-00")

tk.Button(top_frame, text="Конвертировать", command=convert).pack(side=tk.LEFT)
tk.Button(top_frame, text="Очистить", command=clear_table).pack(side=tk.LEFT, padx=5)
tk.Button(top_frame, text="Копировать", command=copy_selected).pack(side=tk.LEFT, padx=5)
tk.Button(top_frame, text="Вставить", command=paste_from_clipboard).pack(side=tk.LEFT)

columns = ("Endian", "HEX", "float32", "float64", "int32", "int16")
tree = ttk.Treeview(root, columns=columns, show="headings")

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center")

tree.pack(expand=True, fill="both")

# стили подсветки
tree.tag_configure("good", foreground="green")
tree.tag_configure("bad", foreground="red")
tree.tag_configure("block", foreground="blue")

status = tk.StringVar()
status.set("Готов")
tk.Label(root, textvariable=status).pack()

root.mainloop()