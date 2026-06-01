import tkinter as tk
from tkinter import messagebox, simpledialog
import random
import time

class TypingTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Тренажёр скорости печати")
        self.root.geometry("950x680") # Чуть увеличено окно по ширине

        # --- Данные ---
        self.default_phrases = [
            "Съешь ещё этих мягких французских булок да выпей же чаю.",
            "В чащах юга жил-был цитрус? Да, но фальшивый экземпляр!",
            "Ловко вскочив на коня, ястреб взвился в небеса.",
            "Python — мощный язык программирования общего назначения."
        ]
        self.current_phrase = ""
        self.start_time = 0
        self.input_state_active = False

        # Основной шрифт для интерфейса
        self.base_font = ("Consolas", 14)

        # --- Создание виджетов главного окна ---
        control_frame = tk.Frame(root)
        control_frame.pack(pady=10, fill='x')

        self.btn_start = tk.Button(control_frame, text="Старт / Начать заново", command=self.start_test, font=self.base_font)
        self.btn_start.grid(row=0, column=0, padx=5)

        self.btn_custom = tk.Button(control_frame, text="Свой текст...", command=self.set_custom_text, font=self.base_font)
        self.btn_custom.grid(row=0, column=1, padx=5)

        # Текст для набора (с тегами)
        self.text_display = tk.Text(
            root,
            height=3,
            width=100,
            font=self.base_font,
            wrap='word',
            bg='#f0f0f0',
            bd=0,
            highlightthickness=0
        )
        self.text_display.tag_configure('error', background='#FFB3BA') # Красный фон
        self.text_display.tag_configure('correct', foreground='#2E8B57', background='#E6FFF2') # Зелёный текст на светл-зелёном фоне
        self.text_display.config(state='disabled')
        self.text_display.pack(pady=10)

        # Поле для ввода пользователя
        self.entry_input = tk.Entry(root, font=self.base_font, width=80)
        self.entry_input.pack(pady=5)

        self.label_stats = tk.Label(root, text="", font=self.base_font, justify='left', fg='#555')
        self.label_stats.pack(pady=10)

        # Привязываем события
        self.entry_input.bind("<KeyRelease>", self.check_input)
        self.entry_input.bind("<FocusIn>", lambda _: self.highlight_errors())

    def set_custom_text(self):
        """Открывает диалоговое окно с большим полем для ввода текста."""
        dialog_window = tk.Toplevel(self.root)
        dialog_window.title("Собственный текст")
        dialog_window.geometry("700x500")
        dialog_window.transient(self.root)

        custom_text_area = tk.Text(dialog_window, font=self.base_font, wrap='word', undo=True)
        custom_text_area.pack(expand=True, fill='both', padx=10, pady=10)

        btn_frame = tk.Frame(dialog_window)
        btn_frame.pack(fill='x', pady=5)

        # Кнопка ОК вызывает метод save_and_close
        btn_ok = tk.Button(btn_frame, text="ОК", command=lambda: self.save_and_close(custom_text_area, dialog_window), font=self.base_font)
        btn_ok.pack(side='right', padx=5)

        btn_cancel = tk.Button(btn_frame, text="Отмена", command=dialog_window.destroy, font=self.base_font)
        btn_cancel.pack(side='right')

    def save_and_close(self, text_widget, window):
        """Обрабатывает нажатие кнопки 'ОК' в окне ввода текста."""
        entered_text = text_widget.get(1.0, tk.END).strip()
        if entered_text:
            self.custom_phrase = entered_text
            messagebox.showinfo("Готово", "Ваш текст установлен. Нажмите 'Старт'!", parent=window)
        window.destroy()

    def start_test(self):
        """Запускает новый тест."""
        if hasattr(self, 'custom_phrase'):
            self.current_phrase = self.custom_phrase
        else:
            self.current_phrase = random.choice(self.default_phrases)

        self.start_time = time.time()
        self.input_state_active = True

        self.text_display.config(state='normal')
        self.text_display.delete(1.0, tk.END)
        self.text_display.insert(tk.END, self.current_phrase)
        for i in range(len(self.current_phrase)):
            idx = f'1.{i}'
            self.text_display.tag_remove('error', idx)
            self.text_display.tag_remove('correct', idx)
        self.text_display.config(state='disabled')

        self.entry_input.config(state='normal')
        self.entry_input.delete(0, tk.END)
        self.label_stats.config(text="Печатайте! Время пошло.")
        self.entry_input.focus_set()

    def check_input(self, event=None):
        """Проверяет ввод и подсвечивает ошибки/правильные символы."""
        if not self.input_state_active:
            return

        user_text = self.entry_input.get()
        elapsed_seconds = max(time.time() - self.start_time, 1)
        wpm = round((len(user_text) / 5) / (elapsed_seconds / 60))

        errors = sum(1 for a, b in zip(self.current_phrase, user_text) if a != b)
        errors += abs(len(self.current_phrase) - len(user_text))
        accuracy_percent = round(((len(self.current_phrase) - errors) / len(self.current_phrase)) * 100) if self.current_phrase else 100

        stats_text = f"Скорость: {wpm} слов/мин | Точность: {accuracy_percent}% | Ошибок: {errors}"
        self.label_stats.config(text=stats_text)

        self.highlight_errors()

        if user_text == self.current_phrase:
            end_time = time.time()
            total_time = round(end_time - self.start_time, 2)
            self.entry_input.config(state='disabled')

            final_msg = (
                f"Тест успешно пройден!\n"
                f"Время: {total_time} сек.\n\n"
                f"{stats_text}"
            )

            # Создаём новое окно с результатом и кнопкой ОК
            result_window = tk.Toplevel(self.root)
            result_window.title("Результат")
            lbl_result = tk.Label(result_window, text=final_msg, font=self.base_font, justify='left')
            lbl_result.pack(padx=20, pady=20)

            btn_ok_result = tk.Button(result_window, text="ОК", command=result_window.destroy, font=self.base_font)
            btn_ok_result.pack(pady=10)

            self.input_state_active = False

    def highlight_errors(self):
        """
        Проходит по каждому символу и применяет теги 'correct' или 'error'.
        ИСПРАВЛЕНО: Безопасно обрабатывает ввод текста большей длины, чем оригинал.
        """
        user_text = self.entry_input.get()
        min_length = min(len(user_text), len(self.current_phrase))

        # Проверяем только до конца более короткой строки
        for i in range(min_length):
            if user_text[i] == self.current_phrase[i]:
                 self.text_display.tag_add('correct', f'1.{i}', f'1.{i+1}')
                 self.text_display.tag_remove('error', f'1.{i}', f'1.{i+1}')
            else:
                 self.text_display.tag_add('error', f'1.{i}', f'1.{i+1}')
                 self.text_display.tag_remove('correct', f'1.{i}', f'1.{i+1}')

        # Если ввод длиннее оригинала, помечаем лишние символы как ошибку
        if len(user_text) > len(self.current_phrase):
            for i in range(len(self.current_phrase), len(user_text)):
                 self.text_display.tag_add('error', f'1.{i}', f'1.{i+1}')
                 self.text_display.tag_remove('correct', f'1.{i}', f'1.{i+1}')

if __name__ == "__main__":
    root = tk.Tk()
    app = TypingTestApp(root)
    root.mainloop()