import tkinter as tk
from tkinter import messagebox


def create_cipher_map(key):
    if len(key) != 10:
        raise ValueError("Ключ должен содержать ровно 10 букв")
    
    key = key.upper()
    digits = ['1','2','3','4','5','6','7','8','9','0']
    
    cipher = dict(zip(key, digits))
    decipher = {v: k for k, v in cipher.items()}
    
    return cipher, decipher


def encrypt():
    try:
        key = entry_key.get().upper()
        text = entry_text.get().upper()
        
        cipher, _ = create_cipher_map(key)
        
        result = ""
        for char in text:
            result += cipher.get(char, char)
        
        result_label.config(text="Результат: " + result)
    
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))


def decrypt():
    try:
        key = entry_key.get().upper()
        text = entry_text.get()
        
        _, decipher = create_cipher_map(key)
        
        result = ""
        for char in text:
            result += decipher.get(char, char)
        
        result_label.config(text="Результат: " + result)
    
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))


# === ОКНО ===
root = tk.Tk()
root.title("Шифратор")
root.geometry("400x300")

# Ключ
tk.Label(root, text="Ключ (10 букв):").pack()
entry_key = tk.Entry(root, width=30)
entry_key.pack()

# Текст
tk.Label(root, text="Текст / Цифры:").pack()
entry_text = tk.Entry(root, width=30)
entry_text.pack()

# Кнопки
tk.Button(root, text="Шифровать", command=encrypt).pack(pady=5)
tk.Button(root, text="Дешифровать", command=decrypt).pack(pady=5)

# Результат
result_label = tk.Label(root, text="Результат: ", font=("Arial", 12))
result_label.pack(pady=10)

root.mainloop()
