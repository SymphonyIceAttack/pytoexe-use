import tkinter as tk
from tkinter import messagebox

# Функция для проверки пароля
def check_password():
    if password_entry.get() == "1234":
        root.destroy()  # Закрываем программу
    else:
        messagebox.showerror("ACCESS DENIED", "НЕВЕРНЫЙ ПАРОЛЬ! УДАЛЕНИЕ ПРОДОЛЖАЕТСЯ...")
        password_entry.delete(0, tk.END)

# Функция, которая срабатывает при попытке закрыть окно (Alt+F4)
def disable_event():
    messagebox.showwarning("WARNING", "SYSTEM IS LOCKED BY SKITTQQ TEAM")

# Создаем главное окно
root = tk.Tk()
root.title("System Failure")
root.attributes("-fullscreen", True) # На весь экран
root.attributes("-topmost", True)    # Поверх всех окон
root.configure(bg="black")           # Черный фон

# Обработка попытки закрытия окна
root.protocol("WM_DELETE_WINDOW", disable_event)

# Основной текст (пугающий)
main_label = tk.Label(root, text="YOUR COMPUTER IS HACKED BY SKITTQQ TEAM", 
                      fg="red", bg="black", font=("Courier", 35, "bold"))
main_label.pack(pady=50)

# Текст имитации удаления
log_label = tk.Label(root, text="Deleting C:/Windows/System32...\nTransferring personal data to remote server...", 
                     fg="white", bg="black", font=("Courier", 18))
log_label.pack(pady=20)

# Фрейм для ввода пароля
frame = tk.Frame(root, bg="black")
frame.pack(side="bottom", pady=100)

tk.Label(frame, text="ENTER DECRYPTION KEY:", fg="lime", bg="black", font=("Courier", 14)).pack()

password_entry = tk.Entry(frame, show="*", font=("Arial", 20), justify="center")
password_entry.pack(pady=10)

btn = tk.Button(frame, text="UNLOCK SYSTEM", command=check_password, 
                bg="red", fg="white", font=("Arial", 12, "bold"), width=20)
btn.pack()

# Дополнительная защита: запрещаем сворачивание (для Windows)
root.bind("<FocusOut>", lambda e: root.focus_force())

root.mainloop()