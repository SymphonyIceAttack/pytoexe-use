import tkinter as tk
from tkinter import messagebox
import winsound
import time
import threading
import random

def fake_delete_mta():
    messages = [
        "Обнаружен MTA San Andreas 1.6...",
        "Удаляю файлы игры...",
        "777 Override ABU — доступ алды пизда",
        "Удаляю GTA San Andreas...",
        "Стираю сохранения...",
        "Удаляю моды и скрипты...",
        "Очистка реестра...",
        "777 Override ABU — операция завершена",
        "MTA San Andreas успешно уничтожен 🔥"
    ]
    
    for msg in messages:
        try:
            winsound.Beep(700, 400)
            messagebox.showerror("777 Override ABU", msg)
            time.sleep(0.8)
        except:
            pass

def spam_windows():
    while True:
        try:
            # Звук
            winsound.Beep(random.randint(600, 1200), 150)
            
            # Основное окно
            messagebox.showerror(
                title="777 Override ABU",
                message="777 Override ABU\n\nMTA San Andreas 1.6\nбыл уничтожен."
            )
        except:
            pass
        time.sleep(0.15)

if __name__ == "__main__":
    # Запускаем фейковое удаление один раз
    threading.Thread(target=fake_delete_mta, daemon=True).start()
    
    # Запускаем бесконечный спам окон
    threading.Thread(target=spam_windows, daemon=True).start()
    
    # Главное скрытое окно
    root = tk.Tk()
    root.withdraw()
    root.mainloop()