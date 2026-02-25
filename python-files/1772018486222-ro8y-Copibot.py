import tkinter as tk
from tkinter import messagebox
import pyperclip

def paste_from_clipboard():
    # Получаем текст из буфера обмена
    tms_link = pyperclip.paste()
    # Очищаем поле ввода
    entry_tms.delete(0, tk.END)
    # Вставляем текст из буфера обмена в поле ввода
    entry_tms.insert(0, tms_link)

def on_test_requirements():
    # Получаем значение из поля ввода
    tms_link = entry_tms.get().strip()

    # Проверяем, что поле не пустое
    if not tms_link:
        messagebox.showwarning("Предупреждение", "Пожалуйста, введите ссылку ТМС.")
        return

    # Формируем итоговый текст
    result_text = f"Тестирование требований пройдено \nСсылка ТМС: {tms_link}"
    result_label.config(text="Требование копировано")

    # Копируем текст в буфер обмена
    pyperclip.copy(result_text)


def paste_from_my_data(button_text):
    if button_text == "Пройдено / Тираж / Разработка":
        pyperclip.copy("Тестирование пройдено в хр. Разработки\nБаза:\nПользователь:\nСценарий тестирования приложен к наряду")
        result_label.config(text=f"[{button_text}] - Шаблон скопирован")

    elif button_text == "Не пройдено / Тираж / Разработка":
        pyperclip.copy("Тестирование не пройдено в хр. Разработки\nБаза:\nПользователь:\nВоспроизведение:\n    Шаг 1: \n    Шаг 2: \n    Шаг 3: \n    Шаг 4: ")
        result_label.config(text=f"[{button_text}] - Шаблон скопирован")
    else:
        print("Неизвестная кнопка")

def toggle_topmost():
    current_state = root.wm_attributes("-topmost")
    root.wm_attributes("-topmost", not current_state)

# Создаём главное окно приложения
root = tk.Tk()
root.title("Копипастер")
root.geometry("500x170")

topmost_var = tk.BooleanVar()

# Создание чекбокса
checkbutton_toggle_topmost = tk.Checkbutton(root, text="Не скрывать окно", variable=topmost_var, command=toggle_topmost)
checkbutton_toggle_topmost.grid(row=0, column=0, sticky=tk.W)

# Создаём фрейм для ввода ссылки
input_frame = tk.Frame(root)
input_frame.grid(row=1, column=0, sticky=tk.W)

testing_treb_label = tk.Label(input_frame, text="ТЕСТИРОВАНИЕ ТРЕБОВАНИЙ")
testing_treb_label.grid(row=0, column=0, sticky=tk.N)

label_tms = tk.Label(input_frame, text="Ссылка ТМС:")
label_tms.grid(row=1, column=0, sticky=tk.W)

entry_tms = tk.Entry(input_frame, width=50)
entry_tms.grid(row=1, column=1, sticky=tk.W)

# Создаём фрейм для кнопок тестирования
test_frame = tk.Frame(root)
test_frame.grid(row=2, column=0, sticky=tk.W)

button_paste = tk.Button(test_frame, text="Вставить из буфера", command=paste_from_clipboard)
button_paste.grid(row=0, column=0, sticky=tk.W)

button_test = tk.Button(test_frame, text="Тестирование требований", command=on_test_requirements)
button_test.grid(row=0, column=1, padx=(5,0), sticky=tk.W)

# Создаём фрейм для кнопок результатов тестирования
result_frame = tk.Frame(root)
result_frame.grid(row=3, column=0, sticky=tk.W)

testing_prod_label = tk.Label(result_frame, text="ТЕСТИРОВАНИЕ ЗАДАЧ")
testing_prod_label.grid(row=0, column=0, sticky=tk.W)

button_test = tk.Button(result_frame, text="Пройдено / Тираж / Разработка",
                          command=lambda: paste_from_my_data("Пройдено / Тираж / Разработка"))
button_test.grid(row=1, column=0, sticky=tk.W)

button_test = tk.Button(result_frame, text="Не пройдено / Тираж / Разработка",
                               command=lambda: paste_from_my_data("Не пройдено / Тираж / Разработка"))
button_test.grid(row=1, column=1, sticky=tk.W)

info_frame = tk.Frame(root)
info_frame.grid(row=4, column=0, sticky=tk.W)

result_label = tk.Label(info_frame, text="")
result_label.grid(row=0, column=0, sticky=tk.W)

# Запускаем главный цикл обработки событий
root.mainloop()
