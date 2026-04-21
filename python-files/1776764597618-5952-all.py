import tkinter as tk
from tkinter import messagebox, ttk
import json
import os

# База данных вопросов (можно расширять)
tickets_data = {
    1: {
        "name": "Основы охраны труда",
        "questions": [
            {"text": "Что означает 'Охрана труда'?", 
             "options": ["Система сохранения жизни и здоровья работников", "Набор штрафов для сотрудников", "Расписание работы"],
             "correct": 0},
            {"text": "Кто обязан обеспечить безопасные условия труда?",
             "options": ["Работник", "Работодатель", "Государственная инспекция"],
             "correct": 1},
            {"text": "Что такое 'вредный производственный фактор'?",
             "options": ["Фактор, который вызывает стресс", "Фактор, который может привести к заболеванию", "Любой фактор на работе"],
             "correct": 1},
            {"text": "Как часто проводится обучение по охране труда?",
             "options": ["Один раз при приеме на работу", "Не реже одного раза в 3 года", "Каждый месяц"],
             "correct": 1},
            {"text": "Что должен сделать работник при несчастном случае?",
             "options": ["Скрыть происшествие", "Сообщить руководителю и оказать первую помощь", "Продолжить работу"],
             "correct": 1},
            {"text": "Какая ответственность за нарушение охраны труда?",
             "options": ["Только дисциплинарная", "Дисциплинарная, административная, уголовная", "Никакой"],
             "correct": 1},
            {"text": "Что такое первичный инструктаж?",
             "options": ["Перед началом работы с новым сотрудником", "Раз в полгода", "После аварии"],
             "correct": 0},
            {"text": "Какой документ фиксирует инструктаж?",
             "options": ["Трудовой договор", "Журнал регистрации инструктажей", "Приказ директора"],
             "correct": 1},
            {"text": "Кто проводит вводный инструктаж?",
             "options": ["Специалист по охране труда", "Любой рабочий", "Бухгалтер"],
             "correct": 0},
            {"text": "Что относится к СИЗ?",
             "options": ["Каска и перчатки", "Стул", "Компьютер"],
             "correct": 0}
        ]
    },
    2: {
        "name": "Пожарная безопасность",
        "questions": [
            {"text": "Как потушить загоревшийся электроприбор?",
             "options": ["Водой", "Порошковым или углекислотным огнетушителем", "Накрыть одеялом"],
             "correct": 1},
            {"text": "Что запрещено при запахе газа?",
             "options": ["Открыть окно", "Включать свет или электроприборы", "Позвонить аварийной службе"],
             "correct": 1},
            {"text": "Можно ли работать с электроинструментом в сыром помещении без перчаток?",
             "options": ["Да", "Нет", "Только с разрешения"],
             "correct": 1},
            {"text": "Какой огнетушитель нельзя использовать при пожаре электроустановок?",
             "options": ["Порошковый", "Углекислотный", "Водный"],
             "correct": 2},
            {"text": "Что означает знак с перечёркнутой каплей воды?",
             "options": ["Нельзя тушить водой", "Выход", "Осторожно, мокрый пол"],
             "correct": 0},
            {"text": "Как часто проверяют изоляцию проводов?",
             "options": ["Раз в год", "Раз в 5 лет", "Никогда"],
             "correct": 0},
            {"text": "Первая помощь при поражении током?",
             "options": ["Обесточить пострадавшего", "Полить водой", "Сделать укол"],
             "correct": 0},
            {"text": "Можно ли оставлять обогреватели без присмотра?",
             "options": ["Да", "Нет", "Только ночью"],
             "correct": 1},
            {"text": "Что делать при возгорании масла на плите?",
             "options": ["Залить водой", "Накрыть крышкой/тканью", "Вылить на пол"],
             "correct": 1},
            {"text": "Номер пожарной службы?",
             "options": ["101 или 112", "02", "03"],
             "correct": 0}
        ]
    },
    3: {
        "name": "Первая помощь",
        "questions": [
            {"text": "При артериальном кровотечении (алая кровь фонтаном) нужно:",
             "options": ["Наложить жгут выше раны", "Наложить тугую повязку", "Опустить конечность"],
             "correct": 0},
            {"text": "Как долго можно держать жгут летом?",
             "options": ["Не более 30 минут", "До 2 часов", "Сколько угодно"],
             "correct": 0},
            {"text": "При ожоге кипятком необходимо:",
             "options": ["Смазать маслом", "Под холодную воду на 10-20 мин", "Проколоть пузыри"],
             "correct": 1},
            {"text": "Признак клинической смерти:",
             "options": ["Нет дыхания и пульса", "Температура 36.6", "Красные глаза"],
             "correct": 0},
            {"text": "Глубина надавливаний при массаже сердца взрослому:",
             "options": ["1-2 см", "5-6 см", "10 см"],
             "correct": 1},
            {"text": "При переломе прежде всего:",
             "options": ["Вправить кость", "Обеспечить неподвижность", "Приложить тепло"],
             "correct": 1},
            {"text": "Что нельзя делать при попадании предмета в дыхательные пути?",
             "options": ["Запрокидывать голову назад", "Наклонить вперёд и ударить по спине", "Вызвать скорую"],
             "correct": 0},
            {"text": "При обмороке нужно:",
             "options": ["Поднять ноги выше головы", "Посадить на стул", "Облить водой"],
             "correct": 0},
            {"text": "С чего начинается сердечно-легочная реанимация?",
             "options": ["30 надавливаний на грудину", "2 вдоха", "Проверки пульса"],
             "correct": 0},
            {"text": "Положение для пострадавшего без сознания, но дышащего:",
             "options": ["На спине", "Устойчивое боковое положение", "Сидя"],
             "correct": 1}
        ]
    }
}

class OTTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Тестирование по охране труда")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Переменные состояния
        self.current_ticket = None
        self.current_question_index = 0
        self.user_answers = []
        self.total_questions = 10
        
        # Создаем главный экран
        self.show_ticket_selection()
    
    def clear_window(self):
        """Очищает окно от всех виджетов"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_ticket_selection(self):
        """Экран выбора билета"""
        self.clear_window()
        
        # Заголовок
        title = tk.Label(self.root, text="Выберите билет для тестирования", 
                        font=("Arial", 20, "bold"), fg="#2c3e50")
        title.pack(pady=30)
        
        # Фрейм для кнопок билетов
        frame_buttons = tk.Frame(self.root)
        frame_buttons.pack(pady=20)
        
        # Создаем кнопки для каждого билета
        for ticket_num, ticket_info in tickets_data.items():
            btn = tk.Button(frame_buttons, 
                          text=f"Билет №{ticket_num}\n{ticket_info['name']}",
                          font=("Arial", 14),
                          bg="#3498db",
                          fg="white",
                          activebackground="#2980b9",
                          width=25,
                          height=3,
                          command=lambda num=ticket_num: self.start_test(num))
            btn.pack(pady=10)
        
        # Кнопка выхода
        exit_btn = tk.Button(self.root, text="Выйти из программы",
                           font=("Arial", 12),
                           bg="#e74c3c",
                           fg="white",
                           command=self.root.quit,
                           width=20,
                           height=2)
        exit_btn.pack(pady=30)
        
        # Информация внизу
        info = tk.Label(self.root, text="Всего билетов: " + str(len(tickets_data)) + 
                       " | В каждом билете 10 вопросов",
                       font=("Arial", 10), fg="#7f8c8d")
        info.pack(side="bottom", pady=10)
    
    def start_test(self, ticket_num):
        """Запускает тестирование по выбранному билету"""
        self.current_ticket = ticket_num
        self.current_question_index = 0
        self.user_answers = []
        self.show_question()
    
    def show_question(self):
        """Показывает текущий вопрос"""
        self.clear_window()
        
        # Получаем данные билета
        ticket = tickets_data[self.current_ticket]
        questions = ticket["questions"]
        current_q = questions[self.current_question_index]
        
        # Заголовок
        header = tk.Frame(self.root)
        header.pack(fill="x", pady=10)
        
        ticket_label = tk.Label(header, text=f"Билет №{self.current_ticket}: {ticket['name']}",
                               font=("Arial", 14, "bold"), fg="#2c3e50")
        ticket_label.pack()
        
        progress_label = tk.Label(header, 
                                 text=f"Вопрос {self.current_question_index + 1} из {self.total_questions}",
                                 font=("Arial", 12), fg="#7f8c8d")
        progress_label.pack()
        
        # Прогресс-бар
        progress = ttk.Progressbar(self.root, length=400, mode='determinate',
                                   maximum=self.total_questions)
        progress.pack(pady=10)
        progress['value'] = self.current_question_index
        
        # Вопрос
        question_frame = tk.Frame(self.root)
        question_frame.pack(pady=30)
        
        question_text = tk.Label(question_frame, text=current_q["text"],
                                font=("Arial", 14), wraplength=700, justify="left")
        question_text.pack(pady=20)
        
        # Варианты ответов
        options_frame = tk.Frame(self.root)
        options_frame.pack(pady=20)
        
        # Переменная для хранения выбранного ответа
        self.answer_var = tk.IntVar()
        
        # Создаем радиокнопки для вариантов
        self.radio_buttons = []
        for i, option in enumerate(current_q["options"]):
            rb = tk.Radiobutton(options_frame, 
                               text=f"{chr(65+i)}. {option}",  # A, B, C
                               variable=self.answer_var,
                               value=i,
                               font=("Arial", 12),
                               wraplength=650,
                               justify="left")
            rb.pack(anchor="w", pady=5)
            self.radio_buttons.append(rb)
        
        # Кнопки управления
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(pady=30)
        
        # Кнопка "Далее" или "Завершить"
        if self.current_question_index == self.total_questions - 1:
            next_btn = tk.Button(buttons_frame, text="Завершить тест",
                               font=("Arial", 12), bg="#27ae60", fg="white",
                               command=self.finish_test, width=15, height=2)
        else:
            next_btn = tk.Button(buttons_frame, text="Далее →",
                               font=("Arial", 12), bg="#3498db", fg="white",
                               command=self.next_question, width=15, height=2)
        
        next_btn.pack(side="left", padx=10)
        
        # Кнопка "Назад" (если не первый вопрос)
        if self.current_question_index > 0:
            back_btn = tk.Button(buttons_frame, text="← Назад",
                               font=("Arial", 12), bg="#95a5a6", fg="white",
                               command=self.prev_question, width=15, height=2)
            back_btn.pack(side="left", padx=10)
        
        # Кнопка "Выйти в меню"
        menu_btn = tk.Button(buttons_frame, text="В меню выбора",
                           font=("Arial", 12), bg="#e74c3c", fg="white",
                           command=self.show_ticket_selection, width=15, height=2)
        menu_btn.pack(side="left", padx=10)
        
        # Если на этот вопрос уже был ответ, восстанавливаем его
        if len(self.user_answers) > self.current_question_index:
            self.answer_var.set(self.user_answers[self.current_question_index])
    
    def next_question(self):
        """Переход к следующему вопросу"""
        # Проверяем, выбран ли ответ
        if self.answer_var.get() == -1:  # Ничего не выбрано
            messagebox.showwarning("Внимание", "Пожалуйста, выберите вариант ответа!")
            return
        
        # Сохраняем ответ
        if len(self.user_answers) <= self.current_question_index:
            self.user_answers.append(self.answer_var.get())
        else:
            self.user_answers[self.current_question_index] = self.answer_var.get()
        
        # Переходим к следующему вопросу
        self.current_question_index += 1
        self.show_question()
    
    def prev_question(self):
        """Возврат к предыдущему вопросу"""
        # Сохраняем текущий ответ
        if self.answer_var.get() != -1:
            if len(self.user_answers) <= self.current_question_index:
                self.user_answers.append(self.answer_var.get())
            else:
                self.user_answers[self.current_question_index] = self.answer_var.get()
        
        # Переходим к предыдущему вопросу
        self.current_question_index -= 1
        self.show_question()
    
    def finish_test(self):
        """Завершает тест и показывает результат"""
        # Сохраняем последний ответ
        if self.answer_var.get() == -1:
            messagebox.showwarning("Внимание", "Пожалуйста, выберите вариант ответа!")
            return
        
        if len(self.user_answers) <= self.current_question_index:
            self.user_answers.append(self.answer_var.get())
        else:
            self.user_answers[self.current_question_index] = self.answer_var.get()
        
        # Подсчитываем результат
        ticket = tickets_data[self.current_ticket]
        questions = ticket["questions"]
        
        correct_count = 0
        for i, answer in enumerate(self.user_answers):
            if answer == questions[i]["correct"]:
                correct_count += 1
        
        # Показываем результат
        self.show_result(correct_count)
    
    def show_result(self, correct_count):
        """Отображает результат тестирования"""
        self.clear_window()
        
        percent = (correct_count / self.total_questions) * 100
        
        # Заголовок
        title = tk.Label(self.root, text="РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ",
                        font=("Arial", 20, "bold"), fg="#2c3e50")
        title.pack(pady=30)
        
        # Результаты
        result_frame = tk.Frame(self.root, relief="groove", bd=2)
        result_frame.pack(pady=20, padx=50, fill="both")
        
        correct_label = tk.Label(result_frame, 
                                text=f"Правильных ответов: {correct_count} из {self.total_questions}",
                                font=("Arial", 16), fg="#27ae60")
        correct_label.pack(pady=10)
        
        percent_label = tk.Label(result_frame,
                               text=f"Процент выполнения: {percent:.1f}%",
                               font=("Arial", 14))
        percent_label.pack(pady=5)
        
        # Оценка
        if percent >= 90:
            grade = "5 (Отлично!)"
            grade_color = "#27ae60"
        elif percent >= 70:
            grade = "4 (Хорошо)"
            grade_color = "#3498db"
        elif percent >= 50:
            grade = "3 (Удовлетворительно)"
            grade_color = "#f39c12"
        else:
            grade = "2 (Неудовлетворительно)"
            grade_color = "#e74c3c"
        
        grade_label = tk.Label(result_frame, text=f"Оценка: {grade}",
                              font=("Arial", 16, "bold"), fg=grade_color)
        grade_label.pack(pady=10)
        
        # Кнопки
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(pady=30)
        
        again_btn = tk.Button(buttons_frame, text="Выбрать другой билет",
                            font=("Arial", 12), bg="#3498db", fg="white",
                            command=self.show_ticket_selection, width=20, height=2)
        again_btn.pack(side="left", padx=10)
        
        exit_btn = tk.Button(buttons_frame, text="Выйти",
                           font=("Arial", 12), bg="#e74c3c", fg="white",
                           command=self.root.quit, width=15, height=2)
        exit_btn.pack(side="left", padx=10)
        
        # Рекомендация
        if correct_count < 7:
            recom_label = tk.Label(self.root, 
                                  text="Совет: Повторите материал по охране труда и попробуйте снова!",
                                  font=("Arial", 10), fg="#e74c3c")
            recom_label.pack(pady=10)

# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = OTTestApp(root)
    root.mainloop()