import tkinter as tk
import time
import threading
import sys
from datetime import datetime, timedelta

# ===== НАСТРОЙКИ =====
PASSWORD = "1267"
MAX_ATTEMPTS = 5
LOCK_TIME_SECONDS = 30

# ===== ПЕРЕМЕННЫЕ =====
attempts = 0
unlocked = False
locked_forever = False
end_time = datetime.now() + timedelta(seconds=LOCK_TIME_SECONDS)

# ===== ФУНКЦИИ =====
def check_password():
    global attempts, unlocked, locked_forever
    
    if unlocked or locked_forever:
        return
        
    attempts += 1
    remaining = MAX_ATTEMPTS - attempts
    attempts_label.config(text=f"Попыток: {attempts}/{MAX_ATTEMPTS}")
    
    if entry.get() == PASSWORD:
        unlocked = True
        status_label.config(text="✅ ДОСТУП РАЗРЕШЁН", fg="green")
        btn.config(state="disabled")
        entry.config(state="disabled")
        root.after(2000, exit_app)
    else:
        if remaining > 0:
            status_label.config(text=f"❌ Неверно! Осталось: {remaining}", fg="red")
            
            # Прикол: после 3 попыток TNT
            if attempts == 3:
                show_tnt()
                
        else:
            locked_forever = True
            status_label.config(text="💀 ПОПЫТКИ ИСЧЕРПАНЫ", fg="red")
            entry.config(state="disabled")
            btn.config(state="disabled")
            threading.Thread(target=show_bsod, daemon=True).start()
        entry.delete(0, tk.END)

def show_tnt():
    tnt = tk.Toplevel(root)
    tnt.title("💥")
    tnt.geometry("300x150")
    tnt.configure(bg='black')
    tk.Label(tnt, text="💥 TNT АКТИВИРОВАНА 💥", 
             font=("Arial", 16, "bold"), bg='black', fg='red').pack(expand=True)
    root.after(1500, tnt.destroy)

def show_bsod():
    time.sleep(1)
    root.after(0, root.destroy)
    time.sleep(0.5)
    
    bsod = tk.Tk()
    bsod.title("")
    bsod.geometry(f"{bsod.winfo_screenwidth()}x{bsod.winfo_screenheight()}+0+0")
    bsod.attributes('-topmost', True)
    bsod.overrideredirect(True)
    bsod.configure(bg='#0000aa')
    
    tk.Label(bsod, text=":(", font=("Segoe UI", 80),
             bg='#0000aa', fg='white').pack(pady=50)
    tk.Label(bsod, text="НОУТБУК ВЗОРВАН", font=("Arial", 30, "bold"),
             bg='#0000aa', fg='white').pack()
    tk.Label(bsod, text="Код: TNT_1267", font=("Arial", 20),
             bg='#0000aa', fg='white').pack(pady=20)
    
    bsod.mainloop()

def update_timer():
    global end_time, locked_forever
    if locked_forever or unlocked:
        return
        
    remaining = (end_time - datetime.now()).total_seconds()
    if remaining <= 0:
        timer_label.config(text="⏰ ВРЕМЯ ВЫШЛО", fg="red")
        status_label.config(text="💀 ДОСТУП ЗАБЛОКИРОВАН", fg="red")
        btn.config(state="disabled")
        entry.config(state="disabled")
        return
    mins = int(remaining // 60)
    secs = int(remaining % 60)
    timer_label.config(text=f"⏳ {mins:02d}:{secs:02d}")
    root.after(1000, update_timer)

def exit_app():
    root.destroy()
    sys.exit()

def disable_close():
    pass

# ===== ОКНО =====
root = tk.Tk()
root.title("⛏️ MINECRAFT LOCKER")
root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
root.attributes('-topmost', True)
root.overrideredirect(True)
root.protocol("WM_DELETE_WINDOW", disable_close)
root.configure(bg='#2d2d2d')

root.bind('<Alt-F4>', lambda e: "break")
root.bind('<Win>', lambda e: "break")

# Центральный блок
main_frame = tk.Frame(root, bg='#3a3a3a', bd=3, relief='ridge')
main_frame.place(relx=0.5, rely=0.5, anchor='center', width=500, height=400)

tk.Label(main_frame, text="⛏️ MINECRAFT LOCKER ⛏️",
         font=("Arial", 18, "bold"), bg='#3a3a3a', fg='#ffff55').pack(pady=20)

tk.Label(main_frame, text="СИСТЕМА ЗАБЛОКИРОВАНА",
         font=("Arial", 14, "bold"), bg='#3a3a3a', fg='#ff5555').pack()

timer_label = tk.Label(main_frame, text="⏳ 00:30",
                       font=("Courier New", 24, "bold"),
                       bg='#3a3a3a', fg='yellow')
timer_label.pack(pady=15)
entry = tk.Entry(main_frame, show="*", font=("Arial", 16), width=15,
                 bg='#1a1a1a', fg='white', justify='center')
entry.pack(pady=10)
entry.focus()

btn = tk.Button(main_frame, text="⛏️ РАЗБЛОКИРОВАТЬ",
                command=check_password,
                font=("Arial", 14, "bold"),
                bg='#5a5a5a', fg='white',
                padx=20, pady=5)
btn.pack(pady=5)

status_label = tk.Label(main_frame, text="", font=("Arial", 12),
                        bg='#3a3a3a', fg='white')
status_label.pack()

attempts_label = tk.Label(main_frame, text=f"Попыток: 0/{MAX_ATTEMPTS}",
                          font=("Arial", 10), bg='#3a3a3a', fg='#aaaaaa')
attempts_label.pack()

tk.Label(main_frame, text="Пароль: 1267 | TNT на 3-й ошибке",
         font=("Arial", 8), bg='#3a3a3a', fg='#888888').pack(side='bottom', pady=10)

root.bind('<Return>', lambda event: check_password())
update_timer()
root.mainloop()