import tkinter as tk
from datetime import datetime
import time

class TimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Таймер з історією")
        self.root.geometry("400x550")
        self.root.configure(bg="#2c3e50")

        # Змінні
        self.start_time = 0
        self.elapsed_time = 0
        self.is_running = False

        # Віджет дисплея
        self.label = tk.Label(root, text="00:00:00.0", font=("Helvetica", 40, "bold"), 
                              bg="#2c3e50", fg="#ecf0f1")
        self.label.pack(pady=30)

        # Фрейм для кнопок
        btn_frame = tk.Frame(root, bg="#2c3e50")
        btn_frame.pack(pady=10)

        self.btn_start = tk.Button(btn_frame, text="СТАРТ", command=self.start_timer, 
                                   width=12, bg="#27ae60", fg="white", font=("Arial", 10, "bold"))
        self.btn_start.grid(row=0, column=0, padx=5)

        self.btn_stop = tk.Button(btn_frame, text="СТОП", command=self.stop_timer, 
                                  width=12, bg="#c0392b", fg="white", font=("Arial", 10, "bold"))
        self.btn_stop.grid(row=0, column=1, padx=5)

        # Кнопка для перегляду часу під час роботи
        self.btn_check = tk.Button(root, text="ЗАФІКСУВАТИ ПОТОЧНИЙ ЧАС", command=self.save_current_split, 
                                   width=30, bg="#2980b9", fg="white", font=("Arial", 10))
        self.btn_check.pack(pady=10)

        # Список історії
        tk.Label(root, text="Історія заїздів/замірів:", bg="#2c3e50", fg="#bdc3c7").pack()
        self.history_list = tk.Listbox(root, width=45, height=12, bg="#34495e", 
                                       fg="white", font=("Courier", 10), borderwidth=0)
        self.history_list.pack(pady=10, padx=20)

        self.btn_clear = tk.Button(root, text="Очистити історію", command=lambda: self.history_list.delete(0, tk.END),
                                   bg="#7f8c8d", fg="white", bd=0)
        self.btn_clear.pack()

    def format_time(self, seconds):
        """Перетворює секунди у формат ГГ:ХХ:СС.мс"""
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        milliseconds = int((secs - int(secs)) * 10)
        return f"{int(hours):02d}:{int(mins):02d}:{int(secs):02d}.{milliseconds}"

    def update_clock(self):
        """Оновлює цифри на екрані кожні 100 мілісекунд"""
        if self.is_running:
            current_elapsed = time.time() - self.start_time
            self.label.config(text=self.format_time(current_elapsed))
            self.root.after(100, self.update_clock)

    def start_timer(self):
        if not self.is_running:
            self.is_running = True
            # Починаємо відлік з поправкою на вже пройдений час (якщо була пауза)
            self.start_time = time.time() - self.elapsed_time
            self.update_clock()

    def stop_timer(self):
        if self.is_running:
            self.is_running = False
            self.elapsed_time = time.time() - self.start_time
            self.add_to_history("ЗУПИНКА")
            # Скидаємо для наступного разу
            self.elapsed_time = 0 

    def save_current_split(self):
        """Кнопка 'скільки пройшло часу' без зупинки"""
        if self.is_running:
            self.add_to_history("ПРОМІЖНИЙ")
        else:
            self.history_list.insert(0, "Спочатку натисніть СТАРТ!")

    def add_to_history(self, tag):
        """Додає запис: Дата | Тип | Час"""
        now = datetime.now().strftime("%d.%m %H:%M:%S")
        current_display = self.label.cget("text")
        record = f"[{now}] {tag}: {current_display}"
        self.history_list.insert(0, record) # Додає в початок списку

if __name__ == "__main__":
    root = tk.Tk()
    app = TimerApp(root)
    root.mainloop()