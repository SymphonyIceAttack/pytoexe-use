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

        self.stats_label = tk.Label(master, text="Буквы: 0", font=("Arial", 12))
        self.stats_label.pack(pady=5)

        self.start_button = tk.Button(master, text="Старт", command=self.start_test)
        self.start_button.pack(pady=5)

        self.reset_button = tk.Button(master, text="Сбросить", command=self.reset_test)
        self.reset_button.pack(pady=5)

        self.correct_letters = 0
        self.total_letters = 0
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
        self.correct_letters = 0
        self.total_letters = len(self.text_to_type)
        self.stats_label.config(text=f"Буквы: 0 / {self.total_letters}")
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
        self.stats_label.config(text=f"Буквы: 0")
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

        # Обновляем отображение оригинального текста
        self.text_display.config(state='normal')
        self.text_display.delete(1.0, tk.END)
        self.text_display.insert(tk.END, original_text)

        # Удаляем предыдущие теги
        self.text_display.tag_remove("correct", "1.0", tk.END)
        self.text_display.tag_remove("error", "1.0", tk.END)

        # Проверка по буквам
        min_length = min(len(typed_text), len(original_text))
        correct_letters = 0

        for i in range(min_length):
            start_pos = f"1.0 + {i}c"
            end_pos = f"1.0 + {i+1}c"
            if typed_text[i] == original_text[i]:
                self.text_display.tag_add("correct", start_pos, end_pos)
                self.text_display.tag_config("correct", foreground="green")
                correct_letters += 1
            else:
                self.text_display.tag_add("error", start_pos, end_pos)
                self.text_display.tag_config("error", foreground="red")

        # Обработка оставшихся символов, если введено больше
        if len(typed_text) > len(original_text):
            for i in range(len(original_text), len(typed_text)):
                start_pos = f"1.0 + {i}c"
                end_pos = f"1.0 + {i+1}c"
                self.text_display.tag_add("error", start_pos, end_pos)
                self.text_display.tag_config("error", foreground="red")

        self.text_display.config(state='disabled')
        self.correct_letters = correct_letters
        self.stats_label.config(text=f"Буквы: {self.correct_letters} / {self.total_letters}")

        # Проверка завершения
        if self.correct_letters == self.total_letters:
            self.end_time = time.time()
            self.stop_timer()
            duration = self.end_time - self.start_time
            wpm = self.total_letters / duration * 60  # по буквам
            messagebox.showinfo("Тест завершен", f"Вы напечатали {self.total_letters} букв за {duration:.2f} секунд.\nСкорость: {wpm:.2f} букв в минуту.")
            self.test_started = False

if __name__ == "__main__":
    root = tk.Tk()
    app = TypingTest(root)
    root.mainloop()