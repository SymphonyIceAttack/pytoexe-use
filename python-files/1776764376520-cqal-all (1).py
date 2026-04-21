import os
import json
import sys
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog

class OTTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Тестирование по охране труда")
        self.root.geometry("900x700")
        
        # Файл для хранения данных (работает и как скрипт, и как EXE)
        if getattr(sys, 'frozen', False):
            # Если программа запущена как EXE
            application_path = os.path.dirname(sys.executable)
        else:
            # Если запущена как скрипт Python
            application_path = os.path.dirname(os.path.abspath(__file__))
        
        self.data_file = os.path.join(application_path, "tickets.json")
        
        # Загружаем билеты
        self.load_tickets()
        
        # Переменные для тестирования
        self.current_ticket = None
        self.current_question_index = 0
        self.user_answers = []
        self.total_questions = 0
        
        # Режим админа (по умолчанию False)
        self.admin_mode = False
        
        # Показываем главное меню
        self.show_main_menu()
    
    def load_tickets(self):
        """Загружает билеты из JSON файла"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.tickets = json.load(f)
        else:
            # Создаем пустую базу
            self.tickets = {}
            self.save_tickets()
    
    def save_tickets(self):
        """Сохраняет билеты в JSON файл"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.tickets, f, ensure_ascii=False, indent=2)
    
    def clear_window(self):
        """Очищает окно"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_main_menu(self):
        """Показывает главное меню"""
        self.clear_window()
        
        # Заголовок
        title = tk.Label(self.root, text="Тестирование по охране труда", 
                        font=("Arial", 24, "bold"), fg="#2c3e50")
        title.pack(pady=30)
        
        # Основные кнопки
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        
        test_btn = tk.Button(btn_frame, text="📝 Пройти тестирование",
                            font=("Arial", 14), bg="#3498db", fg="white",
                            command=self.show_ticket_selection, width=25, height=2)
        test_btn.pack(pady=10)
        
        admin_btn = tk.Button(btn_frame, text="🔧 Режим администратора",
                             font=("Arial", 14), bg="#e67e22", fg="white",
                             command=self.admin_login, width=25, height=2)
        admin_btn.pack(pady=10)
        
        exit_btn = tk.Button(btn_frame, text="🚪 Выход",
                            font=("Arial", 14), bg="#e74c3c", fg="white",
                            command=self.root.quit, width=25, height=2)
        exit_btn.pack(pady=10)
        
        # Информация
        info = tk.Label(self.root, 
                       text=f"Доступно билетов: {len(self.tickets)}\n"
                            f"Всего вопросов: {self.get_total_questions()}",
                       font=("Arial", 10), fg="#7f8c8d")
        info.pack(side="bottom", pady=20)
    
    def get_total_questions(self):
        """Возвращает общее количество вопросов во всех билетах"""
        total = 0
        for ticket in self.tickets.values():
            total += len(ticket.get("questions", []))
        return total
    
    def admin_login(self):
        """Проверка пароля для входа в режим администратора"""
        password = simpledialog.askstring("Пароль", "Введите пароль администратора:", show='*')
        if password == "admin123":
            self.admin_mode = True
            self.show_admin_panel()
        else:
            messagebox.showerror("Ошибка", "Неверный пароль!")
    
    def back_to_main_menu(self):
        """Возврат в главное меню"""
        self.admin_mode = False
        self.show_main_menu()
    
    def show_admin_panel(self):
        """Панель управления администратора"""
        self.clear_window()
        
        title = tk.Label(self.root, text="Панель администратора", 
                        font=("Arial", 20, "bold"), fg="#2c3e50")
        title.pack(pady=20)
        
        # Кнопки управления
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        
        add_ticket_btn = tk.Button(btn_frame, text="➕ Добавить новый билет",
                                  font=("Arial", 12), bg="#27ae60", fg="white",
                                  command=self.add_ticket, width=30, height=2)
        add_ticket_btn.pack(pady=5)
        
        edit_ticket_btn = tk.Button(btn_frame, text="✏️ Редактировать билет",
                                   font=("Arial", 12), bg="#3498db", fg="white",
                                   command=self.edit_ticket_menu, width=30, height=2)
        edit_ticket_btn.pack(pady=5)
        
        delete_ticket_btn = tk.Button(btn_frame, text="🗑️ Удалить билет",
                                     font=("Arial", 12), bg="#e74c3c", fg="white",
                                     command=self.delete_ticket, width=30, height=2)
        delete_ticket_btn.pack(pady=5)
        
        # Список существующих билетов
        if self.tickets:
            list_frame = tk.LabelFrame(self.root, text="Существующие билеты", font=("Arial", 12))
            list_frame.pack(pady=20, padx=20, fill="both")
            
            list_text = tk.Text(list_frame, height=10, width=60, font=("Arial", 10))
            list_text.pack(padx=10, pady=10)
            
            for num, data in self.tickets.items():
                q_count = len(data.get("questions", []))
                list_text.insert("end", f"Билет №{num}: {data.get('name', 'Без названия')} - {q_count} вопросов\n")
            list_text.config(state="disabled")
        
        back_btn = tk.Button(self.root, text="◀ Назад в главное меню",
                            font=("Arial", 12), bg="#95a5a6", fg="white",
                            command=self.back_to_main_menu, width=20, height=2)
        back_btn.pack(pady=10)
    
    def add_ticket(self):
        """Добавление нового билета"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить билет")
        dialog.geometry("400x200")
        dialog.grab_set()
        
        tk.Label(dialog, text="Номер билета:", font=("Arial", 12)).pack(pady=10)
        num_entry = tk.Entry(dialog, font=("Arial", 12))
        num_entry.pack(pady=5)
        
        tk.Label(dialog, text="Название темы:", font=("Arial", 12)).pack(pady=10)
        name_entry = tk.Entry(dialog, font=("Arial", 12))
        name_entry.pack(pady=5)
        
        def save_ticket():
            try:
                ticket_num = int(num_entry.get())
                ticket_name = name_entry.get()
                
                if ticket_num in self.tickets:
                    messagebox.showerror("Ошибка", "Билет с таким номером уже существует!")
                    return
                
                if not ticket_name:
                    messagebox.showerror("Ошибка", "Введите название темы!")
                    return
                
                self.tickets[ticket_num] = {
                    "name": ticket_name,
                    "questions": []
                }
                self.save_tickets()
                messagebox.showinfo("Успех", f"Билет №{ticket_num} добавлен!")
                dialog.destroy()
                
                # Предлагаем добавить вопросы
                if messagebox.askyesno("Добавить вопросы", "Хотите добавить вопросы в этот билет?"):
                    self.add_questions_to_ticket(ticket_num)
                
            except ValueError:
                messagebox.showerror("Ошибка", "Номер билета должен быть числом!")
        
        tk.Button(dialog, text="Сохранить", command=save_ticket, 
                 bg="#27ae60", fg="white", font=("Arial", 12)).pack(pady=20)
    
    def add_questions_to_ticket(self, ticket_num):
        """Добавляет вопросы в билет"""
        self.edit_ticket(ticket_num)
    
    def edit_ticket_menu(self):
        """Меню выбора билета для редактирования"""
        if not self.tickets:
            messagebox.showwarning("Внимание", "Нет билетов для редактирования!")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Выберите билет для редактирования")
        dialog.geometry("400x400")
        dialog.grab_set()
        
        tk.Label(dialog, text="Выберите билет:", font=("Arial", 14)).pack(pady=10)
        
        listbox = tk.Listbox(dialog, font=("Arial", 12), height=15)
        listbox.pack(pady=10, padx=20, fill="both", expand=True)
        
        ticket_list = []
        for num, data in self.tickets.items():
            q_count = len(data.get("questions", []))
            display_text = f"Билет №{num}: {data['name']} ({q_count} вопросов)"
            listbox.insert("end", display_text)
            ticket_list.append(num)
        
        def edit_selected():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Внимание", "Выберите билет!")
                return
            ticket_num = ticket_list[selection[0]]
            dialog.destroy()
            self.edit_ticket(ticket_num)
        
        tk.Button(dialog, text="Редактировать", command=edit_selected,
                 bg="#3498db", fg="white", font=("Arial", 12)).pack(pady=10)
    
    def edit_ticket(self, ticket_num):
        """Редактирование конкретного билета"""
        self.clear_window()
        
        ticket = self.tickets[ticket_num]
        
        title = tk.Label(self.root, text=f"Редактирование билета №{ticket_num}", 
                        font=("Arial", 20, "bold"))
        title.pack(pady=20)
        
        # Информация о билете
        info_frame = tk.Frame(self.root)
        info_frame.pack(pady=10)
        
        tk.Label(info_frame, text=f"Тема: {ticket['name']}", font=("Arial", 14)).pack()
        tk.Label(info_frame, text=f"Вопросов: {len(ticket.get('questions', []))}", 
                font=("Arial", 12)).pack()
        
        # Кнопки управления
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        
        add_q_btn = tk.Button(btn_frame, text="➕ Добавить вопрос",
                             font=("Arial", 12), bg="#27ae60", fg="white",
                             command=lambda: self.add_question(ticket_num), width=20)
        add_q_btn.pack(pady=5)
        
        edit_q_btn = tk.Button(btn_frame, text="✏️ Редактировать вопрос",
                              font=("Arial", 12), bg="#3498db", fg="white",
                              command=lambda: self.edit_question_menu(ticket_num), width=20)
        edit_q_btn.pack(pady=5)
        
        delete_q_btn = tk.Button(btn_frame, text="🗑️ Удалить вопрос",
                                font=("Arial", 12), bg="#e74c3c", fg="white",
                                command=lambda: self.delete_question(ticket_num), width=20)
        delete_q_btn.pack(pady=5)
        
        # Список вопросов
        if ticket.get("questions"):
            list_frame = tk.LabelFrame(self.root, text="Вопросы билета", font=("Arial", 12))
            list_frame.pack(pady=20, padx=20, fill="both", expand=True)
            
            text_widget = tk.Text(list_frame, height=15, font=("Arial", 10))
            text_widget.pack(padx=10, pady=10, fill="both", expand=True)
            
            for i, q in enumerate(ticket["questions"], 1):
                text_widget.insert("end", f"{i}. {q['text']}\n")
                for j, opt in enumerate(q['options']):
                    marker = "✓" if j == q['correct'] else " "
                    text_widget.insert("end", f"   {marker} {chr(65+j)}. {opt}\n")
                text_widget.insert("end", "\n")
            text_widget.config(state="disabled")
        
        back_btn = tk.Button(self.root, text="◀ Назад", font=("Arial", 12),
                            command=self.show_admin_panel, width=15)
        back_btn.pack(pady=10)
    
    def add_question(self, ticket_num):
        """Добавление вопроса в билет"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить вопрос")
        dialog.geometry("600x500")
        dialog.grab_set()
        
        tk.Label(dialog, text="Текст вопроса:", font=("Arial", 12)).pack(pady=10)
        text_entry = tk.Text(dialog, height=3, width=60, font=("Arial", 10))
        text_entry.pack(pady=5)
        
        tk.Label(dialog, text="Вариант А:", font=("Arial", 12)).pack(pady=5)
        opt_a = tk.Entry(dialog, width=50, font=("Arial", 10))
        opt_a.pack()
        
        tk.Label(dialog, text="Вариант Б:", font=("Arial", 12)).pack(pady=5)
        opt_b = tk.Entry(dialog, width=50, font=("Arial", 10))
        opt_b.pack()
        
        tk.Label(dialog, text="Вариант В:", font=("Arial", 12)).pack(pady=5)
        opt_c = tk.Entry(dialog, width=50, font=("Arial", 10))
        opt_c.pack()
        
        tk.Label(dialog, text="Правильный ответ:", font=("Arial", 12)).pack(pady=10)
        correct_var = tk.StringVar(value="А")
        frame = tk.Frame(dialog)
        frame.pack()
        tk.Radiobutton(frame, text="А", variable=correct_var, value="А").pack(side="left", padx=10)
        tk.Radiobutton(frame, text="Б", variable=correct_var, value="Б").pack(side="left", padx=10)
        tk.Radiobutton(frame, text="В", variable=correct_var, value="В").pack(side="left", padx=10)
        
        def save_question():
            question_text = text_entry.get("1.0", "end-1c").strip()
            options = [opt_a.get().strip(), opt_b.get().strip(), opt_c.get().strip()]
            
            if not question_text or not all(options):
                messagebox.showerror("Ошибка", "Заполните все поля!")
                return
            
            correct_map = {"А": 0, "Б": 1, "В": 2}
            correct_idx = correct_map[correct_var.get()]
            
            new_question = {
                "text": question_text,
                "options": options,
                "correct": correct_idx
            }
            
            self.tickets[ticket_num].setdefault("questions", []).append(new_question)
            self.save_tickets()
            messagebox.showinfo("Успех", "Вопрос добавлен!")
            dialog.destroy()
        
        tk.Button(dialog, text="Сохранить вопрос", command=save_question,
                 bg="#27ae60", fg="white", font=("Arial", 12)).pack(pady=20)
    
    def edit_question_menu(self, ticket_num):
        """Меню выбора вопроса для редактирования"""
        ticket = self.tickets[ticket_num]
        if not ticket.get("questions"):
            messagebox.showwarning("Внимание", "В этом билете нет вопросов!")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Выберите вопрос для редактирования")
        dialog.geometry("500x400")
        dialog.grab_set()
        
        tk.Label(dialog, text="Выберите вопрос:", font=("Arial", 14)).pack(pady=10)
        
        listbox = tk.Listbox(dialog, font=("Arial", 11), height=15)
        listbox.pack(pady=10, padx=20, fill="both", expand=True)
        
        for i, q in enumerate(ticket["questions"], 1):
            listbox.insert("end", f"{i}. {q['text'][:50]}...")
        
        def edit_selected():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Внимание", "Выберите вопрос!")
                return
            dialog.destroy()
            self.edit_question(ticket_num, selection[0])
        
        tk.Button(dialog, text="Редактировать", command=edit_selected,
                 bg="#3498db", fg="white", font=("Arial", 12)).pack(pady=10)
    
    def edit_question(self, ticket_num, q_index):
        """Редактирование вопроса"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Редактировать вопрос")
        dialog.geometry("600x500")
        dialog.grab_set()
        
        question = self.tickets[ticket_num]["questions"][q_index]
        
        tk.Label(dialog, text="Текст вопроса:", font=("Arial", 12)).pack(pady=10)
        text_entry = tk.Text(dialog, height=3, width=60, font=("Arial", 10))
        text_entry.insert("1.0", question["text"])
        text_entry.pack(pady=5)
        
        tk.Label(dialog, text="Вариант А:", font=("Arial", 12)).pack(pady=5)
        opt_a = tk.Entry(dialog, width=50, font=("Arial", 10))
        opt_a.insert(0, question["options"][0])
        opt_a.pack()
        
        tk.Label(dialog, text="Вариант Б:", font=("Arial", 12)).pack(pady=5)
        opt_b = tk.Entry(dialog, width=50, font=("Arial", 10))
        opt_b.insert(0, question["options"][1])
        opt_b.pack()
        
        tk.Label(dialog, text="Вариант В:", font=("Arial", 12)).pack(pady=5)
        opt_c = tk.Entry(dialog, width=50, font=("Arial", 10))
        opt_c.insert(0, question["options"][2])
        opt_c.pack()
        
        tk.Label(dialog, text="Правильный ответ:", font=("Arial", 12)).pack(pady=10)
        correct_var = tk.StringVar(value=["А", "Б", "В"][question["correct"]])
        frame = tk.Frame(dialog)
        frame.pack()
        tk.Radiobutton(frame, text="А", variable=correct_var, value="А").pack(side="left", padx=10)
        tk.Radiobutton(frame, text="Б", variable=correct_var, value="Б").pack(side="left", padx=10)
        tk.Radiobutton(frame, text="В", variable=correct_var, value="В").pack(side="left", padx=10)
        
        def save_question():
            question_text = text_entry.get("1.0", "end-1c").strip()
            options = [opt_a.get().strip(), opt_b.get().strip(), opt_c.get().strip()]
            
            if not question_text or not all(options):
                messagebox.showerror("Ошибка", "Заполните все поля!")
                return
            
            correct_map = {"А": 0, "Б": 1, "В": 2}
            correct_idx = correct_map[correct_var.get()]
            
            self.tickets[ticket_num]["questions"][q_index] = {
                "text": question_text,
                "options": options,
                "correct": correct_idx
            }
            self.save_tickets()
            messagebox.showinfo("Успех", "Вопрос обновлен!")
            dialog.destroy()
        
        tk.Button(dialog, text="Сохранить изменения", command=save_question,
                 bg="#27ae60", fg="white", font=("Arial", 12)).pack(pady=20)
    
    def delete_question(self, ticket_num):
        """Удаление вопроса"""
        ticket = self.tickets[ticket_num]
        if not ticket.get("questions"):
            messagebox.showwarning("Внимание", "В этом билете нет вопросов!")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Удалить вопрос")
        dialog.geometry("500x400")
        dialog.grab_set()
        
        tk.Label(dialog, text="Выберите вопрос для удаления:", font=("Arial", 14)).pack(pady=10)
        
        listbox = tk.Listbox(dialog, font=("Arial", 11), height=15)
        listbox.pack(pady=10, padx=20, fill="both", expand=True)
        
        for i, q in enumerate(ticket["questions"], 1):
            listbox.insert("end", f"{i}. {q['text'][:50]}...")
        
        def delete_selected():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Внимание", "Выберите вопрос!")
                return
            
            if messagebox.askyesno("Подтверждение", "Удалить выбранный вопрос?"):
                del ticket["questions"][selection[0]]
                self.save_tickets()
                messagebox.showinfo("Успех", "Вопрос удален!")
                dialog.destroy()
        
        tk.Button(dialog, text="Удалить", command=delete_selected,
                 bg="#e74c3c", fg="white", font=("Arial", 12)).pack(pady=10)
    
    def delete_ticket(self):
        """Удаление билета"""
        if not self.tickets:
            messagebox.showwarning("Внимание", "Нет билетов для удаления!")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Удалить билет")
        dialog.geometry("400x300")
        dialog.grab_set()
        
        tk.Label(dialog, text="Выберите билет для удаления:", font=("Arial", 14)).pack(pady=10)
        
        listbox = tk.Listbox(dialog, font=("Arial", 12), height=10)
        listbox.pack(pady=10, padx=20, fill="both", expand=True)
        
        ticket_list = []
        for num, data in self.tickets.items():
            display_text = f"Билет №{num}: {data['name']}"
            listbox.insert("end", display_text)
            ticket_list.append(num)
        
        def delete_selected():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Внимание", "Выберите билет!")
                return
            
            ticket_num = ticket_list[selection[0]]
            if messagebox.askyesno("Подтверждение", f"Удалить билет №{ticket_num} и все его вопросы?"):
                del self.tickets[ticket_num]
                self.save_tickets()
                messagebox.showinfo("Успех", "Билет удален!")
                dialog.destroy()
                self.show_admin_panel()
        
        tk.Button(dialog, text="Удалить", command=delete_selected,
                 bg="#e74c3c", fg="white", font=("Arial", 12)).pack(pady=10)
    
    def show_ticket_selection(self):
        """Показывает выбор билета для тестирования"""
        if not self.tickets:
            messagebox.showwarning("Внимание", "Нет доступных билетов!\nДобавьте билеты через режим администратора.")
            self.show_main_menu()
            return
        
        self.clear_window()
        
        title = tk.Label(self.root, text="Выберите билет для тестирования", 
                        font=("Arial", 20, "bold"), fg="#2c3e50")
        title.pack(pady=30)
        
        frame = tk.Frame(self.root)
        frame.pack(pady=20)
        
        # Создаем кнопки для каждого билета
        for ticket_num, ticket_info in self.tickets.items():
            q_count = len(ticket_info.get("questions", []))
            if q_count == 0:
                continue
                
            btn = tk.Button(frame, 
                          text=f"Билет №{ticket_num}\n{ticket_info['name']}\n({q_count} вопросов)",
                          font=("Arial", 12),
                          bg="#3498db",
                          fg="white",
                          width=25,
                          height=3,
                          command=lambda num=ticket_num: self.start_test(num))
            btn.pack(pady=10)
        
        back_btn = tk.Button(self.root, text="◀ Назад в главное меню",
                            font=("Arial", 12), bg="#95a5a6", fg="white",
                            command=self.show_main_menu, width=20, height=2)
        back_btn.pack(pady=20)
    
    def start_test(self, ticket_num):
        """Начинает тестирование"""
        self.current_ticket = ticket_num
        self.current_question_index = 0
        self.user_answers = []
        questions = self.tickets[ticket_num].get("questions", [])
        self.total_questions = len(questions)
        self.show_question()
    
    def show_question(self):
        """Показывает текущий вопрос"""
        self.clear_window()
        
        ticket = self.tickets[self.current_ticket]
        questions = ticket["questions"]
        current_q = questions[self.current_question_index]
        
        # Заголовок
        header = tk.Frame(self.root)
        header.pack(fill="x", pady=10)
        
        tk.Label(header, text=f"Билет №{self.current_ticket}: {ticket['name']}",
                font=("Arial", 14, "bold"), fg="#2c3e50").pack()
        tk.Label(header, text=f"Вопрос {self.current_question_index + 1} из {self.total_questions}",
                font=("Arial", 12), fg="#7f8c8d").pack()
        
        # Прогресс
        progress = ttk.Progressbar(self.root, length=500, mode='determinate',
                                   maximum=self.total_questions)
        progress.pack(pady=10)
        progress['value'] = self.current_question_index
        
        # Вопрос
        tk.Label(self.root, text=current_q["text"], font=("Arial", 14),
                wraplength=800, justify="left").pack(pady=30)
        
        # Варианты ответов
        self.answer_var = tk.IntVar()
        options_frame = tk.Frame(self.root)
        options_frame.pack(pady=20)
        
        for i, option in enumerate(current_q["options"]):
            tk.Radiobutton(options_frame, text=f"{chr(65+i)}. {option}",
                          variable=self.answer_var, value=i,
                          font=("Arial", 12), wraplength=750, justify="left").pack(anchor="w", pady=5)
        
        # Кнопки
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(pady=30)
        
        if self.current_question_index == self.total_questions - 1:
            next_btn = tk.Button(buttons_frame, text="Завершить тест", bg="#27ae60",
                                fg="white", font=("Arial", 12), command=self.finish_test, width=15)
        else:
            next_btn = tk.Button(buttons_frame, text="Далее →", bg="#3498db",
                                fg="white", font=("Arial", 12), command=self.next_question, width=15)
        next_btn.pack(side="left", padx=10)
        
        if self.current_question_index > 0:
            tk.Button(buttons_frame, text="← Назад", bg="#95a5a6",
                     fg="white", font=("Arial", 12), command=self.prev_question, width=15).pack(side="left", padx=10)
        
        tk.Button(buttons_frame, text="В меню", bg="#e74c3c",
                 fg="white", font=("Arial", 12), command=self.show_ticket_selection, width=15).pack(side="left", padx=10)
        
        # Восстанавливаем ответ
        if len(self.user_answers) > self.current_question_index:
            self.answer_var.set(self.user_answers[self.current_question_index])
    
    def next_question(self):
        if self.answer_var.get() == -1:
            messagebox.showwarning("Внимание", "Выберите ответ!")
            return
        
        if len(self.user_answers) <= self.current_question_index:
            self.user_answers.append(self.answer_var.get())
        else:
            self.user_answers[self.current_question_index] = self.answer_var.get()
        
        self.current_question_index += 1
        self.show_question()
    
    def prev_question(self):
        if self.answer_var.get() != -1:
            if len(self.user_answers) <= self.current_question_index:
                self.user_answers.append(self.answer_var.get())
            else:
                self.user_answers[self.current_question_index] = self.answer_var.get()
        
        self.current_question_index -= 1
        self.show_question()
    
    def finish_test(self):
        if self.answer_var.get() == -1:
            messagebox.showwarning("Внимание", "Выберите ответ!")
            return
        
        if len(self.user_answers) <= self.current_question_index:
            self.user_answers.append(self.answer_var.get())
        else:
            self.user_answers[self.current_question_index] = self.answer_var.get()
        
        # Подсчет результатов
        questions = self.tickets[self.current_ticket]["questions"]
        correct = sum(1 for i, a in enumerate(self.user_answers) if a == questions[i]["correct"])
        
        self.show_result(correct)
    
    def show_result(self, correct):
        self.clear_window()
        
        percent = (correct / self.total_questions) * 100
        
        tk.Label(self.root, text="РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ",
                font=("Arial", 20, "bold")).pack(pady=30)
        
        result_frame = tk.Frame(self.root, relief="groove", bd=2)
        result_frame.pack(pady=20, padx=50, fill="both")
        
        tk.Label(result_frame, text=f"Правильных ответов: {correct} из {self.total_questions}",
                font=("Arial", 16), fg="#27ae60").pack(pady=10)
        tk.Label(result_frame, text=f"Процент: {percent:.1f}%",
                font=("Arial", 14)).pack(pady=5)
        
        if percent >= 90:
            grade = "5 (Отлично!)"
            color = "#27ae60"
        elif percent >= 70:
            grade = "4 (Хорошо)"
            color = "#3498db"
        elif percent >= 50:
            grade = "3 (Удовлетворительно)"
            color = "#f39c12"
        else:
            grade = "2 (Неудовлетворительно)"
            color = "#e74c3c"
        
        tk.Label(result_frame, text=f"Оценка: {grade}",
                font=("Arial", 16, "bold"), fg=color).pack(pady=10)
        
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(pady=30)
        
        tk.Button(buttons_frame, text="Выбрать другой билет", command=self.show_ticket_selection,
                 bg="#3498db", fg="white", font=("Arial", 12), width=20).pack(side="left", padx=10)
        tk.Button(buttons_frame, text="В главное меню", command=self.show_main_menu,
                 bg="#95a5a6", fg="white", font=("Arial", 12), width=20).pack(side="left", padx=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = OTTestApp(root)
    root.mainloop()