import tkinter as tk
from tkinter import ttk, messagebox

class FootballPredictorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Калькулятор футбольных прогнозов")
        self.participants = []

        # Секция ввода реального результата
        real_score_frame = ttk.LabelFrame(self.root, text=" Финальный результат матча ", padding=10)
        real_score_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(real_score_frame, text="Итоговый счет:").grid(row=0, column=0, padx=5)
        self.real_score_a = ttk.Entry(real_score_frame, width=3)
        self.real_score_a.grid(row=0, column=1, padx=2)
        ttk.Label(real_score_frame, text=":").grid(row=0, column=2)
        self.real_score_b = ttk.Entry(real_score_frame, width=3)
        self.real_score_b.grid(row=0, column=3, padx=2)

        # Секция добавления прогноза участника
        input_frame = ttk.LabelFrame(self.root, text=" Добавить прогноз участника ", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(input_frame, text="Имя:").grid(row=0, column=0, padx=5)
        self.user_name = ttk.Entry(input_frame, width=15)
        self.user_name.grid(row=0, column=1, padx=5)

        ttk.Label(input_frame, text="Прогноз:").grid(row=0, column=2, padx=5)
        self.pred_score_a = ttk.Entry(input_frame, width=3)
        self.pred_score_a.grid(row=0, column=3, padx=2)
        ttk.Label(input_frame, text=":").grid(row=0, column=4)
        self.pred_score_b = ttk.Entry(input_frame, width=3)
        self.pred_score_b.grid(row=0, column=5, padx=2)

        self.add_btn = ttk.Button(input_frame, text="Добавить в список", command=self.add_participant)
        self.add_btn.grid(row=0, column=6, padx=10)

        # Таблица результатов
        self.tree = ttk.Treeview(self.root, columns=("Name", "Prediction", "Points"), show="headings")
        self.tree.heading("Name", text="Участник")
        self.tree.heading("Prediction", text="Прогноз")
        self.tree.heading("Points", text="Баллы")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Кнопки управления
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)

        self.calc_btn = ttk.Button(btn_frame, text="Рассчитать таблицу", command=self.calculate_results)
        self.calc_btn.pack(side="left", padx=5)

        self.clear_btn = ttk.Button(btn_frame, text="Очистить всё", command=self.clear_data)
        self.clear_btn.pack(side="left", padx=5)

    def add_participant(self):
        name = self.user_name.get()
        p_a = self.pred_score_a.get()
        p_b = self.pred_score_b.get()

        if not name or not p_a.isdigit() or not p_b.isdigit():
            messagebox.showwarning("Ошибка", "Заполните имя и прогноз корректно")
            return

        self.participants.append({
            "name": name,
            "pred_a": int(p_a),
            "pred_b": int(p_b),
            "points": 0
        })
        
        # Очистка полей ввода после добавления
        self.user_name.delete(0, tk.END)
        self.pred_score_a.delete(0, tk.END)
        self.pred_score_b.delete(0, tk.END)
        self.update_treeview()

    def calculate_points(self, r_a, r_b, p_a, p_b):
        # 1. Точный счет
        if r_a == p_a and r_b == p_b:
            return 3
        
        # 2. Разница мячей (но не ничья, если счет разный)
        if (r_a - r_b) == (p_a - p_b):
            return 2
        
        # 3. Исход (победа первой, победа второй или ничья)
        real_res = (r_a > r_b) - (r_a < r_b)
        pred_res = (p_a > p_b) - (p_a < p_b)
        if real_res == pred_res:
            return 1
            
        return 0

    def calculate_results(self):
        r_a_str = self.real_score_a.get()
        r_b_str = self.real_score_b.get()

        if not r_a_str.isdigit() or not r_b_str.isdigit():
            messagebox.showwarning("Ошибка", "Введите корректный финальный счет матча")
            return

        r_a, r_b = int(r_a_str), int(r_b_str)

        for p in self.participants:
            p["points"] = self.calculate_points(r_a, r_b, p["pred_a"], p["pred_b"])

        # Сортировка по убыванию очков
        self.participants.sort(key=lambda x: x["points"], reverse=True)
        self.update_treeview()

    def update_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for p in self.participants:
            pred_str = f"{p['pred_a']}:{p['pred_b']}"
            self.tree.insert("", "end", values=(p["name"], pred_str, p["points"]))

    def clear_data(self):
        self.participants = []
        self.update_treeview()
        self.real_score_a.delete(0, tk.END)
        self.real_score_b.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = FootballPredictorApp(root)
    root.mainloop()