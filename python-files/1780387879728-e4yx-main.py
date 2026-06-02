import time
from datetime import datetime
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

def compute_metrics(sample_text: str, typed_text: str, elapsed_seconds: float):
    elapsed_minutes = elapsed_seconds / 60.0 if elapsed_seconds > 0 else 1e-6

    total_chars = len(sample_text)
    total_words = len(sample_text.split())

    chars_per_min = total_chars / elapsed_minutes
    words_per_min = total_words / elapsed_minutes

    min_len = min(len(sample_text), len(typed_text))
    matches = sum(1 for i in range(min_len) if sample_text[i] == typed_text[i])

    accuracy = (matches + max(0, len(sample_text) - min_len)) / max(len(sample_text), 1) * 100

    mismatches_in_overlap = sum(1 for i in range(min_len) if sample_text[i] != typed_text[i])
    length_diff = abs(len(typed_text) - len(sample_text))
    mistakes = mismatches_in_overlap + length_diff

    return {
        "elapsed_seconds": elapsed_seconds,
        "chars_per_min": chars_per_min,
        "words_per_min": words_per_min,
        "accuracy": accuracy,
        "mistakes": mistakes
    }

class TypingTestGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Счётчик скорости печати (GUI)")

        self.sample_text = (
            "The quick brown fox jumps over the lazy dog."
            " Typing speed test: measure how fast you can reproduce this sentence."
        )

        # UI элементы
        self.lbl_info = tk.Label(master, text="Тест скорости печати. Нажмите Start и затем наберите текст.", wraplength=600)
        self.lbl_info.pack(pady=5)

        self.text_to_type = ScrolledText(master, height=4, width=80, wrap="word", state="disabled")
        self.text_to_type.pack(padx=10, pady=5)
        self.text_to_type.configure(state="normal")
        self.text_to_type.insert("1.0", self.sample_text)
        self.text_to_type.configure(state="disabled")

        self.btn_frame = tk.Frame(master)
        self.btn_frame.pack(pady=5)

        self.btn_start = tk.Button(self.btn_frame, text="Start", command=self.start_test)
        self.btn_start.pack(side="left", padx=5)

        self.btn_finish = tk.Button(self.btn_frame, text="Finish", command=self.finish_test, state="disabled")
        self.btn_finish.pack(side="left", padx=5)

        self.btn_reset = tk.Button(self.btn_frame, text="Reset", command=self.reset_test)
        self.btn_reset.pack(side="left", padx=5)

        self.label_time = tk.Label(master, text="Время: 0.00 сек")
        self.label_time.pack()

        self.input_area = ScrolledText(master, height=6, width=80, wrap="word")
        self.input_area.pack(padx=10, pady=5)

        self.res_frame = tk.Frame(master)
        self.res_frame.pack(pady=5)

        self.res_cp = tk.Label(self.res_frame, text="CPM: -   WPM: -   Accuracy: -%   Errors: -")
        self.res_cp.pack()

        # Состояние теста
        self.testing = False
        self.start_time = None
        self.timer_update_id = None

    def start_test(self):
        if self.testing:
            return
        self.testing = True
        self.start_time = time.time()
        self.input_area.delete("1.0", tk.END)
        self.label_time.config(text="Время: 0.00 сек")
        self.btn_start.config(state="disabled")
        self.btn_finish.config(state="normal")
        self.update_timer()

    def update_timer(self):
        if not self.testing:
            return
        now = time.time()
        elapsed = now - self.start_time
        self.label_time.config(text=f"Время: {elapsed:.2f} сек")
        self.timer_update_id = self.master.after(100, self.update_timer)

    def finish_test(self):
        if not self.testing:
            return
        self.testing = False
        if self.timer_update_id:
            self.master.after_cancel(self.timer_update_id)
            self.timer_update_id = None

        end_time = time.time()
        elapsed_seconds = end_time - self.start_time if self.start_time else 0.0

        typed_text = self.input_area.get("1.0", tk.END).rstrip("\n")
        metrics = compute_metrics(self.sample_text, typed_text, elapsed_seconds)

        # Обновление UI
        self.res_cp.config(
            text=f"CPM: {metrics['chars_per_min']:.2f}   WPM: {metrics['words_per_min']:.2f}   "
                 f"Accuracy: {metrics['accuracy']:.2f}%   Errors: {metrics['mistakes']}"
        )

        # Сохранение результатов
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = (
            f"{timestamp} | CPM={metrics['chars_per_min']:.2f} | WPM={metrics['words_per_min']:.2f} | "
            f"Accuracy={metrics['accuracy']:.2f}% | Errors={metrics['mistakes']}\n"
            f"SampleChars={len(self.sample_text)} SampleWords={len(self.sample_text.split())} "
            f"ElapsedSec={elapsed_seconds:.3f}\n"
        )
        try:
            with open("results.txt", "a", encoding="utf-8") as f:
                f.write(log_line)
            # Путь для пользователя об успехе записи можем показать в консоли GUI, но опционально
        except Exception as e:
            # Можно вывести сообщение пользователю
            tk.messagebox.showerror("Ошибка сохранения", str(e))

        self.btn_finish.config(state="disabled")
        self.btn_start.config(state="normal")

    def reset_test(self):
        # Сброс состояния теста
        if self.timer_update_id:
            self.master.after_cancel(self.timer_update_id)
            self.timer_update_id = None
        self.testing = False
        self.start_time = None
        self.label_time.config(text="Время: 0.00 сек")
        self.input_area.delete("1.0", tk.END)
        self.res_cp.config(text="CPM: -   WPM: -   Accuracy: -%   Errors: -")
        self.btn_finish.config(state="disabled")
        self.btn_start.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = TypingTestGUI(root)
    root.mainloop()