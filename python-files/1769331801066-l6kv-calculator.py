import tkinter as tk
import os
import subprocess
# Глобальные переменные для цветов
CURRENT_BG = "SystemButtonFace"  # стандартный фон окна
CURRENT_BTN_BG = "lightgray"      # стандартный фон кнопок

# Карта цветов
color_map = {
    'bg-red': "#ff0000",
    'bg-blue': "#0000ff",
    'bg-yellow': "#ffff00",
    'bg-purple': "#8000ff",
    'bt-red': "#ff0000",
    'bt-blue': "#0000ff",
    'bt-yellow': "#ffff00",
    'bt-purple': "#4000ff"
}

# Создаем главное окно
root = tk.Tk()
root.title("Калькулятор")
root.geometry("200x300")
root.resizable(False, False)

# Поле ввода
entry = tk.Entry(root, font=("Arial", 16), justify="right", bd=5)
entry.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="ew")

buttons = [
    '7', '8', '9', '/',
    '4', '5', '6', '*',
    '1', '2', '3', '-',
    'C', '0', '=', '+',
    'CE', '⚙', '', ''
]
def button_click(char):
    '''Обрабатываем нажатие кнопки'''
    current = entry.get()
    if char == 'C':
        entry.delete(len(current) - 1, tk.END)
    elif char == 'CE':
        entry.delete(0, tk.END)
    elif char == '=':
        try:
            result = eval(current)
            entry.delete(0, tk.END)
            entry.insert(0, str(result))
        except Exception:
            entry.delete(0, tk.END)
            entry.insert(0, "ОШИБКА")
    elif char == '⚙':
        open_settings()
    else:
        entry.insert(tk.END, char)

def apply_colors():
    """Применяет текущие цвета ко всем виджетам главного окна"""
    root.configure(bg=CURRENT_BG)
    # Обновляем цвета всех кнопок калькулятора
    for widget in root.winfo_children():
        if isinstance(widget, tk.Button):
            widget.configure(bg=CURRENT_BTN_BG)

def settings_click(btn_text):
    """Обработчик нажатия кнопок в окне настроек"""
    global CURRENT_BG, CURRENT_BTN_BG
    
    if btn_text in color_map:
        if btn_text.startswith('bg-'):
            CURRENT_BG = color_map[btn_text]
        elif btn_text.startswith('bt-'):
            CURRENT_BTN_BG = color_map[btn_text]
        
        apply_colors()  # Применяем изменения сразу

def open_settings():
    '''Открывает окно настроек'''
    settings = tk.Toplevel(root)
    settings.title("Настройки")
    settings.geometry("250x350")
    settings.resizable(False, False)
    
    # Пример кнопок в настройках
    settings_buttons = [
        'Фон', 'Кнопки',
        'bg-red', 'bt-red',
        'bg-blue', 'bt-blue',
        'bg-yellow', 'bt-yellow',
        'bg-purple', 'bt-purple',
    ]
    
    row = 1
    col = 0
    for btn_text in settings_buttons:
        btn = tk.Button(
            settings,
            text=btn_text,
            font=("Arial", 14),
            width=12,
            height=2,
            command=lambda text=btn_text: settings_click(text)
        )
        btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        # Визуальное отображение текущего цвета
        if btn_text in ['bg-red', 'bg-blue', 'bg-yellow', 'bg-purple']:
            btn.configure(bg=color_map[btn_text])
        elif btn_text in ['bt-red', 'bt-blue', 'bt-yellow', 'bt-purple']:
            btn.configure(bg=color_map[btn_text], fg="black")
        
        col += 1
        if col > 1:  # 2 колонки в настройках
            col = 0
            row += 1

    # Кнопка закрытия
    tk.Button(
        settings,
        text="Закрыть",
        font=("Arial", 14),
        command=settings.destroy
    ).grid(row=row+1, column=0, columnspan=2, pady=10, sticky="ew")
    
    # Настраиваем растяжение для окна настроек
    for i in range(2):
        settings.grid_columnconfigure(i, weight=1)
    for i in range(1, row + 2):  # Учитываем строку с кнопкой «Закрыть»
        settings.grid_rowconfigure(i, weight=1)
    
    # Привязка клавиши Esc к закрытию
    settings.bind("<Escape>", lambda event: settings.destroy())
def run_description():
    #Определяем местонахождение этого файла
    script_dir = os.path.dirname(os.path.abspath(__file__))
    #
    txt_path = os.path.join(script_dir, "Description.txt")
    #Запуск описания
    if os.name == "nt": #Windows
        subprocess.run(["notepad", txt_path])
    else:
        subprocess.run(["xbg-open" if os.name == 'posix' else "open", txt_path])




# Размещение кнопок калькулятора
row = 1
col = 0
for button in buttons:
    if button: 
        tk.Button(
            root,
            text=button,
            font=("Arial", 14),
            width=5,
            height=2,
            command=lambda x=button: button_click(x)
        ).grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
    col += 1
    if col > 3:
        col = 0
        row += 1
tk.Button(
        root,
        text="Описание",
        font=("Arial", 14),
        command=run_description
        ).grid(row=row+1, column=0, columnspan=4, pady=10, sticky="ew")

# Настраиваем растяжение для главного окна
for i in range(4):
    root.grid_columnconfigure(i, weight=1)
for i in range(1, 6):
    root.grid_rowconfigure(i, weight=1)

root.mainloop()
