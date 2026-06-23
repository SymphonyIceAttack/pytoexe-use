import tkinter as tk
from tkinter import messagebox
import time

class TypingTest:
    def __init__(self, master):
        self.master = master
        self.master.title("Тест скорости печати")
        self.text_to_type = ""
        self.start_time = None
        self.end_time = None
        self.timer_running = False

        # Встроенные длинные тексты без тире
        self.texts = {
            "Текст 1": (
                "Это первый пример длинного текста для теста скорости печати. "
                "Пожалуйста, напечатайте его как можно быстрее и без ошибок. "
                "Текст содержит много слов и помогает проверить навыки печати. "
                "Удачи! "
                "Помните, важно не только быстро, но и правильно вводить слова."
            ),
            "Текст 2": (
                "Второй пример текста предназначен для более сложной проверки навыков печати. "
                "Он содержит длинные предложения и разнообразные слова. "
                "Постарайтесь сохранить скорость и точность, чтобы добиться хорошего результата. "
                "Практика делает мастера!"
            ),
            "Текст 3": (
                "Это третий пример с длинным текстом, который поможет вам улучшить навыки скоростной печати. "
                "Чем больше вы тренируетесь, тем лучше становятся ваши навыки. "
                "Не торопитесь, старайтесь вводить слова без ошибок, чтобы повысить свою скорость."
            )
        }

        # Создаем виджеты
        self.frame_top = tk.Frame(master)
        self.frame_top.pack(pady=5)

        self.load_button = tk.Button(self.frame_top, text="Загрузить текст из файла", command=self.load_text)
        self.load_button.pack(side='left', padx=5)

        self.text_choice_var = tk.StringVar(value="Выберите текст")
        self.text_choice_menu = tk.OptionMenu(self.frame_top, self.text_choice_var, *self.texts.keys(), command=self.select_text)
        self.text_choice_menu.pack(side='left', padx=5)

        self.timer_label = tk.Label(master, text="Время: 0 секунд", font=("Arial", 14))
        self.timer_label.pack(pady=5)

        self.text_display = tk.Text(master, height=10, width=80, wrap='word', state='disabled', font=("Arial", 14))
        self.text_display.pack(pady=5)

        self.text_entry = tk.Text(master, height=10, width=80, wrap='word', font=("Arial", 14))
        self.text_entry.pack(pady=5)
        self.text_entry.bind("<KeyRelease>", self.check_text)

        self.stats_label = tk.Label(master, text="Слова: 0", font=("Arial", 12))
        self.stats_label.pack(pady=5)

        self.start_button = tk.Button(master, text="Старт", command=self.start_test)
        self.start_button.pack(pady=5)

        self.reset_button = tk.Button(master, text="Сбросить", command=self.reset_test)
        self.reset_button.pack(pady=5)

        self.correct_words = 0
        self.total_words = 0
        self.test_started = False

        # Изначально выбираем первый текст
        self.select_text(list(self.texts.keys())[0])

    def load_text(self):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.text_to_type = file.read()
            self.display_text()
            self.reset_test()

    def select_text(self, selection):
        self.text_choice_var.set(selection)
        self.text_to_type = self.texts.get(selection, "")
        self.display_text()
        self.reset_test()

    def display_text(self):
        self.text_display.config(state='normal')
        self.text_display.delete(1.0, tk.END)
        self.text_display.insert(tk.END, self.text_to_type)
        self.text_display.config(state='disabled')

    def start_test(self):
        if not self.text_to_type:
            messagebox.showwarning("Внимание", "Пожалуйста, выберите или введите текст перед началом теста.")
            return
        self.text_entry.delete(1.0, tk.END)
        self.correct_words = 0
        self.total_words = len(self.text_to_type.split())
        self.stats_label.config(text=f"Слова: 0 / {self.total_words}")
        self.start_time = time.time()
        self.test_started = True
        self.timer_running = True
        self.update_timer()

    def update_timer(self):
        if self.test_started and self.timer_running:
            elapsed_seconds = int(time.time() - self.start_time)
            self.timer_label.config(text=f"Время: {elapsed_seconds} секунд")
            self.master.after(1000, self.update_timer)

    def stop_timer(self):
        self.timer_running = False

    def reset_test(self):
        self.text_entry.delete(1.0, tk.END)
        self.stats_label.config(text=f"Слова: 0")
        self.test_started = False
        self.start_time = None
        self.end_time = None
        self.stop_timer()
        self.timer_label.config(text="Время: 0 секунд")
        self.clear_tags()

    def clear_tags(self):
        self.text_display.config(state='normal')
        self.text_display.tag_remove("correct", "1.0", tk.END)
        self.text_display.tag_remove("error", "1.0", tk.END)
        self.text_display.config(state='disabled')

    def check_text(self, event=None):
        if not self.test_started:
            return
        typed_text = self.text_entry.get(1.0, tk.END).rstrip()
        original_text = self.text_to_type

        # Очистка предыдущих выделений
        self.text_display.config(state='normal')
        self.text_display.delete(1.0, tk.END)
        self.text_display.insert(tk.END, original_text)
        self.text_display.tag_remove("correct", "1.0", tk.END)
        self.text_display.tag_remove("error", "1.0", tk.END)

        typed_words = typed_text.split()
        original_words = original_text.split()

        # Обработка по словам
        start_index = "1.0"
        correct_count = 0

        for i, word in enumerate(typed_words):
            # Ищем слово в оригинале начиная с текущей позиции
            start_pos = self.text_display.search(word, start_index, stopindex=tk.END)
            if start_pos:
                end_pos = f"{start_pos} + {len(word)}c"
                # Определяем правильное ли слово
                if i < len(original_words) and word == original_words[i]:
                    tag_name = f"word_{i}_correct"
                    self.text_display.tag_add(tag_name, start_pos, end_pos)
                    self.text_display.tag_config(tag_name, foreground="green")
                    correct_count += 1
                else:
                    tag_name = f"word_{i}_error"
                    self.text_display.tag_add(tag_name, start_pos, end_pos)
                    self.text_display.tag_config(tag_name, foreground="red")
                start_index = end_pos
            else:
                # Если слово не найдено, можно пропустить или выделить как ошибку
                pass

        self.text_display.config(state='disabled')
        self.stats_label.config(text=f"Слова: {correct_count} / {self.total_words}")

        if correct_count == self.total_words:
            self.end_time = time.time()
            self.stop_timer()
            duration = self.end_time - self.start_time
            wpm = self.total_words / duration * 60
            messagebox.showinfo("Тест завершен", f"Вы напечатали {self.total_words} слов за {duration:.2f} секунд.\nСкорость: {wpm:.2f} слов в минуту.")
            self.test_started = False

if __name__ == "__main__":
    root = tk.Tk()
    app = TypingTest(root)
    root.mainloop()