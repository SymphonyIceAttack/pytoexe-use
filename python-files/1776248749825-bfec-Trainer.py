import tkinter as tk
from tkinter import messagebox
import random
import sys
import os


def resource_path(relative_path):
    """Получить путь к файлу, работает как для .py, так и для .exe"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class MultiplicationTrainer:
    def __init__(self, root):
        self.root = root
        self.root.title("Тренажёр таблицы умножения")

        # Центрирование окна
        window_width = 500
        window_height = 500
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.root.resizable(False, False)

        # Переменные состояния
        self.correct_answers = 0
        self.total_answers = 0
        self.difficulty = 1

        # Создание интерфейса
        self.create_menu()
        self.create_main_frame()

        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_menu(self):
        """Создание верхнего меню"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        mode_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Режим", menu=mode_menu)
        mode_menu.add_command(label="Лёгкий (1-5)", command=lambda: self.set_difficulty(1))
        mode_menu.add_command(label="Средний (1-9)", command=lambda: self.set_difficulty(2))
        mode_menu.add_command(label="Сложный (1-12)", command=lambda: self.set_difficulty(3))
        mode_menu.add_separator()
        mode_menu.add_command(label="Выход", command=self.on_closing)

        stats_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Статистика", menu=stats_menu)
        stats_menu.add_command(label="Показать статистику", command=self.show_stats)
        stats_menu.add_command(label="Сбросить статистику", command=self.reset_stats)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)

    def create_main_frame(self):
        """Создание основного интерфейса"""
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        title_label = tk.Label(
            main_frame,
            text="ТРЕНАЖЁР ТАБЛИЦЫ УМНОЖЕНИЯ",
            font=("Arial", 18, "bold"),
            bg="#f0f0f0",
            fg="#333333"
        )
        title_label.pack(pady=10)

        score_frame = tk.Frame(main_frame, bg="#f0f0f0")
        score_frame.pack(pady=10)

        self.score_label = tk.Label(
            score_frame,
            text="Правильных ответов: 0 / 0 (0%)",
            font=("Arial", 12),
            bg="#f0f0f0",
            fg="#555555"
        )
        self.score_label.pack()

        question_frame = tk.Frame(main_frame, bg="#ffffff", relief=tk.RAISED, bd=2)
        question_frame.pack(pady=30, padx=20, fill=tk.BOTH)

        self.question_label = tk.Label(
            question_frame,
            text="5 × 3 = ?",
            font=("Arial", 36, "bold"),
            bg="#ffffff",
            fg="#0066cc"
        )
        self.question_label.pack(pady=40)

        input_frame = tk.Frame(main_frame, bg="#f0f0f0")
        input_frame.pack(pady=20)

        tk.Label(
            input_frame,
            text="Ваш ответ:",
            font=("Arial", 14),
            bg="#f0f0f0"
        ).pack(side=tk.LEFT, padx=10)

        self.answer_entry = tk.Entry(
            input_frame,
            font=("Arial", 14),
            width=10,
            justify="center"
        )
        self.answer_entry.pack(side=tk.LEFT, padx=10)
        self.answer_entry.bind("<Return>", self.check_answer)

        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.pack(pady=20)

        self.check_button = tk.Button(
            button_frame,
            text="Проверить",
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=5,
            command=self.check_answer
        )
        self.check_button.pack(side=tk.LEFT, padx=10)

        self.next_button = tk.Button(
            button_frame,
            text="Следующий пример",
            font=("Arial", 12),
            bg="#2196F3",
            fg="white",
            padx=20,
            pady=5,
            command=self.new_question,
            state=tk.DISABLED
        )
        self.next_button.pack(side=tk.LEFT, padx=10)

        self.new_question()

    def set_difficulty(self, level):
        """Установка уровня сложности"""
        self.difficulty = level
        self.new_question()
        difficulty_names = {1: "Лёгкий (1-5)", 2: "Средний (1-9)", 3: "Сложный (1-12)"}
        messagebox.showinfo("Режим", f"Выбран режим: {difficulty_names[level]}")

    def generate_question(self):
        """Генерация нового примера"""
        if self.difficulty == 1:
            max_num = 5
        elif self.difficulty == 2:
            max_num = 9
        else:
            max_num = 12

        self.num1 = random.randint(1, max_num)
        self.num2 = random.randint(1, max_num)
        self.correct_answer = self.num1 * self.num2
        self.question_label.config(text=f"{self.num1} × {self.num2} = ?")

    def check_answer(self, event=None):
        """Проверка ответа пользователя"""
        try:
            user_answer = int(self.answer_entry.get())
            self.total_answers += 1

            if user_answer == self.correct_answer:
                self.correct_answers += 1
                messagebox.showinfo("Результат", "✅ Правильно! Молодец!")
                self.question_label.config(fg="#00cc00")
                self.root.after(500, lambda: self.question_label.config(fg="#0066cc"))
            else:
                messagebox.showerror(
                    "Результат",
                    f"❌ Неправильно!\n\nПравильный ответ: {self.correct_answer}\n\n{self.num1} × {self.num2} = {self.correct_answer}"
                )
                self.question_label.config(fg="#ff0000")
                self.root.after(500, lambda: self.question_label.config(fg="#0066cc"))

            percentage = (self.correct_answers / self.total_answers) * 100
            self.score_label.config(
                text=f"Правильных ответов: {self.correct_answers} / {self.total_answers} ({percentage:.1f}%)"
            )

            self.answer_entry.config(state=tk.DISABLED)
            self.check_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.NORMAL)
            self.next_button.focus()

        except ValueError:
            messagebox.showwarning("Ошибка", "Пожалуйста, введите число!")

    def new_question(self):
        """Генерация нового вопроса"""
        self.answer_entry.delete(0, tk.END)
        self.answer_entry.config(state=tk.NORMAL)
        self.check_button.config(state=tk.NORMAL)
        self.next_button.config(state=tk.DISABLED)
        self.generate_question()
        self.answer_entry.focus()

    def show_stats(self):
        """Показать статистику"""
        if self.total_answers == 0:
            messagebox.showinfo("Статистика", "Нет данных для отображения.\nРешите хотя бы один пример!")
            return

        percentage = (self.correct_answers / self.total_answers) * 100

        if percentage == 100:
            grade = "🌟 Отлично! Ты знаешь таблицу умножения на 5!"
        elif percentage >= 90:
            grade = "👍 Очень хорошо!"
        elif percentage >= 70:
            grade = "👌 Неплохо, но есть к чему стремиться."
        elif percentage >= 50:
            grade = "😊 Учи дальше, ты сможешь!"
        else:
            grade = "💪 Нужно больше практики!"

        stats_text = f"""
📊 Ваша статистика:

✅ Правильных ответов: {self.correct_answers}
❌ Неправильных ответов: {self.total_answers - self.correct_answers}
📈 Всего решено: {self.total_answers}
🎯 Процент правильных: {percentage:.1f}%

{grade}
        """
        messagebox.showinfo("Статистика", stats_text)

    def reset_stats(self):
        """Сброс статистики"""
        if messagebox.askyesno("Сброс статистики", "Вы уверены, что хотите сбросить статистику?"):
            self.correct_answers = 0
            self.total_answers = 0
            self.score_label.config(text="Правильных ответов: 0 / 0 (0%)")
            messagebox.showinfo("Сброс", "Статистика успешно сброшена!")

    def show_about(self):
        """О программе"""
        about_text = """
Тренажёр таблицы умножения
Версия 1.0 (EXE версия)

Лёгкий режим: числа от 1 до 5
Средний режим: числа от 1 до 9
Сложный режим: числа от 1 до 12

Удачи в обучении! 🎓
        """
        messagebox.showinfo("О программе", about_text)

    def on_closing(self):
        """Обработка закрытия программы"""
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MultiplicationTrainer(root)
    root.mainloop()