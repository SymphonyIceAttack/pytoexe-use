import tkinter as tk
import random
import math

class ClickerGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Just A Simple Clicker")
        self.root.geometry("500x250")
        self.root.resizable(False, False)
        self.click_count = 0
        self.escape_mode = False
        self.speed = 0.1               # начальная скорость перемещения (пикселей за шаг)
        self.animation_id = None     # ID текущей анимации for after_cancel
        self.target_x = None
        self.target_y = None

        # Интерфейс
        self.title_label = tk.Label(root, text="Just A Simple Clicker Game", font=("Arial", 25))
        self.title_label.place(x=250, y=30, anchor="center")

        self.counter_label = tk.Label(root, text=f"Кликов: {self.click_count}", font=("Arial", 14))
        self.counter_label.place(x=250, y=80, anchor="center")

        self.message_label = tk.Label(root, text="Нажми на кнопку!", font=("Arial", 12), fg="blue")
        self.message_label.place(x=250, y=120, anchor="center")

        self.btn = tk.Button(root, text="Click Me!", command=self.on_click, font=("Arial", 12))
        self.btn.place(x=200, y=170, width=100, height=40)

        # Событие наведения мыши (для режима убегания)
        self.btn.bind("<Enter>", self.on_mouse_enter)

        # Обновим реальные размеры кнопки для расчётов
        self.root.update_idletasks()
        self.btn_width = self.btn.winfo_width()
        self.btn_height = self.btn.winfo_height()

    def update_message(self):
        """Возвращает текст в зависимости от количества кликов"""
        if self.click_count >= 100:
            return "Поздравляю! Ты победил!"
        elif self.click_count >= 50:
            return "Убегающая кнопка! Лови её!"
        elif self.click_count >= 40:
            return "Ещё немного!"
        elif self.click_count >= 30:
            return "Почти!"
        elif self.click_count >= 20:
            return "Отлично!"
        elif self.click_count >= 10:
            return "Хорошо!"
        else:
            return "Молодец! Теперь попробуй ещё раз!"

    def on_click(self):
        """Обработчик нажатия кнопки"""
        if self.click_count >= 100:
            return

        self.click_count += 1
        self.counter_label.config(text=f"Кликов: {self.click_count}")

        # Ускорение после каждого клика
        self.speed += 0.1

        # Обновляем сообщение
        msg = self.update_message()
        self.message_label.config(text=msg)

        # Включаем режим убегания при достижении 50 кликов (и если ещё не включён)
        if 50 <= self.click_count < 100 and not self.escape_mode:
            self.escape_mode = True
            self.message_label.config(text="Кнопка убегает! Лови её!")

        # Проверка победы
        if self.click_count >= 100:
            self.game_won()

    def on_mouse_enter(self, _event):
        """При наведении мыши (если режим убегания активен) — задаём новую цель"""
        if self.escape_mode and self.click_count < 100:
            self.set_new_target()

    def set_new_target(self):
        """Генерирует новую случайную позицию для кнопки и запускает анимацию"""
        # Отменяем предыдущую анимацию, если она есть
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None

        # Определяем границы окна (с учётом размеров кнопки)
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        max_x = max(0, root_width - self.btn_width)
        max_y = max(0, root_height - self.btn_height)

        if max_x > 0 and max_y > 0:
            self.target_x = random.randint(0, max_x)
            self.target_y = random.randint(0, max_y)
            self.animate_move()

    def animate_move(self):
        """Плавно перемещает кнопку к целевой позиции с текущей скоростью"""
        if not self.escape_mode or self.click_count >= 100:
            return

        # Текущая позиция кнопки
        current_x = self.btn.winfo_x()
        current_y = self.btn.winfo_y()

        # Расстояние до цели
        dx = self.target_x - current_x
        dy = self.target_y - current_y
        distance = math.hypot(dx, dy)

        if distance < self.speed:
            # Достигли цели
            self.btn.place(x=self.target_x, y=self.target_y)
            self.animation_id = None
            return

        # Перемещаем на величину скорости в направлении цели
        step_x = int(dx / distance * self.speed)
        step_y = int(dy / distance * self.speed)

        new_x = current_x + step_x
        new_y = current_y + step_y

        # Корректировка, чтобы не перескочить целевую позицию
        if abs(dx) < abs(step_x):
            new_x = self.target_x
        if abs(dy) < abs(step_y):
            new_y = self.target_y

        self.btn.place(x=new_x, y=new_y)

        # Запускаем следующий шаг анимации через 10 мс
        self.animation_id = self.root.after(10, self.animate_move)

    def game_won(self):
        """Завершает игру: отключает убегание, выводит поздравление"""
        self.escape_mode = False
        self.btn.config(state="disabled", text="Победа!")
        self.message_label.config(text="🎉 Поздравляем! Вы прошли игру! 🎉", fg="green", font=("Arial", 14))
        self.btn.unbind("<Enter>")
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None

def main():
    root = tk.Tk()
    ClickerGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()