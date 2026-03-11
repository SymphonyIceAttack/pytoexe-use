import tkinter as tk
from tkinter import messagebox

score = 0
q = 0

questions = [
    ("Столиця України?", ["Харків", "Київ", "Львів"], "Київ"),
    ("Коли Україна стала незалежною?", ["1991", "2001", "1985"], "1991"),
    ("Найдовша річка України?", ["Дніпро", "Дністер", "Прут"], "Дніпро")
]

def answer(choice):
    global score, q

    if choice == questions[q][2]:
        score += 1

    q += 1

    if q < 3:
        show_question()
    else:
        messagebox.showinfo("Результат", "Твій результат: " + str(score) + " з 3")
        root.destroy()

def show_question():
    question.config(text=questions[q][0])

    b1.config(text=questions[q][1][0], command=lambda: answer(questions[q][1][0]))
    b2.config(text=questions[q][1][1], command=lambda: answer(questions[q][1][1]))
    b3.config(text=questions[q][1][2], command=lambda: answer(questions[q][1][2]))

root = tk.Tk()
root.title("Тест про Україну")

question = tk.Label(root, font=("Arial",12))
question.pack(pady=10)

b1 = tk.Button(root, width=20)
b1.pack(pady=3)

b2 = tk.Button(root, width=20)
b2.pack(pady=3)

b3 = tk.Button(root, width=20)
b3.pack(pady=3)

show_question()

root.mainloop()