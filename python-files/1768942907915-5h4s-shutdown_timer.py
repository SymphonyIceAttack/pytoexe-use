import os
import tkinter as tk
from tkinter import messagebox

def start_timer():
    try:
        minutes = int(entry.get())
        if minutes <= 0:
            raise ValueError
        seconds = minutes * 60
        os.system(f"shutdown -s -t {seconds}")
        lbl_status.config(text=f"Статус: Выключение через {minutes} мин.", fg="#ffcc00")
    except ValueError:
        messagebox.showerror("Ошибка", "Введите целое число минут больше нуля")

def cancel_timer():
    os.system("shutdown -a")
    lbl_status.config(text="Статус: Таймер отменен", fg="#00ff00")

# Настройка интерфейса в стиле "Dark Mode"
root = tk.Tk()
root.title("AI Power Off")
root.geometry("350x250")
root.configure(bg="#2d2d2d")

style = {"bg": "#2d2d2d", "fg": "white", "font": ("Arial", 10)}

tk.Label(root, text="ТАЙМЕР ВЫКЛЮЧЕНИЯ", font=("Arial", 14, "bold"), **style).pack(pady=15)
tk.Label(root, text="Через сколько минут выключить ПК?", **style).pack()

entry = tk.Entry(root, justify='center', font=("Arial", 12))
entry.pack(pady=10)

btn_start = tk.Button(root, text="ЗАПУСТИТЬ", command=start_timer, bg="#0078d4", fg="white", width=20, relief="flat")
btn_start.pack(pady=5)

btn_cancel = tk.Button(root, text="ОТМЕНИТЬ", command=cancel_timer, bg="#d83b01", fg="white", width=20, relief="flat")
btn_cancel.pack(pady=5)

lbl_status = tk.Label(root, text="Статус: Не запущен", **style)
lbl_status.pack(pady=10)

root.mainloop()