import tkinter as tk
from tkinter import ttk, scrolledtext
import sys
from io import StringIO
import traceback


class PythonConsole:
    """Интерактивная консоль Python"""

    def __init__(self, parent):
        self.parent = parent
        self.setup_console()

    def setup_console(self):
        # Фрейм для консоли
        self.console_frame = tk.Frame(self.parent, bg='#1e1e1e')
        self.console_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Заголовок консоли
        title_frame = tk.Frame(self.console_frame, bg='#2b2b2b')
        title_frame.pack(fill=tk.X)

        title_label = tk.Label(title_frame, text="💻 Интерактивная консоль Python",
                               font=('Segoe UI', 10, 'bold'), bg='#2b2b2b', fg='#ffd700')
        title_label.pack(side=tk.LEFT, padx=5)

        # Кнопки управления
        clear_btn = tk.Button(title_frame, text="Очистить", command=self.clear_console,
                              bg='#3c3f41', fg='white', font=('Segoe UI', 9),
                              relief=tk.FLAT, cursor='hand2')
        clear_btn.pack(side=tk.RIGHT, padx=5)

        run_btn = tk.Button(title_frame, text="▶ Выполнить", command=self.execute_code,
                            bg='#4cae4c', fg='white', font=('Segoe UI', 9, 'bold'),
                            relief=tk.FLAT, cursor='hand2')
        run_btn.pack(side=tk.RIGHT, padx=5)

        # Область вывода
        self.output_area = scrolledtext.ScrolledText(self.console_frame,
                                                     wrap=tk.WORD,
                                                     font=('Consolas', 10),
                                                     bg='#1e1e1e',
                                                     fg='#d4d4d4',
                                                     height=12,
                                                     relief=tk.FLAT)
        self.output_area.pack(fill=tk.BOTH, expand=True, pady=(5, 5))

        # Настройка тегов для вывода
        self.output_area.tag_config("error", foreground="#f48771")
        self.output_area.tag_config("success", foreground="#6a9955")
        self.output_area.tag_config("prompt", foreground="#569cd6")

        # Область ввода кода
        input_label = tk.Label(self.console_frame, text="Введите код Python:",
                               font=('Segoe UI', 9), bg='#1e1e1e', fg='#888888')
        input_label.pack(anchor=tk.W, pady=(5, 2))

        self.code_input = scrolledtext.ScrolledText(self.console_frame,
                                                    wrap=tk.WORD,
                                                    font=('Consolas', 10),
                                                    bg='#252526',
                                                    fg='#d4d4d4',
                                                    height=8,
                                                    relief=tk.FLAT,
                                                    insertbackground='white')
        self.code_input.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # Вставка примера
        self.insert_example()

        # Привязка клавиш
        self.code_input.bind('<Control-Return>', lambda e: self.execute_code())
        self.code_input.bind('<F5>', lambda e: self.execute_code())

    def insert_example(self):
        example = '''# Попробуйте написать код здесь!
# Примеры для тестирования:

# 1. Простые вычисления
# print(2 + 2 * 3)

# 2. Работа с переменными
# name = "Python"
# print(f"Привет, {name}!")

# 3. Условные операторы
# for i in range(5):
#     print(f"Квадрат {i} = {i**2}")

# Раскомментируйте и запустите (F5 или Ctrl+Enter)'''

        self.code_input.insert('1.0', example)

    def clear_console(self):
        self.output_area.delete(1.0, tk.END)
        self.add_output(">>> Консоль очищена\n", "success")

    def add_output(self, text, tag=None):
        self.output_area.insert(tk.END, text, tag)
        self.output_area.see(tk.END)

    def execute_code(self):
        code = self.code_input.get('1.0', tk.END).strip()
        if not code:
            self.add_output(">>> Нет кода для выполнения\n", "error")
            return

        # Сохраняем оригинальные stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        # Перенаправляем вывод
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture

        self.add_output(f"\n{'=' * 60}\n", "prompt")
        self.add_output(f"▶ Выполнение кода:\n", "success")
        self.add_output(f"{'=' * 60}\n", "prompt")

        # Отображаем выполняемый код
        for line in code.split('\n'):
            self.add_output(f">>> {line}\n", "prompt")

        self.add_output(f"\n{'─' * 60}\n", "prompt")
        self.add_output("📤 Результат:\n", "success")

        try:
            # Выполняем код
            exec_globals = {'__name__': '__console__'}
            exec(code, exec_globals)

            # Получаем вывод
            stdout_value = stdout_capture.getvalue()
            if stdout_value:
                self.add_output(stdout_value)
            else:
                self.add_output("[Код выполнен успешно, вывод отсутствует]\n", "success")

        except Exception as e:
            error_msg = traceback.format_exc()
            self.add_output(f"\n❌ Ошибка:\n{error_msg}\n", "error")
        finally:
            # Восстанавливаем stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        self.add_output(f"\n{'=' * 60}\n\n", "prompt")


class PythonTutorial:
    def __init__(self, root):
        self.root = root
        self.root.title("📘 Учебник по Python - Базовые знания + Консоль")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2b2b2b')

        # Настройка стилей
        self.setup_styles()

        # Создание главного контейнера с PanedWindow для возможности изменения размера
        self.main_paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Левая панель - теория
        self.left_frame = tk.Frame(self.main_paned, bg='#2b2b2b')
        self.main_paned.add(self.left_frame, weight=1)

        # Правая панель - консоль
        self.right_frame = tk.Frame(self.main_paned, bg='#2b2b2b')
        self.main_paned.add(self.right_frame, weight=1)

        # Создание интерфейса теории
        self.setup_theory_interface()

        # Создание консоли
        self.console = PythonConsole(self.right_frame)

    def setup_styles(self):
        # Настройка цветов и шрифтов
        self.colors = {
            'bg': '#2b2b2b',
            'button': '#3c3f41',
            'button_hover': '#4e5254',
            'text_bg': '#1e1e1e',
            'text_fg': '#d4d4d4',
            'keyword': '#569cd6',
            'string': '#ce9178',
            'comment': '#6a9955',
            'function': '#dcdcaa',
            'number': '#b5cea8'
        }

        self.fonts = {
            'title': ('Segoe UI', 14, 'bold'),
            'heading': ('Segoe UI', 11, 'bold'),
            'normal': ('Segoe UI', 9),
            'code': ('Consolas', 9),
            'button': ('Segoe UI', 9)
        }

    def setup_theory_interface(self):
        # Заголовок
        header_frame = tk.Frame(self.left_frame, bg='#2b2b2b')
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title = tk.Label(header_frame, text="🐍 Python - Базовые знания",
                         font=self.fonts['title'], bg='#2b2b2b', fg='#ffd700')
        title.pack()

        subtitle = tk.Label(header_frame,
                            text="Интерактивный учебник для начинающих | Правая панель - консоль для практики",
                            font=self.fonts['normal'], bg='#2b2b2b', fg='#888888')
        subtitle.pack()

        # Панель с кнопками
        self.create_topics_panel()

        # Область для отображения содержимого
        self.create_content_area()

        # Показать начальное сообщение
        self.show_welcome()

    def create_topics_panel(self):
        # Панель с кнопками
        buttons_frame = tk.Frame(self.left_frame, bg='#2b2b2b')
        buttons_frame.pack(fill=tk.X, pady=(0, 10))

        # Canvas для прокрутки кнопок
        canvas = tk.Canvas(buttons_frame, height=100, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(buttons_frame, orient="horizontal", command=canvas.xview)
        scrollable_frame = tk.Frame(canvas, bg='#2b2b2b')

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(xscrollcommand=scrollbar.set)

        # Список тем
        topics = [
            ("📊 Переменные и типы", self.show_variables),
            ("🔧 Базовые операции", self.show_operations),
            ("📝 Работа со строками", self.show_strings),
            ("📚 Коллекции данных", self.show_collections),
            ("🎮 Управляющие конструкции", self.show_control),
            ("⚙️ Функции", self.show_functions),
            ("⚠️ Обработка ошибок", self.show_errors),
            ("⌨️ Ввод и вывод", self.show_io),
            ("📦 Импорт модулей", self.show_modules),
            ("🎯 Понимание списков", self.show_comprehensions),
            ("🎮 Игры на Python", self.show_games)
        ]

        # Создание кнопок
        for i, (topic_name, command) in enumerate(topics):
            btn = tk.Button(scrollable_frame, text=topic_name, command=command,
                            font=self.fonts['button'], bg=self.colors['button'],
                            fg='white', padx=12, pady=6, relief=tk.FLAT,
                            cursor='hand2')
            btn.pack(side=tk.LEFT, padx=2)

            # Эффект наведения
            def on_enter(e, b=btn):
                b.configure(bg=self.colors['button_hover'])

            def on_leave(e, b=btn):
                b.configure(bg=self.colors['button'])

            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

        canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_content_area(self):
        # Область с содержимым
        self.content_frame = tk.Frame(self.left_frame, bg=self.colors['text_bg'])
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Текстовое поле с прокруткой
        self.text_area = scrolledtext.ScrolledText(self.content_frame,
                                                   wrap=tk.WORD,
                                                   font=self.fonts['code'],
                                                   bg=self.colors['text_bg'],
                                                   fg=self.colors['text_fg'],
                                                   insertbackground='white',
                                                   relief=tk.FLAT,
                                                   padx=10,
                                                   pady=10)
        self.text_area.pack(fill=tk.BOTH, expand=True)

        # Настройка тегов для подсветки синтаксиса
        self.text_area.tag_config("keyword", foreground=self.colors['keyword'])
        self.text_area.tag_config("string", foreground=self.colors['string'])
        self.text_area.tag_config("comment", foreground=self.colors['comment'])
        self.text_area.tag_config("function", foreground=self.colors['function'])
        self.text_area.tag_config("number", foreground=self.colors['number'])
        self.text_area.tag_config("title", font=self.fonts['heading'], foreground='#ffd700')
        self.text_area.tag_config("code_bg", background='#2d2d2d', font=self.fonts['code'], lmargin1=20, lmargin2=20)

        # Делаем текстовое поле только для чтения
        self.text_area.configure(state='disabled')

    def show_welcome(self):
        self.clear_text()
        self.add_text("Добро пожаловать в учебник по Python!\n\n", "title")
        self.add_text("✨ Новые возможности:\n\n", "title")
        self.add_text("• 📖 Слева - теория с примерами кода\n")
        self.add_text("• 💻 Справа - интерактивная консоль Python\n")
        self.add_text("• ⌨️ Пишите код в правой панели и нажимайте F5 или Ctrl+Enter для выполнения\n")
        self.add_text("• 🎨 Подсветка синтаксиса и цветной вывод консоли\n\n")

        self.add_text("Как пользоваться:\n", "title")
        self.add_text("1. Выберите тему из кнопок выше\n")
        self.add_text("2. Изучите теорию и примеры кода\n")
        self.add_text("3. Перейдите в правую панель и попробуйте написать свой код\n")
        self.add_text("4. Нажмите 'Выполнить' или F5 для запуска\n")
        self.add_text("5. Экспериментируйте! Консоль поддерживает любой код Python\n\n")

        self.add_text("💡 Совет: Попробуйте скопировать примеры из теории и вставить их в консоль!\n")

    def clear_text(self):
        self.text_area.configure(state='normal')
        self.text_area.delete(1.0, tk.END)

    def add_text(self, text, tag=None):
        self.text_area.configure(state='normal')
        if tag:
            self.text_area.insert(tk.END, text, tag)
        else:
            self.text_area.insert(tk.END, text)
        self.text_area.configure(state='disabled')
        self.text_area.see(tk.END)

    def add_code(self, code):
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, "\n" + code + "\n", "code_bg")
        self.text_area.configure(state='disabled')

    def show_variables(self):
        self.clear_text()
        self.add_text("📊 Переменные и типы данных\n\n", "title")
        self.add_text("Python — язык с динамической типизацией (тип определяется автоматически).\n\n")

        code = """# Числа
age = 25               # int (целое)
price = 19.99          # float (дробное)

# Строки
name = "Alice"         # str
text = 'Hello'         # можно и одинарные кавычки

# Булевы значения
is_student = True      # bool (True/False)

# None (отсутствие значения)
result = None

# Проверка типов
print(type(age))       # <class 'int'>
print(type(name))      # <class 'str'>
print(type(is_student)) # <class 'bool'>"""

        self.add_text("Примеры:\n\n")
        self.add_code(code)

        self.add_text("\n\n💡 Важно: В Python имена переменных чувствительны к регистру\n")
        self.add_text("🎯 Попробуйте в консоли:\n")
        self.add_code("""
x = 10
y = 20
print(x + y)
print(type(x))""")

    def show_operations(self):
        self.clear_text()
        self.add_text("🔧 Базовые операции\n\n", "title")

        code = """# Арифметика
sum = 10 + 5           # 15 (сложение)
diff = 10 - 5          # 5 (вычитание)
prod = 10 * 5          # 50 (умножение)
div = 10 / 5           # 2.0 (деление, всегда float)
int_div = 10 // 3      # 3 (целочисленное деление)
remainder = 10 % 3     # 1 (остаток от деления)
power = 2 ** 3         # 8 (возведение в степень)"""

        self.add_code(code)
        self.add_text("\n🎯 Попробуйте:\n")
        self.add_code("""
# Вычислите площадь круга радиуса 5
radius = 5
area = 3.14159 * radius ** 2
print(f"Площадь круга: {area}")

# Проверьте, является ли число четным
number = 10
is_even = number % 2 == 0
print(f"{number} четное? {is_even}")""")

    def show_strings(self):
        self.clear_text()
        self.add_text("📝 Работа со строками\n\n", "title")

        code = """name = "Python"

# f-строки (рекомендуемый способ)
message = f"Hello, {name}!"   # "Hello, Python!"

# Методы строк
print(name.upper())           # "PYTHON"
print(name.lower())           # "python"
print(name.startswith("Py"))  # True
print(len(name))              # 6 (длина строки)

# Срезы строк
text = "Hello World"
print(text[0:5])    # "Hello"
print(text[::-1])   # "dlroW olleH" (переворот строки)"""

        self.add_code(code)
        self.add_text("\n🎯 Попробуйте:\n")
        self.add_code("""
# Запросите имя и выведите приветствие
name = input("Как вас зовут? ")
print(f"Привет, {name.upper()}!")

# Создайте палиндром
word = "казак"
is_palindrome = word == word[::-1]
print(f"'{word}' - палиндром? {is_palindrome}")""")

    def show_collections(self):
        self.clear_text()
        self.add_text("📚 Коллекции данных\n\n", "title")

        code = """# Список (list) — изменяемый, упорядоченный
fruits = ["apple", "banana", "cherry"]
fruits.append("orange")   # добавить в конец
print(fruits[0])          # "apple"

# Словарь (dict) — пары ключ-значение
person = {
    "name": "Bob",
    "age": 30,
    "city": "Moscow"
}
print(person["name"])     # "Bob"

# Множество (set) — уникальные значения
unique_nums = {1, 2, 3, 3, 2}   # {1, 2, 3}"""

        self.add_code(code)
        self.add_text("\n🎯 Попробуйте:\n")
        self.add_code("""
# Создайте список чисел и найдите сумму
numbers = [1, 2, 3, 4, 5]
total = sum(numbers)
average = total / len(numbers)
print(f"Сумма: {total}, Среднее: {average}")

# Работа со словарем
student = {"name": "Alice", "grades": [85, 90, 95]}
student["grades"].append(100)
print(f"{student['name']} оценки: {student['grades']}")""")

    def show_control(self):
        self.clear_text()
        self.add_text("🎮 Управляющие конструкции\n\n", "title")

        code = """# Условный оператор if
age = 18

if age < 18:
    print("Доступ запрещен")
elif age == 18:
    print("Только что исполнилось 18")
else:
    print("Доступ разрешен")

# Циклы
for i in range(5):
    print(f"Квадрат {i} = {i ** 2}")

# while цикл
count = 0
while count < 5:
    print(count)
    count += 1"""

        self.add_code(code)
        self.add_text("\n🎯 Попробуйте:\n")
        self.add_code("""
# Таблица умножения
for i in range(1, 6):
    for j in range(1, 6):
        print(f"{i} x {j} = {i*j}")
    print("-" * 10)

# Угадай число
secret = 7
guess = int(input("Угадайте число от 1 до 10: "))
if guess == secret:
    print("Поздравляю! Вы угадали!")
else:
    print(f"Не угадали! Загадано число {secret}")""")

    def show_functions(self):
        self.clear_text()
        self.add_text("⚙️ Функции\n\n", "title")

        code = """# Определение функции
def greet(name):
    \"\"\"Приветствие пользователя\"\"\"
    return f"Hello, {name}!"

# Вызов функции
message = greet("Alice")
print(message)

# Параметры по умолчанию
def power(base, exp=2):
    return base ** exp

print(power(5))      # 25
print(power(2, 3))   # 8

# lambda функции
square = lambda x: x ** 2
print(square(5))     # 25"""

        self.add_code(code)
        self.add_text("\n🎯 Попробуйте:\n")
        self.add_code("""
# Напишите функцию для проверки простого числа
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

print(is_prime(17))  # True
print(is_prime(20))  # False

# Функция для подсчета слов
def word_count(text):
    return len(text.split())

print(word_count("Hello world from Python"))  # 4""")

    def show_errors(self):
        self.clear_text()
        self.add_text("⚠️ Обработка ошибок\n\n", "title")

        code = """try:
    number = int(input("Введите число: "))
    result = 10 / number
    print(f"Результат: {result}")
except ValueError:
    print("Это не число!")
except ZeroDivisionError:
    print("На ноль делить нельзя!")
except Exception as e:
    print(f"Ошибка: {e}")
finally:
    print("Этот блок выполнится всегда")"""

        self.add_code(code)
        self.add_text("\n🎯 Попробуйте:\n")
        self.add_code("""
# Калькулятор с обработкой ошибок
def safe_divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return "Ошибка: деление на ноль"
    except TypeError:
        return "Ошибка: неверный тип данных"

print(safe_divide(10, 2))   # 5.0
print(safe_divide(10, 0))   # Ошибка: деление на ноль
print(safe_divide(10, "2")) # Ошибка: неверный тип данных""")

    def show_io(self):
        self.clear_text()
        self.add_text("⌨️ Ввод и вывод\n\n", "title")

        code = """# Вывод на экран
print("Hello", "World", sep="-", end="!\\n")

# Ввод данных
name = input("Как вас зовут? ")
age = int(input("Сколько лет? "))

# Работа с файлами
with open("test.txt", "w", encoding="utf-8") as file:
    file.write("Hello World\\n")
    file.write("Вторая строка")

# Чтение из файла
with open("test.txt", "r", encoding="utf-8") as file:
    content = file.read()
    print(content)"""

        self.add_code(code)
        self.add_text("\n🎯 Попробуйте:\n")
        self.add_code("""
# Создайте простой журнал
def log_message(message):
    with open("log.txt", "a", encoding="utf-8") as f:
        from datetime import datetime
        f.write(f"{datetime.now()}: {message}\\n")

log_message("Программа запущена")
log_message("Пользователь вошел в систему")
print("Сообщения сохранены в log.txt")

# Чтение файла построчно
with open("log.txt", "r", encoding="utf-8") as f:
    for line in f:
        print(line.strip())""")

    def show_modules(self):
        self.clear_text()
        self.add_text("📦 Импорт модулей\n\n", "title")

        code = """# Импорт всего модуля
import math
print(math.sqrt(16))   # 4.0
print(math.pi)         # 3.141592653589793

# Импорт конкретных функций
from random import randint, choice
print(randint(1, 10))  # случайное число

items = ["apple", "banana", "cherry"]
print(choice(items))   # случайный элемент

# Импорт с псевдонимом
import datetime as dt
print(dt.datetime.now())"""

        self.add_code(code)
        self.add_text("\n🎯 Попробуйте:\n")
        self.add_code("""
# Генератор случайных паролей
import random
import string

def generate_password(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

print(f"Пароль: {generate_password(12)}")

# Работа со временем
import time
print("Начинаем отсчет...")
for i in range(3, 0, -1):
    print(i)
    time.sleep(1)
print("Поехали!")""")

    def show_comprehensions(self):
        self.clear_text()
        self.add_text("🎯 Понимание списков\n\n", "title")

        code = """# List comprehension
squares = [x ** 2 for x in range(5)]  # [0, 1, 4, 9, 16]

# С условием
evens = [x for x in range(10) if x % 2 == 0]  # [0, 2, 4, 6, 8]

# Dictionary comprehension
squares_dict = {x: x**2 for x in range(5)}

# Set comprehension
unique_chars = {char for char in "hello world"}"""

        self.add_code(code)
        self.add_text("\n🎯 Попробуйте:\n")
        self.add_code("""
# Создайте список квадратов четных чисел
even_squares = [x**2 for x in range(10) if x % 2 == 0]
print(even_squares)  # [0, 4, 16, 36, 64]

# Фильтрация слов по длине
words = ["hello", "world", "python", "code", "programming"]
long_words = [word.upper() for word in words if len(word) > 5]
print(long_words)

# Создание словаря из двух списков
names = ["Alice", "Bob", "Charlie"]
scores = [85, 92, 78]
grade_dict = {name: score for name, score in zip(names, scores)}
print(grade_dict)""")

    def show_games(self):
        self.clear_text()
        self.add_text("🎮 Создаем простые игры на Python\n\n", "title")

        code = """# Игра "Угадай число"
import random

def guess_number():
    number = random.randint(1, 100)
    attempts = 0

    print("Я загадал число от 1 до 100!")

    while True:
        try:
            guess = int(input("Ваше предположение: "))
            attempts += 1

            if guess < number:
                print("Больше!")
            elif guess > number:
                print("Меньше!")
            else:
                print(f"Поздравляю! Вы угадали за {attempts} попыток!")
                break
        except ValueError:
            print("Введите число!")

# Запустите игру в консоли!
# guess_number()"""

        self.add_code(code)
        self.add_text("\n🎯 Попробуйте создать свои игры:\n")
        self.add_code("""
# Камень-ножницы-бумага
import random

choices = ["камень", "ножницы", "бумага"]

player = input("Ваш выбор (камень/ножницы/бумага): ").lower()
computer = random.choice(choices)

print(f"Компьютер выбрал: {computer}")

if player == computer:
    print("Ничья!")
elif (player == "камень" and computer == "ножницы") or \\
     (player == "ножницы" and computer == "бумага") or \\
     (player == "бумага" and computer == "камень"):
    print("Вы выиграли!")
else:
    print("Компьютер выиграл!")""")


def main():
    root = tk.Tk()
    app = PythonTutorial(root)
    root.mainloop()


if __name__ == "__main__":
    main()