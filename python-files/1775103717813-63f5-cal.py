import tkinter as tk
from tkcalendar import Calendar
from datetime import datetime

def show_selected_date():
    selected_date = cal.get_date()
    date_label.config(text=f"Выбрана дата: {selected_date}")

def update_time():
    current_time = datetime.now().strftime("%H:%M:%S")
    time_label.config(text=f"Текущее время: {current_time}")
    # Запускаем обновление снова через 1000 мс (1 секунда)
    root.after(1000, update_time)

# Создаём главное окно приложения
root = tk.Tk()
root.title("Календарь с часами")
root.geometry("400x550")

# Получаем текущую дату для установки в календаре
now = datetime.now()
current_year = now.year
current_month = now.month
current_day = now.day

# Создаём виджет календаря с текущей датой
cal = Calendar(
    root,
    selectmode='day',
    year=current_year,
    month=current_month,
    day=current_day,
    date_pattern='dd.mm.yyyy'
)
cal.pack(pady=20)

# Кнопка для получения выбранной даты
get_date_btn = tk.Button(
    root,
    text="Получить дату",
    command=show_selected_date
)
get_date_btn.pack(pady=10)

# Метка для отображения выбранной даты
date_label = tk.Label(root, text="", font=("Arial", 12))
date_label.pack(pady=10)

# Метка для отображения текущего времени
time_label = tk.Label(root, font=("Arial", 14, "bold"), fg="blue")
time_label.pack(pady=10)

# Запускаем первое обновление времени
update_time()

# Запускаем главный цикл приложения
root.mainloop()
