import tkinter as tk
from tkinter import messagebox
import random
import pygame
import pyttsx3
import threading

# Инициализация звука
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Инициализация TTS
tts_engine = pyttsx3.init()
voices = tts_engine.getProperty('voices')
# Попытка выбрать немецкий голос (если есть)
for voice in voices:
    if 'de' in voice.id or 'german' in voice.name.lower():
        tts_engine.setProperty('voice', voice.id)
        break
# Иначе оставим по умолчанию

def speak_text(text):
    # Запуск в отдельном потоке, чтобы не блокировать GUI
    def _speak():
        tts_engine.say(text)
        tts_engine.runAndWait()
    threading.Thread(target=_speak, daemon=True).start()

def play_sound(correct):
    # Генерация короткого звука через pygame (не файлы)
    freq = 800 if correct else 400
    duration = 200  # мс
    sample_rate = 22050
    n_samples = int(duration * sample_rate / 1000)
    buf = bytearray()
    for i in range(n_samples):
        t = float(i) / sample_rate
        val = int(32767.0 * (0.5 * (1 + (t * freq * 2 * 3.14159) % 2 - 1)))  # простой синусоидальный пилообразный
        buf.append(val & 0xff)
        buf.append((val >> 8) & 0xff)
    sound = pygame.mixer.Sound(buffer=bytes(buf))
    sound.play()

# База вопросов: (немецкое слово, правильный перевод, [варианты с русским переводом])
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

# Перемешаем вопросы (опционально)
random.shuffle(QUESTIONS)

class ClothingQuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Тест по немецкому: Одежда")
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", lambda e: root.attributes('-fullscreen', False))
        self.score = 0
        self.current_index = 0
        self.setup_ui()

    def setup_ui(self):
        self.main_frame = tk.Frame(self.root, bg="#f0f0f0", padx=40, pady=40)
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.question_label = tk.Label(
            self.main_frame, text="", font=("Arial", 24, "bold"), bg="#f0f0f0", wraplength=900
        )
        self.question_label.pack(pady=20)

        self.option_buttons = []
        for i in range(3):
            btn = tk.Button(
                self.main_frame, text="", font=("Arial", 18), width=60, height=2,
                command=lambda i=i: self.check_answer(i),
                bg="#e0e0e0", activebackground="#d0d0d0", relief="solid", bd=2
            )
            btn.pack(pady=10)
            self.option_buttons.append(btn)

        self.next_button = tk.Button(
            self.main_frame, text="Далее", font=("Arial", 16), state="disabled",
            command=self.next_question, bg="#4CAF50", fg="white"
        )
        self.next_button.pack(pady=20)

        self.update_question()

    def update_question(self):
        if self.current_index >= len(QUESTIONS):
            self.show_result()
            return

        german_word, correct_ru, options = QUESTIONS[self.current_index]
        self.question_label.config(text=f"Вопрос {self.current_index + 1} из {len(QUESTIONS)}\n\nКак переводится: «{german_word}»?")
        speak_text(german_word)  # озвучиваем слово

        for i, opt in enumerate(options):
            self.option_buttons[i].config(
                text=opt, state="normal", bg="#e0e0e0",
                fg="black", relief="solid", bd=2
            )

        self.correct_answer_index = options.index(f"{german_word.split()[1]} ({correct_ru})")
        self.answered = False
        self.next_button.config(state="disabled")

    def check_answer(self, choice):
        if self.answered:
            return
        self.answered = True

        correct = (choice == self.correct_answer_index)
        if correct:
            self.score += 1
            self.option_buttons[choice].config(bg="#d4edda", fg="#155724")
            play_sound(True)
        else:
            self.option_buttons[choice].config(bg="#f8d7da", fg="#721c24")
            self.option_buttons[self.correct_answer_index].config(bg="#d4edda", fg="#155724")
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
        result_text = f"Тест завершён!\n\nВаш результат: {self.score} из {len(QUESTIONS)}"
        tk.Label(
            self.main_frame, text=result_text, font=("Arial", 28, "bold"),
            bg="#f0f0f0", fg="#2c3e50"
        ).pack(pady=40)
        tk.Button(
            self.main_frame, text="Завершить", font=("Arial", 18),
            command=self.root.destroy, bg="#e74c3c", fg="white"
        ).pack(pady=20)

if __name__ == "__main__":
    root = tk.Tk()
    app = ClothingQuizApp(root)
    root.mainloop()