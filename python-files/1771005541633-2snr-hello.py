import tkinter as tk
from tkinter import messagebox
import sys

# Пароль для разблокировки (можно изменить)
PASSWORD = "1234"

# Секретная комбинация для выхода: Ctrl+Shift+Q
def on_key(event):
    if event.state == 12 and event.keysym == 'q':  # 12 = Control+Shift
        root.destroy()

def check_password():
    if entry.get() == PASSWORD:
        root.destroy()
    else:
        messagebox.showerror("Ошибка", "Неверный пароль!")

# Создаём окно
root = tk.Tk()
root.title("")  # Без заголовка

# На весь экран
root.attributes('-fullscreen', True)
root.attributes('-topmost', True)  # Поверх всех окон

# Убираем рамку (на всякий случай, хотя fullscreen уже убирает)
root.overrideredirect(True)

# Перехватываем попытку закрыть окно (Alt+F4)
def disable_close():
    pass  # Ничего не делаем
root.protocol("WM_DELETE_WINDOW", disable_close)

# Обработчик клавиш
root.bind('<Key>', on_key)

# Настраиваем внешний вид
root.configure(bg='black')

# Сообщение
label = tk.Label(root, text="⚠ ВНИМАНИЕ! ⚠\n\nВаш компьютер заблокирован.\nВведите пароль для разблокировки:",
                 fg='red', bg='black', font=('Arial', 24, 'bold'))
label.pack(pady=50)

# Поле ввода пароля
entry = tk.Entry(root, show='*', font=('Arial', 18), width=20)
entry.pack(pady=20)

# Кнопка разблокировки
button = tk.Button(root, text="Разблокировать", font=('Arial', 16),
                   command=check_password)
button.pack(pady=10)

# Подсказка (необязательно)
hint = tk.Label(root, text="Подсказка: спроси у друга :)",
                fg='gray', bg='black', font=('Arial', 12))
hint.pack(side='bottom', pady=20)

# Запуск
root.mainloop()