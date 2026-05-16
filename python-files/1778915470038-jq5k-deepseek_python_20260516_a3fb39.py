import tkinter as tk
from tkinter import ttk
import random
import time

def fake_mining():
    global mined
    if mined < 999:
        mined += random.uniform(0.001, 0.005)
        btc_var.set(f"{mined:.5f} BTC")
        root.after(500, fake_mining)
    else:
        label_status.config(text="Шутка! Никакого майнинга не было 😄")

def close_joke():
    root.destroy()
    print("Ха-ха, это был псевдомайнер!")

root = tk.Tk()
root.title("Bitcoin Miner PRO")
root.geometry("500x400")
root.resizable(False, False)

mined = 0.0
btc_var = tk.StringVar()
btc_var.set("0.00000 BTC")

# Текст "майнинг"
tk.Label(root, text="⚒️ BITCOIN MINER ⚒️", font=("Arial", 16)).pack(pady=10)
tk.Label(root, text="Добыто BTC:").pack()
tk.Label(root, textvariable=btc_var, font=("Arial", 14), fg="green").pack()

# Анимация текстом
label_status = tk.Label(root, text="⛏️ Шахтёр копает руду... ⛏️", font=("Arial", 12))
label_status.pack(pady=20)

# Прогресс-бар
progress = ttk.Progressbar(root, length=300, mode='determinate')
progress.pack(pady=10)

# Кнопка выхода (обманная)
tk.Button(root, text="STOP MINING", command=close_joke, bg="red", fg="white").pack(pady=20)

# Запускаем фейковый майнинг
root.after(500, fake_mining)
root.mainloop()