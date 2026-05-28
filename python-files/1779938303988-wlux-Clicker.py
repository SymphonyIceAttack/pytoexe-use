import tkinter as tk

class ClickerGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Кликер")
        self.root.geometry("300x250")
        self.root.resizable(False, False)

        # Счётчик кликов
        self.clicks = 0

        # Метка для отображения счёта
        self.label = tk.Label(root, text="Счёт: 0", font=("Arial", 24))
        self.label.pack(pady=20)

        # Кнопка для кликов
        self.click_button = tk.Button(root, text="Кликни меня!", font=("Arial", 14),
                                      command=self.increment, bg="lightblue", activebackground="deepskyblue")
        self.click_button.pack(pady=10)

        # Кнопка сброса
        self.reset_button = tk.Button(root, text="Сброс", font=("Arial", 12),
                                      command=self.reset, bg="lightgray")
        self.reset_button.pack(pady=5)

        # Небольшая подсказка
        self.info_label = tk.Label(root, text="Нажимай на кнопку, чтобы увеличить счёт", font=("Arial", 9))
        self.info_label.pack(side="bottom", pady=10)

    def increment(self):
        """Увеличивает счётчик на 1 и обновляет метку"""
        self.clicks += 1
        self.label.config(text=f"Счёт: {self.clicks}")

    def reset(self):
        """Сбрасывает счётчик в 0"""
        self.clicks = 0
        self.label.config(text="Счёт: 0")

if __name__ == "__main__":
    root = tk.Tk()
    game = ClickerGame(root)
    root.mainloop()