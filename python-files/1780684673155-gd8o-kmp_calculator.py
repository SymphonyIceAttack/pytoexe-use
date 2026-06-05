import tkinter as tk
from tkinter import messagebox

def calculate_kmp(S, T, N, C, D):
    """Вычисляет КМП по формуле."""
    term1 = S / 3
    term2 = T / 3
    term3 = N / 3
    term4 = C / 3
    term5 = 1 - (D / 192.5)
    KMP = (term1 + term2 + term3 + term4 + term5) / 6
    return KMP

def interpret_kmp(KMP):
    """Интерпретирует значение КМП и возвращает цвет."""
    if 0.00 <= KMP <= 0.12:
        return "Норма", "blue"
    elif 0.13 <= KMP <= 0.35:
        return "Слабые изменения", "green"
    elif 0.36 <= KMP <= 0.60:
        return "Умеренные изменения", "orange"
    elif 0.61 <= KMP <= 1.00:
        return "Выраженные изменения", "red"
    else:
        return "Значение КМП выходит за пределы шкалы интерпретации", "black"

def calculate():
    """Обрабатывает нажатие кнопки 'Рассчитать'."""
    try:
        # Получаем значения из полей ввода
        S = float(entry_S.get())
        T = float(entry_T.get())
        N = float(entry_N.get())
        C = float(entry_C.get())
        D = float(entry_D.get())

        # Проверяем диапазоны для S, T, N, C
        if not (0 <= S <= 3):
            messagebox.showerror("Ошибка", "S должно быть в диапазоне от 0 до 3 баллов.")
            return
        if not (0 <= T <= 3):
            messagebox.showerror("Ошибка", "T должно быть в диапазоне от 0 до 3 баллов.")
            return
        if not (0 <= N <= 3):
            messagebox.showerror("Ошибка", "N должно быть в диапазоне от 0 до 3 баллов.")
            return
        if not (0 <= C <= 3):
            messagebox.showerror("Ошибка", "C должно быть в диапазоне от 0 до 3 баллов.")
            return

        # Расчёт КМП и интерпретация
        KMP = calculate_kmp(S, T, N, C, D)
        interpretation, color = interpret_kmp(KMP)

        # Вывод результата в поля на форме с цветовой подсветкой
        result_KMP.config(state="normal")
        result_KMP.delete(0, tk.END)
        result_KMP.insert(0, f"{KMP:.4f}")
        result_KMP.config(state="readonly", fg=color)

        result_interpretation.config(state="normal")
        result_interpretation.delete(0, tk.END)
        result_interpretation.insert(0, interpretation)
        result_interpretation.config(state="readonly", fg=color)

    except ValueError:
        messagebox.showerror("Ошибка", "Пожалуйста, введите корректные числовые значения.")

# Создание главного окна
root = tk.Tk()
root.title("Расчёт коэффициента поражения мозжечка (КМП)")
root.geometry("500x400")
root.resizable(False, False)  # Запрещаем изменение размера окна

# Заголовок
title_label = tk.Label(root, text="Расчёт коэффициента поражения мозжечка (КМП)",
                   font=("Arial", 14, "bold"))
title_label.grid(row=0, column=0, columnspan=2, pady=15)

# Поля ввода с подписями
tk.Label(root, text="S (сладжи и стазы, 0–3 балла):").grid(row=1, column=0, sticky="w", padx=20, pady=5)
entry_S = tk.Entry(root, width=15)
entry_S.grid(row=1, column=1, padx=20, pady=5)

tk.Label(root, text="T (нейроны с тигролизом, 0–3 балла):").grid(row=2, column=0, sticky="w", padx=20, pady=5)
entry_T = tk.Entry(root, width=15)
entry_T.grid(row=2, column=1, padx=20, pady=5)

tk.Label(root, text="N (нейроны с некрозом, 0–3 балла):").grid(row=3, column=0, sticky="w", padx=20, pady=5)
entry_N = tk.Entry(root, width=15)
entry_N.grid(row=3, column=1, padx=20, pady=5)

tk.Label(root, text="C (целлюлярные отёки, 0–3 балла):").grid(row=4, column=0, sticky="w", padx=20, pady=5)
entry_C = tk.Entry(root, width=15)
entry_C.grid(row=4, column=1, padx=20, pady=5)

tk.Label(root, text="D (расстояние между клетками Пуркинье, мкм):").grid(row=5, column=0, sticky="w", padx=20, pady=5)
entry_D = tk.Entry(root, width=15)
entry_D.grid(row=5, column=1, padx=20, pady=5)

# Кнопка расчёта
calculate_button = tk.Button(root, text="Рассчитать КМП", command=calculate,
                         bg="lightblue", font=("Arial", 10, "bold"))
calculate_button.grid(row=6, column=0, columnspan=2, pady=20)

# Поля для вывода результатов
tk.Label(root, text="КМП:").grid(row=7, column=0, sticky="w", padx=20, pady=5)
result_KMP = tk.Entry(root, state="readonly", width=20)
result_KMP.grid(row=7, column=1, padx=20, pady=5)

tk.Label(root, text="Интерпретация:").grid(row=8, column=0, sticky="w", padx=20, pady=5)
result_interpretation = tk.Entry(root, state="readonly", width=20)
result_interpretation.grid(row=8, column=1, padx=20, pady=5)

# Запуск главного цикла обработки событий
root.mainloop()
