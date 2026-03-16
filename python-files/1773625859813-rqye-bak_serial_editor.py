import struct
import tkinter as tk
from tkinter import filedialog, messagebox

OFFSET = 0x00000002  # position of the serial number


def change_serial(file_path, new_number):
    try:
        num = int(new_number)
        if num < 0 or num > 0xFFFFFFFF:
            raise ValueError("Number out of range")

        with open(file_path, "rb") as f:
            data = bytearray(f.read())

        data[OFFSET:OFFSET+4] = struct.pack("<I", num)  # little endian

        new_path = file_path + ".modified"
        with open(new_path, "wb") as f:
            f.write(data)

        messagebox.showinfo("Success", f"Serial updated.\nSaved as:\n{new_path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))


def choose_file():
    path = filedialog.askopenfilename(title="Select FRK1_DATA.BAK")
    if path:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, path)


def run_change():
    file_path = file_entry.get()
    serial = serial_entry.get()

    if not file_path:
        messagebox.showwarning("Warning", "Choose a file first")
        return

    if not serial:
        messagebox.showwarning("Warning", "Enter serial number")
        return

    change_serial(file_path, serial)


root = tk.Tk()
root.title("BAK Serial Editor")
root.geometry("420x180")

frame = tk.Frame(root)
frame.pack(pady=10)

tk.Label(frame, text="BAK File:").grid(row=0, column=0, sticky="e")
file_entry = tk.Entry(frame, width=35)
file_entry.grid(row=0, column=1)

tk.Button(frame, text="Browse", command=choose_file).grid(row=0, column=2, padx=5)

tk.Label(frame, text="New Serial:").grid(row=1, column=0, sticky="e", pady=10)
serial_entry = tk.Entry(frame, width=20)
serial_entry.grid(row=1, column=1, sticky="w")

tk.Button(root, text="Change Serial", command=run_change, height=2, width=20).pack(pady=10)

root.mainloop()
