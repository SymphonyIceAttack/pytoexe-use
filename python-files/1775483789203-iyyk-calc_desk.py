import tkinter as tk
from tkinter import messagebox

def add_numbers():
    """Считывает числа из полей ввода и выводит их сумму."""
    try:
        # Получаем текст из полей и преобразуем в числа с плавающей точкой
        num1 = float(entry1.get())
        num2 = float(entry2.get())
        result = num1 + num2
        # Обновляем метку с результатом
        label_result.config(text=f"Результат: {result}")
    except ValueError:
        # Если введено не число – показываем предупреждение
        messagebox.showerror("Ошибка", "Пожалуйста, введите корректные числа!")

# Создаём главное окно
root = tk.Tk()
root.title("Калькулятор сложения")
root.geometry("300x200")
root.resizable(False, False)

# Поле для первого числа
tk.Label(root, text="Первое число:").pack(pady=5)
entry1 = tk.Entry(root)
entry1.pack(pady=5)

# Поле для второго числа
tk.Label(root, text="Второе число:").pack(pady=5)
entry2 = tk.Entry(root)
entry2.pack(pady=5)

# Кнопка "Сложить"
btn_add = tk.Button(root, text="Сложить", command=add_numbers)
btn_add.pack(pady=10)

# Метка для вывода результата
label_result = tk.Label(root, text="Результат: ")
label_result.pack(pady=10)

# Запуск главного цикла обработки событий
root.mainloop()
