import tkinter as tk
import random
import threading
import sys

# === Попытка подключить звук и озвучку (безопасно) ===
TTS_AVAILABLE = False
SOUND_AVAILABLE = False

try:
    import pyttsx3
    engine = pyttsx3.init()
    # Попытка установить немецкий голос
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'de' in voice.id.lower() or 'german' in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    TTS_AVAILABLE = True
except Exception as e:
    print("⚠️ Озвучка недоступна:", e)

try:
    if sys.platform == "win32":
        import winsound
        SOUND_AVAILABLE = True
    else:
        # На macOS/Linux используем bell или заглушку
        SOUND_AVAILABLE = True
except:
    SOUND_AVAILABLE = False

def speak_german(text):
    if not TTS_AVAILABLE:
        return
    def _speak():
        try:
            engine.say(text)
            engine.runAndWait()
        except:
            pass
    threading.Thread(target=_speak, daemon=True).start()

def play_sound(correct):
    if not SOUND_AVAILABLE:
        return
    try:
        if sys.platform == "win32":
            freq = 800 if correct else 400
            dur = 200 if correct else 400
            winsound.Beep(freq, dur)
        else:
            # Просто системный звук (bell)
            print('\a', end='', flush=True)  # terminal bell
    except:
        pass

# === База вопросов: (немецкое слово, перевод на русский) ===
WORDS = [
    ("das Hemd", "рубашка"),
    ("die Hose", "брюки"),
    ("der Pullover", "свитер"),
    ("der Mantel", "пальто"),
    ("die Jacke", "куртка"),
    ("das Kleid", "платье"),
    ("der Rock", "юбка"),
    ("die Mütze", "шапка"),
    ("der Hut", "шляпа"),
    ("der Schal", "шарф"),
    ("die Handschuhe", "перчатки"),
    ("die Socken", "носки"),
    ("die Schuhe", "обувь"),
    ("die Stiefel", "сапоги"),
    ("die Turnschuhe", "кроссовки"),
    ("die Sandalen", "сандалии"),
    ("die Pantoffeln", "тапочки"),
    ("der Gürtel", "ремень"),
    ("die Brille", "очки"),
    ("die Sonnenbrille", "солнцезащитные очки"),
    ("der Regenschirm", "зонт"),
    ("die Tasche", "сумка"),
    ("die Uhr", "часы"),
    ("der Anzug", "костюм"),
    ("die Jeans", "джинсы"),
    ("der Bademantel", "халат"),
    ("die Strumpfhose", "колготки"),
    ("der Badeanzug", "купальник"),
    ("der Pyjama", "пижама"),
    ("die Weste", "жилет"),
]

class StartScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("Тест: Одежда на немецком")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg="#f0f0f0")
        self.root.bind("<Escape>", lambda e: root.destroy())

        frame = tk.Frame(root, bg="#f0f0f0")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            frame, text="Выберите количество вопросов:",
            font=("Arial", 60, "bold"), bg="#f0f0f0", fg="#2c3e50"
        ).pack(pady=40)

        for n in [10, 20, 30]:
            tk.Button(
                frame, text=f"{n} вопросов", font=("Arial", 48),
                width=15, height=1,
                command=lambda n=n: self.start_quiz(n),
                bg="#3498db", fg="white"
            ).pack(pady=20)

    def start_quiz(self, num_questions):
        selected = random.sample(WORDS, min(num_questions, len(WORDS)))
        self.root.destroy()
        launch_quiz(selected)

def launch_quiz(question_list):
    root = tk.Tk()
    app = QuizApp(root, question_list)
    root.mainloop()

class QuizApp:
    def __init__(self, root, question_list):
        self.root = root
        self.root.title("Тест: Одежда на немецком")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg="#f0f0f0")
        self.root.bind("<Escape>", lambda e: root.destroy())

        self.questions = question_list
        self.score = 0
        self.current_index = 0
        self.setup_ui()

    def setup_ui(self):
        self.main_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.question_label = tk.Label(
            self.main_frame, text="", font=("Arial", 54, "bold"),
            bg="#f0f0f0", fg="#333", wraplength=1400, justify="center"
        )
        self.question_label.pack(pady=40)

        self.option_buttons = []
        for i in range(3):
            btn = tk.Button(
                self.main_frame, text="", font=("Arial", 48), width=30, height=1,
                command=lambda i=i: self.check_answer(i),
                bg="#e0e0e0", activebackground="#d0d0d0", relief="solid", bd=2
            )
            btn.pack(pady=15)
            self.option_buttons.append(btn)

        self.next_button = tk.Button(
            self.main_frame, text="Далее", font=("Arial", 36),
            state="disabled", command=self.next_question,
            bg="#2ecc71", fg="white", width=12
        )
        self.next_button.pack(pady=30)

        self.update_question()

    def update_question(self):
        if self.current_index >= len(self.questions):
            self.show_result()
            return

        german_word, correct_ru = self.questions[self.current_index]

        # Формируем 3 варианта: 1 правильный + 2 случайных других
        all_words = [w for w, _ in self.questions]
        distractors = [w for w in all_words if w != german_word]
        random.shuffle(distractors)
        options = [german_word, distractors[0], distractors[1]]
        random.shuffle(options)

        self.question_label.config(text=f"Вопрос {self.current_index + 1} из {len(self.questions)}\n\nЧто означает: «{german_word}»?")
        speak_german(german_word)

        for i, opt in enumerate(options):
            self.option_buttons[i].config(
                text=opt, state="normal", bg="#e0e0e0", fg="black"
            )

        self.correct_option = german_word
        self.answered = False
        self.next_button.config(state="disabled")

    def check_answer(self, choice):
        if self.answered:
            return
        self.answered = True

        selected = self.option_buttons[choice].cget("text")
        correct = (selected == self.correct_option)

        if correct:
            self.score += 1
            self.option_buttons[choice].config(bg="#c3e6cb", fg="#155724")
            play_sound(True)
        else:
            self.option_buttons[choice].config(bg="#f5c6cb", fg="#721c24")
            # Подсветить правильный
            for btn in self.option_buttons:
                if btn.cget("text") == self.correct_option:
                    btn.config(bg="#c3e6cb", fg="#155724")
            play_sound(False)

        for btn in self.option_buttons:
            btn.config(state="disabled")
        self.next_button.config(state="normal")

    def next_question(self):
        self.current_index += 1
        self.update_question()

    def show_result(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        result = f"Тест завершён!\n\nВаш результат:\n{self.score} из {len(self.questions)}"
        tk.Label(
            self.main_frame, text=result, font=("Arial", 60, "bold"),
            bg="#f0f0f0", fg="#2c3e50", justify="center"
        ).pack(pady=80)
        tk.Button(
            self.main_frame, text="Завершить", font=("Arial", 40),
            command=self.root.destroy, bg="#e74c3c", fg="white", width=12
        ).pack(pady=40)

# === Запуск ===
if __name__ == "__main__":
    root = tk.Tk()
    StartScreen(root)
    root.mainloop()