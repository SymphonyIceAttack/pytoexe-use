import tkinter as tk
from tkinter import ttk

# Ваши функции
def calc_coin(coin):
    return coin / 20.0

def messuary(mess, coin_mess):
    return mess / calc_coin(coin_mess)

def hip(d):
    return f" Размер чашки: {int(d)-2} - {int(d)} - {int(d)+2} Измерение: {d}"

def knee(l):
    if l < 68:
        return f" Размер ББ протеза: 3 - 5 Измерение: {l}"
    elif 67 < l < 72:
        return f" Размер ББ протеза: 5 - 7 Измерение: {l}"
    elif 71 < l < 76:
        return f" Размер ББ протеза: 7 - 9 Измерение: {l}"
    elif 75 < l < 80:
        return f" Размер ББ протеза: 9 - 11 Измерение: {l}"
    elif 79 < l < 84:
        return f" Размер ББ протеза: 11 - 13 Измерение: {l}"
    elif l > 83:
        return f" Размер ББ протеза: 13 Измерение: {l}"
    else:
        return " Размер ББ протеза: не определён"

# Обновление результата
def update_result(*args):
    try:
        mess = float(entry_mess.get())
        coin = float(entry_coin.get())
        real_size = round(messuary(mess, coin), 2)
        
        result_text = ""
        if hip_var.get():
            result_text += hip(real_size) + "\n"
        if knee_var.get():
            result_text += knee(real_size)
        
        if not result_text:
            result_text = "Выберите тип сустава"
        
        label_result.config(text=result_text.strip())
    except ValueError:
        label_result.config(text="Введите корректные числа")

# Создание окна
root = tk.Tk()
root.title("Расчёт размера протеза")
root.geometry("500x300")
root.configure(bg="#2e2e2e")  # темно-серый фон

# Стили
style = ttk.Style()
style.theme_use('default')
style.configure("TCheckbutton", background="#2e2e2e", foreground="white", font=("Arial", 10))
style.map("TCheckbutton", background=[('active', '#2e2e2e')])

# Поля ввода
tk.Label(root, text="Размер объекта на снимке:", bg="#2e2e2e", fg="white", font=("Arial", 10)).pack(pady=(20, 5))
entry_mess = tk.Entry(root, bg="white", fg="black", font=("Arial", 10), width=20)
entry_mess.pack()
entry_mess.bind("<KeyRelease>", update_result)

tk.Label(root, text="Размер монеты на снимке:", bg="#2e2e2e", fg="white", font=("Arial", 10)).pack(pady=(10, 5))
entry_coin = tk.Entry(root, bg="white", fg="black", font=("Arial", 10), width=20)
entry_coin.pack()
entry_coin.bind("<KeyRelease>", update_result)

# Чекбоксы
frame_check = tk.Frame(root, bg="#2e2e2e")
frame_check.pack(pady=15)

hip_var = tk.BooleanVar()
knee_var = tk.BooleanVar()

# Используем ttk.Checkbutton для лучшего стиля
check_hip = ttk.Checkbutton(frame_check, text="Тазобедренный сустав", variable=hip_var, command=update_result)
check_hip.pack(side="left", padx=10)

check_knee = ttk.Checkbutton(frame_check, text="Коленный сустав", variable=knee_var, command=update_result)
check_knee.pack(side="left", padx=10)

# Результат
label_result = tk.Label(root, text="Выберите тип сустава", bg="#2e2e2e", fg="white", font=("Arial", 11), justify="left")
label_result.pack(pady=20)

# Запуск
root.mainloop()