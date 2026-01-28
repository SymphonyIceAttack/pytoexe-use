import tkinter as tk

# --- Питання по колу ---
questions = [
    "Ти дурік?",
    "Ти впевнений?",
    "Ти подумав?",
    "Ти серйозно?",
    "Признайся вже)"
]

current_question = 0
one_counter = 0  # лічильник натискань "1"

def update_question(text):
    canvas.itemconfig(question_text, text=text)
    canvas.itemconfig(question_shadow, text=text)

def on_no():
    global current_question
    current_question += 1
    if current_question >= len(questions):
        current_question = 0
    update_question(questions[current_question])

def on_yes():
    update_question("Я так і знав)")
    yes_button.place_forget()
    no_button.place_forget()
    root.after(1500, root.destroy)

def on_key_press(event):
    global one_counter
    if event.char == "1":
        one_counter += 1
        if one_counter >= 4:
            root.destroy()  # закриваємо програму

# --- Вікно ---
root = tk.Tk()
root.title("Ошибка Windows")
root.attributes("-fullscreen", True)
root.configure(bg="#0a3d91")
root.resizable(False, False)

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()

canvas = tk.Canvas(root, bg="#0a3d91", highlightthickness=0)
canvas.pack(fill="both", expand=True)

center_x = screen_w // 2

# --- Заголовок ---
canvas.create_text(
    center_x, 150,
    text="Ошибка Windows",
    font=("Segoe UI", 40, "bold"),
    fill="white"
)

# --- Питання ---
question_shadow = canvas.create_text(
    center_x + 2, 250,
    text=questions[0],
    font=("Segoe UI", 28, "bold"),
    fill="black"
)
question_text = canvas.create_text(
    center_x, 248,
    text=questions[0],
    font=("Segoe UI", 28, "bold"),
    fill="white"
)

# --- Кнопки ---
yes_button = tk.Button(
    root,
    text="Так",
    font=("Segoe UI", 20),
    width=10,
    command=on_yes,
    bg="#0078D7",
    fg="white",
    activebackground="#005a9e",
    relief="flat"
)
yes_button.place(relx=0.35, rely=0.65, anchor="center")  # використання relx + anchor

no_button = tk.Button(
    root,
    text="Ні",
    font=("Segoe UI", 20),
    width=10,
    command=on_no,
    bg="#D70022",
    fg="white",
    relief="flat"
)
no_button.place(relx=0.65, rely=0.65, anchor="center")  # використання relx + anchor

# --- Прив'язка клавіатури ---
root.bind("<Key>", on_key_press)

root.mainloop()
