import tkinter as tk
from tkinter import messagebox
import hashlib
import time
import datetime

def generate_keys():
    name = entry_name.get()
    surname = entry_surname.get()
    email = entry_email.get()
    card_number = entry_card.get()

    if len(card_number) != 16 or not card_number.isdigit():
        messagebox.showerror("Ошибка", "Номер карты должен содержать ровно 16 цифр!")
        return

    current_time = datetime.datetime.now().isoformat()

    data_string = f"{name}{surname}{email}{card_number}{current_time}"

    public_key = hashlib.sha256(data_string.encode()).hexdigest()

    private_key_input = f"{public_key}secret_salt_{current_time}"
    private_key = hashlib.sha512(private_key_input.encode()).hexdigest()

    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, f"Введённые данные:\n")
    result_text.insert(tk.END, f"Имя: {name}\n")
    result_text.insert(tk.END, f"Фамилия: {surname}\n")
    result_text.insert(tk.END, f"Email: {email}\n")
    result_text.insert(tk.END, f"Номер карты: {card_number}\n\n")
    result_text.insert(tk.END, f"Открытый ключ (SHA-256):\n{public_key}\n\n")
    result_text.insert(tk.END, f"Закрытый ключ (SHA-512):\n{private_key}")

root = tk.Tk()
root.title("Шифровальщик данных")
root.geometry("600x500")

tk.Label(root, text="Имя:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
entry_name = tk.Entry(root, width=40)
entry_name.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="Фамилия:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
entry_surname = tk.Entry(root, width=40)
entry_surname.grid(row=1, column=1, padx=10, pady=5)

tk.Label(root, text="Email:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
entry_email = tk.Entry(root, width=40)
entry_email.grid(row=2, column=1, padx=10, pady=5)

tk.Label(root, text="Номер карты (16 цифр):").grid(row=3, column=0, padx=10, pady=5, sticky="w")
entry_card = tk.Entry(root, width=40)
entry_card.grid(row=3, column=1, padx=10, pady=5)

encrypt_button = tk.Button(root, text="Зашифровать данные", command=generate_keys)
encrypt_button.grid(row=4, column=0, columnspan=2, pady=20)

result_text = tk.Text(root, height=15, width=70)
result_text.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

root.mainloop()
