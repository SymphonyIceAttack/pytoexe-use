import tkinter as tk
from tkinter import ttk, messagebox
import random
import math

class RandomCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("🧮 Калькулятор случайного умножения")
        self.root.geometry("450x500")
        self.root.resizable(False, False)
        
        # История вычислений
        self.history = []
        
        # Основной фрейм
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title = ttk.Label(main_frame, text="СЛУЧАЙНОЕ УМНОЖЕНИЕ", 
                          font=("Arial", 16, "bold"))
        title.pack(pady=(0, 20))
        
        # Поле ввода
        ttk.Label(main_frame, text="Введите число:", font=("Arial", 11)).pack(anchor=tk.W)
        self.entry = ttk.Entry(main_frame, font=("Arial", 14), width=20)
        self.entry.pack(pady=(5, 15))
        self.entry.bind("<Return>", lambda e: self.calculate())
        
        # Кнопка вычисления
        self.calc_btn = ttk.Button(main_frame, text="🔢 ВЫЧИСЛИТЬ", 
                                   command=self.calculate)
        self.calc_btn.pack(pady=(0, 20))
        
        # Рамка с результатом
        result_frame = ttk.LabelFrame(main_frame, text="Результат", padding="10")
        result_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.result_text = tk.StringVar(value="Ожидание ввода...")
        result_label = ttk.Label(result_frame, textvariable=self.result_text, 
                                 font=("Arial", 12), wraplength=380)
        result_label.pack()
        
        # История
        history_frame = ttk.LabelFrame(main_frame, text="История (последние 5)", padding="10")
        history_frame.pack(fill=tk.BOTH, expand=True)
        
        self.history_text = tk.Text(history_frame, height=6, font=("Courier", 10), 
                                    state=tk.DISABLED, wrap=tk.WORD)
        self.history_text.pack(fill=tk.BOTH, expand=True)
        
        # Кнопка очистки истории
        clear_btn = ttk.Button(main_frame, text="Очистить историю", 
                               command=self.clear_history)
        clear_btn.pack(pady=(10, 0))
        
        # Кнопка выхода
        exit_btn = ttk.Button(main_frame, text="Выйти", command=root.quit)
        exit_btn.pack(pady=(5, 0))
        
        # Фокус на поле ввода
        self.entry.focus()
    
    def calculate(self):
        try:
            number = float(self.entry.get())
        except ValueError:
            messagebox.showerror("Ошибка", "❌ Введите корректное число!")
            return
        
        # Генерация случайного числа
        random_factor = random.uniform(0.0, 2.0)
        result = number * random_factor
        rounded = math.floor(result + 0.5)
        
        # Формируем результат
        result_str = f"📊 {number} × {random_factor:.4f} = {result:.4f}\n🔢 Округлено: {rounded}"
        self.result_text.set(result_str)
        
        # Добавляем в историю
        history_entry = f"{number} × {random_factor:.4f} = {result:.4f} → {rounded}"
        self.history.append(history_entry)
        
        # Показываем последние 5 записей
        self.update_history()
        
        # Очищаем поле ввода
        self.entry.delete(0, tk.END)
        self.entry.focus()
    
    def update_history(self):
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete(1.0, tk.END)
        
        # Показываем последние 5 записей
        for entry in self.history[-5:]:
            self.history_text.insert(tk.END, f"• {entry}\n")
        
        self.history_text.config(state=tk.DISABLED)
    
    def clear_history(self):
        self.history = []
        self.update_history()
        self.result_text.set("История очищена")

# Запуск программы
if __name__ == "__main__":
    root = tk.Tk()
    app = RandomCalculator(root)
    root.mainloop()