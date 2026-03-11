import tkinter as tk

questions = [
    {
        "question": "Скільки буде 2 + 2?",
        "options": ["3", "4", "5"],
        "answer": "4"
    },
    {
        "question": "Столиця України?",
        "options": ["Київ", "Львів", "Одеса"],
        "answer": "Київ"
    },
    {
        "question": "Скільки днів у тижні?",
        "options": ["5", "7", "10"],
        "answer": "7"
    }
]

current_question = 0
score = 0

def next_question():
    global current_question, score
    
    selected = var.get()
    
    if selected == questions[current_question]["answer"]:
        score += 1
    
    current_question += 1
    
    if current_question < len(questions):
        show_question()
    else:
        question_label.config(text=f"Тест завершено! Правильних відповідей: {score} з 3")
        for btn in radio_buttons:
            btn.pack_forget()
        next_button.pack_forget()

def show_question():
    var.set(None)
    q = questions[current_question]
    
    question_label.config(text=q["question"])
    
    for i, option in enumerate(q["options"]):
        radio_buttons[i].config(text=option, value=option)

root = tk.Tk()
root.title("Тест")

question_label = tk.Label(root, text="", font=("Arial", 14))
question_label.pack(pady=20)

var = tk.StringVar()

radio_buttons = []
for i in range(3):
    btn = tk.Radiobutton(root, text="", variable=var, value="", font=("Arial", 12))
    btn.pack(anchor="w")
    radio_buttons.append(btn)

next_button = tk.Button(root, text="Далі", command=next_question)
next_button.pack(pady=20)

show_question()

root.mainloop()