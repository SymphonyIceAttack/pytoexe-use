import tkinter as tk
from tkinter import messagebox
import threading
import platform
import os

# ---------- Звуковое оповещение (кроссплатформенное) ----------
def play_alert_sound():
    """Проигрывает системный звук в зависимости от ОС."""
    system = platform.system()
    try:
        if system == "Windows":
            import winsound
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        elif system == "Darwin":  # macOS
            os.system("afplay /System/Library/Sounds/Ping.aiff")
        else:  # Linux и др.
            if os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga") != 0:
                print("\a")
    except Exception:
        print("\a")

# ---------- Полноэкранное уведомление (закрывается только клавишей Q) ----------
def show_fullscreen_alert():
    """Создаёт окно на весь экран, которое можно закрыть только нажатием Q."""
    alert = tk.Toplevel()
    alert.attributes('-fullscreen', True)
    alert.attributes('-topmost', True)
    alert.configure(bg='red')
    alert.title("Время вышло!")

    # Запрещаем закрытие через крестик, Alt+F4 и другие системные способы
    alert.protocol("WM_DELETE_WINDOW", lambda: None)

    # Текст предупреждения (без подсказки)
    label = tk.Label(
        alert,
        text="⏰ ВРЕМЯ ИСТЕКЛО!",
        font=("Arial", 60, "bold"),
        fg="white",
        bg="red"
    )
    label.pack(expand=True)

    # Закрытие только по нажатию клавиши Q
    def close_on_q(event):
        if event.char.lower() == 'q':
            alert.destroy()

    alert.bind("<Key>", close_on_q)

    # Принудительно переводим фокус на окно
    alert.focus_force()
    # Запускаем звук в отдельном потоке
    threading.Thread(target=play_alert_sound, daemon=True).start()

# ---------- Основной класс таймера ----------
class TimerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Таймер")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)

        self.remaining_seconds = 0
        self.running = False
        self.paused = False
        self.after_id = None

        # --- Виджеты установки времени ---
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)

        tk.Label(control_frame, text="Часы").grid(row=0, column=0)
        tk.Label(control_frame, text="Минуты").grid(row=0, column=1)
        tk.Label(control_frame, text="Секунды").grid(row=0, column=2)

        self.hours_var = tk.StringVar(value="0")
        self.minutes_var = tk.StringVar(value="0")
        self.seconds_var = tk.StringVar(value="0")

        self.hours_spin = tk.Spinbox(control_frame, from_=0, to=23, width=3,
                                     textvariable=self.hours_var, font=("Arial", 12))
        self.minutes_spin = tk.Spinbox(control_frame, from_=0, to=59, width=3,
                                       textvariable=self.minutes_var, font=("Arial", 12))
        self.seconds_spin = tk.Spinbox(control_frame, from_=0, to=59, width=3,
                                       textvariable=self.seconds_var, font=("Arial", 12))

        self.hours_spin.grid(row=1, column=0, padx=5)
        self.minutes_spin.grid(row=1, column=1, padx=5)
        self.seconds_spin.grid(row=1, column=2, padx=5)

        # --- Отображение оставшегося времени ---
        self.time_label = tk.Label(self.root, text="00:00:00", font=("Arial", 28, "bold"))
        self.time_label.pack(pady=10)

        # --- Кнопки управления ---
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        self.start_button = tk.Button(button_frame, text="Старт", command=self.start_timer, width=8)
        self.start_button.grid(row=0, column=0, padx=5)

        self.pause_button = tk.Button(button_frame, text="Пауза", command=self.pause_resume, width=8, state=tk.DISABLED)
        self.pause_button.grid(row=0, column=1, padx=5)

        self.reset_button = tk.Button(button_frame, text="Сброс", command=self.reset_timer, width=8, state=tk.DISABLED)
        self.reset_button.grid(row=0, column=2, padx=5)

        self.root.mainloop()

    # ---------- Логика таймера ----------
    def start_timer(self):
        if self.running:
            return

        try:
            h = int(self.hours_var.get())
            m = int(self.minutes_var.get())
            s = int(self.seconds_var.get())
        except ValueError:
            messagebox.showwarning("Ошибка", "Введите целые числа!")
            return

        total = h * 3600 + m * 60 + s
        if total <= 0:
            messagebox.showwarning("Ошибка", "Задайте время больше нуля!")
            return

        self.remaining_seconds = total
        self.running = True
        self.paused = False

        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL, text="Пауза")
        self.reset_button.config(state=tk.NORMAL)

        self._countdown()

    def _countdown(self):
        if not self.running or self.paused:
            return

        if self.remaining_seconds > 0:
            self._update_display()
            self.remaining_seconds -= 1
            self.after_id = self.root.after(1000, self._countdown)
        else:
            self._update_display()
            self._timer_finished()

    def pause_resume(self):
        if not self.running:
            return

        if self.paused:
            self.paused = False
            self.pause_button.config(text="Пауза")
            self._countdown()
        else:
            self.paused = True
            self.pause_button.config(text="Продолжить")
            if self.after_id:
                self.root.after_cancel(self.after_id)
                self.after_id = None

    def reset_timer(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        self.running = False
        self.paused = False
        self.remaining_seconds = 0
        self._update_display()

        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="Пауза")
        self.reset_button.config(state=tk.DISABLED)

    def _timer_finished(self):
        self.running = False
        self.paused = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED, text="Пауза")
        self.reset_button.config(state=tk.NORMAL)

        show_fullscreen_alert()

    def _update_display(self):
        h = self.remaining_seconds // 3600
        m = (self.remaining_seconds % 3600) // 60
        s = self.remaining_seconds % 60
        self.time_label.config(text=f"{h:02d}:{m:02d}:{s:02d}")

# ---------- Точка входа ----------
if __name__ == "__main__":
    app = TimerApp()