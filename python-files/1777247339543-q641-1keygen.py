import random
import tkinter as tk
from tkinter import messagebox

def generate_key():
    prefix = f"{random.randint(111, 998)}{random.randint(0, 6)}"
    
    while True:
        digits = [random.randint(0, 9) for _ in range(7)]
        if digits[-1] in [0, 8, 9]:
            continue
        if sum(digits) % 7 == 0:
            suffix = "".join(map(str, digits))
            return f"{prefix}-{suffix}"

def generate_keys():
    output.delete(1.0, tk.END)
    for i in range(1, 6):
        output.insert(tk.END, f"Anahtar {i}: {generate_key()}\n")

def copy_keys():
    keys = output.get(1.0, tk.END)
    root.clipboard_clear()
    root.clipboard_append(keys)
    messagebox.showinfo("Kopyalandı", "Anahtarlar panoya kopyalandı!")

root = tk.Tk()
root.title("Office 97 Key Generator")
root.geometry("400x300")

btn_generate = tk.Button(root, text="Anahtar Üret", command=generate_keys)
btn_generate.pack(pady=10)

btn_copy = tk.Button(root, text="Kopyala", command=copy_keys)
btn_copy.pack(pady=5)

output = tk.Text(root, height=10, width=45)
output.pack(pady=10)

root.mainloop()