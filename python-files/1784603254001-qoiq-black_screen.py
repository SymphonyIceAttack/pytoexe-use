import tkinter as tk
import keyboard
import threading

def close_program():
    root.quit()
    keyboard.unhook_all()

def key_handler(event):
    # Разрешаем только клавиши Alt (левая и правая)
    if event.name in ['alt', 'alt_l', 'alt_r']:
        return True   # не блокируем Alt
    # Если нажата P и зажат Alt – закрываем программу
    if event.name == 'p' and (keyboard.is_pressed('alt') or keyboard.is_pressed('alt_l') or keyboard.is_pressed('alt_r')):
        close_program()
        return False  # блокируем само нажатие P
    # Все остальные клавиши блокируем
    return False

def keyboard_block():
    keyboard.hook(key_handler, suppress=True)  # глобальный перехват
    while root.winfo_exists():
        pass

root = tk.Tk()
root.attributes('-fullscreen', True)
root.attributes('-topmost', True)
root.overrideredirect(True)
root.configure(bg='black')
root.config(cursor="none")

label = tk.Label(root, text="Windows заблокирован", font=("Arial", 64, "bold"),
                 fg="white", bg="black")
label.pack(expand=True)

# Запускаем блокировку в отдельном потоке
threading.Thread(target=keyboard_block, daemon=True).start()

# Автоматическое закрытие через 10 минут
root.after(600000, close_program)

root.mainloop()
