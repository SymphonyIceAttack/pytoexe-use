import tkinter as tk
import random

def on_no_click():
    global yes_font_size

    phrases = ["ну пж 🥺", "точно нет? 💔", "а может подумаешь?", "пожалуйстааа ", "ну как так", "котек"]
    btn_no.config(text=random.choice(phrases))

    # Увеличиваем кнопку "Да"
    yes_font_size += 5
    btn_yes.config(font=("Arial", yes_font_size))

def on_yes_click():
    container.pack_forget()

    # Новый контейнер по центру
    final_frame = tk.Frame(root)
    final_frame.pack(expand=True)

    # Большая надпись по центру
    big_text = tk.Label(final_frame, text="УРААААААА 💖", font=("Arial", 40))
    big_text.pack(pady=10)

    # Надпись поменьше под ней
    small_text = tk.Label(final_frame, text="(я тебя люблю)", font=("Arial", 18))
    small_text.pack()
    
# === Окно ===
root = tk.Tk()
root.title("Валентинка 💘")
root.geometry("400x600")

# Контейнер для центрирования (ВАЖНО)
container = tk.Frame(root)
container.pack(expand=True)

yes_font_size = 14  # начальный размер кнопки "Да"

# Сердечко
label_heart = tk.Label(container, text="💖", font=("Arial", 80))
label_heart.pack(pady=10)

# Текст
label_text = tk.Label(
    container,
    text="Будешь моим валентином? 💘",
    font=("Arial", 16)
)
label_text.pack(pady=20)

# Кнопка ДА
btn_yes = tk.Button(
    container,
    text="Да 💕",
    font=("Arial", yes_font_size),
    command=on_yes_click
)
btn_yes.pack(pady=10)

# Кнопка НЕТ
btn_no = tk.Button(
    container,
    text="Нет 😐",
    font=("Arial", 14),
    command=on_no_click
)
btn_no.pack(pady=10)

root.mainloop()
