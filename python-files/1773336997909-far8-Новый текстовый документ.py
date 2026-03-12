import tkinter as tk
import random
import time
import threading

# ========== НАСТРОЙКИ ==========
PASSWORD = "12345GOG"
attempts = 0
MAX_ATTEMPTS = 3
running = True
# ================================

# Создаём окно
root = tk.Tk()
root.attributes('-fullscreen', True)
root.attributes('-topmost', True)
root.configure(bg='#0a2f1a')  # Тёмно-лесной фон
root.overrideredirect(True)

# Холст
canvas = tk.Canvas(root, width=root.winfo_screenwidth(), 
                  height=root.winfo_screenheight(), 
                  bg='#0a2f1a', highlightthickness=0)
canvas.pack()

# ========== ЛЕСНОЙ ИНТЕРФЕЙС ==========

def draw_forest_bg():
    """Лесной фон"""
    # Небо
    canvas.create_rectangle(0, 0, root.winfo_screenwidth(), 300, 
                          fill='#0a1a2a', outline='')
    
    # Деревья слева
    for i in range(3):
        x = 100 + i*150
        canvas.create_rectangle(x-20, 400, x+20, 700, fill='saddle brown')
        canvas.create_polygon(x-70, 400, x+70, 200, x, 400, fill='dark green')
    
    # Деревья справа
    for i in range(3):
        x = root.winfo_screenwidth() - 200 - i*150
        canvas.create_rectangle(x-20, 400, x+20, 700, fill='saddle brown')
        canvas.create_polygon(x-70, 400, x+70, 200, x, 400, fill='dark green')
    
    # Костёр внизу
    cx = root.winfo_screenwidth() // 2
    cy = root.winfo_screenheight() - 100
    canvas.create_rectangle(cx-40, cy-20, cx-10, cy+40, fill='saddle brown')
    canvas.create_rectangle(cx+10, cy-20, cx+40, cy+40, fill='saddle brown')
    
    # Огонь
    for i in range(3):
        canvas.create_oval(cx-20 + i*10, cy-50 - i*5, 
                         cx+10 + i*10, cy-20 - i*5, 
                         fill='orange', outline='red')

def draw_locker_ui():
    """Интерфейс блокировки"""
    cx = root.winfo_screenwidth() // 2
    cy = root.winfo_screenheight() // 2 - 50
    
    # Полупрозрачная панель
    canvas.create_rectangle(cx-250, cy-100, cx+250, cy+150, 
                          fill='#222222', outline='#555555', width=3)
    
    canvas.create_text(cx, cy-50, text="⚠️ СИСТЕМА ЗАБЛОКИРОВАНА ⚠️", 
                      fill='red', font=("Arial", 28, "bold"))
    
    canvas.create_text(cx, cy, text="Введите пароль для разблокировки:", 
                      fill='white', font=("Arial", 16))
    
    # Счётчик попыток
    canvas.create_text(cx, cy+80, text=f"Попыток: {attempts} / {MAX_ATTEMPTS}", 
                      fill='gray', font=("Arial", 14))

# ========== ПОЛЕ ВВОДА ==========

entry = tk.Entry(root, font=("Arial", 20), show="*", 
                width=15, justify='center', bg='#333333', fg='lime')
entry.place(relx=0.5, rely=0.55, anchor='center')
entry.focus()

error_label = tk.Label(root, text="", font=("Arial", 12), 
                      fg='yellow', bg='#222222')
error_label.place(relx=0.5, rely=0.65, anchor='center')

# ========== ФУНКЦИЯ BSOD ==========

def show_windows10_bsod():
    """Фейковый синий экран Windows 10"""
    canvas.delete("all")
    
    # Синий фон как в Windows 10
    canvas.configure(bg='#1073c7')
    
    # Грустный смайлик
    canvas.create_text(150, 200, text=":(", 
                      fill='white', font=("Segoe UI", 120))
    
    # Заголовок
    canvas.create_text(150, 350, text="Your PC ran into a problem and needs to restart.", 
                      fill='white', font=("Segoe UI", 24), anchor='w')
    
    canvas.create_text(150, 400, text="We're just collecting some error info, and then we'll restart for you.", 
                      fill='white', font=("Segoe UI", 16), anchor='w')
    
    # Прогресс
    canvas.create_text(150, 470, text="0% complete", 
                      fill='white', font=("Segoe UI", 16), anchor='w', tags="progress")
    
    # Код остановки (рандомный, как в настоящем BSOD)
    stop_code = f"PRANK_ERROR_0x{random.randint(1000, 9999):X}"
    canvas.create_text(150, 520, text=f"Stop code: {stop_code}", 
                      fill='white', font=("Segoe UI", 16), anchor='w')
    
    # Анимация прогресса
    for i in range(0, 101, 5):
        canvas.itemconfig("progress", text=f"{i}% complete")
        root.update()
        time.sleep(0.1)
    
    # Добавляем шутку
    canvas.create_text(root.winfo_screenwidth()//2, 650, 
                      text="😂 Just kidding! This is a prank. Press ESC to continue.", 
                      fill='white', font=("Segoe UI", 20))

# ========== ПРОВЕРКА ПАРОЛЯ ==========

def unlock(event=None):
    global attempts
    
    if entry.get() == PASSWORD:
        # Правильный пароль
        canvas.delete("all")
        canvas.configure(bg='#0a2f1a')
        draw_forest_bg()
        canvas.create_text(root.winfo_screenwidth()//2, root.winfo_screenheight()//2,
                          text="✅ ДОСТУП РАЗРЕШЕН! ✅", 
                          fill='lime', font=("Arial", 40, "bold"))
        canvas.create_text(root.winfo_screenwidth()//2, root.winfo_screenheight()//2 + 80,
                          text="Нажми ESC для выхода", 
                          fill='white', font=("Arial", 20))
        draw_locker_ui()
        error_label.config(text="")
        entry.place_forget()
    else:
        # Неправильный пароль
        attempts += 1
        error_label.config(text=f"❌ Неверный пароль! (Попытка {attempts}/{MAX_ATTEMPTS})")
        entry.delete(0, tk.END)
        
        # Обновляем счётчик на экране
        canvas.delete("counter")
        canvas.create_text(root.winfo_screenwidth()//2, root.winfo_screenheight()//2 + 100, 
                          text=f"Попыток: {attempts} / {MAX_ATTEMPTS}", 
                          fill='gray', font=("Arial", 14), tags="counter")
        
        # Если 3 попытки - BSOD
        if attempts >= MAX_ATTEMPTS:
            error_label.config(text="💀 ТРИ НЕВЕРНЫХ ПОПЫТКИ! 💀")
            root.update()
            time.sleep(1)
            show_windows10_bsod()

# ========== ВЫХОД ПО ESC ==========

def on_key(event):
    if event.keysym == 'Escape':
        global running
        running = False
        root.destroy()

# ========== АНИМАЦИЯ ==========

def snow_animation():
    """Падающий снег"""
    flakes = []
    for _ in range(30):
        flakes.append([random.randint(0, root.winfo_screenwidth()), 
                      random.randint(0, root.winfo_screenheight())])
    
    while running:
        canvas.delete("snow")
        for flake in flakes:
            flake[1] += 2
            if flake[1] > root.winfo_screenheight():
                flake[1] = 0
                flake[0] = random.randint(0, root.winfo_screenwidth())
            
            canvas.create_text(flake[0], flake[1], text='❄️', 
                             fill='white', font=("Arial", 12), tags="snow")
        root.update()
        time.sleep(0.05)

# ========== ЗАПУСК ==========

# Рисуем фон
draw_forest_bg()
draw_locker_ui()

# Запускаем анимацию снега
threading.Thread(target=snow_animation, daemon=True).start()

# Привязки клавиш
root.bind('<Return>', unlock)
root.bind('<Escape>', on_key)

# Подпись
signature = tk.Label(root, text="Коллин ❄️ 2024", 
                    fg='gray', bg='#0a2f1a', font=("Arial", 8))
signature.place(x=10, y=root.winfo_screenheight()-30)

root.mainloop()