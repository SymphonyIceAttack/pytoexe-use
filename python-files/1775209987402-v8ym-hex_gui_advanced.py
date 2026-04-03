import struct
import tkinter as tk
from tkinter import ttk

def parse_hex(hex_str):
    hex_str = hex_str.replace(" ", "").replace("-", "").replace(",", "").replace("0x","")
    return bytes.fromhex(hex_str)

def reorder(data, order):
    return bytes([data[i] for i in order])

def to_float32(b):
    try:
        return struct.unpack('>f', b)[0]
    except:
        return "err"

def to_float64(b):
    try:
        return struct.unpack('>d', b + b)[0]  # из 4 байт делаем 8
    except:
        return "err"

def to_int32(b):
    return int.from_bytes(b, byteorder='big', signed=True)

def to_int16_pairs(b):
    return [
        int.from_bytes(b[0:2], byteorder='big', signed=True),
        int.from_bytes(b[2:4], byteorder='big', signed=True)
    ]

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
        results.append((
            name,
            b.hex(" ").upper(),
            f"{to_float32(b):.6g}" if isinstance(to_float32(b), float) else "err",
            f"{to_float64(b):.6g}" if isinstance(to_float64(b), float) else "err",
            str(to_int32(b)),
            str(to_int16_pairs(b))
        ))
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

            # строка-разделитель блока
            tree.insert("", "end", values=(f"Блок {block_num}", block.hex(" ").upper(), "", "", "", ""))

            for row in process_block(block):
                tree.insert("", "end", values=row)

            block_num += 1

        status.set("✅ Готово")

    except Exception as e:
        status.set(f"Ошибка: {e}")

def copy_selected():
    selected = tree.focus()
    if selected:
        values = tree.item(selected, 'values')
        root.clipboard_clear()
        root.clipboard_append(" | ".join(values))

# GUI
root = tk.Tk()
root.title("HEX Converter (Advanced)")
root.geometry("900x400")

top_frame = tk.Frame(root)
top_frame.pack(pady=5)

entry = tk.Entry(top_frame, width=60)
entry.pack(side=tk.LEFT, padx=5)
entry.insert(0, "42-00-00-00")

btn = tk.Button(top_frame, text="Конвертировать", command=convert)
btn.pack(side=tk.LEFT)

copy_btn = tk.Button(top_frame, text="Копировать строку", command=copy_selected)
copy_btn.pack(side=tk.LEFT, padx=5)

columns = ("Endian", "HEX", "float32", "float64", "int32", "int16")
tree = ttk.Treeview(root, columns=columns, show="headings")

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center")

tree.pack(expand=True, fill="both")

status = tk.StringVar()
status.set("Готов")
status_label = tk.Label(root, textvariable=status)
status_label.pack()

root.mainloop()