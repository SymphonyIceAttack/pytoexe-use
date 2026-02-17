import tkinter as tk
from tkinter import ttk


def check(event=None):
    try:
        buy = float(entry1.get())
        sell = float(entry2.get())
        percent = ((sell - buy) / buy) * 100

        # Показываем процент
        percent_label.config(text=f"{percent:.1f}%")

        if percent >= 30:
            result.config(text="✅ ВЫГОДНО", fg="#27ae60")
        else:
            result.config(text="❌ НЕТ", fg="#c0392b")
    except:
        result.config(text="⚠️ ОШИБКА", fg="#e67e22")
        percent_label.config(text="")


def next_field(event):
    event.widget.tk_focusNext().focus()
    return "break"


# Окно
window = tk.Tk()
window.title("Проверка выгодности")
window.geometry("400x300")
window.configure(bg="#e6f3ff")
window.resizable(False, False)

# Заголовок
title = tk.Label(
    window,
    text="Калькулятор выгодности",
    font=("Arial", 16, "bold"),
    bg="#e6f3ff",
    fg="#2c3e50"
)
title.pack(pady=15)

# Рамка для первого поля (чтобы разместить процент)
frame1 = tk.Frame(window, bg="#e6f3ff")
frame1.pack(pady=5, padx=30, fill="x")

tk.Label(frame1, text="Цена покупки:", font=("Arial", 10), bg="#e6f3ff", fg="#34495e").pack(anchor="w")

entry_frame1 = tk.Frame(frame1, bg="#e6f3ff")
entry_frame1.pack(fill="x", expand=True)

entry1 = tk.Entry(
    entry_frame1,
    font=("Arial", 11),
    bd=2,
    relief="groove",
    highlightthickness=2,
    highlightcolor="#3498db",
    highlightbackground="#bdd8f0"
)
entry1.pack(side="left", fill="x", expand=True)
entry1.bind("<Return>", next_field)

# Рамка для второго поля
frame2 = tk.Frame(window, bg="#e6f3ff")
frame2.pack(pady=5, padx=30, fill="x")

tk.Label(frame2, text="Цена продажи:", font=("Arial", 10), bg="#e6f3ff", fg="#34495e").pack(anchor="w")

entry_frame2 = tk.Frame(frame2, bg="#e6f3ff")
entry_frame2.pack(fill="x", expand=True)

entry2 = tk.Entry(
    entry_frame2,
    font=("Arial", 11),
    bd=2,
    relief="groove",
    highlightthickness=2,
    highlightcolor="#3498db",
    highlightbackground="#bdd8f0"
)
entry2.pack(side="left", fill="x", expand=True)
entry2.bind("<Return>", check)

# Процент сбоку
percent_label = tk.Label(
    entry_frame2,
    text="",
    font=("Arial", 9),
    bg="#e6f3ff",
    fg="#7f8c8d",
    width=6
)
percent_label.pack(side="right", padx=(5, 0))

# Кнопка
btn = tk.Button(
    window,
    text="Проверить",
    font=("Arial", 11, "bold"),
    bg="#3498db",
    fg="white",
    activebackground="#2980b9",
    activeforeground="white",
    bd=0,
    padx=25,
    pady=8,
    cursor="hand2",
    command=check
)
btn.pack(pady=10)

# Результат
result = tk.Label(
    window,
    text="",
    font=("Arial", 14, "bold"),
    bg="#e6f3ff"
)
result.pack(pady=10)

window.mainloop()