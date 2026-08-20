import tkinter as tk

class ClickerGame:
    def __init__(self, root):
        self.root = root
        self.root.title("🖱️ КЛИКЕР ААА")
        self.root.geometry("400x500")
        self.root.configure(bg="#1a1a2e")

        self.count = 0
        self.multiplier = 1
        self.auto_clickers = 0
        self.auto_cost = 50
        self.mult_cost = 30

        # Заголовок
        tk.Label(root, text="🔥 КЛИКЕР ААА 🔥", font=("Arial", 24, "bold"),
                 bg="#1a1a2e", fg="#e94560").pack(pady=10)

        # Счёт
        self.label = tk.Label(root, text="0", font=("Arial", 60, "bold"),
                              bg="#1a1a2e", fg="#ffffff")
        self.label.pack(pady=20)

        # Кнопка клика
        self.click_btn = tk.Button(root, text="👆 КЛИК!", font=("Arial", 20, "bold"),
                                   bg="#e94560", fg="white", relief="raised", bd=4,
                                   activebackground="#c73652", command=self.click)
        self.click_btn.pack(pady=20, ipadx=20, ipady=10)

        # Рамка для улучшений
        frame = tk.Frame(root, bg="#1a1a2e")
        frame.pack(pady=20)

        self.auto_btn = tk.Button(frame, text=f"🤖 Автокликер ({self.auto_cost})",
                                  font=("Arial", 12), bg="#16213e", fg="white",
                                  command=self.buy_auto)
        self.auto_btn.grid(row=0, column=0, padx=10)

        self.mult_btn = tk.Button(frame, text=f"⚡ Множитель x{self.multiplier+1} ({self.mult_cost})",
                                  font=("Arial", 12), bg="#16213e", fg="white",
                                  command=self.buy_multiplier)
        self.mult_btn.grid(row=0, column=1, padx=10)

        # Кнопка сброса
        tk.Button(root, text="🔄 Сброс", font=("Arial", 10),
                  bg="#0f3460", fg="white", command=self.reset).pack(pady=10)

        # Авто-обновление
        self.update_auto()

    def click(self):
        self.count += self.multiplier
        self.update_display()

    def buy_auto(self):
        if self.count >= self.auto_cost:
            self.count -= self.auto_cost
            self.auto_clickers += 1
            self.auto_cost = int(self.auto_cost * 1.5)
            self.auto_btn.config(text=f"🤖 Автокликер ({self.auto_cost})")
            self.update_display()

    def buy_multiplier(self):
        if self.count >= self.mult_cost:
            self.count -= self.mult_cost
            self.multiplier += 1
            self.mult_cost = int(self.mult_cost * 1.8)
            self.mult_btn.config(text=f"⚡ Множитель x{self.multiplier+1} ({self.mult_cost})")
            self.update_display()

    def update_auto(self):
        if self.auto_clickers > 0:
            self.count += self.auto_clickers
            self.update_display()
        self.root.after(1000, self.update_auto)

    def update_display(self):
        self.label.config(text=str(self.count))

    def reset(self):
        self.count = 0
        self.multiplier = 1
        self.auto_clickers = 0
        self.auto_cost = 50
        self.mult_cost = 30
        self.auto_btn.config(text=f"🤖 Автокликер (50)")
        self.mult_btn.config(text=f"⚡ Множитель x2 (30)")
        self.update_display()

if __name__ == "__main__":
    root = tk.Tk()
    game = ClickerGame(root)
    root.mainloop()