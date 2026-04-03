import struct
import tkinter as tk
from tkinter import ttk

def parse_hex(hex_str):
    hex_str = hex_str.replace(" ", "").replace("0x", "")
    return bytes.fromhex(hex_str)

def reorder(data, order):
    return bytes([data[i] for i in order])

def to_float(b):
    try:
        return struct.unpack('>f', b)[0]
    except:
        return "err"

def to_int32(b):
    return int.from_bytes(b, byteorder='big', signed=True)

def to_int16_pairs(b):
    return [
        int.from_bytes(b[0:2], byteorder='big', signed=True),
        int.from_bytes(b[2:4], byteorder='big', signed=True)
    ]

def convert():
    tree.delete(*tree.get_children())
    hex_input = entry.get()

    try:
        data = parse_hex(hex_input)

        if len(data) != 4:
            status.set("❌ Нужно ровно 4 байта (8 hex символов)")
            return

        variants = {
            "ABCD (Big)": [0,1,2,3],
            "DCBA (Little)": [3,2,1,0],
            "BADC": [1,0,3,2],
            "CDAB": [2,3,0,1],
        }

        for name, order in variants.items():
            b = reorder(data, order)

            tree.insert("", "end", values=(
                name,
                b.hex(" ").upper(),
                to_float(b),
                to_int32(b),
                str(to_int16_pairs(b))
            ))

        status.set("✅ Готово")

    except Exception as e:
        status.set(f"Ошибка: {e}")

# GUI
root = tk.Tk()
root.title("HEX Converter (Offline)")
root.geometry("700x300")

frame = tk.Frame(root)
frame.pack(pady=10)

entry = tk.Entry(frame, width=40)
entry.pack(side=tk.LEFT, padx=5)
entry.insert(0, "41 20 00 00")

btn = tk.Button(frame, text="Конвертировать", command=convert)
btn.pack(side=tk.LEFT)

columns = ("Format", "HEX", "float32", "int32", "int16 (2x)")
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