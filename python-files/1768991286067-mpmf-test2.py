import tkinter as tk
import random

formulas = [
    "CH3OH",
    "C2H5OH",
    "C5H11OH",
    "C16H33OH",
    "C2H4(OH)2",
    "C3H5(OH)3",
    "C5H7(OH)5",
    "C6H8(OH)6",
    "C3H5OH",
    "C10H17OH",
    "C6H6(OH)6",
    "C10H19OH"
]

names = [
    "Древесный спирт",
    "Винный спирт",
    "Амиловый спирт",
    "Цетиловый спирт",
    "Этиленгликоль",
    "Глицерин",
    "Ксилит",
    "Сорбит",
    "Аллиловый спирт",
    "Гераниол",
    "Инозит",
    "Ментол"
]

prev_i = None

root = tk.Tk()
root.title("Угадай брутто-формулу")

current_index = tk.IntVar(value=-1)

def next_substance():
    global prev_i
    i = random.randint(0, len(formulas) - 1)
    while i == prev_i:
        i = random.randint(0, len(formulas) - 1)
    prev_i = i
    current_index.set(i)
    label_name.config(text=names[i])
    entry_formula.delete(0, tk.END)

def check_answer():
    i = current_index.get()
    answer = entry_formula.get().strip().upper()
    if answer == formulas[i]:
        label_result.config(text=f"✅ Верно! Формула: {formulas[i]}", fg="green")
    else:
        label_result.config(text=f"❌ Неверно. Правильный ответ: {formulas[i]}", fg="red")

label_prompt = tk.Label(root, text="Введите брутто-формулу вещества:")
label_prompt.pack(pady=5)

label_name = tk.Label(root, text="", font=("Arial", 14, "bold"))
label_name.pack(pady=5)

entry_formula = tk.Entry(root, font=("Arial", 12))
entry_formula.pack(pady=5)

btn_check = tk.Button(root, text="Проверить", command=check_answer)
btn_check.pack(pady=5)

label_result = tk.Label(root, text="", font=("Arial", 12))
label_result.pack(pady=5)

btn_next = tk.Button(root, text="Следующее вещество", command=next_substance)
btn_next.pack(pady=5)

btn_exit = tk.Button(root, text="Выход", command=root.destroy)
btn_exit.pack(pady=5)

next_substance()
root.mainloop()
