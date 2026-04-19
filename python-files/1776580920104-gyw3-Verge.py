import tkinter as tk
from tkinter import ttk, messagebox
import random
import json
import os

# База данных неправильных глаголов (Infinitive - Past Simple - Past Participle)
VERBS_DB = {
    "begin": ["began", "begun"],
    "break": ["broke", "broken"],
    "bring": ["brought", "brought"],
    "buy": ["bought", "bought"],
    "choose": ["chose", "chosen"],
    "come": ["came", "come"],
    "do": ["did", "done"],
    "drink": ["drank", "drunk"],
    "drive": ["drove", "driven"],
    "eat": ["ate", "eaten"],
    "fall": ["fell", "fallen"],
    "feel": ["felt", "felt"],
    "find": ["found", "found"],
    "fly": ["flew", "flown"],
    "forget": ["forgot", "forgotten"],
    "get": ["got", "gotten"],
    "give": ["gave", "given"],
    "go": ["went", "gone"],
    "have": ["had", "had"],
    "hear": ["heard", "heard"],
    "keep": ["kept", "kept"],
    "know": ["knew", "known"],
    "leave": ["left", "left"],
    "make": ["made", "made"],
    "meet": ["met", "met"],
    "read": ["read", "read"],
    "ring": ["rang", "rung"],
    "run": ["ran", "run"],
    "say": ["said", "said"],
    "see": ["saw", "seen"],
    "sell": ["sold", "sold"],
    "sing": ["sang", "sung"],
    "sit": ["sat", "sat"],
    "sleep": ["slept", "slept"],
    "speak": ["spoke", "spoken"],
    "stand": ["stood", "stood"],
    "swim": ["swam", "swum"],
    "take": ["took", "taken"],
    "teach": ["taught", "taught"],
    "tell": ["told", "told"],
    "think": ["thought", "thought"],
    "understand": ["understood", "understood"],
    "wear": ["wore", "worn"],
    "win": ["won", "won"],
    "write": ["wrote", "written"],
}

# Уровни сложности
LEVELS = {
    "Легкий (20 глаголов)": list(VERBS_DB.keys())[:20],
    "Средний (30 глаголов)": list(VERBS_DB.keys())[:30],
    "Сложный (все глаголы)": list(VERBS_DB.keys()),
}


class IrregularVerbsTrainer:
    def __init__(self, root):
        self.root = root
        self.root.title("Тренажёр неправильных глаголов")
        self.root.geometry("700x600")
        self.root.resizable(False, False)

        # Переменные состояния
        self.current_verb = None
        self.current_form = None  # 'past' или 'participle'
        self.score = 0
        self.total = 0
        self.current_level = "Средний (30 глаголов)"
        self.verbs_list = LEVELS[self.current_level].copy()
        self.remaining_verbs = self.verbs_list.copy()
        random.shuffle(self.remaining_verbs)

        # Статистика по глаголам (для отслеживания ошибок)
        self.stats = {verb: {"correct": 0, "wrong": 0} for verb in VERBS_DB.keys()}
        self.load_stats()

        self.setup_ui()
        self.next_question()

    def setup_ui(self):
        # Стиль
        style = ttk.Style()
        style.theme_use('clam')

        # Заголовок
        title_label = tk.Label(self.root, text="🏆 Тренажёр неправильных глаголов 🏆",
                               font=("Arial", 20, "bold"), fg="#2c3e50")
        title_label.pack(pady=15)

        # Рамка для уровня сложности
        level_frame = tk.Frame(self.root)
        level_frame.pack(pady=10)

        tk.Label(level_frame, text="Уровень сложности:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        self.level_var = tk.StringVar(value=self.current_level)
        level_menu = ttk.Combobox(level_frame, textvariable=self.level_var, values=list(LEVELS.keys()),
                                  state="readonly", width=20, font=("Arial", 11))
        level_menu.pack(side=tk.LEFT, padx=5)
        level_menu.bind("<<ComboboxSelected>>", self.change_level)

        # Рамка для счёта
        score_frame = tk.Frame(self.root)
        score_frame.pack(pady=10)

        self.score_label = tk.Label(score_frame, text="Счёт: 0 / 0", font=("Arial", 14, "bold"), fg="#27ae60")
        self.score_label.pack()

        # Рамка для вопроса
        question_frame = tk.Frame(self.root, bg="#ecf0f1", relief=tk.RAISED, bd=2)
        question_frame.pack(pady=30, padx=20, fill=tk.BOTH)

        self.question_label = tk.Label(question_frame, text="", font=("Arial", 18), bg="#ecf0f1", height=3)
        self.question_label.pack()

        # Рамка для ввода ответа
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=20)

        tk.Label(input_frame, text="Ваш ответ:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        self.answer_entry = tk.Entry(input_frame, font=("Arial", 14), width=25)
        self.answer_entry.pack(side=tk.LEFT, padx=5)
        self.answer_entry.bind("<Return>", lambda event: self.check_answer())

        # Кнопки
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)

        self.check_button = tk.Button(button_frame, text="✅ Проверить", command=self.check_answer,
                                      bg="#3498db", fg="white", font=("Arial", 12), padx=20, pady=5)
        self.check_button.pack(side=tk.LEFT, padx=10)

        self.next_button = tk.Button(button_frame, text="➡ Следующий", command=self.next_question,
                                     bg="#2ecc71", fg="white", font=("Arial", 12), padx=20, pady=5, state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT, padx=10)

        self.reset_button = tk.Button(button_frame, text="🔄 Сброс", command=self.reset_game,
                                      bg="#e74c3c", fg="white", font=("Arial", 12), padx=20, pady=5)
        self.reset_button.pack(side=tk.LEFT, padx=10)

        # Рамка для результата
        result_frame = tk.Frame(self.root, bg="#f8f9fa", relief=tk.SUNKEN, bd=1)
        result_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

        self.result_text = tk.Text(result_frame, height=8, font=("Arial", 11), wrap=tk.WORD, bg="#f8f9fa")
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Статусная строка
        self.status_label = tk.Label(self.root, text="Готов к работе!", font=("Arial", 10), fg="#7f8c8d")
        self.status_label.pack(side=tk.BOTTOM, pady=5)

        # Фокус на поле ввода
        self.answer_entry.focus()

    def change_level(self, event=None):
        new_level = self.level_var.get()
        if new_level != self.current_level:
            self.current_level = new_level
            self.reset_game()

    def next_question(self):
        # Проверяем, остались ли глаголы
        if not self.remaining_verbs:
            self.finish_game()
            return

        self.current_verb = self.remaining_verbs[0]
        self.current_form = random.choice(['past', 'participle'])

        if self.current_form == 'past':
            question_text = f"Напишите Past Simple для глагола:\n\n{self.current_verb.upper()}"
            self.correct_answer = VERBS_DB[self.current_verb][0]
        else:
            question_text = f"Напишите Past Participle для глагола:\n\n{self.current_verb.upper()}"
            self.correct_answer = VERBS_DB[self.current_verb][1]

        self.question_label.config(text=question_text)
        self.answer_entry.delete(0, tk.END)
        self.answer_entry.config(state=tk.NORMAL)
        self.check_button.config(state=tk.NORMAL)
        self.next_button.config(state=tk.DISABLED)
        self.result_text.delete(1.0, tk.END)
        self.answer_entry.focus()
        self.status_label.config(text=f"Отвечаем на вопрос... (Осталось: {len(self.remaining_verbs)})")

    def check_answer(self):
        user_answer = self.answer_entry.get().strip().lower()

        if not user_answer:
            messagebox.showwarning("Внимание", "Пожалуйста, введите ответ!")
            return

        if user_answer == self.correct_answer.lower():
            # Правильный ответ
            self.score += 1
            self.stats[self.current_verb]["correct"] += 1
            self.result_text.insert(tk.END, f"✅ Правильно! '{self.correct_answer}' - верный ответ.\n\n", "green")
            self.result_text.tag_config("green", foreground="#27ae60")
            self.status_label.config(text="Отлично! Правильный ответ!")
        else:
            # Неправильный ответ
            self.stats[self.current_verb]["wrong"] += 1
            self.result_text.insert(tk.END, f"❌ Неправильно!\n", "red")
            self.result_text.insert(tk.END, f"Ваш ответ: {user_answer}\n", "red")
            self.result_text.insert(tk.END, f"Правильный ответ: {self.correct_answer}\n\n", "blue")
            self.result_text.tag_config("red", foreground="#e74c3c")
            self.result_text.tag_config("blue", foreground="#3498db")
            self.status_label.config(text="Неправильно! Запомните правильную форму.")

        self.total += 1
        self.score_label.config(text=f"Счёт: {self.score} / {self.total}")

        # Убираем текущий глагол из списка оставшихся
        if self.remaining_verbs:
            self.remaining_verbs.pop(0)

        # Блокируем поле ввода и кнопку проверки
        self.answer_entry.config(state=tk.DISABLED)
        self.check_button.config(state=tk.DISABLED)
        self.next_button.config(state=tk.NORMAL)

        self.save_stats()

    def finish_game(self):
        percent = (self.score / self.total * 100) if self.total > 0 else 0
        messagebox.showinfo("Поздравляем!",
                            f"🎉 Тренировка завершена! 🎉\n\n"
                            f"Правильных ответов: {self.score} из {self.total}\n"
                            f"Процент: {percent:.1f}%\n\n"
                            f"Нажмите 'Сброс' для новой тренировки.")

        # Показываем глаголы, в которых были ошибки
        wrong_verbs = {verb: data for verb, data in self.stats.items()
                       if data["wrong"] > 0 and verb in self.verbs_list}

        if wrong_verbs:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "📝 Глаголы, требующие повторения:\n\n")
            for verb, data in wrong_verbs.items():
                self.result_text.insert(tk.END, f"• {verb}: {data['wrong']} ошибок\n")

    def reset_game(self):
        self.current_level = self.level_var.get()
        self.verbs_list = LEVELS[self.current_level].copy()
        self.remaining_verbs = self.verbs_list.copy()
        random.shuffle(self.remaining_verbs)

        self.score = 0
        self.total = 0
        self.score_label.config(text="Счёт: 0 / 0")
        self.result_text.delete(1.0, tk.END)
        self.status_label.config(text=f"Игра сброшена. Уровень: {self.current_level}")

        self.next_question()

    def save_stats(self):
        try:
            with open("verb_stats.json", "w", encoding="utf-8") as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
        except:
            pass

    def load_stats(self):
        try:
            if os.path.exists("verb_stats.json"):
                with open("verb_stats.json", "r", encoding="utf-8") as f:
                    loaded_stats = json.load(f)
                    for verb in self.stats:
                        if verb in loaded_stats:
                            self.stats[verb] = loaded_stats[verb]
        except:
            pass


def main():
    root = tk.Tk()
    app = IrregularVerbsTrainer(root)
    root.mainloop()


if __name__ == "__main__":
    main()