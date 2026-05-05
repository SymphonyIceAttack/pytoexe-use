import tkinter as tk
from tkinter import messagebox
import random
import threading

# Список смешных сообщений
messages = [
    "💀 ВИРУС ОБНАРУЖЕН 💀\n(шучу, я просто окно)",
    "🍕 Ваша пицца заражена вирусом пепперони!",
    "🤖 Я ИИ-вирус. Ваш компьютер теперь будет писать стихи.",
    "🎵 Внимание! Вирус заразил динамики! Сейчас будет играть 'Barbie Girl'...",
    "💾 Форматирование мозга: 0%... ШУЧУ!",
    "🐱 На вашем компе завёлся котовирус. Мяу!",
    "📸 Доступ к веб-камере получен! Но я видел только кота.",
    "🌍 Ваш IP: 127.0.0.1 (ты сам себе хакер 😅)"
]

def create_window():
    win = tk.Toplevel()
    win.title("🔴 ВИРУС! 🔴")
    win.geometry(f"400x200+{random.randint(0, 800)}+{random.randint(0, 500)}")
    win.configure(bg="black")
    
    msg = random.choice(messages)
    label = tk.Label(win, text=msg, font=("Comic Sans MS", 12, "bold"),
                     fg="red", bg="black", wraplength=380)
    label.pack(expand=True, fill="both", padx=20, pady=30)
    
    def close_window():
        win.destroy()
        if not any(w.winfo_exists() for w in root.winfo_children() if w != root):
            root.quit()
    
    btn = tk.Button(win, text="❌ ЗАКРЫТЬ ВИРУС ❌", command=close_window,
                    bg="red", fg="white", font=("Arial", 10, "bold"))
    btn.pack(pady=10)
    
    # Мигаем
    def blink():
        if win.winfo_exists():
            current = win.title()
            win.title("⚠️ ШУТКА ⚠️" if current == "🔴 ВИРУС! 🔴" else "🔴 ВИРУС! 🔴")
            win.after(400, blink)
    blink()

# Главное окно
root = tk.Tk()
root.title("🤡 УПРАВЛЕНИЕ ВИРУСАМИ 🤡")
root.geometry("400x300")
root.configure(bg="#2b2b2b")

label = tk.Label(root, text="ДОБРО ПОЖАЛОВАТЬ В ЛАБОРАТОРИЮ ВИРУСОВ!",
                 font=("Arial", 14, "bold"), fg="#ff4444", bg="#2b2b2b")
label.pack(pady=20)

info = tk.Label(root, text="Каждый клик создаёт новый 'вирус'\n(который можно закрыть)", 
                font=("Arial", 10), fg="#888888", bg="#2b2b2b")
info.pack(pady=10)

def spawn_virus():
    create_window()
    spawn_btn.config(text=f"СОЗДАТЬ ВИРУС ({len(root.winfo_children()) - 1} шт.)")

spawn_btn = tk.Button(root, text="СОЗДАТЬ ВИРУС (0 шт.)", command=spawn_virus,
                      font=("Arial", 12, "bold"), bg="red", fg="white", 
                      padx=20, pady=10, cursor="hand2")
spawn_btn.pack(pady=20)

exit_btn = tk.Button(root, text="ЭВАКУАЦИЯ (закрыть всё)", command=root.quit,
                     font=("Arial", 10), bg="#555", fg="white", padx=15, pady=5)
exit_btn.pack(pady=10)

root.mainloop()
