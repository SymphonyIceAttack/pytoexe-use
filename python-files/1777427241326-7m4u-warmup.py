import tkinter as tk
from tkinter import messagebox
import time

class HealthTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Контроль активности")
        self.root.geometry("400x450")

        # Основные показатели статистики
        self.total_completed = 0      
        self.cumulative_seconds = 0   

        # Настройка таймера: 7200 секунд = 2 часа
        self.wait_duration = 7200     

        self.mode = "IDLE"            # Состояния: IDLE (покой), WORKOUT (разминка), COUNTDOWN (ожидание)
        self.start_time = 0           # Точка отсчета для секундомера
        self.target_time = 0          # Момент времени, когда таймер должен обнулиться

        self.setup_ui()

    def setup_ui(self):
        """Инициализация графического интерфейса"""
        self.status_label = tk.Label(self.root, text="Программа запущена", font=("Arial", 12))
        self.status_label.pack(pady=20)

        # Главное табло (2 часа по умолчанию)
        self.time_display = tk.Label(self.root, text="02:00:00", font=("Courier", 40, "bold"), fg="#2c3e50")
        self.time_display.pack(pady=10)

        self.btn_start = tk.Button(self.root, text="НАЧАТЬ РАЗМИНКУ", bg="#27ae60", fg="white", 
                                   width=25, height=2, command=self.start_workout)
        self.btn_start.pack(pady=5)

        self.btn_finish = tk.Button(self.root, text="ЗАВЕРШИТЬ", bg="#2980b9", fg="white", 
                                    width=25, height=2, state=tk.DISABLED, command=self.finish_workout)
        self.btn_finish.pack(pady=5)

        self.btn_stop = tk.Button(self.root, text="СТОП / СБРОС", bg="#c0392b", fg="white", 
                                  width=25, height=2, command=self.reset_system)
        self.btn_stop.pack(pady=5)

        tk.Button(self.root, text="Статистика", command=self.show_stats).pack(pady=20)

    def format_time(self, seconds):
        """Преобразование секунд в формат ЧЧ:ММ:СС"""
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def update_clock(self):
        """
        Универсальный цикл обновления. 
        Использует разницу во времени (delta), чтобы избежать ускорения таймера.
        """
        now = time.time()

        if self.mode == "WORKOUT":
            # Считаем время разминки «вперед»
            elapsed = int(now - self.start_time)
            self.time_display.config(text=self.format_time(elapsed), fg="#27ae60")
            self.root.after(200, self.update_clock)

        elif self.mode == "COUNTDOWN":
            # Считаем время ожидания «назад» (от цели до текущего момента)
            remaining = int(self.target_time - now)
            if remaining > 0:
                self.time_display.config(text=self.format_time(remaining), fg="#e67e22")
                self.root.after(200, self.update_clock)
            else:
                self.time_display.config(text="00:00:00")
                self.trigger_alarm()

    def start_workout(self):
        """Включение режима разминки"""
        self.mode = "WORKOUT"
        self.start_time = time.time()
        self.btn_start.config(state=tk.DISABLED)
        self.btn_finish.config(state=tk.NORMAL)
        self.status_label.config(text="ИДЕТ РАЗМИНКА", fg="#27ae60")
        self.update_clock()

    def finish_workout(self):
        """Завершение разминки и запуск таймера на 2 часа"""
        duration = int(time.time() - self.start_time)
        self.cumulative_seconds += duration
        self.total_completed += 1

        self.mode = "COUNTDOWN"
        # Установка цели: текущее время + 7200 секунд (2 часа)
        self.target_time = time.time() + self.wait_duration
        self.btn_finish.config(state=tk.DISABLED)
        self.status_label.config(text="ДО СЛЕДУЮЩЕЙ РАЗМИНКИ:", fg="#34495e")
        self.update_clock()

    def trigger_alarm(self):
        """Событие при окончании 2-х часов"""
        if self.mode != "IDLE":
            self.mode = "IDLE"
            self.btn_start.config(state=tk.NORMAL)
            self.root.bell()
            messagebox.showinfo("Таймер", "Прошло 2 часа! Пора сделать перерыв и размяться.")

    def reset_system(self):
        """Сброс всех активных таймеров в исходное положение"""
        self.mode = "IDLE"
        self.time_display.config(text="02:00:00", fg="#2c3e50")
        self.status_label.config(text="Система сброшена", fg="black")
        self.btn_start.config(state=tk.NORMAL)
        self.btn_finish.config(state=tk.DISABLED)

    def show_stats(self):
        """Окно статистики сессии"""
        m, s = divmod(self.cumulative_seconds, 60)
        msg = f"Разминок выполнено: {self.total_completed}\nОбщее время упражнений: {m} мин. {s} сек."
        messagebox.showinfo("Ваша статистика", msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = HealthTracker(root)
    root.mainloop()
