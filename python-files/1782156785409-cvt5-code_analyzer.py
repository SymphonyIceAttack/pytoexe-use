import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import re
import os
import ast
import keyword
import math


class CodeAnalyzer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("КодАнализатор — Человек vs ИИ")
        self.root.geometry("1100x750")
        self.root.configure(bg="#1e1e2e")
        self.root.minsize(900, 600)
        self.create_styles()
        self.create_widgets()

    def create_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#1e1e2e", borderwidth=0)
        style.configure("TNotebook.Tab", background="#313244", foreground="#cdd6f4",
                         padding=[15, 8], font=("Segoe UI", 10))
        style.map("TNotebook.Tab",
                  background=[("selected", "#45475a")],
                  foreground=[("selected", "#f5c2e7")])
        style.configure("TFrame", background="#1e1e2e")
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4",
                         font=("Segoe UI", 10))
        style.configure("Title.TLabel", background="#1e1e2e", foreground="#f5c2e7",
                         font=("Segoe UI", 14, "bold"))
        style.configure("Header.TLabel", background="#1e1e2e", foreground="#89b4fa",
                         font=("Segoe UI", 11, "bold"))
        style.configure("Metric.TLabel", background="#1e1e2e", foreground="#a6e3a1",
                         font=("Consolas", 10))
        style.configure("Warning.TLabel", background="#1e1e2e", foreground="#fab387",
                         font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=[12, 6])
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", background="#313244", foreground="#cdd6f4",
                         fieldbackground="#313244", font=("Consolas", 9), rowheight=24)
        style.configure("Treeview.Heading", background="#45475a", foreground="#89b4fa",
                         font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#585b70")])

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        title_label = ttk.Label(main_frame, text="КодАнализатор — Человек vs ИИ",
                                style="Title.TLabel")
        title_label.pack(pady=(0, 8))

        subtitle = ttk.Label(main_frame,
                             text="Анализатор качества кода: определяет стиль, метрики и демонстрирует ограничения ИИ",
                             style="TLabel")
        subtitle.pack(pady=(0, 10))

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_input = ttk.Frame(self.notebook)
        self.tab_results = ttk.Frame(self.notebook)
        self.tab_compare = ttk.Frame(self.notebook)
        self.tab_about = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_input, text="  Ввод кода  ")
        self.notebook.add(self.tab_results, text="  Результаты анализа  ")
        self.notebook.add(self.tab_compare, text="  Человек vs ИИ  ")
        self.notebook.add(self.tab_about, text="  О проекте  ")

        self.create_input_tab()
        self.create_results_tab()
        self.create_compare_tab()
        self.create_about_tab()

    def create_input_tab(self):
        top_frame = ttk.Frame(self.tab_input)
        top_frame.pack(fill=tk.X, pady=(5, 5))

        ttk.Label(top_frame, text="Исходный код для анализа:",
                  style="Header.TLabel").pack(anchor=tk.W)

        btn_frame = ttk.Frame(top_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(btn_frame, text="Загрузить файл",
                   command=self.load_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Вставить пример (Человек)",
                   command=self.insert_human_example).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Вставить пример (ИИ)",
                   command=self.insert_ai_example).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Очистить",
                   command=self.clear_input).pack(side=tk.LEFT, padx=5)

        self.code_text = scrolledtext.ScrolledText(
            self.tab_input, wrap=tk.WORD, font=("Consolas", 10),
            bg="#313244", fg="#cdd6f4", insertbackground="#f5c2e7",
            selectbackground="#585b70", relief=tk.FLAT, padx=8, pady=8
        )
        self.code_text.pack(fill=tk.BOTH, expand=True, pady=(5, 5))

        bottom_frame = ttk.Frame(self.tab_input)
        bottom_frame.pack(fill=tk.X)

        self.status_label = ttk.Label(bottom_frame, text="Готов к анализу",
                                       style="TLabel")
        self.status_label.pack(side=tk.LEFT)

        ttk.Button(bottom_frame, text="Анализировать код",
                   style="Accent.TButton",
                   command=self.analyze_code).pack(side=tk.RIGHT, padx=5)
        ttk.Button(bottom_frame, text="Сравнить с ИИ",
                   style="Accent.TButton",
                   command=self.compare_with_ai).pack(side=tk.RIGHT, padx=5)

    def create_results_tab(self):
        paned = ttk.PanedWindow(self.tab_results, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Метрики кода",
                  style="Header.TLabel").pack(anchor=tk.W, pady=(5, 5))

        self.metrics_tree = ttk.Treeview(left_frame,
                                          columns=("metric", "value"),
                                          show="headings", height=15)
        self.metrics_tree.heading("metric", text="Метрика")
        self.metrics_tree.heading("value", text="Значение")
        self.metrics_tree.column("metric", width=220)
        self.metrics_tree.column("value", width=180)
        self.metrics_tree.pack(fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)

        ttk.Label(right_frame, text="Детали анализа",
                  style="Header.TLabel").pack(anchor=tk.W, pady=(5, 5))

        self.details_text = scrolledtext.ScrolledText(
            right_frame, wrap=tk.WORD, font=("Consolas", 9),
            bg="#313244", fg="#cdd6f4", relief=tk.FLAT, padx=8, pady=8
        )
        self.details_text.pack(fill=tk.BOTH, expand=True)

        bottom_frame = ttk.Frame(self.tab_results)
        bottom_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(bottom_frame, text="Общая оценка:",
                  style="Header.TLabel").pack(side=tk.LEFT)

        self.score_label = ttk.Label(bottom_frame, text="—",
                                      style="Title.TLabel")
        self.score_label.pack(side=tk.LEFT, padx=10)

    def create_compare_tab(self):
        ttk.Label(self.tab_compare,
                  text="Сравнение: Человек-программист vs Генеративный ИИ",
                  style="Header.TLabel").pack(anchor=tk.W, pady=(10, 5))

        intro_text = (
            "Эта вкладка демонстрирует типичные отличия между кодом, "
            "написанным человеком, и кодом, сгенерированным ИИ.\n"
            "Нажмите кнопку для генерации примера сравнения."
        )
        ttk.Label(self.tab_compare, text=intro_text,
                  style="TLabel", wraplength=1000).pack(anchor=tk.W, pady=(0, 10))

        ttk.Button(self.tab_compare, text="Показать сравнение",
                   style="Accent.TButton",
                   command=self.show_comparison).pack(anchor=tk.W, pady=(0, 10))

        paned = ttk.PanedWindow(self.tab_compare, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(paned)
        paned.add(left, weight=1)
        ttk.Label(left, text="Код человека", style="Header.TLabel").pack(anchor=tk.W)
        self.human_code_text = scrolledtext.ScrolledText(
            left, wrap=tk.WORD, font=("Consolas", 9),
            bg="#313244", fg="#a6e3a1", relief=tk.FLAT, padx=8, pady=8
        )
        self.human_code_text.pack(fill=tk.BOTH, expand=True)

        right = ttk.Frame(paned)
        paned.add(right, weight=1)
        ttk.Label(right, text="Код ИИ", style="Header.TLabel").pack(anchor=tk.W)
        self.ai_code_text = scrolledtext.ScrolledText(
            right, wrap=tk.WORD, font=("Consolas", 9),
            bg="#313244", fg="#fab387", relief=tk.FLAT, padx=8, pady=8
        )
        self.ai_code_text.pack(fill=tk.BOTH, expand=True)

        self.compare_notes = scrolledtext.ScrolledText(
            self.tab_compare, wrap=tk.WORD, font=("Segoe UI", 9),
            bg="#313244", fg="#f9e2af", relief=tk.FLAT, padx=8, pady=8, height=6
        )
        self.compare_notes.pack(fill=tk.X, pady=(5, 0))

    def create_about_tab(self):
        about_text = (
            "ПРОЕКТ: «Влияние ИИ на программирование»\n\n"
            "ЦЕЛЬ ПРОГРАММЫ:\n"
            "Продемонстрировать, что искусственный интеллект является лишь "
            "инструментом помощи программисту, а не его заменой.\n\n"
            "КАК ЭТО РАБОТАЕТ:\n"
            "Программа анализирует исходный код по множеству метрик:\n"
            "  • Структура кода (функции, классы, модули)\n"
            "  • Качество именования переменных и функций\n"
            "  • Уровень комментирования\n"
            "  • Сложность кода (ветвления, циклы)\n"
            "  • Наличие магических чисел\n"
            "  • Длина функций\n"
            "  • Уровень вложенности\n\n"
            "На основании анализа программа определяет стиль кода:\n"
            "  — Стиль «человека»: уникальные решения, комментарии, понятные имена,\n"
            "     осознанная архитектура\n"
            "  — Стиль «ИИ»: шаблонность, избыточность, «вода»,\n"
            "     типичные паттерны генеративных моделей\n\n"
            "ОГРАНИЧЕНИЯ ИИ, КОТОРЫЕ ДЕМОНСТРИРУЕТ ПРОГРАММА:\n"
            "  1. ИИ не понимает контекст бизнес-задачи\n"
            "  2. ИИ генерирует избыточный, шаблонный код\n"
            "  3. ИИ не учитывает особенности проекта\n"
            "  4. ИИ не способен к творческому подходу\n"
            "  5. ИИ не может принимать архитектурные решения\n\n"
            "ТЕХНОЛОГИИ: Python 3, Tkinter (стандартная библиотека)\n\n"
            "Автор: [ФИО]\n"
            "Направление подготовки: 09.02.07 Информационные системы и программирование\n"
        )
        text_widget = scrolledtext.ScrolledText(
            self.tab_about, wrap=tk.WORD, font=("Segoe UI", 10),
            bg="#313244", fg="#cdd6f4", relief=tk.FLAT, padx=15, pady=15
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, about_text)
        text_widget.config(state=tk.DISABLED)

    def load_file(self):
        filepath = filedialog.askopenfilename(
            title="Выберите файл с кодом",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                self.code_text.delete("1.0", tk.END)
                self.code_text.insert(tk.END, content)
                self.status_label.config(
                    text=f"Загружен: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось прочитать файл:\n{e}")

    def clear_input(self):
        self.code_text.delete("1.0", tk.END)
        self.status_label.config(text="Готов к анализу")

    def insert_human_example(self):
        example = '''\
def calculate_average(numbers):
    """Calculate the arithmetic mean of a list of numbers."""
    if not numbers:
        return 0
    total = sum(numbers)
    return total / len(numbers)


def find_max_value(data):
    """Find the maximum value in a list, handling empty list."""
    if not data:
        return None
    max_val = data[0]
    for item in data[1:]:
        if item > max_val:
            max_val = item
    return max_val


# Main program
scores = [85, 92, 78, 90, 88, 76, 95, 89]
average = calculate_average(scores)
highest = find_max_value(scores)

print(f"Average score: {average:.1f}")
print(f"Highest score: {highest}")
'''
        self.code_text.delete("1.0", tk.END)
        self.code_text.insert(tk.END, example)
        self.status_label.config(text="Вставлен пример: код человека")

    def insert_ai_example(self):
        example = '''\
def function_1(param_1):
    result = []
    for i in range(len(param_1)):
        if param_1[i] is not None:
            if param_1[i] > 0:
                result.append(param_1[i] * 2)
            else:
                result.append(param_1[i])
        else:
            result.append(0)
    return result

def function_2(param_2):
    temp_var = 0
    for element in param_2:
        if element > temp_var:
            temp_var = element
    if len(param_2) == 0:
        return None
    else:
        return temp_var

def function_3(param_3, param_4):
    output = []
    count = 0
    while count < len(param_3):
        if param_3[count] % 2 == 0:
            output.append(param_3[count] + param_4)
        else:
            output.append(param_3[count] - param_4)
        count = count + 1
    return output

data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
result_1 = function_1(data)
result_2 = function_2(data)
result_3 = function_3(data, 5)
'''
        self.code_text.delete("1.0", tk.END)
        self.code_text.insert(tk.END, example)
        self.status_label.config(text="Вставлен пример: код ИИ")

    def analyze_code(self):
        code = self.code_text.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("Внимание", "Введите или загрузите код для анализа.")
            return

        metrics = self.calculate_metrics(code)
        score = self.calculate_quality_score(metrics)

        self.display_metrics(metrics)
        self.display_details(code, metrics, score)
        self.score_label.config(text=f"{score}/100")

        self.status_label.config(text="Анализ завершён")

        self.notebook.select(self.tab_results)

    def compare_with_ai(self):
        code = self.code_text.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("Внимание", "Введите или загрузите код для анализа.")
            return

        metrics = self.calculate_metrics(code)
        style = self.detect_style(metrics)

        if style == "human":
            msg = (
                "Определён стиль: ЧЕЛОВЕК\n\n"
                "Код содержит признаки написания человеком:\n"
                "• осмысленные имена переменных\n"
                "• наличие комментариев/документации\n"
                "• осознанная структура\n\n"
                "Это подтверждает, что ИИ пока не способен генерировать\n"
                "код с такой же осмысленностью и контекстуальностью."
            )
        elif style == "ai":
            msg = (
                "Определён стиль: ИИ\n\n"
                "Код содержит характерные признаки генеративного ИИ:\n"
                "• шаблонные имена (function_1, param_1)\n"
                "• избыточные условия и ветвления\n"
                "• отсутствие документации\n"
                "• «вода» и повторяющиеся паттерны\n\n"
                "Это демонстрирует ограничения ИИ: он генерирует\n"
                "работоспособный, но низкокачественный код."
            )
        else:
            msg = (
                "Стиль кода: НЕОПРЕДЕЛЁННЫЙ\n\n"
                "Код содержит признаки обоих стилей.\n"
                "Возможно, это результат совместной работы человека и ИИ."
            )

        messagebox.showinfo("Определение стиля", msg)
        self.status_label.config(text=f"Определён стиль: {style}")

    def calculate_metrics(self, code):
        lines = code.split("\n")
        non_empty = [l for l in lines if l.strip()]
        code_lines = [l for l in non_empty if not l.strip().startswith("#")]

        comment_lines = [l for l in lines if l.strip().startswith("#")]
        docstring_count = len(re.findall(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', code))

        functions = re.findall(r'def\s+(\w+)', code)
        classes = re.findall(r'class\s+(\w+)', code)
        imports = re.findall(r'(?:from\s+\S+\s+)?import\s+\S+', code)

        variable_names = re.findall(
            r'(?:(?:def|class|for|with)\s+(\w+)|(?:=|,)\s*(\w+)\s*[=,\n])', code)
        flat_names = [n for pair in variable_names for n in pair if n]

        magic_numbers = re.findall(
            r'(?<!=\s)(?<!\w)\d{2,}(?!\w)', code)
        magic_numbers = [m for m in magic_numbers
                         if int(m) not in (0, 1, 2, 10, 100)]

        short_names = [n for n in flat_names if len(n) <= 1 and n not in ('_', 'i', 'j', 'k')]
        descriptive_names = [n for n in flat_names if len(n) > 3]

        for_count = len(re.findall(r'\bfor\b', code))
        while_count = len(re.findall(r'\bwhile\b', code))
        if_count = len(re.findall(r'\bif\b', code))
        try_count = len(re.findall(r'\btry\b', code))

        nesting = self._max_nesting(code)

        func_lengths = self._function_lengths(code)

        avg_func_len = (sum(func_lengths) / len(func_lengths)) if func_lengths else 0

        total_lines = len(lines)
        comment_ratio = len(comment_lines) / total_lines if total_lines else 0
        name_quality = len(descriptive_names) / len(flat_names) if flat_names else 0

        return {
            "total_lines": total_lines,
            "code_lines": len(code_lines),
            "comment_lines": len(comment_lines),
            "comment_ratio": round(comment_ratio, 3),
            "docstrings": docstring_count,
            "functions": len(functions),
            "classes": len(classes),
            "imports": len(imports),
            "variables": len(flat_names),
            "descriptive_names": len(descriptive_names),
            "short_names": len(short_names),
            "name_quality": round(name_quality, 3),
            "magic_numbers": len(magic_numbers),
            "for_loops": for_count,
            "while_loops": while_count,
            "if_statements": if_count,
            "try_blocks": try_count,
            "max_nesting": nesting,
            "function_lengths": func_lengths,
            "avg_func_length": round(avg_func_len, 1),
        }

    def _max_nesting(self, code):
        max_depth = 0
        current_depth = 0
        for line in code.split("\n"):
            stripped = line.lstrip()
            if not stripped:
                continue
            indent = len(line) - len(stripped)
            depth = indent // 4
            if depth > max_depth:
                max_depth = depth
        return max_depth

    def _function_lengths(self, code):
        lengths = []
        lines = code.split("\n")
        in_func = False
        func_start = 0
        func_indent = 0
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith("def "):
                in_func = True
                func_start = i
                func_indent = len(line) - len(stripped)
            elif in_func and stripped and (len(line) - len(stripped)) <= func_indent and stripped:
                if not stripped.startswith(" ") and not stripped.startswith("\t"):
                    lengths.append(i - func_start)
                    in_func = False
        if in_func:
            lengths.append(len(lines) - func_start)
        return lengths

    def calculate_quality_score(self, m):
        score = 0

        if m["comment_ratio"] > 0.1:
            score += 15
        elif m["comment_ratio"] > 0.03:
            score += 8

        if m["docstrings"] > 0:
            score += 10

        if m["name_quality"] > 0.5:
            score += 15
        elif m["name_quality"] > 0.3:
            score += 8

        if m["short_names"] == 0:
            score += 10
        elif m["short_names"] <= 2:
            score += 5

        if m["magic_numbers"] == 0:
            score += 10
        elif m["magic_numbers"] <= 2:
            score += 5

        if m["avg_func_length"] <= 15:
            score += 10
        elif m["avg_func_length"] <= 30:
            score += 5

        if m["max_nesting"] <= 3:
            score += 10
        elif m["max_nesting"] <= 5:
            score += 5

        if m["functions"] > 0:
            score += 5

        if m["try_blocks"] > 0:
            score += 5

        if m["code_lines"] > 5:
            score += 5

        if m["classes"] > 0:
            score += 5

        return min(score, 100)

    def detect_style(self, m):
        ai_signs = 0
        human_signs = 0

        if m["name_quality"] < 0.3:
            ai_signs += 2
        else:
            human_signs += 2

        if m["short_names"] > 2:
            ai_signs += 1
        else:
            human_signs += 1

        if m["comment_ratio"] < 0.03 and m["docstrings"] == 0:
            ai_signs += 2
        else:
            human_signs += 2

        if m["magic_numbers"] > 3:
            ai_signs += 1
        else:
            human_signs += 1

        if m["avg_func_length"] > 25:
            ai_signs += 1
        else:
            human_signs += 1

        if m["functions"] >= 3 and m["name_quality"] < 0.3:
            ai_signs += 2

        if ai_signs > human_signs + 2:
            return "ai"
        elif human_signs > ai_signs + 2:
            return "human"
        return "mixed"

    def display_metrics(self, m):
        for item in self.metrics_tree.get_children():
            self.metrics_tree.delete(item)

        rows = [
            ("Строк всего", m["total_lines"]),
            ("Строк кода", m["code_lines"]),
            ("Строк комментариев", m["comment_lines"]),
            ("Доля комментариев", f'{m["comment_ratio"]:.1%}'),
            ("Документ-строки (docstring)", m["docstrings"]),
            ("Функций", m["functions"]),
            ("Классов", m["classes"]),
            ("Импортов", m["imports"]),
            ("Переменных", m["variables"]),
            ("Осмысленных имён", m["descriptive_names"]),
            ("Коротких имён (<=1 символ)", m["short_names"]),
            ("Качество имён", f'{m["name_quality"]:.1%}'),
            ("Магических чисел", m["magic_numbers"]),
            ("Циклов for", m["for_loops"]),
            ("Циклов while", m["while_loops"]),
            ("Условий if", m["if_statements"]),
            ("Блоков try/except", m["try_blocks"]),
            ("Макс. вложенность", m["max_nesting"]),
            ("Средняя длина функции", f'{m["avg_func_length"]} строк'),
        ]
        for metric, value in rows:
            self.metrics_tree.insert("", tk.END, values=(metric, value))

    def display_details(self, code, m, score):
        self.details_text.delete("1.0", tk.END)

        style = self.detect_style(m)

        lines = []
        lines.append("=" * 45)
        lines.append("  РЕЗУЛЬТАТЫ АНАЛИЗА КОДА")
        lines.append("=" * 45)
        lines.append("")

        if style == "human":
            lines.append("ОПРЕДЕЛЁННЫЙ СТИЛЬ: ЧЕЛОВЕК")
            lines.append("Код написан человеком или содержит")
            lines.append("характерные признаки человеческого стиля.")
        elif style == "ai":
            lines.append("ОПРЕДЕЛЁННЫЙ СТИЛЬ: ИИ (генеративный)")
            lines.append("Код содержит признаки генерации ИИ.")
        else:
            lines.append("ОПРЕДЕЛЁННЫЙ СТИЛЬ: СМЕШАННЫЙ")
            lines.append("Возможно совместная работа человека и ИИ.")

        lines.append("")
        lines.append(f"ОБЩАЯ ОЦЕНКА: {score} / 100")
        lines.append("")

        lines.append("-" * 45)
        lines.append("ПОЗИТИВНЫЕ МОМЕНТЫ:")
        lines.append("-" * 45)
        if m["comment_ratio"] > 0.1:
            lines.append("+ Хороший уровень комментирования")
        elif m["comment_ratio"] > 0.03:
            lines.append("+ Есть комментарии (можно улучшить)")
        else:
            lines.append("- Мало комментариев")

        if m["docstrings"] > 0:
            lines.append("+ Есть документ-строки")
        else:
            lines.append("- Нет документ-строк")

        if m["name_quality"] > 0.5:
            lines.append("+ Качественные имена переменных")
        elif m["name_quality"] > 0.3:
            lines.append("~ Имена переменных среднего качества")
        else:
            lines.append("- Некачественные имена переменных")

        if m["magic_numbers"] == 0:
            lines.append("+ Нет магических чисел")
        else:
            lines.append(f"- {m['magic_numbers']} магических чисел")

        if m["try_blocks"] > 0:
            lines.append("+ Есть обработка ошибок")
        else:
            lines.append("- Нет обработки ошибок")

        if m["classes"] > 0:
            lines.append("+ Используются классы (ООП)")

        lines.append("")
        lines.append("-" * 45)
        lines.append("ОГРАНИЧЕНИЯ / ЗАМЕЧАНИЯ:")
        lines.append("-" * 45)

        if m["avg_func_length"] > 20:
            lines.append(
                f"! Средняя длина функции {m['avg_func_length']} строк"
                " (рекомендуется <= 15)")
        if m["max_nesting"] > 4:
            lines.append(
                f"! Высокая вложенность: {m['max_nesting']} уровней"
                " (рекомендуется <= 3)")
        if m["short_names"] > 3:
            lines.append(
                f"! Много коротких имён: {m['short_names']}")
        if m["magic_numbers"] > 3:
            lines.append(
                f"! Много магических чисел: {m['magic_numbers']}")
        if m["functions"] == 0 and m["code_lines"] > 10:
            lines.append("! Нет функций при большом объёме кода")

        lines.append("")
        lines.append("-" * 45)
        lines.append("ОЦЕНКА ОГРАНИЧЕНИЙ ИИ:")
        lines.append("-" * 45)

        if style == "ai":
            lines.append("• ИИ генерирует шаблонные имена (function_1, x)")
            lines.append("• ИИ создаёт избыточные условия")
            lines.append("• ИИ не добавляет документацию")
            lines.append("• ИИ не учитывает контекст задачи")
            lines.append("• ИИ не оптимизирует структуру кода")
        elif style == "human":
            lines.append("• Человек понимает бизнес-логику")
            lines.append("• Человек даёт осмысленные имена")
            lines.append("• Человек пишет документацию")
            lines.append("• Человек оптимизирует архитектуру")
            lines.append("• ИИ не способен на такой уровень понимания")
        else:
            lines.append("• Смешанный стиль затрудняет оценку")

        self.details_text.insert(tk.END, "\n".join(lines))

    def show_comparison(self):
        human_code = '''\
def calculate_discount(price, customer_type):
    """Calculate discount based on price and customer type.
    
    Args:
        price: Original product price
        customer_type: 'regular', 'vip', or 'wholesale'
    
    Returns:
        Discounted price
    """
    DISCOUNT_RATES = {
        'regular': 0.0,
        'vip': 0.15,
        'wholesale': 0.25,
    }
    
    rate = DISCOUNT_RATES.get(customer_type, 0.0)
    discount = price * rate
    final_price = price - discount
    
    # Ensure minimum price
    MIN_PRICE = 10.0
    if final_price < MIN_PRICE:
        final_price = MIN_PRICE
    
    return round(final_price, 2)
'''

        ai_code = '''\
def function_1(param_1, param_2):
    if param_2 == "regular":
        temp_var = 0.0
    elif param_2 == "vip":
        temp_var = 0.15
    elif param_2 == "wholesale":
        temp_var = 0.25
    else:
        temp_var = 0.0
    if param_1 > 0:
        if temp_var > 0:
            result = param_1 - (param_1 * temp_var)
            if result < 10:
                result = 10
            return result
        else:
            return param_1
    else:
        return 0

def function_2(param_3, param_4):
    output = []
    count = 0
    while count < len(param_3):
        result = function_1(param_3[count], param_4)
        output.append(result)
        count = count + 1
    return output

data = [100, 200, 300, 50, 10, 500]
result_1 = function_2(data, "vip")
result_2 = function_2(data, "wholesale")
'''

        notes = (
            "СРАВНЕНИЕ:\n"
            "• ЧЕЛОВЕК: использует словарь для маппинга, docstring, именованные константы, "
            "handles edge cases осознанно.\n"
            "• ИИ: использует цепочки if/elif (неоптимально), шаблонные имена (function_1, param_1), "
            "нет документации, избыточная вложенность, магические числа (10, 0.15, 0.25).\n\n"
            "ВЫВОД: ИИ создаёт рабочий, но низкокачественный код. Человек пишет "
            "читаемый, поддерживаемый, архитектурно верный код."
        )

        self.human_code_text.delete("1.0", tk.END)
        self.human_code_text.insert(tk.END, human_code)
        self.ai_code_text.delete("1.0", tk.END)
        self.ai_code_text.insert(tk.END, ai_code)
        self.compare_notes.delete("1.0", tk.END)
        self.compare_notes.insert(tk.END, notes)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = CodeAnalyzer()
    app.run()
