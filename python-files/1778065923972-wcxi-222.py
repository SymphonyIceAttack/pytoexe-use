import tkinter as tk
from tkinter import messagebox

class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Индекс комплаентности")
        self.root.geometry("3000x2000")

        # Данные теста: вопросы и варианты ответов
        self.questions = [
            {
                "question": "Я чувствую себя в хорошей физической форме",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "question": "Я способен справляться со стрессом в повседневной жизни",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "question": "Я чувствую, что могу контролировать свою жизнь",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "question": "Я доволен своим лечением",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "question": "Я активно включен в обсуждение своего лечения с врачом",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "question": "Я удовлетворен тем, как справляюсь со своей болезнью",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "question": "Я испытываю беспокойство по поводу лечения",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "question": "Я часто думаю о своей болезни",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "question": "Я хорошо сплю ночью",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "question": "Я нахожу время для отдыха и расслабления",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "question": "Я забочусь о своем питании",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "question": "Я чувствую поддержку со стороны семьи и друзей",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "question": "Я слежу за своей физической активностью",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "question": "Я чувствую, что врач слушает и учитывает мои пожелания",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "question": "Я часто чувствую печаль и уныние",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "question": "Я рассматриваю разные источники информации о своей болезни",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "question": "Я участвую в группах поддержки или общении с другими пациентами",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "question": "Я чувствую, что моя болезнь мешает мне жить полной жизнью",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "question": "Я готов следовать рекомендациям врача",
                "options": ["1", "2", "3", "4", "5"]
            },
            {
                "question": "Я верю в свою способность выздороветь",
                "options": ["1", "2", "3", "4", "5"]
            }
        ]

        self.current_question = 0
        self.score = 0

        # Создание виджетов
        self.create_widgets()
        self.show_question()

    def create_widgets(self):
        # Метка для вопроса
        self.question_label = tk.Label(
            self.root,
            text="",
            wraplength=450,
            font=("Arial", 14)
        )
        self.question_label.pack(pady=20)

        # Переменная для хранения выбранного ответа
        self.answer_var = tk.IntVar()

        # Фрейм для вариантов ответов
        self.options_frame = tk.Frame(self.root)
        self.options_frame.pack(pady=10)

        # Кнопки вариантов ответов (будут созданы позже)
        self.option_buttons = []

        # Кнопка «Следующий вопрос»
        self.next_button = tk.Button(
            self.root,
            text="Следующий вопрос",
            command=self.next_question,
            bg="lightblue",
            font=("Arial", 12)
        )
        self.next_button.pack(pady=20)

        # Метка для отображения текущего счёта
        self.score_label = tk.Label(
            self.root,
            text="Баллы: 0",
            font=("Arial", 12)
        )
        self.score_label.pack()

    def show_question(self):
        # Очистка предыдущих вариантов ответов
        for widget in self.options_frame.winfo_children():
            widget.destroy()

        # Отображение текущего вопроса
        question_data = self.questions[self.current_question]
        self.question_label.config(text=question_data["question"])

        # Создание кнопок вариантов ответов
        self.option_buttons.clear()
        for i, option in enumerate(question_data["options"]):
            # Номер ответа = количество баллов
            value = i + 1

            button = tk.Radiobutton(
                self.options_frame,
                text=option,
                variable=self.answer_var,
                value=value,
                wraplength=400,
                anchor="w",
                justify="left",
                font=("Arial", 12),
                pady=5
            )
            button.pack(anchor="w")
            self.option_buttons.append(button)

    def next_question(self):
        # Получение выбранного ответа (номер варианта)
        selected_answer = self.answer_var.get()

        if selected_answer:
            # Добавление баллов (номер ответа = количество баллов)
            self.score += selected_answer
            self.score_label.config(text=f"Баллы: {self.score}")

            # Переход к следующему вопросу или завершение теста
            self.current_question += 1
            if self.current_question < len(self.questions):
                self.show_question()
            else:
                self.show_result()
        else:
            messagebox.showwarning("Внимание", "Пожалуйста, выберите ответ!")

    def show_result(self):
        # Скрываем элементы теста
        self.question_label.pack_forget()
        self.options_frame.pack_forget()
        self.next_button.pack_forget()
        self.score_label.pack_forget()

        # Показываем результат
        if self.score < 60:
            result_text = f"Низкий уровень комплаентности\n\nВаш итоговый счёт: {self.score} баллов\n\nПациент не настроен на лечение\n\nВоспринимает информацию негативно\n\nРекомендуется дополнительная поддержка и мотивация"
            result_label = tk.Label(
                self.root,
                text=result_text,
                font=("Arial", 16, "bold"),
                justify="center"
            )
            result_label.pack(expand=True)
        elif self.score > 60 and self.score < 80:
            result_text = f"Средний уровень комплаентности\n\nВаш итоговый счёт: {self.score} баллов\n\nПациент имеет некоторые проблемы\n\nГотов к сотрудничеству\n\nНеобходим диалог и обсуждение вопросов"
            result_label = tk.Label(
                self.root,
                text=result_text,
                font=("Arial", 16, "bold"),
                justify="center"
            )
            result_label.pack(expand=True)
        else:
            result_text = f"Высокий уровень комплаентности\n\nВаш итоговый счёт: {self.score} баллов\n\nПациент активно участвует в процессе лечения\n\nВоспринимает информацию положительно\n\nРекомендуется поддерживать текущий уровень мотивации и информированности"
            result_label = tk.Label(
                self.root,
                text=result_text,
                font=("Arial", 16, "bold"),
                justify="center"
            )
            result_label.pack(expand=True)

# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()