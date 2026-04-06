import tkinter as tk
import random
import threading
import time
import winsound
import sys

PASSWORD = "141412"

def beep():
    for _ in range(3):
        winsound.Beep(1000, 200)
        time.sleep(0.1)

def show_password_screen():
    """Экран ввода пароля"""
    for widget in root.winfo_children():
        widget.destroy()
    
    root.configure(bg='black')
    
    label = tk.Label(root, text="ВВЕДИТЕ ПАРОЛЬ ДЛЯ РАЗБЛОКИРОВКИ", 
                    font=('Arial', 28, 'bold'), 
                    bg='black', fg='red')
    label.pack(expand=True, pady=50)
    
    entry = tk.Entry(root, font=('Arial', 24), show='*', justify='center', width=20)
    entry.pack(pady=20)
    entry.focus()
    
    error_label = tk.Label(root, text="", font=('Arial', 14), bg='black', fg='red')
    error_label.pack(pady=10)
    
    def check_password():
        if entry.get() == PASSWORD:
            root.destroy()
        else:
            error_label.config(text="НЕВЕРНЫЙ ПАРОЛЬ!")
            entry.delete(0, tk.END)
            winsound.Beep(500, 300)
    
    btn = tk.Button(root, text="РАЗБЛОКИРОВАТЬ", command=check_password,
                   font=('Arial', 16), bg='red', fg='white', width=20, height=2)
    btn.pack(pady=20)
    
    root.bind('<Return>', lambda event: check_password())

# Главное окно
root = tk.Tk()
root.title("⚠️")
root.attributes('-fullscreen', True)
root.configure(bg='black')

# Блокируем закрытие
def block():
    pass
root.protocol("WM_DELETE_WINDOW", block)
root.bind('<Escape>', lambda e: None)
root.bind('<Alt-F4>', lambda e: None)

# Страшная надпись
label = tk.Label(root, text="ВАС ЗАМЕТИЛИ", 
                font=('Arial', 52, 'bold'), 
                bg='black', fg='red')
label.pack(expand=True)

sub = tk.Label(root, text="Доступ к вашему компьютеру отслеживается", 
              font=('Arial', 18), 
              bg='black', fg='white')
sub.pack(pady=20)

# Мигание
def blink():
    colors = ['red', '#ff3333', '#cc0000', '#ff0000']
    while True:
        try:
            label.config(fg=random.choice(colors))
            time.sleep(0.2)
        except:
            break
threading.Thread(target=blink, daemon=True).start()

# Тряска окна
def shake():
    original_x = root.winfo_x()
    original_y = root.winfo_y()
    for _ in range(15):
        root.geometry(f"+{original_x + random.randint(-12, 12)}+{original_y + random.randint(-8, 8)}")
        time.sleep(0.03)
    root.geometry(f"+{original_x}+{original_y}")
threading.Thread(target=shake, daemon=True).start()

# Звук
beep()

# Через 3 секунды показываем экран с паролем
root.after(3000, show_password_screen)

root.mainloop()