import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import glob

class NumberSystemConverter:    
    @staticmethod
    def decimal_to_binary(decimal_num):
        try:
            if isinstance(decimal_num, str):
                decimal_num = int(decimal_num)
            return bin(decimal_num)[2:]
        except:
            return "Ошибка"
    
    @staticmethod
    def decimal_to_octal(decimal_num):
        try:
            if isinstance(decimal_num, str):
                decimal_num = int(decimal_num)
            return oct(decimal_num)[2:]
        except:
            return "Ошибка"
    
    @staticmethod
    def decimal_to_hex(decimal_num):
        try:
            if isinstance(decimal_num, str):
                decimal_num = int(decimal_num)
            return hex(decimal_num)[2:].upper()
        except:
            return "Ошибка"
    
    @staticmethod
    def binary_to_decimal(binary_num):
        try:
            return int(binary_num, 2)
        except:
            return "Ошибка"
    
    @staticmethod
    def octal_to_decimal(octal_num):
        try:
            return int(octal_num, 8)
        except:
            return "Ошибка"
    
    @staticmethod
    def hex_to_decimal(hex_num):
        try:
            return int(hex_num, 16)
        except:
            return "Ошибка"
    
    @staticmethod
    def convert_number(number_str, from_base, to_base):
        try:
            if from_base == 2:
                decimal_val = NumberSystemConverter.binary_to_decimal(number_str)
            elif from_base == 8:
                decimal_val = NumberSystemConverter.octal_to_decimal(number_str)
            elif from_base == 10:
                decimal_val = int(number_str)
            elif from_base == 16:
                decimal_val = NumberSystemConverter.hex_to_decimal(number_str)
            else:
                return "Ошибка: неверная исходная система счисления"
            
            if decimal_val == "Ошибка":
                return "Ошибка"
            
            if to_base == 2:
                return NumberSystemConverter.decimal_to_binary(decimal_val)
            elif to_base == 8:
                return NumberSystemConverter.decimal_to_octal(decimal_val)
            elif to_base == 10:
                return str(decimal_val)
            elif to_base == 16:
                return NumberSystemConverter.decimal_to_hex(decimal_val)
            else:
                return "Ошибка: неверная конечная система счисления"
                
        except Exception as e:
            return f"Ошибка: {str(e)}"
    
    @staticmethod
    def detect_base(number_str):
        number_str = str(number_str).strip().upper()
        
        if number_str.startswith("0B"):
            return 2, number_str[2:]
        elif number_str.startswith("0O"):
            return 8, number_str[2:]
        elif number_str.startswith("0X"):
            return 16, number_str[2:]
        elif all(c in "01" for c in number_str):
            return 2, number_str
        elif all(c in "01234567" for c in number_str):
            return 8, number_str
        elif all(c in "0123456789" for c in number_str):
            return 10, number_str
        elif all(c in "0123456789ABCDEF" for c in number_str):
            return 16, number_str
        else:
            return None, number_str

class LearningProgram:
    def __init__(self, root):
        self.root = root
        self.root.title("Программа обучения")
        self.root.geometry("1920x1080")
        
        self.converter = NumberSystemConverter()
        
        self.current_lesson_images = []
        self.current_image_index = 0
        self.current_lesson_number = 1
        self.current_section = ""
        
        self.practice_numbers = []
        self.user_answers = []
        self.correct_answers = []
        self.practice_tasks = []
        
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        self.create_menu(main_frame)
        
        self.content_frame = ttk.Frame(main_frame, relief=tk.SUNKEN, borderwidth=2)
        self.content_frame.grid(row=0, column=1, padx=(20, 0), sticky=(tk.W, tk.E, tk.N, tk.S))
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        
        self.show_welcome_screen()
        
        self.root.bind("<Left>", self.prev_image)
        self.root.bind("<Right>", self.next_image)
        self.root.bind("<Up>", lambda e: None)
        self.root.bind("<Down>", lambda e: None)
    
    def create_menu(self, parent):
        menu_frame = ttk.Frame(parent)
        menu_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        style = ttk.Style()
        style.configure("Menu.TButton", font=("Arial", 12), padding=10)
        
        buttons = [
            ("Теоретическая часть", self.show_theory_menu),
            ("Практическая часть", self.show_practice_menu),
            ("Контроль знаний", self.show_knowledge_test),
            ("Рекомендации и правила", self.show_method_info)
        ]
        
        for i, (text, command) in enumerate(buttons):
            btn = ttk.Button(menu_frame, text=text, style="Menu.TButton", 
                           command=command, width=20)
            btn.grid(row=i, column=0, pady=5, sticky=(tk.W, tk.E))
        
        exit_btn = ttk.Button(menu_frame, text="Выход", 
                            command=self.root.quit, width=20)
        exit_btn.grid(row=len(buttons), column=0, pady=(20, 0), sticky=(tk.W, tk.E))
    
    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_welcome_screen(self):
        self.clear_content_frame()
        
        instruction_label = ttk.Label(self.content_frame,
                                    text="Выберите раздел в меню слева для начала работы.",
                                    font=("Times New Roman", 14))
        instruction_label.pack(pady=20)
        
    def show_theory_menu(self):
        self.show_lessons_menu("Теоретическая часть")
    
    def show_practice_menu(self):
        self.show_lessons_menu("Практическая часть")
    
    def show_lessons_menu(self, section_name):
        self.clear_content_frame()
        
        title_label = ttk.Label(self.content_frame, 
                              text=section_name,
                              font=("Times New Roman", 14, "bold"))
        title_label.pack(pady=(20, 30))
        
        lessons_frame = ttk.Frame(self.content_frame)
        lessons_frame.pack(expand=True)
        
        for i in range(1, 6):
            lesson_btn = ttk.Button(lessons_frame, 
                                  text=f"Урок №{i}",
                                  command=lambda idx=i: self.show_lesson(section_name, idx),
                                  width=20)
            lesson_btn.pack(pady=10)
        
        back_btn = ttk.Button(self.content_frame, 
                            text="Назад в главное меню",
                            command=self.show_welcome_screen)
        back_btn.pack(pady=(30, 20))
    
    def load_images_for_lesson(self, lesson_number):
        """Загрузка изображений для указанного урока"""
        folder_path = f"data/lesson_{lesson_number}"
        images = []
        
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp']
            image_files = []
            
            for ext in image_extensions:
                image_files.extend(glob.glob(os.path.join(folder_path, ext)))
            
            image_files.sort()
            
            for img_path in image_files:
                try:
                    img = Image.open(img_path)
                    max_size = (600, 400)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    images.append((photo, img_path, img))
                except Exception as e:
                    print(f"Ошибка загрузки изображения {img_path}: {e}")
        
        return images


    def load_practice_numbers(self, lesson_number):
        BASE_DIR = os.path.dirname(__file__)
        file_path = os.path.join(BASE_DIR, "data", "practice", f"practice_{lesson_number}.txt")
        numbers = []
    
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            numbers.append(line)
            except Exception as e:
                print(f"Ошибка чтения файла {file_path}: {e}")
                return []
            #на случай пустых файлов сделал себе, в будущем заменю на вывод ошибки
        else:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            sample = {
                3: ["1010", "1101", "1001", "1110", "1011"],
                4: ["17", "25", "33", "41", "57"],
                5: ["A", "F", "1A", "2F", "3C"],
            }.get(lesson_number, [])
    
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(sample))
            except Exception as e:
                print(f"Не удалось создать файл {file_path}: {e}")
    
            numbers = sample
    
        return numbers

    
    def show_lesson(self, section_name, lesson_number):
        self.clear_content_frame()
        self.current_section = section_name
        self.current_lesson_number = lesson_number
        
        if section_name == "Теоретическая часть":
            self.show_theory_lesson(lesson_number)
        else:
            self.show_practice_lesson(lesson_number)
    
    def show_theory_lesson(self, lesson_number):
        title_label = ttk.Label(self.content_frame,
                              text=f"Теоретическая часть\nУрок №{lesson_number}",
                              font=("Times New Roman", 14, "bold"),
                              justify=tk.CENTER)
        title_label.pack(pady=(10, 20))
        
        self.current_lesson_images = self.load_images_for_lesson(lesson_number)
        self.current_image_index = 0
        
        image_frame = ttk.Frame(self.content_frame)
        image_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.image_label = ttk.Label(image_frame)
        self.image_label.pack(expand=True)
        
        self.image_label.bind("<Button-1>", self.next_image)
        
        info_frame = ttk.Frame(self.content_frame)
        info_frame.pack(pady=5)
        
        self.image_info_label = ttk.Label(info_frame, 
                                         text="",
                                         font=("Times New Roman", 14))
        self.image_info_label.pack()
        
        nav_frame = ttk.Frame(self.content_frame)
        nav_frame.pack(pady=10)
        
        prev_btn = ttk.Button(nav_frame,
                            text="← Предыдущее",
                            command=self.prev_image)
        prev_btn.grid(row=0, column=0, padx=5)
        
        self.image_counter_label = ttk.Label(nav_frame,
                                           text="0/0",
                                           font=("Arial", 10))
        self.image_counter_label.grid(row=0, column=1, padx=10)
        
        next_btn = ttk.Button(nav_frame,
                            text="Следующее →",
                            command=self.next_image)
        next_btn.grid(row=0, column=2, padx=5)
        
        if self.current_lesson_images:
            self.display_current_image()
        else:
            no_images_text = f"В папке data/lesson_{lesson_number} нет изображений или они сохранены не в корректном формате. Поддерживаемые форматы: .jpg, .jpeg, .png, .gif, .bmp"
            
            no_images_label = ttk.Label(image_frame,
                                      text=no_images_text,
                                      font=("Times New Roman", 14),
                                      justify=tk.CENTER,
                                      wraplength=500,
                                      foreground="red")
            no_images_label.pack(pady=50)
            
            self.image_counter_label.config(text="0/0")
        
        bottom_frame = ttk.Frame(self.content_frame)
        bottom_frame.pack(pady=20)
        
        if lesson_number <= 5:
            switch_btn = ttk.Button(bottom_frame,
                                  text=f"Перейти к Практической части (Урок {lesson_number})",
                                  command=lambda: self.show_lesson("Практическая часть", lesson_number))
            switch_btn.grid(row=0, column=0, padx=10)
        
        back_btn = ttk.Button(bottom_frame,
                            text="Вернуться к списку уроков",
                            command=lambda: self.show_lessons_menu("Теоретическая часть"))
        back_btn.grid(row=0, column=1, padx=10)
        
        instruction_label = ttk.Label(self.content_frame,
                                    text="Управление: Клик по изображению → следующее, ←/→ на клавиатуре, кнопки ниже",
                                    font=("Times New Roman", 14),
                                    foreground="gray")
        instruction_label.pack(pady=5)
    
    def display_current_image(self):
        """Отобразить текущее изображение"""
        if 0 <= self.current_image_index < len(self.current_lesson_images):
            photo, img_path, img = self.current_lesson_images[self.current_image_index]
            self.image_label.config(image=photo)
            self.image_label.image = photo
            
            filename = os.path.basename(img_path)
            self.image_info_label.config(text=f"Файл: {filename} | Размер: {img.width}x{img.height}")
            self.image_counter_label.config(text=f"{self.current_image_index + 1}/{len(self.current_lesson_images)}")
    
    def prev_image(self, event=None):
        """Перейти к предыдущему изображению"""
        if self.current_lesson_images and self.current_image_index > 0:
            self.current_image_index -= 1
            self.display_current_image()
    
    def next_image(self, event=None):
        """Перейти к следующему изображению"""
        if self.current_lesson_images and self.current_image_index < len(self.current_lesson_images) - 1:
            self.current_image_index += 1
            self.display_current_image()
    
    def show_practice_lesson(self, lesson_number):
        """Показать практический урок"""
        self.clear_content_frame()
        self.current_lesson_number = lesson_number
        
        title_label = ttk.Label(self.content_frame,
                              text=f"Практическая часть\nУрок №{lesson_number}",
                              font=("Times New Roman", 14, "bold"),
                              justify=tk.CENTER)
        title_label.pack(pady=(10, 20))
        
        self.practice_numbers = self.load_practice_numbers(lesson_number)
        self.user_answers = [""] * len(self.practice_numbers)
        self.correct_answers = []
        self.practice_tasks = []
        
        if lesson_number == 3:
            task_type = "двоичной"
            from_base = 2
            to_base = 10
            instruction = "Переведите следующие двоичные числа в десятичную систему:"
        elif lesson_number == 4:
            task_type = "восьмеричной"
            from_base = 8
            to_base = 10
            instruction = "Переведите следующие восьмеричные числа в десятичную систему:"
        elif lesson_number == 5:
            task_type = "шестнадцатеричной"
            from_base = 16
            to_base = 10
            instruction = "Переведите следующие шестнадцатеричные числа в десятичную систему:"
        else:
            task_type = "десятичной"
            from_base = 10
            to_base = 2
            instruction = "Практические задания для этого урока:"
        
        instruction_label = ttk.Label(self.content_frame,
                                    text=instruction,
                                    font=("Times New Roman", 14),
                                    justify=tk.LEFT)
        instruction_label.pack(pady=(0, 20), padx=20, anchor=tk.W)
        
        canvas_frame = ttk.Frame(self.content_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        for i, number in enumerate(self.practice_numbers):
            task_frame = ttk.Frame(scrollable_frame, padding="10")
            task_frame.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=5)
            
            task_num_label = ttk.Label(task_frame, 
                                     text=f"Задание {i+1}:",
                                     font=("Times New Roman", 14, "bold"))
            task_num_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
            
            number_label = ttk.Label(task_frame,
                                   text=f"Число: {number} ({task_type} система)",
                                   font=("Times New Roman", 14))
            number_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
            
            answer_label = ttk.Label(task_frame,
                                   text="Ваш ответ:",
                                   font=("Times New Roman", 14))
            answer_label.grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
            
            answer_var = tk.StringVar()
            answer_entry = ttk.Entry(task_frame,
                                   textvariable=answer_var,
                                   width=20,
                                   font=("Times New Roman", 14))
            answer_entry.grid(row=1, column=1, sticky=tk.W, pady=(10, 0))
            
            correct_answer = self.converter.convert_number(number, from_base, to_base)
            self.correct_answers.append(correct_answer)
            
            self.practice_tasks.append({
                'index': i,
                'number': number,
                'answer_var': answer_var,
                'answer_entry': answer_entry,
                'correct_answer': correct_answer,
                'task_frame': task_frame
            })
            
            answer_var.trace('w', lambda *args, idx=i: self.update_user_answer(idx))
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        buttons_frame = ttk.Frame(self.content_frame)
        buttons_frame.pack(pady=20)
        
        result_btn = ttk.Button(buttons_frame,
                              text="Результат",
                              command=self.show_results,
                              width=20)
        result_btn.grid(row=0, column=0, padx=10)
        
        switch_btn = ttk.Button(buttons_frame,
                              text=f"Перейти к Теоретической части (Урок {lesson_number})",
                              command=lambda: self.show_lesson("Теоретическая часть", lesson_number))
        switch_btn.grid(row=0, column=1, padx=10)
        
        back_btn = ttk.Button(buttons_frame,
                            text="Вернуться к списку уроков",
                            command=lambda: self.show_lessons_menu("Практическая часть"))
        back_btn.grid(row=0, column=2, padx=10)
        
        nav_frame = ttk.Frame(self.content_frame)
        nav_frame.pack(pady=10)
        
        if lesson_number > 1:
            prev_btn = ttk.Button(nav_frame,
                                text="← Предыдущий урок",
                                command=lambda: self.show_lesson("Практическая часть", lesson_number-1))
            prev_btn.grid(row=0, column=0, padx=5)
        
        if lesson_number < 5:
            next_btn = ttk.Button(nav_frame,
                                text="Следующий урок →",
                                command=lambda: self.show_lesson("Практическая часть", lesson_number+1))
            next_btn.grid(row=0, column=1, padx=5)
    
    def update_user_answer(self, index):
        """Обновление ответа пользователя"""
        if index < len(self.user_answers):
            self.user_answers[index] = self.practice_tasks[index]['answer_var'].get().strip()
    
    def show_results(self):
        """Показать результаты выполнения заданий"""
        if not self.practice_tasks:
            messagebox.showinfo("Результаты", "Нет заданий для проверки.")
            return
        
        correct_count = 0
        results = []
        
        for i, task in enumerate(self.practice_tasks):
            user_answer = self.user_answers[i]
            correct_answer = task['correct_answer']
            
            is_correct = (user_answer.upper() == correct_answer.upper())
            
            if is_correct:
                correct_count += 1
            
            results.append({
                'task_num': i + 1,
                'number': task['number'],
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct
            })
        
        results_window = tk.Toplevel(self.root)
        results_window.title(f"Результаты урока {self.current_lesson_number}")
        results_window.geometry("700x500")
        
        title_label = ttk.Label(results_window,
                              text=f"Результаты практического задания\nУрок №{self.current_lesson_number}",
                              font=("Times New Roman", 14, "bold"))
        title_label.pack(pady=10)
        
        stats_text = f"Правильных ответов: {correct_count} из {len(results)}"
        if len(results) > 0:
            percentage = (correct_count / len(results)) * 100
            stats_text += f" ({percentage:.1f}%)"
        
        stats_label = ttk.Label(results_window,
                              text=stats_text,
                              font=("Times New Roman", 14))
        stats_label.pack(pady=5)
        
        table_frame = ttk.Frame(results_window)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        headers = ["№", "Исходное число", "Ваш ответ", "Правильный ответ", "Статус"]
        
        for col, header in enumerate(headers):
            header_label = ttk.Label(table_frame,
                                   text=header,
                                   font=("Times New Roman", 14, "bold"),
                                   relief=tk.RIDGE,
                                   padding=5)
            header_label.grid(row=0, column=col, sticky=(tk.W, tk.E))
        
        for row, result in enumerate(results, start=1):
            task_label = ttk.Label(table_frame,
                                 text=str(result['task_num']),
                                 font=("Times New Roman", 14),
                                 relief=tk.RIDGE,
                                 padding=5)
            task_label.grid(row=row, column=0, sticky=(tk.W, tk.E))
            
            num_label = ttk.Label(table_frame,
                                text=result['number'],
                                font=("Times New Roman", 14),
                                relief=tk.RIDGE,
                                padding=5)
            num_label.grid(row=row, column=1, sticky=(tk.W, tk.E))
            
            user_label = ttk.Label(table_frame,
                                 text=result['user_answer'] if result['user_answer'] else "(не ответил)",
                                 font=("Times New Roman", 14),
                                 relief=tk.RIDGE,
                                 padding=5)
            user_label.grid(row=row, column=2, sticky=(tk.W, tk.E))
            
            correct_label = ttk.Label(table_frame,
                                    text=result['correct_answer'],
                                    font=("Times New Roman", 14),
                                    relief=tk.RIDGE,
                                    padding=5)
            correct_label.grid(row=row, column=3, sticky=(tk.W, tk.E))
            
            status_text = "✓ Правильно" if result['is_correct'] else "✗ Неправильно"
            status_color = "green" if result['is_correct'] else "red"
            
            status_label = ttk.Label(table_frame,
                                   text=status_text,
                                   font=("Times New Roman", 14, "bold"),
                                   foreground=status_color,
                                   relief=tk.RIDGE,
                                   padding=5)
            status_label.grid(row=row, column=4, sticky=(tk.W, tk.E))
        
        for col in range(5):
            table_frame.columnconfigure(col, weight=1)
        
        close_btn = ttk.Button(results_window,
                             text="Закрыть",
                             command=results_window.destroy)
        close_btn.pack(pady=10)
    
    def show_knowledge_test(self):
        """Показать раздел контроля знаний"""
        self.clear_content_frame()
        
        title_label = ttk.Label(self.content_frame,
                              text="Контроль знаний",
                              font=("Times New Roman", 14, "bold"))
        title_label.pack(pady=(20, 30))
        
        content_text = "Тут будет само тестирование, в котором будут задания для 2, 8 и 16 СС: 1 на перевод в другую СС и 1 на арифметику"
        
        content_label = ttk.Label(self.content_frame,
                                text=content_text,
                                font=("Times New Roman", 14),
                                justify=tk.LEFT,
                                wraplength=400)
        content_label.pack(pady=20, padx=20)
        
        back_btn = ttk.Button(self.content_frame,
                            text="Назад в главное меню",
                            command=self.show_welcome_screen)
        back_btn.pack(pady=20)
    
    def show_method_info(self):
        """Показать рекомендации и правила"""
        self.clear_content_frame()
        
        title_label = ttk.Label(self.content_frame,
                              text="Рекомендации и правила",
                              font=("Times New Roman", 14, "bold"))
        title_label.pack(pady=(20, 30))
        
        content_text = "Тут должны быть описаны правила оценивания, а также даты сдачи практических работ, которые подгружаются с /data/manifest.txt"
        
        content_label = ttk.Label(self.content_frame,
                                text=content_text,
                                font=("Times New Roman", 14),
                                justify=tk.LEFT,
                                wraplength=500)
        content_label.pack(pady=20, padx=20)
        
        back_btn = ttk.Button(self.content_frame,
                            text="Назад в главное меню",
                            command=self.show_welcome_screen)
        back_btn.pack(pady=20)

def main():
    root = tk.Tk()
    app = LearningProgram(root)
    root.mainloop()

if __name__ == "__main__":
    main()