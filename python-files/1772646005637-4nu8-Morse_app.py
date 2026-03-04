import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext

# =======================
# СЛОВАРЬ МОРЗЕ
# =======================

MORSE_CODE = {
    'А': '.-', 'Б': '-...', 'В': '.--', 'Г': '--.', 'Д': '-..',
    'Е': '.', 'Ё': '.', 'Ж': '...-', 'З': '--..', 'И': '..',
    'Й': '.---', 'К': '-.-', 'Л': '.-..', 'М': '--', 'Н': '-.',
    'О': '---', 'П': '.--.', 'Р': '.-.', 'С': '...', 'Т': '-',
    'У': '..-', 'Ф': '..-.', 'Х': '....', 'Ц': '-.-.', 'Ч': '---.',
    'Ш': '----', 'Щ': '--.-', 'Ъ': '--.--', 'Ы': '-.--',
    'Ь': '-..-', 'Э': '..-..', 'Ю': '..--', 'Я': '.-.-',

    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..',
    'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
    'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
    'Q': '--.-', 'R': '.-.', 'S': '...',
    'T': '-', 'U': '..-', 'V': '...-',
    'W': '.--', 'X': '-..-', 'Y': '-.--', 'Z': '--..',

    '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....',
    '6': '-....', '7': '--...', '8': '---..',
    '9': '----.'
}

REVERSE_MORSE_CODE = {v: k for k, v in MORSE_CODE.items()}

# =======================
# ЛОГИКА
# =======================

def text_to_morse(text):
    result = []
    for char in text.upper():
        if char == ' ':
            result.append('/')
        elif char in MORSE_CODE:
            result.append(MORSE_CODE[char])
        else:
            result.append('?')
    return ' '.join(result)

def morse_to_text(morse):
    result = []
    words = morse.split(' / ')
    for word in words:
        for letter in word.split():
            result.append(REVERSE_MORSE_CODE.get(letter, '?'))
        result.append(' ')
    return ''.join(result).strip()

def encrypt_text():
    text = input_text.get("1.0", tk.END).strip()
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, text_to_morse(text))

def decrypt_text():
    text = input_text.get("1.0", tk.END).strip()
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, morse_to_text(text))

def clear_fields():
    input_text.delete("1.0", tk.END)
    output_text.delete("1.0", tk.END)

# =======================
# ИНТЕРФЕЙС
# =======================

root = tk.Tk()
root.title("Азбука Морзе")
root.geometry("750x600")
root.minsize(650, 500)

style = ttk.Style()
style.theme_use("clam")

# Тёмная цветовая схема
root.configure(bg="#1e1e1e")
style.configure("TFrame", background="#1e1e1e")
style.configure("TLabel", background="#1e1e1e", foreground="white", font=("Segoe UI", 11))
style.configure("TButton", font=("Segoe UI", 10), padding=6)
style.map("TButton",
          background=[("active", "#3a3a3a")],
          foreground=[("active", "white")])

main_frame = ttk.Frame(root, padding=20)
main_frame.pack(fill="both", expand=True)

title = ttk.Label(main_frame, text="Азбука Морзе", font=("Segoe UI", 18, "bold"))
title.pack(pady=(0, 20))

# Ввод
ttk.Label(main_frame, text="Ввод текста или кода Морзе:").pack(anchor="w")
input_text = scrolledtext.ScrolledText(
    main_frame,
    height=7,
    font=("Consolas", 12),
    bg="#2b2b2b",
    fg="white",
    insertbackground="white"
)
input_text.pack(fill="both", expand=True, pady=5)

# Кнопки
button_frame = ttk.Frame(main_frame)
button_frame.pack(pady=15)

encrypt_btn = ttk.Button(button_frame, text="Зашифровать", command=encrypt_text)
encrypt_btn.grid(row=0, column=0, padx=10)

decrypt_btn = ttk.Button(button_frame, text="Дешифровать", command=decrypt_text)
decrypt_btn.grid(row=0, column=1, padx=10)

clear_btn = ttk.Button(button_frame, text="Очистить", command=clear_fields)
clear_btn.grid(row=0, column=2, padx=10)

# Вывод
ttk.Label(main_frame, text="Результат:").pack(anchor="w")
output_text = scrolledtext.ScrolledText(
    main_frame,
    height=7,
    font=("Consolas", 12),
    bg="#2b2b2b",
    fg="#00ff99",
    insertbackground="white"
)
output_text.pack(fill="both", expand=True, pady=5)

root.mainloop()