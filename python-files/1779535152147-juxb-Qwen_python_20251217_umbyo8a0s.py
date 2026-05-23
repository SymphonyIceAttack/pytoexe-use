import tkinter as tk
import random

# База вопросов: (немецкое слово, правильный перевод, [варианты с переводом])
QUESTIONS = [
    ("das Hemd", "рубашка", ["der Pullover (свитер)", "das Hemd (рубашка)", "die Hose (брюки)"]),
    ("die Hose", "брюки", ["der Rock (юбка)", "die Hose (брюки)", "die Mütze (шапка)"]),
    ("der Pullover", "свитер", ["der Mantel (пальто)", "das Kleid (платье)", "der Pullover (свитер)"]),
    ("der Mantel", "пальто", ["der Mantel (пальто)", "die Jacke (куртка)", "die Schuhe (обувь)"]),
    ("die Jacke", "куртка", ["die Jacke (куртка)", "der Schal (шарф)", "die Socken (носки)"]),
    ("das Kleid", "платье", ["das Kleid (платье)", "der Gürtel (ремень)", "die Handschuhe (перчатки)"]),
    ("der Rock", "юбка", ["die Mütze (шапка)", "der Rock (юбка)", "der Anzug (костюм)"]),
    ("die Mütze", "шапка", ["die Mütze (шапка)", "der Hut (шляпа)", "die Sonnenbrille (солнцезащитные очки)"]),
    ("der Hut", "шляпа", ["der Hut (шляпа)", "die Brille (очки)", "der Regenschirm (зонт)"]),
    ("der Schal", "шарф", ["der Schal (шарф)", "die Tasche (сумка)", "die Uhr (часы)"]),
    ("die Handschuhe", "перчатки", ["die Handschuhe (перчатки)", "die Socken (носки)", "die Schuhe (обувь)"]),
    ("die Socken", "носки", ["die Socken (носки)", "die Sandalen (сандалии)", "die Stiefel (сапоги)"]),
    ("die Schuhe", "обувь", ["die Schuhe (обувь)", "die Turnschuhe (кроссовки)", "die Pantoffeln (тапочки)"]),
    ("die Stiefel", "сапоги", ["die Stiefel (сапоги)", "die Schuhe (обувь)", "die Sandalen (сандалии)"]),
    ("die Turnschuhe", "кроссовки", ["die Turnschuhe (кроссовки)", "die Pantoffeln (тапочки)", "der Gürtel (ремень)"]),
    ("die Sandalen", "сандалии", ["die Sandalen (сандалии)", "die Handschuhe (перчатки)", "der Rock (юбка)"]),
    ("die Pantoffeln", "тапочки", ["die Pantoffeln (тапочки)", "die Mütze (шапка)", "der Pullover (свитер)"]),
    ("der Gürtel", "ремень", ["der Gürtel (ремень)", "die Uhr (часы)", "die Tasche (сумка)"]),
    ("die Brille", "очки", ["die Brille (очки)", "die Sonnenbrille (солнцезащитные очки)", "der Hut (шляпа)"]),
    ("die Sonnenbrille", "солнцезащитные очки", ["die Sonnenbrille (солнцезащитные очки)", "die Brille (очки)", "der Regenschirm (зонт)"]),
    ("der Regenschirm", "зонт", ["der Regenschirm (зонт)", "die Jacke (куртка)", "der Mantel (пальто)"]),
    ("die Tasche", "сумка", ["die Tasche (сумка)", "die Uhr (часы)", "der Gürtel (ремень)"]),
    ("die Uhr", "часы", ["die Uhr (часы)", "die Brille (очки)", "die Mütze (шапка)"]),
    ("der Anzug", "костюм", ["der Anzug (костюм)", "das Kleid (платье)", "der Pullover (свитер)"]),
    ("die Jeans", "джинсы", ["die Jeans (джинсы)", "die Hose (брюки)", "der Rock (юбка)"]),
    ("der Bademantel", "халат", ["der Bademantel (халат)", "der Pullover (свитер)", "die Jacke (куртка)"]),
    ("die Strumpfhose", "колготки", ["die Strumpfhose (колготки)", "die Socken (носки)", "die Handschuhe (перчатки)"]),
    ("der Badeanzug", "купальник", ["der Badeanzug (купальник)", "das Kleid (платье)", "die Hose (брюки)"]),
    ("der Pyjama", "пижама", ["der Pyjama (пижама)", "der Bademantel (халат)", "der Anzug (костюм)"]),
    ("die Weste", "жилет", ["die Weste (жилет)", "die Jacke (куртка)", "der Pullover (свитер)"]),
]

# Перемешиваем (опционально)
random.shuffle(QUESTIONS)

class ClothingQuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Тест по немецкому: Одежда")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg="#f0f0f0")
        self.root.bind("<Escape>", lambda e: root.destroy())

        self.score = 0
        self.current_index = 0
        self.setup_ui()

    def setup_ui(self):
        self.main_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.question_label = tk.Label(
            self.main_frame, text="", font=("Arial", 22, "bold"),
            bg="#f0f0f0", fg="#333", wraplength=900, justify="center"
        )
        self.question_label.pack(pady=20)

        self.option_buttons = []
        for i in range(3):
            btn = tk.Button(
                self.main_frame, text="", font=("Arial", 16), width=70, height=2,
                command=lambda i=i: self.check_answer(i),
                bg="#e0e0e0", activebackground="#d0d0d0", relief="solid", bd=1
            )
            btn.pack(pady=6)
            self.option_buttons.append(btn)

        self.next_button = tk.Button(
            self.main_frame, text="Далее", font=("Arial", 16),
            state="disabled", command=self.next_question,
            bg="#4CAF50", fg="white", width=15
        )
        self.next_button.pack(pady=20)

        self.update_question()

    def update_question(self):
        if self.current_index >= len(QUESTIONS):
            self.show_result()
            return

        german, correct_ru, options = QUESTIONS[self.current_index]
        self.question_label.config(text=f"Вопрос {self.current_index + 1} из {len(QUESTIONS)}\n\nКак переводится: «{german}»?")

        for i, opt in enumerate(options):
            self.option_buttons[i].config(
                text=opt, state="normal", bg="#e0e0e0", fg="black"
            )

        # НАДЕЖНЫЙ поиск правильного индекса по переводу
        self.correct_idx = None
        for i, opt in enumerate(options):
            if opt.endswith(f"({correct_ru})"):
                self.correct_idx = i
                break
        if self.correct_idx is None:
            self.correct_idx = 0  # fallback

        self.answered = False
        self.next_button.config(state="disabled")

    def check_answer(self, choice):
        if self.answered:
            return
        self.answered = True

        if choice == self.correct_idx:
            self.score += 1
            self.option_buttons[choice].config(bg="#c3e6cb", fg="#155724")  # зелёный
        else:
            self.option_buttons[choice].config(bg="#f5c6cb", fg="#721c24")  # красный
            self.option_buttons[self.correct_idx].config(bg="#c3e6cb", fg="#155724")  # правильный — зелёный

        for btn in self.option_buttons:
            btn.config(state="disabled")
        self.next_button.config(state="normal")

    def next_question(self):
        self.current_index += 1
        self.update_question()

    def show_result(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        result = f"Тест завершён!\n\nВаш результат: {self.score} из {len(QUESTIONS)}"
        tk.Label(
            self.main_frame, text=result, font=("Arial", 26, "bold"),
            bg="#f0f0f0", fg="#2c3e50", justify="center"
        ).pack(pady=60)
        tk.Button(
            self.main_frame, text="Завершить", font=("Arial", 18),
            command=self.root.destroy, bg="#e74c3c", fg="white", width=15
        ).pack(pady=20)

if __name__ == "__main__":
    root = tk.Tk()
    app = ClothingQuizApp(root)
    root.mainloop()