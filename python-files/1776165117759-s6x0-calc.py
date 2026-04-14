import tkinter as tk
from datetime import datetime

class SimpleSumCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Сумматор 500/1000/2000")
        # Начальный размер окна (ширина x высота)
        self.root.geometry("500x450")
        # РАЗРЕШАЕМ изменять размер окна (True, True)
        self.root.resizable(True, True)

        self.total = 0
        self.add_mode = True  # True = сложение, False = вычитание

        # Метка с итоговой суммой (только число, крупный шрифт)
        self.label_total = tk.Label(root, text="0", font=("Arial", 28, "bold"))
        self.label_total.pack(pady=15)

        # Текстовое поле для лога (будет растягиваться при изменении окна)
        self.log_text = tk.Text(root, height=12, width=60, state="disabled", wrap=tk.WORD)
        # pack с expand=True и fill=BOTH позволяет полю занимать всё свободное место
        self.log_text.pack(pady=5, padx=10, expand=True, fill=tk.BOTH)

        # Рамка для кнопок сложения/вычитания
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        self.btn_500 = tk.Button(button_frame, text="+ 500", command=lambda: self.add(500), width=10, height=2, font=("Arial", 12))
        self.btn_500.pack(side=tk.LEFT, padx=5)

        self.btn_1000 = tk.Button(button_frame, text="+ 1000", command=lambda: self.add(1000), width=10, height=2, font=("Arial", 12))
        self.btn_1000.pack(side=tk.LEFT, padx=5)

        self.btn_2000 = tk.Button(button_frame, text="+ 2000", command=lambda: self.add(2000), width=10, height=2, font=("Arial", 12))
        self.btn_2000.pack(side=tk.LEFT, padx=5)

        # Кнопки управления (под кнопками сумм)
        self.exit_button = tk.Button(root, text="ВЫХОД УЧАСТНИКА", command=self.toggle_mode, width=22, height=1, font=("Arial", 10, "bold"), bg="lightcoral")
        self.exit_button.pack(pady=5)

        self.reset_button = tk.Button(root, text="Сбросить", command=self.reset, width=15, height=1, font=("Arial", 10), bg="lightgray")
        self.reset_button.pack(pady=5)

        # Приветствие при запуске
        self.log_message("ДАВАЙ СНОВА НА НЁМ ЗАРАБОТАЕМ", is_welcome=True)

    def log_message(self, msg, is_welcome=False):
        now = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state="normal")
        if is_welcome:
            self.log_text.insert(tk.END, f"\n{msg}\n\n")
        else:
            self.log_text.insert(tk.END, f"[{now}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def add(self, value):
        if self.add_mode:
            self.total += value
            sign = "+"
        else:
            self.total -= value
            sign = "-"

        self.label_total.config(text=str(self.total))

        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {sign}{value} → {self.total}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def toggle_mode(self):
        self.add_mode = not self.add_mode
        if self.add_mode:
            self.exit_button.config(text="ВЫХОД УЧАСТНИКА (ВЫКЛ)", bg="lightcoral")
            self.btn_500.config(text="+ 500")
            self.btn_1000.config(text="+ 1000")
            self.btn_2000.config(text="+ 2000")
            self.log_message("ДОБАВКА УЧАСТНИКА")
        else:
            self.exit_button.config(text="ВЫХОД УЧАСТНИКА (ВКЛ)", bg="salmon")
            self.btn_500.config(text="- 500")
            self.btn_1000.config(text="- 1000")
            self.btn_2000.config(text="- 2000")
            self.log_message("ВЫХОД УЧАСТНИКА")

    def reset(self):
        self.total = 0
        self.label_total.config(text="0")
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] ---- СБРОС ---- сумма обнулена\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleSumCalculator(root)
    root.mainloop()